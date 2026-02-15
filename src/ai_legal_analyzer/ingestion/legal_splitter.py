import re
import logging
from typing import List, Optional, Any
from langchain_text_splitters import TextSplitter
from langchain_core.documents import Document

logger = logging.getLogger("splitter")

class LegalClauseSplitter(TextSplitter):
    # split text by common legal markers like ARTICLE I or Section 1.1
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # regex for headers
        patterns = [
            r"^\s*ARTICLE\s+[IVX0-9]+",
            r"^\s*SECTION\s+[0-9]+(\.[0-9]+)*",
            r"^\s*[0-9]+\.[0-9]+(\.[0-9]+)*",
            r"^\s*[0-9]+\.\s+[A-Z]",
        ]
        self._pattern = re.compile("|".join(patterns), re.IGNORECASE | re.MULTILINE)

    def split_text(self, text: str):
        # basic line split loop
        if not text: return []
        lines = text.splitlines()
        chunks = []
        current = []
        for line in lines:
            if self._pattern.match(line):
                if current: chunks.append("\n".join(current))
                current = [line]
            else:
                current.append(line)
        if current: chunks.append("\n".join(current))
        return chunks

    def create_documents(self, texts, metadatas=None):
        # convert text to docs with metadata
        documents = []
        for i, text in enumerate(texts):
            clauses = self.split_text(text)
            base = metadatas[i] if metadatas else {}
            for clause in clauses:
                match = self._pattern.match(clause)
                id = match.group(0).strip() if match else "Intro"
                meta = base.copy()
                meta["clause_id"] = id
                documents.append(Document(page_content=clause, metadata=meta))
        return documents
