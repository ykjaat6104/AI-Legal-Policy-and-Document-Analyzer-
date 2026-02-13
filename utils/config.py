import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    CHROMA_PERSIST_DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
    EMBEDDING_MODEL = "models/embedding-001"
    LLM_MODEL = "gemini-pro"
