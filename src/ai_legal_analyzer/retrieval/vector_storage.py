import os
import shutil
import logging
import chromadb
from typing import List, Tuple
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from src.ai_legal_analyzer.utils.project_config import Config

logger = logging.getLogger("vector_store")

class VectorStoreManager:
    # manage chroma db with gemini embeddings
    
    def __init__(self):
        # init embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=Config.EMBEDDING_MODEL,
            google_api_key=Config.GOOGLE_API_KEY
        )
        
        persist_dir = Config.CHROMA_PERSIST_DIRECTORY
        os.makedirs(persist_dir, exist_ok=True)
        
        # init client with auto-repair
        try:
            chroma_client = self._get_client(persist_dir)
        except Exception as e:
            # reset on failure
            logger.warning(f"init failed, resetting db: {e}")
            if os.path.exists(persist_dir):
                shutil.rmtree(persist_dir, ignore_errors=True)
            os.makedirs(persist_dir, exist_ok=True)
            chroma_client = self._get_client(persist_dir)
        
        self.vector_store = Chroma(
            client=chroma_client,
            embedding_function=self.embeddings,
            collection_name="legal_clauses"
        )
    
    def _get_client(self, path):
        return chromadb.PersistentClient(
            path=path,
            settings=Settings(anonymized_telemetry=False, allow_reset=True)
        )
    
    def add_documents(self, documents: List[Document], clear_existing: bool = True):
        # add docs to store, clear old ones for demo
        if not documents: return []
        if clear_existing:
            self.clear_all()
        return self.vector_store.add_documents(documents)
    
    def clear_all(self):
        # wipe the collection for a fresh start
        try:
            self.vector_store.delete_collection()
            # re-init after delete
            self.vector_store = Chroma(
                client=self.vector_store._client,
                embedding_function=self.embeddings,
                collection_name="legal_clauses"
            )
        except Exception as e:
            logger.error(f"clear failed: {e}")
        
    def search(self, query: str, k: int = 5):
        # similarity search
        return self.vector_store.similarity_search_with_score(query, k=k)
    
    def get_retriever(self, k: int = 5):
        return self.vector_store.as_retriever(search_kwargs={"k": k})
