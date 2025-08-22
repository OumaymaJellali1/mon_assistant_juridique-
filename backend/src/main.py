from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
# Import des endpoints
from api.endpoints import chat, health

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Création de l'application FastAPI
app = FastAPI(
    title="Smart Legal Interface API",
    description="API pour l'interface du chatbot juridique intelligent",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS pour permettre les requêtes depuis le frontend Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Alternative port
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Inclusion des routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")

@app.get("/")
async def root():
    """
    Endpoint racine avec informations de base sur l'API
    """
    return {
        "message": "Smart Legal Interface API",
        "version": "1.0.0",
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs",
        "health": "/api/v1/health"
    }

@app.get("/api")
async def api_info():
    """
    Informations sur l'API
    """
    return {
        "api_name": "Smart Legal Interface",
        "version": "1.0.0",
        "description": "API pour chatbot juridique avec AdvancedLegalChatbot",
        "available_endpoints": {
            "health": "/api/v1/health",
            "detailed_health": "/api/v1/health/detailed",
            "metrics": "/api/v1/metrics",
            "chat": "/api/v1/chat",
            "test": "/api/v1/chat/test",
            "conversations": "/api/v1/chat/conversations"
        },
        "timestamp": datetime.now().isoformat()
    }

# Gestionnaire d'erreur global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Gestionnaire d'erreur global pour capturer toutes les exceptions non gérées
    """
    logger.error(f"Erreur non gérée: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erreur interne du serveur",
            "message": "Une erreur inattendue s'est produite",
            "timestamp": datetime.now().isoformat()
        }
    )

# Gestionnaire d'erreur 404
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """
    Gestionnaire pour les routes non trouvées
    """
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint non trouvé",
            "message": f"L'endpoint {request.url.path} n'existe pas",
            "available_endpoints": [
                "/api/v1/health",
                "/api/v1/chat",
                "/docs"
            ],
            "timestamp": datetime.now().isoformat()
        }
    )

# Event handlers
@app.on_event("startup")
async def startup_event():
    """
    Actions à effectuer au démarrage de l'API
    """
    logger.info(" Démarrage de l'API Smart Legal Interface")
    logger.info(" Initialisation du service de chat bridge...")
    
    # Ici, on peut ajouter d'autres initialisations si nécessaire
    
    logger.info(" API prête à recevoir des requêtes")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Actions à effectuer à l'arrêt de l'API
    """
    logger.info(" Arrêt de l'API Smart Legal Interface")
    logger.info(" Sauvegarde des données en cours...")
    
    # Ici, on peut ajouter la sauvegarde de l'historique si nécessaire
    
    logger.info(" Arrêt terminé proprement")

# Middleware de logging des requêtes
@app.middleware("http")
async def log_requests(request, call_next):
    """
    Middleware pour logger toutes les requêtes HTTP
    """
    start_time = datetime.now()
    
    # Log de la requête entrante
    logger.info(f" {request.method} {request.url.path}")
    
    # Traitement de la requête
    response = await call_next(request)
    
    # Calcul du temps de traitement
    process_time = (datetime.now() - start_time).total_seconds()
    
    # Log de la réponse
    logger.info(f" {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )