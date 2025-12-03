"""
Configuration module for the Hyper-Personalized Retail Support Agent.
Stores constants and provides access to environment variables.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow logging (0=all, 1=info, 2=warning, 3=error)
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN custom operations warnings

# Suppress other warnings
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# Load environment variables from .env file
load_dotenv()

# Model configuration
DEFAULT_MODEL_NAME = "llama-3.3-70b-versatile"

# Database configuration
DB_PATH = "hyper_support.db"

# RAG configuration
PDF_DIR = "data/pdfs"
VECTOR_STORE_DIR = "chroma_db"
TOP_K_RAG = 4
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def get_groq_api_key() -> Optional[str]:
    """
    Retrieve the Groq API key from environment variables.
    
    Returns:
        Optional[str]: The API key if set, None otherwise.
    """
    return os.getenv("GROQ_API_KEY")


def validate_groq_api_key() -> None:
    """
    Validate that the Groq API key is set.
    
    Raises:
        RuntimeError: If GROQ_API_KEY is not set in environment variables.
    """
    api_key = get_groq_api_key()
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Please define it in your .env file or environment variables.\n"
            "Example .env file:\n"
            "GROQ_API_KEY=your_actual_groq_api_key_here"
        )
