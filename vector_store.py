# vector_store.py
import os
import faiss
import numpy as np
import pickle
import logging
from typing import List, Dict, Tuple, Optional, Any
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader
import re


class Document:
    """Document class to mimic Langchain Document structure"""

    def __init__(self, page_content: str, metadata: Dict[str, Any] = None):
        self.page_content = page_content
        self.metadata = metadata or {}


class MarineEdgeVectorStore:
    def __init__(self,
                 pdf_directory: str = "pdfs",
                 persist_directory: str = "faiss_db",
                 embedding_model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the vector store"""
        self.pdf_directory = pdf_directory
        self.persist_directory = persist_directory
        self.embedding_model_name = embedding_model_name

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Initialize attributes
        self.embedding_model = None
        self.index = None
        self.documents = []
        self.embedding_size = None

        # Load the embedding model right away
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        self.embedding_size = self.embedding_model.get_sentence_embedding_dimension()

        # Create directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)

        # Try to load existing index
        self._load_or_create_index()

    def _load_or_create_index(self):
        """Load existing index or create a new one"""
        index_path = os.path.join(self.persist_directory, "faiss_index.bin")
        docs_path = os.path.join(self.persist_directory, "documents.pkl")

        if os.path.exists(index_path) and os.path.exists(docs_path):
            try:
                self.logger.info(f"Loading existing FAISS index from {index_path}")
                self.index = faiss.read_index(index_path)

                with open(docs_path, 'rb') as f:
                    self.documents = pickle.load(f)

                self.logger.info(f"Loaded index with {len(self.documents)} documents")
            except Exception as e:
                self.logger.error(f"Error loading index: {str(e)}")
                self._create_new_index()
        else:
            self.logger.info("No existing index found. Creating new FAISS index")
            self._create_new_index()

    def _create_new_index(self):
        """Create a new FAISS index"""
        self.index = faiss.IndexFlatL2(self.embedding_size)
        self.documents = []

    def create_or_load_vector_store(self):
        """Legacy method for backward compatibility"""
        # This method now does nothing since initialization handles loading
        pass

    def add_texts(self, texts, metadatas=None):
        """Add texts and their metadata to the vector store"""
        if not texts:
            return []

        # Create default metadata if not provided
        if metadatas is None:
            metadatas = [{} for _ in texts]

        # Create embeddings for texts
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)

        # Store documents with their metadata
        doc_ids = []
        for i, (text, metadata) in enumerate(zip(texts, metadatas)):
            doc_id = len(self.documents)
            doc_ids.append(doc_id)

            # Create Document object to match interface
            doc = Document(page_content=text, metadata=metadata)
            self.documents.append(doc)

        # Add to FAISS index
        self.index.add(np.array(embeddings).astype('float32'))

        # Save updated index and documents
        self._save_index()

        return doc_ids

    def add_documents(self, documents: List[Document]):
        """Add documents to the vector store"""
        if not documents:
            return []

        # Extract text and metadata
        texts = [doc.page_content for doc in documents]

        # Create embeddings
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)

        # Store document IDs
        doc_ids = list(range(len(self.documents), len(self.documents) + len(documents)))

        # Add to FAISS index
        self.index.add(np.array(embeddings).astype('float32'))

        # Store documents
        self.documents.extend(documents)

        # Save updated index and documents
        self._save_index()

        return doc_ids

    def _save_index(self):
        """Save index and documents to disk"""
        index_path = os.path.join(self.persist_directory, "faiss_index.bin")
        docs_path = os.path.join(self.persist_directory, "documents.pkl")

        # Save FAISS index
        faiss.write_index(self.index, index_path)

        # Save documents
        with open(docs_path, 'wb') as f:
            pickle.dump(self.documents, f)

        self.logger.info(f"Saved index with {len(self.documents)} documents")

    def get_document_count(self):
        """Return the number of documents in the index"""
        return len(self.documents)

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Search for documents similar to the query"""
        if not self.index or self.index.ntotal == 0:
            self.logger.warning("Index is empty, returning empty results")
            return []

        # Create embedding for query
        query_embedding = self.embedding_model.encode([query])

        # Search FAISS index
        distances, indices = self.index.search(np.array(query_embedding).astype('float32'), k)

        # Return documents
        results = []
        for i, idx in enumerate(indices[0]):
            if 0 <= idx < len(self.documents):
                results.append(self.documents[idx])

        return results

    def similarity_search_with_score(self, query: str, k: int = 4) -> List[Tuple[Document, float]]:
        """Search for documents with similarity scores"""
        if not self.index or self.index.ntotal == 0:
            self.logger.warning("Index is empty, returning empty results")
            return []

        # Create embedding for query
        query_embedding = self.embedding_model.encode([query])

        # Search FAISS index
        distances, indices = self.index.search(np.array(query_embedding).astype('float32'), k)

        # Return documents with scores
        results = []
        for i, idx in enumerate(indices[0]):
            if 0 <= idx < len(self.documents):
                # Convert L2 distance to similarity score (smaller distance = higher similarity)
                # Normalize to a 0-1 scale (1 being identical)
                similarity = 1.0 / (1.0 + distances[0][i])
                results.append((self.documents[idx], similarity))

        return results
