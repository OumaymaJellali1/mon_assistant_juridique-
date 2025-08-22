#!/usr/bin/env python3
"""
Script de lancement pour le serveur FastAPI
Utilisation: python run_server.py
"""

import os
import sys
import uvicorn
from pathlib import Path

# Ajouter le dossier racine au PYTHONPATH pour les imports
current_dir = Path(__file__).parent
root_dir = current_dir.parent
sys.path.insert(0, str(root_dir))

def main():
    """Lance le serveur FastAPI avec les bonnes configurations"""
    
    print(" Lancement du serveur Smart Legal Interface")
    print("=" * 50)
    
    # Vérifications préalables
    print(" Vérification de l'environnement...")
    
    # Vérifier la structure des dossiers
    required_dirs = [
        "backend/data",
        "backend/cache", 
        "backend/src"
    ]
    
    for dir_path in required_dirs:
        full_path = root_dir / dir_path
        if not full_path.exists():
            print(f"⚠️  Dossier manquant: {dir_path}")
            print(f"   Création du dossier...")
            full_path.mkdir(parents=True, exist_ok=True)
        else:
            print(f" Dossier OK: {dir_path}")
    
    print("\n📡 Configuration du serveur:")
    print("   Host: 127.0.0.1")
    print("   Port: 8000")
    print("   Mode: Development (reload activé)")
    print("   Docs: http://127.0.0.1:8000/docs")
    print("   API Info: http://127.0.0.1:8000/api")
    
    print("\n CORS configuré pour:")
    print("   - http://localhost:3000 (Next.js)")
    print("   - http://127.0.0.1:3000")
    
    print("\n" + "=" * 50)
    print(" Serveur en cours de démarrage...")
    print("   Appuyez sur Ctrl+C pour arrêter")
    print("=" * 50)
    
    try:
        # Lancement du serveur
        uvicorn.run(
            "backend.api.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            reload_dirs=[str(root_dir / "backend")],
            log_level="info",
            access_log=True
        )
    
    except KeyboardInterrupt:
        print("\n\n Arrêt du serveur demandé")
        print(" Serveur arrêté proprement")
    
    except Exception as e:
        print(f"\nErreur lors du démarrage: {str(e)}")
        print(" Vérifiez que:")
        print("   - Toutes les dépendances sont installées")
        print("   - Le port 8000 n'est pas déjà utilisé")
        print("   - Votre configuration est correcte")
        sys.exit(1)

if __name__ == "__main__":
    main()