from sentence_transformers import SentenceTransformer
from src.config.settings import EMBEDDING_MODEL

model = SentenceTransformer(EMBEDDING_MODEL)

def embed_text(text: str) -> list:
    return model.encode(text).tolist()