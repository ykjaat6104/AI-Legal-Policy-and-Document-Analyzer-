import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Get project root (4 levels up from this file)
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
    CHROMA_PERSIST_DIRECTORY = str(PROJECT_ROOT / "chroma_db")
    
    EMBEDDING_MODEL = "models/gemini-embedding-001"
    
    # gemini-2.5-flash is confirmed available in your environment and has generous quotas
    LLM_SCAN_MODEL = "gemini-2.5-flash" 
    LLM_REASONING_MODEL = "gemini-2.5-flash"
    LLM_MODEL = "gemini-2.5-flash"
    
    @classmethod
    def validate_api_key(cls):
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is missing in .env file")
        if cls.GOOGLE_API_KEY.startswith("your_") or len(cls.GOOGLE_API_KEY) < 30:
            raise ValueError(f"Invalid GOOGLE_API_KEY detected. Please check your .env file.")
