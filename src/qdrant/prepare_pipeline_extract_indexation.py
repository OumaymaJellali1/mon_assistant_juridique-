from src.qdrant.qdrant import PDFProcessor
from src.qdrant.qdrant import EmbeddingGenerator
from src.qdrant.qdrant import QdrantIndexer

def run_all():
    print("Étape 1 : Extraction des chunks depuis les PDFs")
    pdf_processor = PDFProcessor()
    pdf_processor.process_all_pdfs()
    print("Étape 2 : Génération des embeddings")
    embedder = EmbeddingGenerator()
    embedder.generate_embeddings()

    print("Étape 3 : Indexation dans Qdrant")
    indexer = QdrantIndexer()
    indexer.create_or_reset_collection()
    indexer.upload_vectors()

    print("Pipeline terminée.")
    

if __name__ == "__main__":
    run_all()
