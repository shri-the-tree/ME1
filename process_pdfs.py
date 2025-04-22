from vector_store import MarineEdgeVectorStore
from config import PDF_DIRECTORY, VECTOR_DB_DIRECTORY


def main():
    """Process all PDFs and create/update the vector store."""
    print("Marine Edge PDF Processor")
    print("-" * 50)

    # Initialize and create vector store
    vector_store = MarineEdgeVectorStore(
        pdf_directory=PDF_DIRECTORY,
        persist_directory=VECTOR_DB_DIRECTORY
    )

    # Force reload the vector store
    vector_store.create_or_load_vector_store(force_reload=True)

    print("Vector store created and persisted successfully!")
    # Fix the count line:
    print(f"Total documents processed: {vector_store.db._collection.count()}")  # Remove len()


if __name__ == "__main__":
    main()