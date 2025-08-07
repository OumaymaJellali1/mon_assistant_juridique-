import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PDF_FOLDER = os.path.join(BASE_DIR, "data", "pdfs")
CHUNKS_FOLDER = os.path.join(BASE_DIR, "data", "chunks")
EMBEDDINGS_FOLDER = os.path.join(BASE_DIR, "data", "embeddings")
CACHE_FOLDER = os.path.join(BASE_DIR, "cache")

# Fichiers spécifiques
CACHE_FILE = os.path.join(CACHE_FOLDER, "title_cache.json")
EMBEDDINGS_FILE = os.path.join(EMBEDDINGS_FOLDER, "vectors.json")

# GEMINI / GEMMA API
GEMINI_API_KEY = "****"
GEMMA_MODEL = "gemma-3n-e2b-it"

# Modèle embeddings
EMBEDDING_MODEL= "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Qdrant config
QDRANT_HOST = "..."
QDRANT_PORT = ...
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
