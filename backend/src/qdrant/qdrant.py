import os
import re
import time
import json
import fitz  
import uuid
from tqdm import tqdm
from typing import List, Dict, Tuple, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.storage import LocalFileStore
from langchain.embeddings import CacheBackedEmbeddings
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from config import settings
from prompts.legal_prompts import get_title_prompt, get_split_prompt
from langchain_core.documents import Document
from qdrant.qdrant_client import QdrantClientWrapper
from qdrant_client.http.models import PointStruct

class CacheManager:
    """Gère le cache des titres générés"""
    
    def __init__(self, cache_file: str = settings.CACHE_FILE):
        self.cache_file = cache_file
        self._cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def save_cache(self) -> None:
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, ensure_ascii=False, indent=2)
    
    def get(self, key: str) -> Optional[str]:
        return self._cache.get(key)
    
    def set(self, key: str, value: str) -> None:
        self._cache[key] = value
        self.save_cache()


class TextProcessor:
    """Classe pour le nettoyage et le traitement du texte"""
    
    @staticmethod
    def truncate_text(text: str, max_chars: int = settings.MAX_TITLE_CHARS) -> str:
        return text[:max_chars] + " [...]" if len(text) > max_chars else text
    
    @staticmethod
    def remove_isolated_numbers(text: str) -> str:
        lines = text.splitlines()
        return "\n".join([line for line in lines if not re.match(r"^\s*\d{1,3}\s*$", line)])
    
    @staticmethod
    def merge_fragmented_lines(text: str) -> str:
        lines = text.splitlines()
        merged_lines = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.upper() == "ARTICLE" and i + 1 < len(lines):
                next_line = lines[i+1].strip()
                if re.match(r"^(PREMIER|\d+)", next_line, re.IGNORECASE):
                    merged_lines.append(f"ARTICLE {next_line}")
                    i += 2
                    continue
            if re.match(r"^TITRE\s*$", line, re.IGNORECASE) and i + 1 < len(lines):
                next_line = lines[i+1].strip()
                merged_lines.append(f"TITRE {next_line}")
                i += 2
                continue
            if re.match(r"^CHAPITRE\s*$", line, re.IGNORECASE) and i + 1 < len(lines):
                next_line = lines[i+1].strip()
                merged_lines.append(f"CHAPITRE {next_line}")
                i += 2
                continue
            merged_lines.append(line)
            i += 1
        return "\n".join(merged_lines)
    
    @staticmethod
    def join_short_lines(text: str, max_len: int = 40) -> str:
        lines = text.splitlines()
        new_lines = []
        buffer = ""
        for line in lines:
            line = line.strip()
            if not line:
                if buffer:
                    new_lines.append(buffer)
                    buffer = ""
                continue
            if len(line) < max_len:
                if buffer:
                    buffer += " " + line
                else:
                    buffer = line
            else:
                if buffer:
                    new_lines.append(buffer)
                    buffer = ""
                new_lines.append(line)
        if buffer:
            new_lines.append(buffer)
        return "\n".join(new_lines)
    
    def clean_text(self, text: str) -> str:
        """Pipeline complet de nettoyage du texte"""
        text = self.remove_isolated_numbers(text)
        text = self.merge_fragmented_lines(text)
        text = self.join_short_lines(text)
        return text


