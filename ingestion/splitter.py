import re
from typing import List, Optional, Any, Dict
from langchain_text_splitters import TextSplitter
from langchain_core.documents import Document

class LegalClauseSplitter(TextSplitter):
    """
    Splits legal documents by clauses (e.g., "1.1", "Article I", "Section 2.3").
    Preserves the clause number in metadata.
    """
    
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        # Regex patterns for common legal clause headers
        self.clause_patterns = [
            r"^\s*ARTICLE\s+[IVX0-9]+",           # ARTICLE I, ARTICLE 1
            r"^\s*SECTION\s+[0-9]+(\.[0-9]+)*",   # SECTION 2.1, SECTION 3
            r"^\s*[0-9]+\.[0-9]+(\.[0-9]+)*",     # 1.1, 1.1.1 (Common in commercial contracts)
            r"^\s*[0-9]+\.\s+[A-Z]",              # 1. Definitions (Numbered headers)
        ]
        self.combined_pattern = re.compile("|".join(self.clause_patterns), re.IGNORECASE | re.MULTILINE)

    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks based on clause boundaries.
        Note: This method returns raw text chunks. 
        metadata logic is handled in create_documents.
        """
        # This basic split_text doesn't easily support metadata attachment per chunk 
        # based on the header found *within* the text if we just return strings.
        # So we primarily rely on create_documents or implement internal logic here.
        
        # For this implementation, we will perform the splitting and return text.
        # The metadata extraction typically happens during the processing.
        
        lines = text.splitlines()
        chunks = []
        current_chunk = []
        
        for line in lines:
            if self.combined_pattern.match(line):
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                current_chunk = [line]
            else:
                current_chunk.append(line)
                
        if current_chunk:
            chunks.append("\n".join(current_chunk))
            
        return chunks

    def create_documents(self, texts: List[str], metadatas: Optional[List[dict]] = None) -> List[Document]:
        """
        Create documents from a list of texts.
        This override allows us to extract the clause number from the *start* of the text
        and add it to metadata.
        """
        documents = []
        for i, text in enumerate(texts):
            # If input is a list of full documents, we split each.
            # Usually 'texts' here is a list of file contents.
            
            # We first split the full text into clauses
            clauses = self.split_text(text)
            
            base_metadata = metadatas[i] if metadatas else {}
            
            for clause in clauses:
                # Extract clause number/header for metadata
                match = self.combined_pattern.match(clause)
                clause_id = match.group(0).strip() if match else "Intro/Recitals"
                
                # Clean up metadata
                chunk_metadata = base_metadata.copy()
                chunk_metadata["clause_id"] = clause_id
                
                # Heuristic for clause type
                if "indemn" in clause.lower():
                    chunk_metadata["details"] = "Indemnity"
                elif "terminat" in clause.lower():
                    chunk_metadata["details"] = "Termination"
                elif "liabil" in clause.lower():
                    chunk_metadata["details"] = "Liability"
                
                documents.append(Document(page_content=clause, metadata=chunk_metadata))
                
        return documents
