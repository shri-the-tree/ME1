import os
import chromadb
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

class MarineEdgeVectorStore:
    def __init__(self, pdf_directory, persist_directory="./chroma_db"):
        self.pdf_directory = pdf_directory
        self.persist_directory = persist_directory
        # Using a lightweight but effective embedding model
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.db = None

    def load_documents(self):
        """Load PDF documents from the specified directory"""
        print(f"Loading documents from {self.pdf_directory}...")
        loader = DirectoryLoader(self.pdf_directory, glob="**/*.pdf", loader_cls=PyPDFLoader)
        documents = loader.load()
        print(f"Loaded {len(documents)} documents")
        return documents

    def split_documents(self, documents, chunk_size=1000, chunk_overlap=200):
        """Split documents into chunks for better retrieval"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)
        print(f"Split into {len(chunks)} chunks")
        return chunks

    def create_or_load_vector_store(self, force_reload=False):
        """Create a new vector store or load an existing one"""
        if os.path.exists(self.persist_directory) and not force_reload:
            print("Loading existing vector store...")
            self.db = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
        else:
            print("Creating new vector store...")
            # Load and process documents
            documents = self.load_documents()
            chunks = self.split_documents(documents)

            # Create vector store - remove the persist() call
            self.db = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            # Remove this line: self.db.persist()

        return self.db

    def query_vector_store(self, query, k=5):
        """Query the vector store to find relevant document chunks"""
        if not self.db:
            self.create_or_load_vector_store()

        results = self.db.similarity_search_with_score(query, k=k)
        return results