class DocumentSplitter:
    """Classe pour découper les documents en chunks"""
    
    @staticmethod
    def split_by_articles(text: str) -> List[Tuple[str, str]]:
        pattern_article = r"(ART(?:\.|ICLE)?\s+(?:[0-9]{1,3}|[IVXLCDM]+|PREMIER))\s*:"
        pattern_titre = r"(TITRE\s+[IVXLCDM0-9\-]+[\s:]+[^\n]*)"
        pattern = re.compile(f"{pattern_titre}|{pattern_article}", re.IGNORECASE)
        matches = list(pattern.finditer(text))
        
        if not matches:
            return [("TEXTE COMPLET", text)]
        
        chunks = []
        i = 0
        while i < len(matches):
            current_match = matches[i]
            current_str = current_match.group()
            start = current_match.start()
            
            if re.match(pattern_titre, current_str, re.IGNORECASE):
                if i + 1 < len(matches) and re.match(pattern_article, matches[i + 1].group(), re.IGNORECASE):
                    end = matches[i + 2].start() if i + 2 < len(matches) else len(text)
                    chunk_text = text[start:end].strip()
                    chunks.append(("ARTICLE", chunk_text))
                    i += 2
                else:
                    i += 1
            elif re.match(pattern_article, current_str, re.IGNORECASE):
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                chunk_text = text[start:end].strip()
                chunks.append(("ARTICLE", chunk_text))
                i += 1
            else:
                i += 1
        return chunks


class HierarchyExtractor:
    """Classe pour extraire la hiérarchie des documents juridiques"""
    
    @staticmethod
    def is_title_continuation(line: str) -> bool:
        return bool(re.match(r"^[A-Z0-9\s\-,:;()\u00c0-\u017f]+$", line.strip()))
    
    def extract_hierarchy_from_text(self, text_chunk: str, last_hierarchy: Dict) -> Tuple[Dict, str]:
        hierarchy = {}
        lines = text_chunk.splitlines()
        cleaned_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            if re.match(r"^LOI\s+(N°|n°)?\s*\d{4}[\-\u2013]\d+", line) and line.isupper():
                loi_lines = [line]
                j = i + 1
                while j < len(lines) and self.is_title_continuation(lines[j]):
                    loi_lines.append(lines[j].strip())
                    j += 1
                hierarchy["Loi"] = " ".join(loi_lines).strip()
                for k in ["Chapitre", "Titre", "Section", "Sous-section", "Article"]:
                    last_hierarchy[k] = "Non spécifié"
                i = j
                continue
            
            elif re.match(r"^TITRE\s+(?:[IVXLCDM]+|\d+)(?:\s*[\-:]|$)", line, re.IGNORECASE) and line.isupper():
                title_lines = [line]
                j = i + 1
                while j < len(lines) and self.is_title_continuation(lines[j]):
                    next_line = lines[j].strip()
                    if re.match(r"^(CHAPITRE|ARTICLE|SECTION|SOUS-SECTION)", next_line, re.IGNORECASE):
                        break
                    title_lines.append(next_line)
                    j += 1
                hierarchy["Titre"] = " ".join(title_lines).strip()
                i = j
                continue
            
            elif re.match(r"^CHAPITRE\s+[^\n:]+", line, re.IGNORECASE):
                chapitre_lines = [line]
                j = i + 1
                while j < len(lines) and self.is_title_continuation(lines[j]):
                    next_line = lines[j].strip()
                    if re.match(r"^(ARTICLE|SECTION|SOUS-SECTION)", next_line, re.IGNORECASE):
                        break
                    chapitre_lines.append(next_line)
                    j += 1
                hierarchy["Chapitre"] = " ".join(chapitre_lines).strip()
                i = j
                continue
            
            matched = False
            for key, pattern in {
                "Section": r"^SECTION\s+[^\n:]+",
                "Sous-section": r"^SOUS-SECTION\s+[^\n:]+",
                "Article": r"^(ARTICLE\s+(?:PREMIER|\d+)|ART\.?\s+\d+)",
            }.items():
                if re.match(pattern, line, re.IGNORECASE):
                    hierarchy[key] = line
                    matched = True
                    break
            
            if not matched:
                cleaned_lines.append(line)
            i += 1
        
        for key in ["Loi", "Chapitre", "Titre", "Section", "Sous-section", "Article"]:
            if key not in hierarchy:
                hierarchy[key] = last_hierarchy.get(key, "Non spécifié")
        
        cleaned_text = "\n".join(cleaned_lines).strip()
        return hierarchy, cleaned_text


