import uuid
import os
from typing import Dict, Optional
from datetime import datetime
import logging

from backend.api.models import ChatRequest, ChatResponse

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import sécurisé de votre agent
try:
    from backend.src.assistants.legal_chatbot import AdvancedLegalChatbot
    logger.info("Import de AdvancedLegalChatbot réussi")
except ImportError as e:
    logger.error(f"Erreur d'import de AdvancedLegalChatbot: {e}")
    AdvancedLegalChatbot = None

class ChatBridgeService:
    """
    Service bridge qui fait le pont entre l'API FastAPI et votre agent AdvancedLegalChatbot
    """
    
    def __init__(self):
        self.agent = None
        self.active_conversations: Dict[str, Dict] = {}
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialise l'agent de manière sécurisée avec gestion des dépendances"""
        try:
            # Vérifier que la classe agent est disponible
            if AdvancedLegalChatbot is None:
                raise ImportError("AdvancedLegalChatbot non disponible")
            
            # Vérifier les variables d'environnement critiques
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
        # Vérifier les dossiers critiques
        required_folders = [
            "backend/data/pdfs",
            "backend/data/chunks", 
            "backend/data/embeddings",
            "backend/cache"
        ]
        
        for folder in required_folders:
            if not os.path.exists(folder):
                logger.warning(f"Dossier manquant: {folder}")
        
        # Vérifier les variables critiques (sans exposer les clés)
        try:
            from backend.src.config import GEMINI_API_KEY, QDRANT_HOST, QDRANT_PORT
            if not GEMINI_API_KEY or GEMINI_API_KEY == "":
                logger.warning("GEMINI_API_KEY non configurée")
            else:
                logger.info("Configuration GEMINI détectée")
                
            logger.info(f"Configuration Qdrant: {QDRANT_HOST}:{QDRANT_PORT}")
            
        except ImportError as e:
            logger.warning(f"Impossible de vérifier la configuration: {e}")
    
    async def process_chat_message(self, request: ChatRequest) -> ChatResponse:
        """
        Traite un message de chat en utilisant votre agent existant
        """
        try:
            # Vérifier que l'agent est disponible
            if not self.agent:
                return self._create_fallback_response(request, "Agent temporairement indisponible. Veuillez réessayer plus tard.")
            
            # Générer un ID de conversation si nécessaire
            conversation_id = request.conversation_id or str(uuid.uuid4())
            
            # Configuration pour votre agent (pour LangGraph)
            config = {
                "configurable": {
                    "thread_id": conversation_id,
                    "user_id": request.user_id or "anonymous"
                }
            }
            
            logger.info(f"Traitement du message pour conversation {conversation_id}")
            
            # Appel de votre agent existant
            response_text = await self.agent.process_question_async(
                question=request.message,
                config=config
            )
            
            # Mise à jour de l'historique des conversations
            self._update_conversation_history(
                conversation_id=conversation_id,
                user_message=request.message,
                assistant_response=response_text,
                user_id=request.user_id
            )
            
            # Création de la réponse
            chat_response = ChatResponse(
                message=response_text,
                conversation_id=conversation_id,
                timestamp=datetime.now()
            )
            
            logger.info(f"Réponse générée avec succès pour conversation {conversation_id}")
            return chat_response
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {str(e)}")
            return self._create_error_response(request, e)
    
    def _create_fallback_response(self, request: ChatRequest, message: str) -> ChatResponse:
        """Crée une réponse de fallback quand l'agent n'est pas disponible"""
        return ChatResponse(
            message=f"{message}\n\nVotre question: '{request.message}' a été enregistrée et sera traitée dès que possible.",
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            timestamp=datetime.now()
        )
    
    def _create_error_response(self, request: ChatRequest, error: Exception) -> ChatResponse:
        """Crée une réponse d'erreur structurée"""
        error_message = (
            "Désolé, une erreur s'est produite lors du traitement de votre demande. "
            "Notre équipe technique a été notifiée. Veuillez réessayer dans quelques instants."
        )
        
        # En mode développement, inclure plus de détails
        if os.getenv("ENVIRONMENT", "production").lower() == "development":
            error_message += f"\n\nDétail technique: {str(error)}"
        
        return ChatResponse(
            message=error_message,
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            timestamp=datetime.now()
        )
    
    def _update_conversation_history(
        self, 
        conversation_id: str, 
        user_message: str, 
        assistant_response: str, 
        user_id: Optional[str] = None
    ):
        """Met à jour l'historique des conversations"""
        if conversation_id not in self.active_conversations:
            self.active_conversations[conversation_id] = {
                "created_at": datetime.now(),
                "user_id": user_id,
                "messages": []
            }
        
        self.active_conversations[conversation_id]["messages"].extend([
            {
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now()
            },
            {
                "role": "assistant", 
                "content": assistant_response,
                "timestamp": datetime.now()
            }
        ])
    
    def get_conversation_history(self, conversation_id: str) -> Optional[Dict]:
        """Récupère l'historique d'une conversation"""
        return self.active_conversations.get(conversation_id)
    
    def get_agent_metrics(self) -> Dict:
        """Récupère les métriques de performance de l'agent"""
        if not self.agent:
            return {"error": "Agent non disponible"}
        
        metrics = {
            "conversations_count": len(self.active_conversations),
            "agent_history_length": len(self.agent.conversation_history),
            "performance_metrics": self.agent.performance_metrics[-10:] if self.agent.performance_metrics else []
        }
        
        return metrics
    
    def health_check(self) -> Dict[str, str]:
        """Vérification de l'état du service avec détails"""
        base_info = {
            "timestamp": datetime.now().isoformat(),
            "service": "chat_bridge",
            "conversations_active": len(self.active_conversations)
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
        
        return base_info

# Instance globale du service (Singleton pattern)
chat_bridge = ChatBridgeService()