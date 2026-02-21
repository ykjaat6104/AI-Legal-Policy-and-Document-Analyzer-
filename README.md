# AI Legal Policy & Document Analyzer

A powerful web application for analyzing legal documents using advanced AI technologies. This tool allows users to upload legal documents (PDF, DOCX, TXT) and perform intelligent queries to extract insights, assess risks, and generate reports.

## Features

- **Document Ingestion**: Upload and process legal documents in PDF, DOCX, or TXT formats.
- **AI-Powered Analysis**: Use Google Gemini AI to analyze queries against ingested documents.
- **Vector Search**: Efficient retrieval of relevant clauses using ChromaDB vector database.
- **Risk Analysis**: Automated risk assessment and report generation.
- **Web Interface**: User-friendly web UI for uploading documents and querying.
- **REST API**: Programmatic access via RESTful endpoints.
- **CLI Tool**: Command-line interface for batch processing and analysis.

## Tech Stack

- **Backend**: Python, FastAPI
- **AI/ML**: LangChain, Google Generative AI (Gemini)
- **Database**: ChromaDB (vector database)
- **Document Processing**: PyPDF, python-docx, LangChain text splitters
- **Web Server**: Uvicorn
- **Frontend**: HTML/CSS/JS (static files in web/ directory)

## Data Flow Architecture Workflow

```
Legal Document (PDF/DOCX/TXT) ──┐
                                 ├──► Parse ──► Split Clauses ──► Clauses
                                 ▼
                         Generate Embeddings ──► Store in ChromaDB
                                 │
                                 ▼
                         User Query ──► Embed Query ──► Vector Search ──► Relevant Clauses
                                 │
                                 ▼
                         AI Analysis (Gemini) ──► Generate Report/Answer
                                 │
                                 ▼
                         Response to User (Web/API/CLI)
```

This ASCII diagram illustrates the data flow in the AI Legal Document Analyzer, ensuring efficient, scalable, and accurate legal document analysis.

## Installation

### Prerequisites

- Python 3.8+
- A Google Cloud API key with Generative AI API enabled

### Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ai_legal_analyzer1
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   - Copy `.env` file and set your Google API key:
     ```
     GOOGLE_API_KEY=your_google_api_key_here
     ```

4. **Run the application**:
   ```bash
   python web_server.py
   ```

   The server will start at `http://localhost:8001`.

## Usage

### Web Interface

1. Open your browser and navigate to `http://localhost:8001`.
2. Upload a legal document (PDF, DOCX, or TXT).
3. Ask questions about the document in the query field.
4. View the analysis results and reports.

### API Endpoints

- `GET /`: Serve the main web interface.
- `POST /api/ingest`: Upload and ingest a legal document.
  - Body: `file` (multipart/form-data)
  - Response: JSON with status and document ID.
- `POST /api/analyze`: Analyze a query against ingested documents.
  - Body: JSON `{"query": "your question here"}`
  - Response: JSON with analysis results.
- `GET /api/health`: Health check endpoint.
  - Response: JSON with status and version.

### CLI Usage

The application includes a command-line interface for batch processing:

#### Ingest a document:
```bash
python main.py ingest path/to/document.pdf
```

#### Analyze a query:
```bash
python main.py analyze "What are the termination conditions?"
```

#### Examples:
```bash
python main.py ingest samples/saas_contract.txt
python main.py analyze "What is the liability cap?"
```

## Configuration

- **GOOGLE_API_KEY**: Your Google Cloud API key for Generative AI.
- **Port**: Server runs on port 8001 by default (configurable in `web_server.py`).
- **Vector DB**: ChromaDB persists data in the `chroma_db/` directory.

## Project Structure

```
ai_legal_analyzer1/
├── src/
│   └── ai_legal_analyzer/
│       ├── ingestion/
│       │   ├── ingestion_loader.py
│       │   └── legal_splitter.py
│       ├── retrieval/
│       │   └── vector_storage.py
│       ├── utils/
│       │   └── project_config.py
│       └── workflows/
│           └── workflow_graph.py
├── web/
│   ├── index.html
│   └── static/
├── tests/
├── samples/
├── main.py
├── web_server.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Add tests if applicable.
5. Submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for informational purposes only and does not constitute legal advice. Always consult with qualified legal professionals for legal matters.
