import uuid
import os
from typing import Dict, Optional, List
from datetime import datetime
import logging
from pathlib import Path
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
     print(f"full path {full_path}")
     exists = os.path.isfile(full_path)
     if not exists:
        logger.warning(f"Document non trouvé: {full_path}")
     return exists


    def _extract_sources_from_response(self, response_text: str) -> tuple[str, List[Dict]]:
     """
     Extrait les sources du texte de réponse et retourne le texte nettoyé + les sources formatées
     """
     sources = []
     seen_sources = set()

     source_pattern = r'(\w+.*?\.pdf),?\s*Page\s*(\d+|-?\d*)'
     source_matches = re.findall(source_pattern, response_text, re.IGNORECASE)

     for doc_name, page in source_matches:
        doc_name = self._normalize_doc_name(doc_name.strip())
        page_num = int(page) if page and page.isdigit() else None
        source_key = f"{doc_name}_{page_num}"
        if source_key in seen_sources:
            continue

        if not self._validate_document_exists(doc_name):
            logger.warning(f"Document référencé mais non trouvé: {doc_name}")

        source_obj = {
            "title": self._format_document_title(doc_name),
            "document_name": doc_name,
            "page": page_num,
            "source": doc_name,
            "url": f"{self.documents_endpoint_base}/{doc_name}" + (f"#page={page_num}" if page_num else ""),
            "file_exists": self._validate_document_exists(doc_name)
        }
        sources.append(source_obj)
        seen_sources.add(source_key)

     sources_section_pattern = r'\*\*Sources(?:\s+utilisées)?\s*:\*\*(.*?)(?:\n\*\*|$)'
     sources_match = re.search(sources_section_pattern, response_text, re.DOTALL | re.IGNORECASE)

     if sources_match:
        sources_text = sources_match.group(1).strip()
        source_lines = [line.strip() for line in sources_text.split('\n') if line.strip()]
        for line in source_lines:
            if '.pdf' in line:
                pdf_match = re.search(r'(\w+.*?\.pdf).*?(?:Page\s*(\d+))?', line, re.IGNORECASE)
                if pdf_match:
                    doc_name = self._normalize_doc_name(pdf_match.group(1).strip())
                    page = pdf_match.group(2)
                    page_num = int(page) if page and page.isdigit() else None
                    source_key = f"{doc_name}_{page_num}"
                    if source_key in seen_sources:
                        continue
                    if not self._validate_document_exists(doc_name):
                        logger.warning(f"Document référencé mais non trouvé: {doc_name}")
                    source_obj = {
                        "title": self._format_document_title(doc_name),
                        "document_name": doc_name,
                        "page": page_num,
                        "source": doc_name,
                        "url": f"{self.documents_endpoint_base}/{doc_name}" + (f"#page={page_num}" if page_num else ""),
                        "file_exists": self._validate_document_exists(doc_name)
                    }
                    sources.append(source_obj)
                    seen_sources.add(source_key)

     clean_text = re.sub(r'\*\*Sources\s*(?:utilisées)?\s*:\*\*.*$', '', response_text, flags=re.DOTALL | re.IGNORECASE).strip()

     logger.info(f"Extraites {len(sources)} sources uniques du texte de réponse")
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
        if not self.agent:
            return {"error": "Agent non disponible"}
        return {
            "conversations_count": len(self.active_conversations),
            "agent_history_length": len(self.agent.conversation_history),
            "performance_metrics": self.agent.performance_metrics[-10:] if self.agent.performance_metrics else []
        }

    def health_check(self) -> Dict[str, str]:
        base_info = {
            "timestamp": datetime.now().isoformat(),
            "service": "chat_bridge",
            "conversations_active": len(self.active_conversations),
            "documents_path": self.documents_base_path,
            "documents_endpoint": self.documents_endpoint_base
        }
        if self.agent:
            base_info.update({"status": "healthy", "agent_status": "active", "agent_type": "AdvancedLegalChatbot"})
        else:
            base_info.update({"status": "degraded", "agent_status": "inactive", "message": "Agent indisponible, fonctionnement en mode dégradé"})
        return base_info

    def get_available_documents(self) -> List[str]:
        print(f"document path {self.documents_base_path}")
        print(f"path {self.documents_base_path}") 
        if not os.path.exists(self.documents_base_path): return []

        return [f for f in os.listdir(self.documents_base_path) if f.endswith('.pdf')]

chat_bridge = ChatBridgeService()
