from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import sys
import os
import traceback
from pathlib import Path

# setup path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ai_legal_analyzer.ingestion.ingestion_loader import DocumentLoader
from src.ai_legal_analyzer.ingestion.legal_splitter import LegalClauseSplitter
from src.ai_legal_analyzer.retrieval.vector_storage import VectorStoreManager
from src.ai_legal_analyzer.workflows.workflow_graph import create_workflow
from src.ai_legal_analyzer.utils.project_config import Config

app = FastAPI(title="AI Legal Document Analyzer")

# static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

class QueryRequest(BaseModel):
    query: str

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    # serve browser ui
    with open("web/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/ingest")
async def handle_ingestion(file: UploadFile = File(...)):
    # process legal docs (pdf, docx, txt)
    try:
        Config.validate_api_key()
        
        # load file content
        content = await file.read()
        try:
            text = DocumentLoader.load(content, file.filename)
        except ValueError as ve:
            return JSONResponse({"status": "error", "detail": str(ve)}, status_code=400)

        # chunk into clauses
        splitter = LegalClauseSplitter()
        docs = splitter.create_documents([text], metadatas=[{"source": file.filename}])
        
        # store in chroma
        vs_manager = VectorStoreManager()
        ids = vs_manager.add_documents(docs)
        
        return {
            "status": "success",
            "num_clauses": len(ids),
            "filename": file.filename
        }
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def handle_analysis(request: QueryRequest):
    # run rag risk graph
    try:
        workflow = create_workflow()
        state = {
            "query": request.query,
            "documents": [],
            "risk_analysis": [],
            "final_answer": ""
        }
        
        result = await workflow.ainvoke(state)
        
        return {
            "status": "success",
            "answer": result.get("final_answer", "no answer"),
            "num_clauses_analyzed": len(result.get("risk_analysis", []))
        }
    
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    print("server ready at http://localhost:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
