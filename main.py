import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ai_legal_analyzer.utils.project_config import Config
from src.ai_legal_analyzer.ingestion.legal_splitter import LegalClauseSplitter
from src.ai_legal_analyzer.retrieval.vector_storage import VectorStoreManager
from src.ai_legal_analyzer.workflows.workflow_graph import create_workflow

def ingest_file(file_path: str):
    """
    Ingest a legal document into the vector store.
    """
    print(f"I: Reading file {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        print(f"E: Failed to read file: {e}")
        return

    print("I: Splitting text into clauses...")
    splitter = LegalClauseSplitter()
    docs = splitter.create_documents([text], metadatas=[{"source": file_path}])
    print(f"I: Generated {len(docs)} clauses.")
    
    print("I: Storing in Vector DB...")
    vs_manager = VectorStoreManager()
    ids = vs_manager.add_documents(docs)
    print(f"I: Successfully stored {len(ids)} clauses.")

def run_analysis(query: str):
    """
    Run the RAG analysis workflow.
    """
    print(f"I: Analyzing query: '{query}'")
    
    workflow = create_workflow()
    
    initial_state = {
        "query": query,
        "documents": [],
        "risk_analysis": [],
        "final_answer": ""
    }
    
    result = workflow.invoke(initial_state)
    
    print("\n=== FINAL ANSWER ===\n")
    print(result.get("final_answer"))
    print("\n====================\n")

def main():
    parser = argparse.ArgumentParser(description="AI Legal Document Analyzer")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Ingest Command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest a document")
    ingest_parser.add_argument("file", help="Path to the text file")
    
    # Analyze Command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a query")
    analyze_parser.add_argument("query", help="The legal query or analysis request")
    
    args = parser.parse_args()
    
    if args.command == "ingest":
        ingest_file(args.file)
    elif args.command == "analyze":
        run_analysis(args.query)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
