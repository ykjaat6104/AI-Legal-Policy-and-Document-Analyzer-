import sys
import os
import traceback
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# Ensure project root is in path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ingestion.ingestion_loader import DocumentLoader
from src.ingestion.legal_splitter import LegalClauseSplitter
from src.retrieval.vector_storage import VectorStoreManager
from src.workflows.workflow_graph import create_workflow
from src.utils.project_config import Config

app = FastAPI(title="AI Legal Document Analyzer", version="1.0.0")

# Serve static assets (CSS, JS)
app.mount("/static", StaticFiles(directory="web/static"), name="static")


class QueryRequest(BaseModel):
    query: str


@app.get("/", response_class=HTMLResponse)
async def serve_home():
    """Serve the main UI."""
    html_path = project_root / "web" / "index.html"
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/ingest")
async def handle_ingestion(file: UploadFile = File(...)):
    """Process and ingest a legal document (PDF, DOCX, TXT)."""
    try:
        Config.validate_api_key()

        content = await file.read()
        try:
            text = DocumentLoader.load(content, file.filename)
        except ValueError as ve:
            return JSONResponse({"status": "error", "detail": str(ve)}, status_code=400)

        splitter = LegalClauseSplitter()
        docs = splitter.create_documents([text], metadatas=[{"source": file.filename}])

        vs_manager = VectorStoreManager()
        ids = vs_manager.add_documents(docs, clear_existing=True)

        return {
            "status": "success",
            "num_clauses": len(ids),
            "filename": file.filename,
            "message": f"Successfully processed {len(ids)} clauses from '{file.filename}'"
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze")
async def handle_analysis(request: QueryRequest):
    """Run RAG + risk analysis workflow on the ingested document."""
    try:
        workflow = create_workflow()
        state = {
            "query": request.query,
            "documents": [],
            "risk_analysis": [],
            "final_answer": "",
            "overall_report": {}
        }

        result = await workflow.ainvoke(state)

        return {
            "status": "success",
            "answer": result.get("final_answer", "No answer generated."),
            "overall_report": result.get("overall_report", {}),
            "num_clauses_analyzed": len(result.get("risk_analysis", []))
        }

    except Exception as e:
        traceback.print_exc()
        error_msg = str(e)

        # Handle quota errors gracefully
        if "429" in error_msg or "quota" in error_msg.lower():
            return JSONResponse({
                "status": "success",
                "answer": (
                    "⚠️ **API Quota Exceeded**\n\n"
                    "The free-tier Google Gemini API limit has been reached (typically 20 requests/day or 15 RPM).\n"
                    "Please wait a few minutes or until the next day and try again.\n\n"
                    "To increase limits, upgrade to a paid Google AI Studio plan."
                ),
                "num_clauses_analyzed": 0
            })

        return JSONResponse({"status": "error", "detail": error_msg}, status_code=500)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    print("🏛  AI Legal Document Analyzer")
    print("   Server starting at http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)