class GemmaManager:
    """Classe pour gérer les interactions avec Gemma/Gemini"""
    def __init__(self):
      self.cache_manager = CacheManager()
      self.langchain_llm = ChatGoogleGenerativeAI(
        model=settings.GEMMA_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.3,
        convert_system_message_to_human=True
     )

    
    @staticmethod
    def clean_title(raw_title: str) -> str:
        lines = raw_title.strip().split("\n")
        return lines[0].strip().strip('"').strip("'")
    
    def generate_title(self, text_chunk: str) -> str:
        key = str(hash(text_chunk))
        cached_title = self.cache_manager.get(key)
        if cached_title:
            return cached_title
        
        prompt = get_title_prompt(TextProcessor.truncate_text(text_chunk))
        
        for attempt in range(1, settings.MAX_RETRIES + 1):
            try:
                response = self.model.generate_content(prompt)
                time.sleep(settings.SLEEP_BETWEEN_CALLS)
                title = self.clean_title(response.text.strip())
                self.cache_manager.set(key, title)
                return title
            except Exception as e:
                print(f"[ERREUR GEMMA titre] tentative {attempt}: {e}")
                time.sleep(5)
        return "Titre non généré"
    
    def split_with_fallback(self, text: str) -> List[str]:
        prompt = get_split_prompt(text)
        for attempt in range(1, settings.MAX_RETRIES + 1):
            try:
                response = self.model.generate_content(prompt)
                time.sleep(settings.SLEEP_BETWEEN_CALLS)
                return [s.strip() for s in response.text.split("=== Section ===") if s.strip()]
            except Exception as e:
                print(f"[ERREUR découpage Gemini] tentative {attempt}: {e}")
                time.sleep(5)
        return [text]


