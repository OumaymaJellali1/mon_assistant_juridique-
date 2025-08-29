import uuid
import os
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import logging
import re

from api.models import ChatRequest, ChatResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from assistants.legal_chatbot import AdvancedLegalChatbot
    logger.info("Import de AdvancedLegalChatbot réussi")
except ImportError as e:
    logger.error(f"Erreur d'import de AdvancedLegalChatbot: {e}")
    AdvancedLegalChatbot = None
    raise ValueError(f"AdvancedLegalChatbot non disponible, vérifiez votre configuration {e}")

class ChatBridgeService:
    """
    Service bridge qui fait le pont entre l'API FastAPI et votre agent AdvancedLegalChatbot
    """
    
    def __init__(self):
        self.agent = None
        self.active_conversations: Dict[str, Dict] = {}
        self.documents_base_path = "./data/pdfs"
        self.documents_endpoint_base = "/api/v1/documents"
        
        self._health_cache = None
        self._health_cache_expiry = None
        self._health_cache_duration = timedelta(minutes=5)  
        
        self._metrics_cache = None
        self._metrics_cache_expiry = None
        self._metrics_cache_duration = timedelta(minutes=2)  
        
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialise l'agent de manière sécurisée avec gestion des dépendances"""
        try:
            if AdvancedLegalChatbot is None:
                raise ImportError("AdvancedLegalChatbot non disponible")
            self._check_environment()
            logger.info("Initialisation de l'agent AdvancedLegalChatbot...")
            self.agent = AdvancedLegalChatbot()
            logger.info("Agent initialisé avec succès")
            self._invalidate_health_cache()
        except ImportError as e:
            logger.error(f"Erreur d'import de l'agent: {str(e)}")
            logger.info("L'agent ne sera pas disponible, mais l'API peut fonctionner en mode dégradé")
            self.agent = None
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de l'agent: {str(e)}")
            logger.info("Tentative de fonctionnement en mode dégradé")
            self.agent = None
    
    def _check_environment(self):
        """Vérifie que l'environnement est correctement configuré"""
        required_folders = [
            "backend/data/pdfs",
            "backend/data/chunks", 
            "backend/data/embeddings",
            "backend/cache"
        ]
        for folder in required_folders:
            if not os.path.exists(folder):
                logger.warning(f"Dossier manquant: {folder}")
        try:
            from backend.src.config import GEMINI_API_KEY, QDRANT_HOST, QDRANT_PORT
            if not GEMINI_API_KEY or GEMINI_API_KEY == "":
                logger.warning("GEMINI_API_KEY non configurée")
            else:
                logger.info("Configuration GEMINI détectée")
            logger.info(f"Configuration Qdrant: {QDRANT_HOST}:{QDRANT_PORT}")
        except ImportError as e:
            logger.warning(f"Impossible de vérifier la configuration: {e}")

    def _invalidate_health_cache(self):
        """Invalide le cache de health check"""
        self._health_cache = None
        self._health_cache_expiry = None
    
    def _invalidate_metrics_cache(self):
        """Invalide le cache de métriques"""
        self._metrics_cache = None
        self._metrics_cache_expiry = None

    def _is_cache_valid(self, cache_expiry):
        """Vérifie si le cache est encore valide"""
        return cache_expiry is not None and datetime.now() < cache_expiry

    def _normalize_doc_name(self, doc_name: str) -> str:
        if not doc_name:
            return ""
        doc_name = re.sub(r"^\\+", "", doc_name)
        doc_name = re.sub(r"^\d+\.\s*", "", doc_name)
        doc_name = doc_name.replace("\\", "_").replace("/", "_")
        return doc_name.strip()

    def _validate_document_exists(self, doc_name: str) -> bool:
        normalized_name = self._normalize_doc_name(doc_name)
        full_path = os.path.join(self.documents_base_path, normalized_name)
        full_path = full_path.replace("\\", "/")  
        exists = os.path.isfile(full_path)
        if not exists:
            logger.warning(f"Document non trouvé: {full_path}")
        return exists

    def _extract_sources_from_response(self, response_text: str) -> tuple[str, List[Dict]]:
     """
    Extraction universelle de sources - fonctionne avec toutes les langues
    Se base sur les patterns structurels plutôt que sur des mots-clés spécifiques
    """
     sources = []
     seen_sources = set()

     pdf_with_numbers_pattern = r'([a-zA-Z0-9_.-]+\.pdf)[^a-zA-Z0-9]*?(\d+(?:\s*[,;]\s*\d+)*)'
    
     matches = re.finditer(pdf_with_numbers_pattern, response_text, re.IGNORECASE)
     for match in matches:
        doc_name = match.group(1).strip()
        numbers_str = match.group(2).strip()
        
        page_numbers = re.findall(r'\d+', numbers_str)
        
        for page_str in page_numbers:
            doc_name_normalized = self._normalize_doc_name(doc_name)
            page_num = int(page_str) if page_str.isdigit() else None
            source_key = f"{doc_name_normalized}_{page_num}"
            
            if source_key not in seen_sources:
                source_obj = {
                    "title": self._format_document_title(doc_name_normalized),
                    "document_name": doc_name_normalized,
                    "page": page_num,
                    "source": doc_name_normalized,
                    "url": f"{self.documents_endpoint_base}/{doc_name_normalized}" + (f"#page={page_num}" if page_num else ""),
                    "file_exists": self._validate_document_exists(doc_name_normalized)
                }
                sources.append(source_obj)
                seen_sources.add(source_key)

     pdf_alone_pattern = r'([a-zA-Z0-9_.-]+\.pdf)(?![^a-zA-Z0-9]*?\d)'
    
     matches = re.finditer(pdf_alone_pattern, response_text, re.IGNORECASE)
     for match in matches:
        doc_name = match.group(1).strip()
        doc_name_normalized = self._normalize_doc_name(doc_name)
        source_key = f"{doc_name_normalized}_None"
        
        if source_key not in seen_sources:
            source_obj = {
                "title": self._format_document_title(doc_name_normalized),
                "document_name": doc_name_normalized,
                "page": None,
                "source": doc_name_normalized,
                "url": f"{self.documents_endpoint_base}/{doc_name_normalized}",
                "file_exists": self._validate_document_exists(doc_name_normalized)
            }
            sources.append(source_obj)
            seen_sources.add(source_key)

     structured_section_pattern = r'\*\*[^:*]+:\*\*(.*?)(?:\n\*\*|$)'
    
     matches = re.finditer(structured_section_pattern, response_text, re.DOTALL | re.IGNORECASE)
     for match in matches:
        section_content = match.group(1).strip()
        
        if '.pdf' in section_content.lower():
            
            section_matches = re.finditer(pdf_with_numbers_pattern, section_content, re.IGNORECASE)
            for section_match in section_matches:
                doc_name = section_match.group(1).strip()
                numbers_str = section_match.group(2).strip()
                page_numbers = re.findall(r'\d+', numbers_str)
                
                for page_str in page_numbers:
                    doc_name_normalized = self._normalize_doc_name(doc_name)
                    page_num = int(page_str) if page_str.isdigit() else None
                    source_key = f"{doc_name_normalized}_{page_num}"
                    
                    if source_key not in seen_sources:
                        source_obj = {
                            "title": self._format_document_title(doc_name_normalized),
                            "document_name": doc_name_normalized,
                            "page": page_num,
                            "source": doc_name_normalized,
                            "url": f"{self.documents_endpoint_base}/{doc_name_normalized}" + (f"#page={page_num}" if page_num else ""),
                            "file_exists": self._validate_document_exists(doc_name_normalized)
                        }
                        sources.append(source_obj)
                        seen_sources.add(source_key)
            
            section_alone_matches = re.finditer(pdf_alone_pattern, section_content, re.IGNORECASE)
            for section_alone_match in section_alone_matches:
                doc_name = section_alone_match.group(1).strip()
                doc_name_normalized = self._normalize_doc_name(doc_name)
                source_key = f"{doc_name_normalized}_None"
                
                if source_key not in seen_sources:
                    source_obj = {
                        "title": self._format_document_title(doc_name_normalized),
                        "document_name": doc_name_normalized,
                        "page": None,
                        "source": doc_name_normalized,
                        "url": f"{self.documents_endpoint_base}/{doc_name_normalized}",
                        "file_exists": self._validate_document_exists(doc_name_normalized)
                    }
                    sources.append(source_obj)
                    seen_sources.add(source_key)

     bullet_lines = re.findall(r'^[\s]*[*\-•]\s*(.+\.pdf.*)$', response_text, re.MULTILINE | re.IGNORECASE)
     for line in bullet_lines:
        line_pdf_matches = re.finditer(pdf_with_numbers_pattern, line, re.IGNORECASE)
        for line_match in line_pdf_matches:
            doc_name = line_match.group(1).strip()
            numbers_str = line_match.group(2).strip()
            page_numbers = re.findall(r'\d+', numbers_str)
            
            for page_str in page_numbers:
                doc_name_normalized = self._normalize_doc_name(doc_name)
                page_num = int(page_str) if page_str.isdigit() else None
                source_key = f"{doc_name_normalized}_{page_num}"
                
                if source_key not in seen_sources:
                    source_obj = {
                        "title": self._format_document_title(doc_name_normalized),
                        "document_name": doc_name_normalized,
                        "page": page_num,
                        "source": doc_name_normalized,
                        "url": f"{self.documents_endpoint_base}/{doc_name_normalized}" + (f"#page={page_num}" if page_num else ""),
                        "file_exists": self._validate_document_exists(doc_name_normalized)
                    }
                    sources.append(source_obj)
                    seen_sources.add(source_key)

     clean_text = response_text
     sections_to_remove = re.findall(r'(\*\*[^:*]+:\*\*.*?)(?:\n\*\*|$)', response_text, re.DOTALL | re.IGNORECASE)
    
     for section in sections_to_remove:
        if '.pdf' in section.lower():
            clean_text = clean_text.replace(section, '').strip()

     lines = clean_text.split('\n')
     cleaned_lines = []
     for line in lines:
        if re.match(r'^\s*[*\-•]\s*.*\.pdf.*$', line, re.IGNORECASE):
            continue  
        cleaned_lines.append(line)
     clean_text = '\n'.join(cleaned_lines).strip()

     clean_text = re.sub(r'\n\s*\n\s*\n', '\n\n', clean_text)

     logger.info(f"Sources extraites (universelles): {len(sources)} sources uniques")
    
     return clean_text, sources

    def _format_document_title(self, doc_name: str) -> str:
        """Formate le nom du document en un titre lisible"""
        title = doc_name.replace('.pdf', '').replace('_', ' ')
        return ' '.join(word.capitalize() for word in title.split())
    
    async def process_chat_message(self, request: ChatRequest) -> ChatResponse:
        """Traite un message de chat en utilisant votre agent existant"""
        try:
            if not self.agent:
                return self._create_fallback_response(request, "Agent temporairement indisponible. Veuillez réessayer plus tard.")
            
            conversation_id = request.conversation_id or str(uuid.uuid4())
            config = {"configurable": {"thread_id": conversation_id, "user_id": request.user_id or "anonymous"}}
            result = await self.agent.process_question_async(question=request.message, config=config)
            raw_answer = result.get("answer", "")
            clean_answer, extracted_sources = self._extract_sources_from_response(raw_answer)
            self._update_conversation_history(conversation_id, request.message, clean_answer, request.user_id)
            
            self._invalidate_metrics_cache()
            
            return ChatResponse(message=clean_answer, conversation_id=conversation_id, timestamp=datetime.now(), sources=extracted_sources)
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {str(e)}")
            return self._create_error_response(request, e)

    def _create_fallback_response(self, request: ChatRequest, message: str) -> ChatResponse:
        return ChatResponse(
            message=f"{message}\n\nVotre question: '{request.message}' a été enregistrée et sera traitée dès que possible.",
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            timestamp=datetime.now(),
            sources=[]
        )

    def _create_error_response(self, request: ChatRequest, error: Exception) -> ChatResponse:
        error_message = (
            "Désolé, une erreur s'est produite lors du traitement de votre demande. "
            "Notre équipe technique a été notifiée. Veuillez réessayer dans quelques instants."
        )
        if os.getenv("ENVIRONMENT", "production").lower() == "development":
            error_message += f"\n\nDétail technique: {str(error)}"
        return ChatResponse(message=error_message, conversation_id=request.conversation_id or str(uuid.uuid4()), timestamp=datetime.now(), sources=[])

    def _update_conversation_history(self, conversation_id: str, user_message: str, assistant_response: str, user_id: Optional[str] = None):
        if conversation_id not in self.active_conversations:
            self.active_conversations[conversation_id] = {"created_at": datetime.now(), "user_id": user_id, "messages": []}
        self.active_conversations[conversation_id]["messages"].extend([
            {"role": "user", "content": user_message, "timestamp": datetime.now()},
            {"role": "assistant", "content": assistant_response, "timestamp": datetime.now()}
        ])

    def get_conversation_history(self, conversation_id: str) -> Optional[Dict]:
        return self.active_conversations.get(conversation_id)

    def get_agent_metrics(self) -> Dict:
        """Retourne les métriques avec cache"""
        if self._is_cache_valid(self._metrics_cache_expiry):
            logger.debug("Utilisation du cache pour les métriques")
            return self._metrics_cache
        
        logger.info("Génération de nouvelles métriques (cache expiré)")
        
        if not self.agent:
            metrics = {"error": "Agent non disponible"}
        else:
            metrics = {
                "conversations_count": len(self.active_conversations),
                "agent_history_length": len(self.agent.conversation_history) if hasattr(self.agent, 'conversation_history') else 0,
                "performance_metrics": (self.agent.performance_metrics[-10:] 
                                     if hasattr(self.agent, 'performance_metrics') and self.agent.performance_metrics 
                                     else [])
            }
        
        self._metrics_cache = metrics
        self._metrics_cache_expiry = datetime.now() + self._metrics_cache_duration
        
        return metrics

    def health_check(self) -> Dict[str, str]:
        """Health check avec cache pour éviter les appels répétés"""
        if self._is_cache_valid(self._health_cache_expiry):
            logger.debug("Utilisation du cache pour le health check")
            return self._health_cache
        
        logger.info("Génération d'un nouveau health check (cache expiré)")
        
        base_info = {
            "timestamp": datetime.now().isoformat(),
            "service": "chat_bridge",
            "conversations_active": len(self.active_conversations),
            "documents_path": self.documents_base_path,
            "documents_endpoint": self.documents_endpoint_base
        }
        
        if self.agent:
            base_info.update({
                "status": "healthy", 
                "agent_status": "active", 
                "agent_type": "AdvancedLegalChatbot"
            })
        else:
            base_info.update({
                "status": "degraded", 
                "agent_status": "inactive", 
                "message": "Agent indisponible, fonctionnement en mode dégradé"
            })
        
        self._health_cache = base_info
        self._health_cache_expiry = datetime.now() + self._health_cache_duration
        
        return base_info

    def get_available_documents(self) -> List[str]:
        if not os.path.exists(self.documents_base_path): 
            return []
        return [f for f in os.listdir(self.documents_base_path) if f.endswith('.pdf')]

    def force_health_refresh(self):
        """Force le rafraîchissement du cache de health check (utile pour les tests)"""
        self._invalidate_health_cache()
        self._invalidate_metrics_cache()
        logger.info("Cache de health check et métriques invalidé manuellement")

chat_bridge = ChatBridgeService()