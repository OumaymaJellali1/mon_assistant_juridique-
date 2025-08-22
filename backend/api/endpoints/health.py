from fastapi import APIRouter
from datetime import datetime
from typing import Dict, Any

from backend.api.models import HealthCheck
from backend.services.chat_bridge import chat_bridge

router = APIRouter()

@router.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """
    Vérification de l'état de santé de l'API et de l'agent
    """
    service_health = chat_bridge.health_check()
    
    return HealthCheck(
        status=service_health.get("status", "unknown"),
        timestamp=datetime.now(),
        version="1.0.0"
    )

@router.get("/health/detailed", tags=["Health"])
async def detailed_health_check() -> Dict[str, Any]:
    """
    Health check détaillé avec informations sur tous les composants
    """
    service_health = chat_bridge.health_check()
    
    # Informations détaillées
    detailed_info = {
        "api": {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        },
        "chat_bridge": service_health,
        "system": {
            "python_version": "3.x",
            "environment": "development"  # À adapter selon votre config
        }
    }
    
    # Status global basé sur les composants
    if service_health.get("status") == "healthy":
        detailed_info["global_status"] = "healthy"
    else:
        detailed_info["global_status"] = "degraded"
    
    return detailed_info

@router.get("/metrics", tags=["Health"])
async def get_metrics() -> Dict[str, Any]:
    """
    Métriques de performance de l'agent et du service
    """
    try:
        metrics = chat_bridge.get_agent_metrics()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        }
    
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "metrics": {}
        }