class PDFProcessor:
    """Classe principale pour traiter les PDFs"""
    
    def __init__(self):
        self.text_processor = TextProcessor()
        self.splitter = DocumentSplitter()
        self.hierarchy_extractor = HierarchyExtractor()
        self.gemma_manager = GemmaManager()
    
    @staticmethod
    def is_annexe_page(text: str) -> bool:
        return bool(re.search(r"^\s*ANNEXE\s+[\w\d\-]+", text, re.IGNORECASE | re.MULTILINE))
    
    @staticmethod
    def is_tableau_page(text: str) -> bool:
        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
        if len(lines) < 5:
            return False
        tab_lines = sum(1 for line in lines if any(sep in line for sep in ['|', '\t', ';', ',']) and re.search(r'\d', line))
        return tab_lines / len(lines) >= 0.4
    
    def process_single_pdf(self, pdf_path: str) -> None:
        pdf_name = os.path.basename(pdf_path)
        pdf_base = os.path.splitext(pdf_name)[0]
        output_file = os.path.join(settings.CHUNKS_FOLDER, f"chunks_{pdf_base}.txt")
        
        print(f"\nTraitement du fichier : {pdf_name}")
        doc = fitz.open(pdf_path)
        
        full_text = ""
        page_offsets = []
        current_offset = 0
        ignored_pages = []
        table_annex_chunks = []
        
        # Extraction du texte
        for i, page in enumerate(doc):
            page_text = page.get_text()
            page_offsets.append(current_offset)
            
            if "sommaire" in page_text.lower() or "table des matières" in page_text.lower():
                print(f"[Ignoré] Page {i + 1} détectée comme sommaire.")
                ignored_pages.append(i)
                continue
            
            if re.findall(r"(ARTICLE\s+\d+.*?\.{3,}\s*\d+)", page_text, re.IGNORECASE):
                print(f"[Ignoré] Page {i + 1} détectée comme sommaire d'articles.")
                ignored_pages.append(i)
                continue
            
            if self.is_annexe_page(page_text):
                print(f"[Annexe détectée] Page {i + 1}")
                table_annex_chunks.append(("Annexe détectée", i + 1, page_text))
                continue
            
            if self.is_tableau_page(page_text):
                print(f"[Tableau détecté] Page {i + 1}")
                table_annex_chunks.append(("Tableau détecté", i + 1, page_text))
                continue
            
            full_text += page_text
            current_offset += len(page_text)
        
        if not full_text.strip():
            print("Aucun contenu exploitable trouvé.")
            return
        
        # Traitement des chunks
        self._process_chunks(full_text, pdf_name, page_offsets, output_file, table_annex_chunks)
        print(f"Fichier sauvegardé : {output_file}")
    
    def _process_chunks(self, full_text: str, pdf_name: str, page_offsets: List[int], 
                       output_file: str, table_annex_chunks: List) -> None:
        chunk_id = 1
        last_hierarchy = {}
        
        with open(output_file, "w", encoding="utf-8") as f:
            chunks = self.splitter.split_by_articles(full_text)
            if len(chunks) <= 1:
                chunks = self.gemma_manager.split_with_fallback(full_text)
            
            for content in (c if isinstance(c, str) else c[1] for c in chunks):
                start = full_text.find(content)
                page_num = next(
                    (i + 1 for i in range(len(page_offsets)) 
                     if page_offsets[i] <= start < (page_offsets[i + 1] if i + 1 < len(page_offsets) else float("inf"))),
                    -1
                )
                
                cleaned = self.text_processor.clean_text(content)
                hierarchy, cleaned = self.hierarchy_extractor.extract_hierarchy_from_text(cleaned, last_hierarchy)
                last_hierarchy = hierarchy.copy()
                
                title = self.gemma_manager.generate_title(cleaned)
                
                f.write(f"=== CHUNK {chunk_id} | PDF: {pdf_name} | Page: {page_num} | Titre_Gemma: {title} ===\n")
                
                for key in ["Loi", "Chapitre", "Titre", "Section", "Sous-section", "Article"]:
                    f.write(f"{key} : {hierarchy.get(key, 'Non spécifié')}\n")
                f.write(cleaned + "\n\n")
                chunk_id += 1
            
            # Traitement des annexes et tableaux
            for page_num, content in table_annex_chunks:
                cleaned = self.text_processor.clean_text(content)
                title = self.gemma_manager.generate_title(cleaned)
                
                f.write(f"=== CHUNK {chunk_id} | PDF: {pdf_name} | Page: {page_num} | Titre_Gemma: {title} ===\n")
                f.write("Loi : Non spécifié\nChapitre : Non spécifié\nTitre : Non spécifié\nSection : Non spécifié\nSous-section : Non spécifié\nArticle : Non spécifié\n")
                f.write(cleaned + "\n\n")
                chunk_id += 1
    
    def process_all_pdfs(self) -> None:
        for pdf in os.listdir(settings.PDF_FOLDER):
            if pdf.lower().endswith(".pdf"):
                self.process_single_pdf(os.path.join(settings.PDF_FOLDER, pdf))


