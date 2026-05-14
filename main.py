import os
import sys
import traceback
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure project root is in path.
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ingestion.ingestion_loader import DocumentLoader
from src.ingestion.legal_splitter import LegalClauseSplitter
from src.retrieval.vector_storage import VectorStoreManager
from src.utils.project_config import Config
from src.workflows.workflow_graph import create_workflow

app = FastAPI(title="AI Legal Document Analyzer", version="1.0.0")

# Serve the frontend assets used by the static UI.
app.mount("/static", StaticFiles(directory="web/static"), name="static")


class QueryRequest(BaseModel):
    query: str


@app.get("/", response_class=HTMLResponse)
async def serve_home():
    """Serve the main UI."""
    html_path = project_root / "web" / "index.html"
    with open(html_path, "r", encoding="utf-8") as file:
        return file.read()


@app.post("/api/ingest")
async def handle_ingestion(file: UploadFile = File(...)):
    """Process and ingest a legal document (PDF, DOCX, TXT)."""
    try:
        Config.validate_api_key()

        content = await file.read()
        try:
            text = DocumentLoader.load(content, file.filename)
        except ValueError as error:
            return JSONResponse({"status": "error", "detail": str(error)}, status_code=400)

        splitter = LegalClauseSplitter()
        docs = splitter.create_documents([text], metadatas=[{"source": file.filename}])

        vs_manager = VectorStoreManager()
        ids = vs_manager.add_documents(docs, clear_existing=True)

        return {
            "status": "success",
            "num_clauses": len(ids),
            "filename": file.filename,
            "message": f"Successfully processed {len(ids)} clauses from '{file.filename}'",
        }

    except Exception as error:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(error))


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
            "overall_report": {},
        }

        result = await workflow.ainvoke(state)

        return {
            "status": "success",
            "answer": result.get("final_answer", "No answer generated."),
            "overall_report": result.get("overall_report", {}),
            "num_clauses_analyzed": len(result.get("risk_analysis", [])),
        }

    except Exception as error:
        traceback.print_exc()
        error_message = str(error)

        # Handle quota errors gracefully.
        if "429" in error_message or "quota" in error_message.lower():
            return JSONResponse(
                {
                    "status": "success",
                    "answer": (
                        "⚠️ **API Quota Exceeded**\n\n"
                        "The free-tier Google Gemini API limit has been reached (typically 20 requests/day or 15 RPM).\n"
                        "Please wait a few minutes or until the next day and try again.\n\n"
                        "To increase limits, upgrade to a paid Google AI Studio plan."
                    ),
                    "num_clauses_analyzed": 0,
                }
            )

        return JSONResponse({"status": "error", "detail": error_message}, status_code=500)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}
