import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    # Chroma DB stored at project root
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
    CHROMA_PERSIST_DIRECTORY = str(PROJECT_ROOT / "chroma_db")

    EMBEDDING_MODEL = "models/gemini-embedding-001"

    # gemini-2.0-flash: fast, high quota model
    LLM_SCAN_MODEL = "gemini-2.0-flash"
    LLM_REASONING_MODEL = "gemini-2.0-flash"
    LLM_MODEL = "gemini-2.0-flash"

    @classmethod
    def validate_api_key(cls):
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is missing in .env file")
        if cls.GOOGLE_API_KEY.startswith("your_") or len(cls.GOOGLE_API_KEY) < 30:
            raise ValueError(f"Invalid GOOGLE_API_KEY. Please check your .env file.")
