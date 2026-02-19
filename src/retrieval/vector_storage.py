import os
import shutil
import logging
import chromadb
from typing import List
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from src.utils.project_config import Config

logger = logging.getLogger("vector_store")


class VectorStoreManager:
    """Manages the ChromaDB vector store with Google Gemini embeddings."""

    COLLECTION_NAME = "legal_clauses"

    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=Config.EMBEDDING_MODEL,
            google_api_key=Config.GOOGLE_API_KEY
        )
        persist_dir = Config.CHROMA_PERSIST_DIRECTORY
        os.makedirs(persist_dir, exist_ok=True)

        try:
            self._chroma_client = self._make_client(persist_dir)
        except Exception as e:
            logger.warning(f"ChromaDB init failed ({e}), resetting DB…")
            shutil.rmtree(persist_dir, ignore_errors=True)
            os.makedirs(persist_dir, exist_ok=True)
            self._chroma_client = self._make_client(persist_dir)

        self.vector_store = self._make_store()

    def _make_client(self, path: str) -> chromadb.PersistentClient:
        return chromadb.PersistentClient(
            path=path,
            settings=Settings(anonymized_telemetry=False, allow_reset=True)
        )

    def _make_store(self) -> Chroma:
        return Chroma(
            client=self._chroma_client,
            embedding_function=self.embeddings,
            collection_name=self.COLLECTION_NAME,
        )

    def add_documents(self, documents: List[Document], clear_existing: bool = True) -> List[str]:
        if not documents:
            return []
        if clear_existing:
            self.clear_all()
        return self.vector_store.add_documents(documents)

    def clear_all(self):
        """Drop and recreate the collection for a fresh start."""
        try:
            self.vector_store.delete_collection()
        except Exception as e:
            logger.warning(f"Could not delete collection: {e}")
        self.vector_store = self._make_store()

    def search(self, query: str, k: int = 5):
        """Return top-k similar (Document, score) pairs."""
        return self.vector_store.similarity_search_with_score(query, k=k)

    def get_retriever(self, k: int = 5):
        return self.vector_store.as_retriever(search_kwargs={"k": k})
