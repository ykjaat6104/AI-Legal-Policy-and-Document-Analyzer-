"""
Integration test scenarios — requires a valid GOOGLE_API_KEY in .env
Run: python tests/test_scenarios.py
"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_legal_analyzer.ingestion.ingestion_loader import DocumentLoader
from src.ai_legal_analyzer.ingestion.legal_splitter import LegalClauseSplitter
from src.ai_legal_analyzer.retrieval.vector_storage import VectorStoreManager
from src.ai_legal_analyzer.workflows.workflow_graph import create_workflow

SAMPLES_DIR = Path(__file__).parent.parent / "samples"


async def run_scenario(filename: str, query: str):
    print(f"\n{'='*60}")
    print(f"  Scenario: {filename}")
    print(f"  Query: {query}")
    print('='*60)

    file_path = SAMPLES_DIR / filename
    with open(file_path, "rb") as f:
        content = f.read()

    text = DocumentLoader.load(content, filename)
    splitter = LegalClauseSplitter()
    docs = splitter.create_documents([text], metadatas=[{"source": filename}])
    print(f"  → Ingested {len(docs)} clauses")

    vs = VectorStoreManager()
    vs.add_documents(docs, clear_existing=True)

    workflow = create_workflow()
    state = {
        "query": query,
        "documents": [],
        "risk_analysis": [],
        "final_answer": "",
        "overall_report": {}
    }

    result = await workflow.ainvoke(state)
    print("\nResult:")
    print(result["final_answer"])
    return result["final_answer"]


async def main():
    # Scenario A: AI usage restrictions in NDA
    await run_scenario(
        "sample_nda.txt",
        "Does this contract permit the use of OpenAI to summarize it?"
    )

    # Scenario B: Liability cap
    await run_scenario(
        "sample_vendor_agreement.txt",
        "What is the maximum liability cap in this contract?"
    )

    # Scenario C: Termination for convenience
    await run_scenario(
        "sample_vendor_agreement.txt",
        "Can this contract be terminated for convenience?"
    )

    # Scenario D: Full SaaS contract analysis
    await run_scenario(
        "saas_contract.txt",
        "What are the high-risk clauses in this contract?"
    )


if __name__ == "__main__":
    asyncio.run(main())
