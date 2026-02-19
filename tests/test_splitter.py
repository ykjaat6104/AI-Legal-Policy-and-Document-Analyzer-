import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ai_legal_analyzer.ingestion.legal_splitter import LegalClauseSplitter


class TestLegalClauseSplitter(unittest.TestCase):

    def test_split_numbered_clauses(self):
        text = """1.1 Definitions
"Agreement" means this document.

1.2 Term
The term of this agreement is 1 year."""
        splitter = LegalClauseSplitter()
        docs = splitter.create_documents([text])
        non_empty = [d for d in docs if d.page_content.strip()]
        self.assertEqual(len(non_empty), 2)
        self.assertEqual(non_empty[0].metadata["clause_id"], "1.1")
        self.assertEqual(non_empty[1].metadata["clause_id"], "1.2")

    def test_split_articles(self):
        text = """ARTICLE I: INTRO
Here is the intro.

ARTICLE II: TERMS
Here are the terms."""
        splitter = LegalClauseSplitter()
        docs = splitter.create_documents([text])
        non_empty = [d for d in docs if d.page_content.strip()]
        self.assertEqual(len(non_empty), 2)
        self.assertIn("ARTICLE I", non_empty[0].metadata["clause_id"])

    def test_intro_fallback(self):
        text = "This is a preamble with no clause markers."
        splitter = LegalClauseSplitter()
        docs = splitter.create_documents([text])
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].metadata["clause_id"], "Intro")

    def test_empty_text(self):
        splitter = LegalClauseSplitter()
        docs = splitter.create_documents([""])
        self.assertEqual(len(docs), 0)

    def test_metadata_preserved(self):
        text = "1.1 Term\nThe term is 1 year."
        splitter = LegalClauseSplitter()
        docs = splitter.create_documents([text], metadatas=[{"source": "test.txt"}])
        self.assertEqual(docs[0].metadata["source"], "test.txt")


if __name__ == "__main__":
    unittest.main()