class EmbeddingGenerator:
    """Classe pour générer les embeddings """
    
    def __init__(self, model_name: str = None):
        if model_name is None:
            model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        
        fs = LocalFileStore("./cache/embeddings")
        self.cached_embedder = CacheBackedEmbeddings.from_bytes_store(
            self.model,
            fs,
            namespace=self.model_name                 
        )

    @staticmethod
    def parse_chunks_file(file_path: str) -> List[Tuple[Dict, str]]:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        chunks = []
        for chunk in content.split("=== CHUNK "):
            if not chunk.strip():
                continue
            lines = chunk.strip().splitlines()
            metadata = {
                "chunk_id": lines[0].split(" | ")[0].strip(),
                "pdf": lines[0].split("PDF:")[1].split("|")[0].strip(),
                "page": lines[0].split("Page:")[1].split("|")[0].strip(),
                "titre_gemma": lines[0].split("Titre_Gemma:")[1].strip()
            }
            for line in lines[1:7]:
                if ':' in line:
                    key, val = line.split(":", 1)
                    metadata[key.strip()] = val.strip()
            text = "\n".join(lines[7:]).strip()
            chunks.append((metadata, text))
        return chunks
    
    def generate_embeddings(self) -> None:
        all_vectors = []
        
        for file in os.listdir(settings.CHUNKS_FOLDER):
            if file.startswith("chunks_") and file.endswith(".txt"):
                file_path = os.path.join(settings.CHUNKS_FOLDER, file)
                print(f"Traitement de : {file}")
                chunks = self.parse_chunks_file(file_path)
                
                for metadata, text in tqdm(chunks):
                    vector = self.model.encode(text)
                    all_vectors.append({
                        "metadata": metadata,
                        "embedding": vector.tolist(),
                        "text": text  
                    })
        
        os.makedirs(settings.EMBEDDINGS_FOLDER, exist_ok=True)
        with open(settings.EMBEDDINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(all_vectors, f, ensure_ascii=False, indent=2)


class QdrantIndexer:
    """CORRECTION PRINCIPALE ICI - Stocker le texte complet"""
    
    def __init__(self, host: str = settings.QDRANT_HOST, port: int = settings.QDRANT_PORT):
        self.client = QdrantClient(host=host, port=port)
    
    def create_or_reset_collection(self, collection_name: str = settings.QDRANT_COLLECTION) -> None:
        self.client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
    
    def upload_vectors(self, collection_name: str = settings.QDRANT_COLLECTION) -> None:
        with open(settings.EMBEDDINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    
        points = []
        for item in data:
            point_id = str(uuid.uuid4())
            vector = item["embedding"]
            
            payload = {
                **item["metadata"],
                "content": item["text"],  
                "page": int(item["metadata"]["page"]) if item["metadata"]["page"].isdigit() else item["metadata"]["page"]
            }
            
            points.append(PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            ))
    
        self.client.upsert(collection_name=collection_name, points=points)
        print(f"Indexation réussie de {len(points)} documents avec texte complet")


class DocumentRetriever:
    
    def __init__(self, qdrant_client: QdrantClientWrapper, embedder: SentenceTransformer):
        self.qdrant_client = qdrant_client
        self.embedder = embedder

    def retrieve_documents(self, question: str, top_k: int = 20) -> List[Document]:
        if isinstance(question, list):
            question = " ".join(question)
        
        try:
            embedded_question = self.embedder.encode(question).tolist()
            
            results = self.qdrant_client.query(embedded_question, top_k=top_k)
            
            documents = []
            seen_content_hashes = set()
            
            print(f"Nombre de résultats Qdrant: {len(results)}")
            
            for i, hit in enumerate(results):
                payload = hit.payload
                score = hit.score if hasattr(hit, 'score') else 0.0
                
                content = payload.get("content", "").strip()
                
                if not content or len(content) < 10:
                    print(f"Document {i} ignoré: contenu vide ou trop court")
                    continue
                
                content_hash = hash(content[:200])
                if content_hash in seen_content_hashes:
                    print(f"Document {i} ignoré: contenu dupliqué")
                    continue
                seen_content_hashes.add(content_hash)
                
                doc = Document(
                    page_content=content,  
                    metadata={
                        "source": payload.get("pdf", "unknown"),
                        "page": payload.get("page", "N/A"),
                        "chunk_id": payload.get("chunk_id", "unknown"),
                        "titre_gemma": payload.get("titre_gemma", ""),
                        "score": score,
                        "rank": i + 1,
                        # Toutes les autres métadonnées sauf content
                        **{k: v for k, v in payload.items() 
                           if k not in ["content", "pdf", "page", "chunk_id", "titre_gemma"]}
                    }
                )
                
                documents.append(doc)
                print(f" Document {i+1} ajouté - Score: {score:.3f}, Longueur: {len(content)} caractères")

            print(f"Total final: {len(documents)} documents récupérés")
            return documents
            
        except Exception as e:
            print(f" Erreur de recherche: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    
    
        