from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Optional
from datetime import datetime
import logging

from backend.api.models import ChatRequest, ChatResponse, ChatMessage, ErrorResponse
from backend.services.chat_bridge import chat_bridge

# Configuration du logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def send_message(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Envoie un message au chatbot juridique et retourne la réponse
    """
    try:
        logger.info(f"Nouveau message reçu: {request.message[:50]}...")
        
        # Validation basique
        if not request.message or len(request.message.strip()) == 0:
            raise HTTPException(
                status_code=400, 
                detail="Le message ne peut pas être vide"
            )
        
        if len(request.message) > 5000:  # Limite raisonnable
            raise HTTPException(
                status_code=400,
                detail="Message trop long (maximum 5000 caractères)"
            )
        
        # Traitement du message via le bridge
        response = await chat_bridge.process_chat_message(request)
        
        # Log en arrière-plan pour les métriques
        background_tasks.add_task(
            _log_interaction, 
            request.message, 
            response.message, 
            response.conversation_id
        )
        
        return response
        
    except HTTPException:
        # Re-lancer les exceptions HTTP
        raise
        
    except Exception as e:
        logger.error(f"Erreur inattendue dans send_message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erreur interne du serveur"
        )

@router.get("/chat/{conversation_id}/history", tags=["Chat"])
async def get_conversation_history(conversation_id: str) -> Dict:
    """
    Récupère l'historique d'une conversation
    """
    try:
        history = chat_bridge.get_conversation_history(conversation_id)
        
        if not history:
            raise HTTPException(
                status_code=404,
                detail="Conversation non trouvée"
            )
        
        return {
            "conversation_id": conversation_id,
            "history": history,
            "retrieved_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération de l'historique"
        )

@router.get("/chat/conversations", tags=["Chat"])
async def list_active_conversations() -> Dict:
    """
    Liste toutes les conversations actives (utile pour le développement)
    """
    try:
        conversations = []
        
        for conv_id, conv_data in chat_bridge.active_conversations.items():
            conversations.append({
                "conversation_id": conv_id,
                "created_at": conv_data["created_at"].isoformat(),
                "user_id": conv_data.get("user_id"),
                "message_count": len(conv_data.get("messages", []))
            })
        
        return {
            "active_conversations": conversations,
            "total_count": len(conversations),
            "retrieved_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des conversations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération des conversations"
        )

@router.delete("/chat/{conversation_id}", tags=["Chat"])
async def delete_conversation(conversation_id: str) -> Dict:
    """
    Supprime une conversation (utile pour nettoyer pendant le développement)
    """
    try:
        if conversation_id in chat_bridge.active_conversations:
            del chat_bridge.active_conversations[conversation_id]
            return {
                "message": f"Conversation {conversation_id} supprimée",
                "deleted_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Conversation non trouvée"
            )
            
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la suppression"
        )

@router.post("/chat/test", tags=["Chat"])
async def test_agent() -> Dict:
    """
    Endpoint de test pour vérifier que l'agent fonctionne
    """
    try:
        test_request = ChatRequest(
            message="Bonjour, pouvez-vous me confirmer que vous fonctionnez ?",
            user_id="test_user"
        )
        
        response = await chat_bridge.process_chat_message(test_request)
        
        return {
            "test_status": "success",
            "agent_available": chat_bridge.agent is not None,
            "test_response": response.message[:100] + "..." if len(response.message) > 100 else response.message,
            "conversation_id": response.conversation_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "test_status": "failed",
            "agent_available": chat_bridge.agent is not None,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Fonction utilitaire pour logging en arrière-plan
def _log_interaction(user_message: str, bot_response: str, conversation_id: str):
    """Log les interactions pour analyse future"""
    try:
        logger.info(
            f"Interaction logged - Conversation: {conversation_id}, "
            f"User: {user_message[:50]}..., "
            f"Bot: {bot_response[:50]}..."
        )
    except Exception as e:
        logger.error(f"Erreur lors du logging: {str(e)}")