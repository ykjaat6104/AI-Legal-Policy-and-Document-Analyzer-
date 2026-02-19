import argparse
import sys
import os
import asyncio

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.project_config import Config
from src.ingestion.legal_splitter import LegalClauseSplitter
from src.retrieval.vector_storage import VectorStoreManager
from src.workflows.workflow_graph import create_workflow


async def ingest_file(file_path: str):
    """Ingest a legal document into the vector store."""
    print(f"[INFO] Reading file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        print(f"[ERROR] Failed to read file: {e}")
        return

    print("[INFO] Splitting into clauses…")
    splitter = LegalClauseSplitter()
    docs = splitter.create_documents([text], metadatas=[{"source": file_path}])
    print(f"[INFO] Generated {len(docs)} clauses.")

    print("[INFO] Storing in Vector DB…")
    vs_manager = VectorStoreManager()
    ids = vs_manager.add_documents(docs)
    print(f"[INFO] Successfully stored {len(ids)} clauses. Done!")


async def run_analysis(query: str):
    """Run the full RAG analysis workflow."""
    print(f"[INFO] Analyzing query: '{query}'")
    workflow = create_workflow()

    initial_state = {
        "query": query,
        "documents": [],
        "risk_analysis": [],
        "final_answer": "",
        "overall_report": {}
    }

    result = await workflow.ainvoke(initial_state)

    print("\n" + "=" * 60)
    print("  ANALYSIS RESULT")
    print("=" * 60)
    print(result.get("final_answer", "No answer generated."))
    print("=" * 60 + "\n")


async def main():
    parser = argparse.ArgumentParser(
        description="AI Legal Document Analyzer — CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py ingest samples/saas_contract.txt
  python main.py analyze "What are the termination conditions?"
  python main.py analyze "What is the liability cap?"
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    ingest_parser = subparsers.add_parser("ingest", help="Ingest a legal document")
    ingest_parser.add_argument("file", help="Path to TXT/PDF/DOCX file")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a query against ingested documents")
    analyze_parser.add_argument("query", help="Legal question or analysis request")

    args = parser.parse_args()

    if args.command == "ingest":
        await ingest_file(args.file)
    elif args.command == "analyze":
        await run_analysis(args.query)
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
