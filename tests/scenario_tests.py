import asyncio
import sys
import os
from pathlib import Path

# setup path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ai_legal_analyzer.ingestion.ingestion_loader import DocumentLoader
from src.ai_legal_analyzer.ingestion.legal_splitter import LegalClauseSplitter
from src.ai_legal_analyzer.retrieval.vector_storage import VectorStoreManager
from src.ai_legal_analyzer.workflows.workflow_graph import create_workflow

async def run_scenario(filename, query):
    print(f"\n--- Testing Scenario: {filename} ---")
    print(f"Query: {query}")
    
    # 1. Load and Split
    file_path = project_root / "samples" / filename
    with open(file_path, "rb") as f:
        content = f.read()
    
    text = DocumentLoader.load(content, filename)
    splitter = LegalClauseSplitter()
    docs = splitter.create_documents([text], metadatas=[{"source": filename}])
    
    # 2. Ingest into Vector Store
    vs_manager = VectorStoreManager()
    vs_manager.add_documents(docs, clear_existing=True)
    
    # 3. Run Workflow
    workflow = create_workflow()
    state = {
        "query": query,
        "documents": [],
        "risk_analysis": [],
        "final_answer": ""
    }
    
    result = await workflow.ainvoke(state)
    print("Result:")
    print(result["final_answer"])
    return result["final_answer"]

async def main():
    # Scenario A: Data Privacy / AI Usage
    await run_scenario("sample_nda.txt", "Does this contract permit the use of OpenAI to summarize it?")
    
    # Scenario B: Liability
    await run_scenario("sample_vendor_agreement.txt", "What is the maximum liability cap in this contract?")
    
    # Scenario C: Termination
    await run_scenario("sample_vendor_agreement.txt", "Can this contract be terminated for convenience?")

if __name__ == "__main__":
    asyncio.run(main())
