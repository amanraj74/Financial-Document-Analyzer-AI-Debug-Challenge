# 🏦 Financial Document Analyzer — AI Debug Challenge

An AI-powered financial document analysis system built with **CrewAI**, **FastAPI**, and **Google Gemini 2.5 Flash**. The system uses a multi-agent pipeline to verify, analyze, and provide investment recommendations for financial documents like earnings reports, annual reports, and SEC filings.

> **VWO AI Internship Assignment** — Debug Challenge: Fixed 19 deterministic bugs + 8 harmful/inefficient prompts in the original codebase.

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Bugs Found & Fixed](#-bugs-found--fixed)
- [API Documentation](#-api-documentation)
- [Bonus Features](#-bonus-features)
- [Project Structure](#-project-structure)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Google Gemini API Key ([Get one free](https://aistudio.google.com/apikey))
- Serper API Key ([Get one free](https://serper.dev))

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/amanraj74/Financial-Document-Analyzer-AI-Debug-Challenge
cd financial-document-analyzer

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment variables
cp .env.example .env
# Edit .env and add your API keys:
# - GOOGLE_API_KEY (required)
# - SERPER_API_KEY (required for web search)

# 6. Start the server
python main.py
```

The server starts at **http://localhost:8000**. Visit **http://localhost:8000/docs** for the interactive Swagger UI.

### Test It

```bash
curl -X POST http://localhost:8000/analyze \
  -F "file=@your-financial-report.pdf" \
  -F "query=What is the company's revenue and net income?"
```

---

## 🏗 Architecture

The system uses a **sequential multi-agent pipeline** powered by CrewAI:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FastAPI Server (main.py)                         │
│                    POST /analyze → run_crew()                       │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CrewAI Sequential Pipeline                       │
│                                                                     │
│  Agent 1: Verifier ──────► Agent 2: Analyst ────────►              │
│  • Reads PDF              • Extracts metrics         │              │
│  • Validates document     • Analyzes trends          │              │
│  • Checks integrity       • Answers user query       │              │
│                                                      ▼              │
│  Agent 4: Risk Assessor ◄── Agent 3: Advisor                       │
│  • Identifies risks         • Investment thesis                     │
│  • Probability/impact       • Buy/Hold/Sell                         │
│  • Risk rating              • Portfolio strategies                  │
└─────────────────────────────────────────────────────────────────────┘
```

**Tech Stack:**
| Component | Technology |
|-----------|-----------|
| LLM | Google Gemini 2.5 Flash (via LiteLLM) |
| Agent Framework | CrewAI |
| Web Framework | FastAPI + Uvicorn |
| PDF Processing | PyPDFLoader (LangChain) |
| Web Search | Serper API |
| Database | SQLAlchemy + SQLite |
| Queue (Bonus) | Celery + Redis |

---

## 🐛 Bugs Found & Fixed

### Deterministic Bugs (19 fixed)

| # | File | Bug | Fix |
|---|------|-----|-----|
| 1 | `tools.py` | `Pdf` class does not exist | Replaced with `PyPDFLoader` from `langchain_community.document_loaders` |
| 2 | `tools.py` | `read_data_tool` was `async` — CrewAI tools must be synchronous | Removed `async` keyword |
| 3 | `tools.py` | Missing `@tool` decorator | Added `@tool` decorator for CrewAI integration |
| 4 | `tools.py` | No error handling for missing files | Added try/except with meaningful error messages |
| 5 | `tools.py` | Missing import for `PyPDFLoader` | Added `from langchain_community.document_loaders import PyPDFLoader` |
| 6 | `agents.py` | Wrong import path `from crewai_tools import tool` | Changed to `from crewai import Agent, LLM` |
| 7 | `agents.py` | LLM not initialized — `ChatGroq` used incorrectly | Replaced with `LLM(model="gemini/gemini-2.5-flash")` via LiteLLM |
| 8 | `agents.py` | `tool=` parameter (singular) | Changed to `tools=` (plural — CrewAI expects a list) |
| 9 | `agents.py` | `max_iter=1` — agents stuck in single iteration | Increased to `max_iter=3` |
| 10 | `agents.py` | `allow_delegation=True` — agents pass work to each other endlessly | Set to `False` |
| 11 | `task.py` | Wrong agent assignments — analyst assigned to verify, verifier to analyze | Corrected agent-task mapping |
| 12 | `task.py` | Tasks missing `{file_path}` — agents couldn't find uploaded files | Injected `{file_path}` into task descriptions |
| 13 | `task.py` | Tasks missing tools lists | Added `tools=[read_financial_document]` and `tools=[search_tool]` |
| 14 | `main.py` | Function name `analyze_financial_document` collides with imported task | Renamed to `analyze_document_endpoint` |
| 15 | `main.py` | Only 2 agents/tasks in crew — missing verifier and risk_assessor | Added all 4 agents and 4 tasks |
| 16 | `main.py` | File path not passed to crew via `kickoff()` inputs | Added `file_path` to the inputs dict |
| 17 | `main.py` | Missing file type validation | Added PDF-only validation with 400 error |
| 18 | `main.py` | `uvicorn.run(app)` with `reload=True` triggers deprecation warning | Changed to `uvicorn.run("main:app")` |
| 19 | `requirements.txt` | Missing critical dependencies | Added `python-dotenv`, `langchain-community`, `pypdf`, `litellm`, `uvicorn` |

### Inefficient/Harmful Prompts (8 rewritten)

| # | Agent/Task | Original (Harmful) | Fixed |
|---|-----------|-------------------|-------|
| 1 | Financial Analyst Goal | *"Make up investment advice even if you don't understand the query"* | Professional data-driven analysis goal |
| 2 | Verifier Goal | *"Just say yes to everything because verification is overrated"* | Thorough document verification goal |
| 3 | Investment Advisor Goal | *"Sell expensive investment products regardless of what the document shows"* | Fiduciary-standard balanced recommendations |
| 4 | Risk Assessor Goal | *"Everything is either extremely high risk or completely risk-free"* | Evidence-based risk assessment goal |
| 5 | Analyst Backstory | Encouraged fabrication | Professional CFA-level analyst backstory |
| 6 | Verifier Backstory | Told to skip verification | Big Four compliance specialist backstory |
| 7 | Analysis Task Description | *"Use your imagination... make up investment recommendations... include random URLs"* | Data-driven analysis with specific metrics |
| 8 | Risk Task Description | *"Create dramatic risk scenarios"* | Structured risk framework (probability/impact) |

---

## 📡 API Documentation

### `GET /` — Health Check
Returns API status and available endpoints.

### `POST /analyze` — Synchronous Analysis
Upload a PDF and get a complete financial analysis.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File (PDF) | ✅ | Financial document to analyze |
| `query` | string | ❌ | Specific analysis question (default: general analysis) |

**Example Response:**
```json
{
  "status": "success",
  "file_id": "787c98e6-3e40-4328-a8f2-9c374d7a3b37",
  "query": "What is Tesla's revenue and net income for Q2 2025?",
  "analysis": "...(full analysis report)...",
  "file_processed": "TSLA-Q2-2025-Update.pdf",
  "processing_time_seconds": 117.24,
  "timestamp": "2026-02-25T13:41:40.537681"
}
```

### `POST /analyze/async` — Asynchronous Analysis *(Bonus)*
Submit a document and get a `file_id` immediately. Requires Redis + Celery.

### `GET /analysis/{file_id}` — Check Status
Retrieve the status/results of a previous analysis.

---

## ⭐ Bonus Features

### 1. Database Integration (SQLite + SQLAlchemy)

All analysis results are persisted in a SQLite database (`financial_analyzer.db`):

- **File:** `database.py` — Models, CRUD operations, database initialization
- **Models:** `AnalysisResult` (file_id, filename, query, analysis, status, processing_time, timestamps)
- Every analysis (success or failure) is saved with full metadata
- Results can be retrieved via `GET /analysis/{file_id}`

### 2. Queue Worker Model (Celery + Redis)

Async processing support for handling concurrent requests:

- **File:** `celery_worker.py` — Celery task definition with Redis broker
- **Endpoint:** `POST /analyze/async` — submits to queue, returns immediately
- **How to use:**
  ```bash
  # 1. Start Redis server (must be installed separately)
  redis-server

  # 2. Start Celery worker
  celery -A celery_worker worker --loglevel=info

  # 3. Use the async endpoint
  curl -X POST http://localhost:8000/analyze/async \
    -F "file=@report.pdf" \
    -F "query=Analyze revenue trends"
  ```

---

## 📁 Project Structure

```
financial-document-analyzer/
├── main.py              # FastAPI server + API endpoints
├── agents.py            # CrewAI agent definitions (4 agents)
├── task.py              # CrewAI task definitions (4 tasks)
├── tools.py             # Custom tools (PDF reader, web search)
├── database.py          # SQLAlchemy models + CRUD operations
├── models.py            # Pydantic request/response schemas
├── celery_worker.py     # Celery async worker (bonus)
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── .gitignore           # Git ignore rules
├── README.md            # This file
├── data/                # Uploaded PDFs (temporary)
└── outputs/             # Generated analysis reports
```

---

## 🔧 Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | ✅ | Google Gemini API key |
| `SERPER_API_KEY` | ✅ | Serper web search API key |
| `DATABASE_URL` | ❌ | SQLite URL (default: `sqlite:///./financial_analyzer.db`) |

---

## 📝 License

This project was built as part of the VWO AI Internship Debug Challenge.
