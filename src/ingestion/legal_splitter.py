import re
import logging
from typing import List, Optional
from langchain_text_splitters import TextSplitter
from langchain_core.documents import Document

logger = logging.getLogger("splitter")


class LegalClauseSplitter(TextSplitter):
    """
    Splits legal documents on clause/article/section boundaries.
    Recognises patterns like: 1.1, 2.3.1, ARTICLE I, SECTION 5, 3. TITLE
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        patterns = [
            r"^\s*ARTICLE\s+[IVX0-9]+",
            r"^\s*SECTION\s+[0-9]+(\.[0-9]+)*",
            r"^\s*[0-9]+\.[0-9]+(\.[0-9]+)*",
            r"^\s*[0-9]+\.\s+[A-Z]",
        ]
        self._pattern = re.compile("|".join(patterns), re.IGNORECASE | re.MULTILINE)

    def split_text(self, text: str) -> List[str]:
        if not text:
            return []
        lines = text.splitlines()
        chunks: List[str] = []
        current: List[str] = []

        for line in lines:
            if self._pattern.match(line):
                if current:
                    chunks.append("\n".join(current))
                current = [line]
            else:
                current.append(line)

        if current:
            chunks.append("\n".join(current))

        return chunks

    def create_documents(self, texts: List[str], metadatas: Optional[List[dict]] = None) -> List[Document]:
        documents: List[Document] = []
        for i, text in enumerate(texts):
            clauses = self.split_text(text)
            base_meta = metadatas[i] if metadatas else {}
            for clause in clauses:
                if not clause.strip():
                    continue
                match = self._pattern.match(clause)
                clause_id = match.group(0).strip() if match else "Intro"
                meta = base_meta.copy()
                meta["clause_id"] = clause_id
                documents.append(Document(page_content=clause, metadata=meta))
        return documents
