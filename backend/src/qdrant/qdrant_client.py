
from qdrant_client import QdrantClient
from config.settings import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION

class QdrantClientWrapper:
    def __init__(self):
        self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        self.collection_name = QDRANT_COLLECTION

    def query(self, vector, top_k=30):
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=top_k,
            # with_payload=True
        )
        return results.points
    