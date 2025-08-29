from fastapi import APIRouter, Query
from datetime import datetime
from typing import Dict, Any

from api.models import HealthCheck
from services.chat_bridge import chat_bridge

router = APIRouter()

@router.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """
    Health check léger qui n'utilise PAS le LLM
    """
    basic_health = {
        "status": "healthy" if chat_bridge.agent is not None else "degraded",
        "agent_available": chat_bridge.agent is not None,
        "conversations_count": len(chat_bridge.active_conversations)
    }
    
    return HealthCheck(
        status=basic_health["status"],
        timestamp=datetime.now(),
        version="1.0.0"
    )

@router.get("/health/detailed", tags=["Health"])
async def detailed_health_check() -> Dict[str, Any]:
    """
    Health check détaillé avec cache - évite les appels LLM répétés
    """
    service_health = chat_bridge.health_check()  
    
    detailed_info = {
        "api": {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        },
        "chat_bridge": service_health,
        "system": {
            "python_version": "3.x",
            "environment": "development",
            "cache_info": {
                "health_cached": chat_bridge._is_cache_valid(chat_bridge._health_cache_expiry),
                "cache_expiry": chat_bridge._health_cache_expiry.isoformat() if chat_bridge._health_cache_expiry else None,
            }
        }
    }
    
    detailed_info["global_status"] = "healthy" if service_health.get("status") == "healthy" else "degraded"
    
    return detailed_info

@router.get("/health/agent-test", tags=["Health"])  
async def test_agent_with_llm():
    """
    Test spécifique de l'agent qui UTILISE le LLM - à utiliser avec parcimonie
    """
    try:
        if not chat_bridge.agent:
            return {
                "test_status": "failed",
                "error": "Agent non disponible",
                "quota_used": False
            }
        
        from api.models import ChatRequest
        test_request = ChatRequest(
            message="Test rapide",  
            user_id="health_check"
        )
        
        response = await chat_bridge.process_chat_message(test_request)
        
        return {
            "test_status": "success",
            "agent_responsive": True,
            "response_length": len(response.message),
            "conversation_id": response.conversation_id,
            "quota_used": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "test_status": "failed",
            "error": str(e),
            "quota_used": True,  
            "timestamp": datetime.now().isoformat()
        }

@router.get("/health/refresh", tags=["Health"])
async def force_health_refresh():
    """
    Force le rafraîchissement du cache SANS utiliser le LLM
    """
    chat_bridge.force_health_refresh()
    
    basic_status = "healthy" if chat_bridge.agent is not None else "degraded"
    
    return {
        "message": "Cache rafraîchi",
        "timestamp": datetime.now().isoformat(),
        "status": basic_status,
        "agent_available": chat_bridge.agent is not None,
        "quota_used": False
    }

@router.get("/metrics", tags=["Health"])
async def get_metrics(force_refresh: bool = Query(False, description="Force le rafraîchissement du cache")) -> Dict[str, Any]:
    """
    Métriques sans utiliser le LLM
    """
    try:
        if force_refresh:
            chat_bridge._invalidate_metrics_cache()
        
        basic_metrics = {
            "conversations_active": len(chat_bridge.active_conversations),
            "agent_available": chat_bridge.agent is not None,
            "documents_available": len(chat_bridge.get_available_documents()),
            "uptime": "N/A", 
        }
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "metrics": basic_metrics,
            "quota_used": False,
            "cache_info": {
                "metrics_cached": chat_bridge._is_cache_valid(chat_bridge._metrics_cache_expiry),
                "cache_expiry": chat_bridge._metrics_cache_expiry.isoformat() if chat_bridge._metrics_cache_expiry else None
            }
        }
    
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "metrics": {},
            "quota_used": False
        }