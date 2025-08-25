
import os
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PDF_FOLDER = os.path.join(BASE_DIR, "data", "pdfs")
CHUNKS_FOLDER = os.path.join(BASE_DIR, "data", "chunks")
EMBEDDINGS_FOLDER = os.path.join(BASE_DIR, "data", "embeddings")
CACHE_FOLDER = os.path.join(BASE_DIR, "cache")

# Fichiers spécifiques
CACHE_FILE = os.path.join(CACHE_FOLDER, "title_cache.json")
EMBEDDINGS_FILE = os.path.join(EMBEDDINGS_FOLDER, "vectors.json")

# GEMINI / GEMMA API
GEMINI_API_KEY = "AIzaSyBJ5xLmhvTIDzJo3MPbhLejZjAIHhFD7-E"
#GEMMA_MODEL = "gemini-2.0-flash"
GEMMA_MODEL = "gemma-3n-e2b-it"

# Modèle embeddings - CHANGEMENT ICI
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

print(f"Chargement du modèle d'embedding: {EMBEDDING_MODEL_NAME}")
try:
    EMBEDDING_MODEL = SentenceTransformer(EMBEDDING_MODEL_NAME)
    print(f"Modèle d'embedding chargé avec succès: {type(EMBEDDING_MODEL)}")
except Exception as e:
    print(f"Erreur lors du chargement du modèle d'embedding: {e}")
    # Modèle de secours plus léger
    EMBEDDING_MODEL = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    print(f"Utilisation du modèle de secours: {type(EMBEDDING_MODEL)}")

# Test du modèle
try:
    test_embedding = EMBEDDING_MODEL.encode("test")
    print(f"Test du modèle d'embedding réussi. Dimension: {len(test_embedding)}")
except Exception as e:
    print(f"Test du modèle d'embedding échoué: {e}")

# Qdrant config
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_COLLECTION = "chunks_juridiques"

# Divers
MAX_RETRIES = 3
SLEEP_BETWEEN_CALLS = 2
MAX_TITLE_CHARS = 1000
MAX_PROMPT_TOKENS = 3500

# Création dossiers si besoin
os.makedirs(CACHE_FOLDER, exist_ok=True)
os.makedirs(CHUNKS_FOLDER, exist_ok=True)
os.makedirs(EMBEDDINGS_FOLDER, exist_ok=True)