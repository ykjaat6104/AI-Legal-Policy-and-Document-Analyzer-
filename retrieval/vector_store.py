from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from typing import List, Tuple
import os
from ai_legal_analyzer.utils.config import Config

class VectorStoreManager:
    """
    Manages interactions with ChromaDB using Gemini Embeddings.
    """
    def __init__(self):
        # Initialize Embeddings
        # Note: Ensure GOOGLE_API_KEY is set in environment or Config
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=Config.EMBEDDING_MODEL,
            google_api_key=Config.GOOGLE_API_KEY
        )
        
        # Initialize ChromaDB
        self.vector_store = Chroma(
            persist_directory=Config.CHROMA_PERSIST_DIRECTORY,
            embedding_function=self.embeddings,
            collection_name="legal_clauses"
        )
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Embed and store documents in ChromaDB.
        Returns list of IDs.
        """
        if not documents:
            return []
        return self.vector_store.add_documents(documents)
        
    def search(self, query: str, k: int = 5, score_threshold: float = 0.0) -> List[Tuple[Document, float]]:
        """
        Perform similarity search with relevance scores.
        """
        # Chroma returns distance by default for some metrics, but LangChain wrapper usually normalizes to score.
        # Verify metric in Chroma defaults (cosine distance usually). 
        # langchain_chroma defaults to cosine similarity (1.0 = identical).
        
        results = self.vector_store.similarity_search_with_score(query, k=k)
        
        # Filter by threshold if needed
        filtered_results = [
            (doc, score) for doc, score in results 
            if score >= score_threshold  # Note: Score meaning depends on distance function.
        ]
        
        return filtered_results
    
    def get_retriever(self, k: int = 5):
        """Returns a standard LangChain retriever interface."""
        return self.vector_store.as_retriever(search_kwargs={"k": k})
