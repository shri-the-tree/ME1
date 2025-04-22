import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Bot configuration
MAX_HISTORY_LENGTH = 10  # Number of messages to keep in history
MODEL_NAME = "gemini-2.0-flash"  # Gemini model to use

# Vector database configuration
PDF_DIRECTORY = os.getenv("PDF_DIRECTORY", "./pdfs")  # Directory containing your PDFs
VECTOR_DB_DIRECTORY = os.getenv("VECTOR_DB_DIRECTORY", "./chroma_db")  # Directory to store vector database
CHUNK_SIZE = 1000  # Size of text chunks for embedding
CHUNK_OVERLAP = 200  # Overlap between chunks
RETRIEVAL_K = 3  # Number of relevant chunks to retrieve