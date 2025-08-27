from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from urllib.parse import unquote
from services.chat_bridge import chat_bridge
from datetime import datetime

router = APIRouter()

@router.get("/", tags=["Documents"])
async def list_documents():
    """
    Retourne la liste des documents PDF disponibles
    """
    docs = chat_bridge.get_available_documents()
    return {"available_documents": docs, "total_count": len(docs)}

@router.get("/{file_path:path}", tags=["Documents"])
async def get_document(file_path: str):
    """
    Permet de récupérer un PDF depuis le serveur
    """
    print(f" Fichier demandé (brut): '{file_path}'")
    
    file_path = unquote(file_path)
    print(f" Fichier demandé (décodé): '{file_path}'")
    
    if '__' in file_path:
        original_path = file_path
        file_path = file_path.replace('__', '_')
        print(f" Correction appliquée: '{original_path}' -> '{file_path}'")
    
    base_path = Path(chat_bridge.documents_base_path)
    full_path = base_path / file_path
    
    print(f" Chemin complet: {full_path}")
    print(f" Existe?: {full_path.exists()}")
    
    if not full_path.exists() or not full_path.is_file():
        if base_path.exists():
            available_files = [f.name for f in base_path.glob("*.pdf")]
            similar_files = [f for f in available_files if file_path.replace('_', '').lower() in f.replace('_', '').lower()]
            print(f" Fichiers similaires trouvés: {similar_files}")
            
            exact_match = None
            for available_file in available_files:
                if available_file.lower() == file_path.lower():
                    exact_match = available_file
                    break
            
            if exact_match:
                print(f"Correspondance exacte trouvée: {exact_match}")
                full_path = base_path / exact_match
            else:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Document non trouvé: {file_path}. Fichiers disponibles: {available_files[:5]}"
                )

    return FileResponse(full_path, media_type="application/pdf", filename=full_path.name)

@router.get("/health", tags=["Documents"])
async def documents_health():
    """
    Vérifie que le service documents fonctionne
    """
    docs = chat_bridge.get_available_documents()
    return {
        "status": "healthy" if docs is not None else "degraded",
        "total_documents": len(docs),
        "timestamp": datetime.now().isoformat()
    }
