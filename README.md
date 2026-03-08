<div align="center">

# 🤖 DocuChat AI

### Enterprise-Grade RAG Chatbot for Intelligent Document Interaction

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-Visit_Site-blue?style=for-the-badge)](https://docuchartai-production.up.railway.app/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg?style=for-the-badge&logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg?style=for-the-badge&logo=typescript)](https://www.typescriptlang.org/)

![DocuChat AI Interface](./assets/screenshot.png)

*A premium, modern interface for document-powered AI conversations with dark/light theming*

[Features](#-features) • [Architecture](#-architecture) • [Tech Stack](#-tech-stack) • [Installation](#-installation) • [API Reference](#-api-reference) • [Testing](#-testing) • [Deployment](#-deployment)

</div>

---

## 📖 Overview

**DocuChat AI** is a production-ready, full-stack **Retrieval-Augmented Generation (RAG)** system that transforms how users interact with their documents. Upload PDFs, Word files, Excel sheets, CSVs, or plain text files—then ask questions in natural language and receive accurate, source-cited answers enriched with auto-generated data visualizations.

### 🎯 The Problem It Solves

Modern professionals spend **hours** sifting through dense documents to extract specific information. Traditional search falls short when you need:

- **Context-aware answers** — not just keyword matching
- **Synthesized insights** — from multiple sections across documents
- **Data-driven charts** — auto-generated from tabular content
- **Source citations** — for every claim, with relevance scores
- **Persistent sessions** — resume conversations from any device

DocuChat AI eliminates this friction by combining BM25 sparse retrieval, LLM-powered summarization, and intelligent data visualization in one seamless interface.

---

## ✨ Features

### 🚀 Core Capabilities

| Feature | Description |
|---------|-------------|
| 📄 **Multi-Format Document Support** | Upload and process PDF, DOCX, XLSX, CSV, and TXT files up to 50MB |
| 🔍 **BM25 + TF-IDF Hybrid Search** | Lightweight, zero-dependency retrieval engine with Okapi BM25 scoring and IDF boosting |
| 💡 **Auto-Generated Summaries** | Comprehensive document summaries generated on upload via LLM |
| 📊 **Smart Data Visualization** | Detects tabular/numerical data and renders interactive Bar, Line, and Pie charts |
| 🏷️ **Source Citations** | Every answer includes expandable citations with relevance scores and document references |
| 💬 **Multi-Conversation Sessions** | Create, switch, and manage multiple conversation threads within a session |
| 🌗 **Dark / Light Mode** | Premium UI with dynamic theme switching persisted across sessions |
| 🗂️ **Document Management** | View, track processing status, and delete uploaded documents |
| 📈 **Performance Metrics** | Built-in query tracking with response times, confidence scores, and success rates |
| 🔒 **API Key Authentication** | Secure endpoints with header-based API key verification |
| ⏱️ **Rate Limiting** | Configurable request throttling via SlowAPI to prevent abuse |
| 🧹 **Auto-Cleanup** | Automated purge of stale sessions and data older than configurable thresholds |

### 🎨 User Experience

| Feature | Description |
|---------|-------------|
| 🖱️ **Drag & Drop Upload** | Effortless file management with drag-and-drop zone |
| ↔️ **Resizable Panels** | Drag-to-resize sidebar and document panels with persistence |
| 📱 **Responsive Design** | Flawless experience across desktop, tablet, and mobile viewports |
| 🎯 **Welcome View** | Guided onboarding with quick-start prompts for first-time users |
| 💬 **Message Bubbles** | Rich message rendering with Markdown support, code blocks, and embedded charts |
| ⚠️ **Graceful Error Handling** | User-friendly error messages with fallback states |
| 🔄 **Document Processing Status** | Real-time polling to show upload → processing → ready state transitions |

---

## 🏗️ Architecture

### High-Level System Overview

```mermaid
graph TB
    subgraph Frontend ["Frontend (React + TypeScript)"]
        UI[App Shell] --> SB[Sidebar]
        UI --> CI[Chat Interface]
        UI --> DL[Document List]
        UI --> FU[File Upload]
        CI --> MB[Message Bubbles]
        CI --> CV[Chart Visualizer]
        UI --> API_SVC[API Service Layer]
    end

    subgraph Backend ["Backend (FastAPI)"]
        MAIN[main.py — App Router] --> EP[endpoints.py — RAG Chat API]
        MAIN --> APP[app.py — Hybrid Search API]
        EP --> DP[Document Processor]
        EP --> PI[Page Index — BM25]
        EP --> LLM[LLM Client]
        EP --> SM[Session Manager]
        APP --> IDX[Hybrid Indexer]
        APP --> MT[Metrics Tracker]
    end

    subgraph Storage ["Data Layer"]
        DB[(Supabase PostgreSQL)]
        FS[Local File Index — JSON]
    end

    API_SVC -->|REST API| MAIN
    DP -->|Extract & Chunk| PI
    PI -->|BM25 Search| EP
    LLM -->|OpenRouter / OpenAI| EXT_LLM[LLM API]
    SM --> DB
    EP --> DB
    PI --> FS
    MT --> FS
```

### RAG Pipeline — Deep Dive

#### 1. Document Ingestion

```
User uploads file → Backend receives via FastAPI UploadFile
  ↓
DocumentProcessor.detect_file_type() → Identifies PDF / DOCX / XLSX / CSV / TXT
  ↓
DocumentProcessor.extract_text() → Extracts text using PyPDF2, pdfplumber, python-docx, or pandas
  ↓
DocumentProcessor.chunk_text() → Splits into 2000-char chunks with 400-char overlap
  ↓
PageIndex.add_document_chunks() → Tokenizes, calculates TF, rebuilds IDF scores
  ↓
LLMClient.generate_summary() → Produces structured summary via LLM
  ↓
Database: Document record saved with metadata + summary
```

#### 2. Query Processing

```
User asks a question → POST /api/chat
  ↓
PageIndex.search() → BM25 + TF-IDF scoring → Top 5 relevant chunks retrieved
  ↓
LLMClient.generate_chat_response() → Prompt constructed with context chunks + conversation history
  ↓
LLM generates answer (grounded ONLY in provided context) with source attribution
  ↓
LLMClient._detect_chart_need() → Checks if response contains chartable data
  ↓
If chart needed: LLMClient._extract_chart_data() → Extracts structured JSON for visualization
  ↓
Response returned with: answer, sources (with relevance scores), optional chart_data
```

#### 3. Data Visualization

```
Chat response contains structured data → Frontend parses chart_data JSON
  ↓
ChartVisualizer.tsx → Renders using Recharts library
  ↓
Supported types: BarChart, LineChart, PieChart
  ↓
Chart linked to Message via Chart model in database
```

---

## 🛠️ Tech Stack

### Backend

| Technology | Purpose |
|-----------|---------|
| [FastAPI](https://fastapi.tiangolo.com/) | High-performance async Python web framework |
| [SQLAlchemy](https://www.sqlalchemy.org/) | ORM for database models and queries |
| [Supabase](https://supabase.com/) (PostgreSQL) | Cloud-hosted relational database for persistence |
| [BM25 (rank_bm25)](https://github.com/dorianbrown/rank_bm25) | Sparse retrieval algorithm for document search |
| [OpenAI / OpenRouter](https://openrouter.ai/) | LLM API integration for chat and summarization |
| [PyPDF2](https://pypdf2.readthedocs.io/) + [pdfplumber](https://github.com/jsvine/pdfplumber) | PDF text extraction |
| [python-docx](https://python-docx.readthedocs.io/) | DOCX text extraction |
| [pandas](https://pandas.pydata.org/) + [openpyxl](https://openpyxl.readthedocs.io/) | Excel/CSV tabular data parsing |
| [SlowAPI](https://github.com/laurentS/slowapi) | Rate limiting middleware |
| [tiktoken](https://github.com/openai/tiktoken) | Token counting for cost estimation |
| [Alembic](https://alembic.sqlalchemy.org/) | Database migration management |

### Frontend

| Technology | Purpose |
|-----------|---------|
| [React 18](https://react.dev/) | Component-based UI framework |
| [TypeScript](https://www.typescriptlang.org/) | Type-safe JavaScript |
| [Vite](https://vitejs.dev/) | Lightning-fast build tool and dev server |
| [Material-UI (MUI)](https://mui.com/) | Premium component library |
| [Recharts](https://recharts.org/) | Composable charting library for data visualization |
| [Axios](https://axios-http.com/) | HTTP client for API communication |
| [Lucide React](https://lucide.dev/) | Beautiful, consistent icon library |
| [uuid](https://www.npmjs.com/package/uuid) | Session ID generation |

### DevOps & Infrastructure

| Technology | Purpose |
|-----------|---------|
| [Docker](https://www.docker.com/) | Multi-stage containerized builds (Node + Python) |
| [Railway](https://railway.app/) | Cloud hosting with auto-deploy from Dockerfile |
| [GitHub](https://github.com/) | Source control and CI/CD integration |

---

## 📁 Project Structure

```
DocuChartAI/
├── api/                          # FastAPI application layer
│   ├── __init__.py
│   ├── main.py                  # App entry point, SPA serving, CORS, router mounting
│   ├── app.py                   # Hybrid search API with rate limiting, caching, metrics
│   └── endpoints.py             # RAG chatbot endpoints (upload, chat, CRUD operations)
│
├── src/                          # Core business logic
│   ├── __init__.py
│   ├── database.py              # SQLAlchemy engine, session factory, environment diagnostics
│   ├── models.py                # ORM models: Session, Document, Conversation, Message, Chart
│   ├── document_processor.py    # Multi-format text extraction and chunking pipeline
│   ├── page_index.py            # BM25 + TF-IDF sparse retrieval engine (replaces ChromaDB)
│   ├── indexer.py               # Hybrid document indexer
│   ├── llm.py                   # OpenAI/OpenRouter LLM client (chat, summaries, chart detection)
│   ├── session_manager.py       # Session CRUD, conversation management, auto-cleanup
│   ├── metrics.py               # Performance metrics tracker (response times, confidence)
│   ├── rag_engine.py            # RAG orchestration engine
│   ├── init_db.py               # Database initialization script
│   ├── parser.py                # Additional parsing utilities
│   ├── pipeline_manager.py      # Processing pipeline orchestration
│   ├── refactoring_engine.py    # Code refactoring utilities
│   └── visualizer.py            # Visualization helpers
│
├── frontend/                     # React + TypeScript SPA
│   ├── src/
│   │   ├── App.tsx              # Main app shell with 3-panel layout, theme, state management
│   │   ├── App.css              # Global app styles
│   │   ├── index.css            # Design system tokens, dark/light theme variables
│   │   ├── main.tsx             # React entry point
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx     # Real-time chat with message streaming
│   │   │   ├── MessageBubble.tsx     # Rich message rendering (Markdown, code, charts)
│   │   │   ├── ChartVisualizer.tsx   # Recharts-based data visualization
│   │   │   ├── Sidebar.tsx           # Collapsible conversation list with actions
│   │   │   ├── FileUpload.tsx        # Drag-and-drop file upload component
│   │   │   ├── DocumentList.tsx      # Upload tracking with status indicators
│   │   │   ├── KnowledgeBase.tsx     # Knowledge base view
│   │   │   ├── WelcomeView.tsx       # Onboarding screen with quick-start prompts
│   │   │   └── ConversationSidebar.tsx  # Conversation navigation
│   │   ├── services/
│   │   │   └── api.ts           # Typed Axios API client (all REST operations)
│   │   └── hooks/               # Custom React hooks
│   ├── vite.config.ts           # Vite configuration with proxy
│   ├── tsconfig.json            # TypeScript configuration
│   └── package.json             # Frontend dependencies
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── test_api.py              # API endpoint integration tests
│   ├── test_indexer.py          # Hybrid indexer unit tests
│   ├── test_page_index.py       # BM25 page index unit tests
│   └── postman_collection.json  # Exported Postman collection for manual testing
│
├── data/                         # Runtime data (gitignored)
├── assets/                       # Static assets
│   └── screenshot.png           # Application screenshot
├── Dockerfile                    # Multi-stage Docker build (Node 18 + Python 3.11)
├── railway.json                  # Railway deployment configuration
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variable template
├── .dockerignore                 # Docker build exclusions
├── .gitignore                    # Git exclusions
└── README.md                     # This file
```

---

## 🗄️ Database Schema

The application uses **5 SQLAlchemy models** backed by Supabase (PostgreSQL):

```mermaid
erDiagram
    sessions ||--o{ documents : "has"
    sessions ||--o{ conversations : "has"
    sessions ||--o{ charts : "has"
    conversations ||--o{ messages : "contains"
    messages ||--o| charts : "may have"

    sessions {
        string id PK
        datetime created_at
        datetime last_active
        text user_agent
        string ip_address
    }

    documents {
        string id PK
        string session_id FK
        string filename
        string original_filename
        text file_path
        int file_size
        string file_type
        string status
        datetime indexed_at
        datetime created_at
        json doc_metadata
    }

    conversations {
        string id PK
        string session_id FK
        string title
        datetime created_at
        datetime updated_at
    }

    messages {
        string id PK
        string conversation_id FK
        string role
        text content
        datetime created_at
        json sources
        float confidence
        int tokens_used
        string chart_id FK
    }

    charts {
        string id PK
        string session_id FK
        string chart_type
        json data
        text image_path
        datetime created_at
    }
```

---

## 🚀 Installation

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** and **npm**
- **Supabase Account** — [Sign up free](https://supabase.com/)
- **OpenRouter** or **OpenAI API Key** — [Get one here](https://openrouter.ai/)

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Soberrex/DocuChartAI.git
cd DocuChartAI
```

### 2️⃣ Backend Setup

```bash
# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows

# Install Python dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

**Configure your `.env` file:**

```env
# LLM API (at least one required)
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENAI_API_KEY=your-openai-api-key-here

# Database (required)
DATABASE_URL=postgresql://user:password@host:5432/database

# API Security
API_KEY=your-secret-api-key-change-this-in-production

# Server
PORT=8000
ENVIRONMENT=production
LOG_LEVEL=INFO
```

**Start the FastAPI server:**

```bash
uvicorn api.main:app --reload --port 8000
```

✅ API available at `http://localhost:8000`  
📚 Swagger docs at `http://localhost:8000/docs`  
📖 ReDoc at `http://localhost:8000/redoc`

### 3️⃣ Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

✅ App opens at `http://localhost:5173`

### 4️⃣ Running Both (Development)

Open two terminals:

```bash
# Terminal 1 — Backend
uvicorn api.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|:--------:|---------|
| `DATABASE_URL` | PostgreSQL connection string (Supabase) | ✅ | — |
| `OPENROUTER_API_KEY` | OpenRouter LLM API key | ⚡ | — |
| `OPENAI_API_KEY` | OpenAI API key (fallback) | ⚡ | — |
| `API_KEY` | API authentication key | ✅ | `your-secret-key...` |
| `PORT` | Server port | ❌ | `8000` |
| `ENVIRONMENT` | Deployment environment | ❌ | `production` |
| `LOG_LEVEL` | Logging verbosity | ❌ | `INFO` |
| `VITE_API_URL` | Frontend API base URL | ❌ | `''` (same origin) |
| `VITE_API_KEY` | Frontend API key | ❌ | `dev-test-key-12345` |

> ⚡ At least one LLM API key is required (`OPENROUTER_API_KEY` or `OPENAI_API_KEY`).

### Supabase Setup

1. Create a new project on [Supabase](https://supabase.com/)
2. Go to **Settings → Database → Connection String**
3. Copy the URI and set it as `DATABASE_URL` in your `.env`
4. Tables are auto-created on first startup via SQLAlchemy

---

## 💻 Usage

### Using the Application

1. **Upload Documents** — Drag & drop or click to upload PDF, DOCX, XLSX, CSV, or TXT files
2. **Wait for Processing** — System extracts text, chunks it, and builds the BM25 index
3. **Start Chatting** — Ask questions in natural language about your documents
4. **View Citations** — Expand the "Sources" section to see where answers came from
5. **Explore Charts** — If the LLM detects numerical data, charts render automatically
6. **Manage Conversations** — Create new chats, switch between threads, or delete old ones

### Example Workflows

```
📄 Upload: quarterly_earnings.pdf
💬 Ask:   "What was the revenue growth in Q3 compared to Q2?"
📊 Get:   Answer with source citations + auto-generated bar chart

📄 Upload: research_paper.docx
💬 Ask:   "Summarize the methodology section"
📝 Get:   A concise, citation-backed summary

📄 Upload: sales_data.xlsx
💬 Ask:   "Show me the top 5 products by revenue"
📊 Get:   Tabular summary + interactive pie chart
```

---

## 📡 API Reference

All endpoints are prefixed with `/api` and require an `X-API-Key` header.

### Document Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload` | Upload and process a document |
| `GET` | `/api/documents/{session_id}` | List all documents for a session |
| `DELETE` | `/api/documents/{document_id}` | Delete a specific document |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Send a message and get an AI response |

### Conversations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/conversations` | Create a new conversation |
| `GET` | `/api/sessions/{session_id}/conversations` | List all conversations for a session |
| `GET` | `/api/conversations/{conversation_id}/messages` | Get all messages in a conversation |
| `DELETE` | `/api/conversations/{conversation_id}` | Delete a conversation |

### Session & Maintenance

| Method | Endpoint | Description |
|--------|----------|-------------|
| `DELETE` | `/api/sessions/{session_id}` | Delete an entire session and all data |
| `DELETE` | `/api/cleanup?days=30` | Auto-cleanup data older than N days |
| `GET` | `/health` | Health check endpoint |

### Example Requests

#### Upload a Document

```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "X-API-Key: your-api-key" \
  -F "file=@document.pdf" \
  -F "session_id=your-session-id"
```

**Response:**
```json
{
  "document_id": "abc-123-def",
  "filename": "document.pdf",
  "status": "ready",
  "message": "Document processed successfully",
  "file_kept": true,
  "summary": {
    "overview": "This document discusses...",
    "key_topics": ["revenue", "growth", "Q3"],
    "chart_suggestions": ["bar_chart"]
  }
}
```

#### Send a Chat Message

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "message": "What is the total revenue?",
    "conversation_id": "conv-123",
    "session_id": "session-456"
  }'
```

**Response:**
```json
{
  "message": {
    "id": "msg-789",
    "role": "assistant",
    "content": "Based on the uploaded documents, the total revenue was $5M in Q3...",
    "sources": [
      {
        "document_id": "abc-123",
        "filename": "earnings.pdf",
        "chunk_index": 3,
        "content": "Q3 revenue reached $5M...",
        "relevance_score": 0.92
      }
    ],
    "confidence": 0.89,
    "chart_data": {
      "type": "bar",
      "labels": ["Q1", "Q2", "Q3"],
      "values": [3.2, 4.1, 5.0]
    }
  }
}
```

📚 **Full Interactive Docs:** Visit `http://localhost:8000/docs` after starting the server.

---

## 🧪 Testing

### Automated Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test modules
pytest tests/test_api.py -v          # API endpoint tests
pytest tests/test_indexer.py -v      # Hybrid indexer tests  
pytest tests/test_page_index.py -v   # BM25 search engine tests
```

### Postman Collection

A comprehensive Postman collection is included at `tests/postman_collection.json`. Import it to manually test all API endpoints with pre-configured requests and example payloads.

### Test Coverage

| Module | Tests |
|--------|-------|
| `test_api.py` | Upload, chat, CRUD operations on documents/conversations/sessions |
| `test_indexer.py` | Document indexing, search accuracy, edge cases |
| `test_page_index.py` | BM25 scoring, TF-IDF boosting, multi-document search, deletion |

---

## 🚢 Deployment

### Railway (Recommended)

This project includes Railway-specific configuration for one-click deployment.

1. **Fork** this repository on [GitHub](https://github.com/Soberrex/DocuChartAI)
2. **Create a new project** on [Railway](https://railway.app/) → **Deploy from GitHub repo**
3. **Set environment variables** in the Railway dashboard:
   - `DATABASE_URL` — Your Supabase PostgreSQL connection string
   - `OPENROUTER_API_KEY` — Your LLM API key
   - `API_KEY` — Your secret API key
   - `VITE_API_URL` — Leave empty (same-origin in production)
4. Railway auto-detects `railway.json` and `Dockerfile`, then builds and deploys

**`railway.json` configuration:**
```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Docker (Self-Hosted)

The multi-stage `Dockerfile` builds both the React frontend and Python backend into a single image:

```bash
# Build the image
docker build -t docuchat-ai \
  --build-arg VITE_API_URL="" \
  --build-arg VITE_API_KEY="your-frontend-api-key" \
  .

# Run the container
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e OPENROUTER_API_KEY="sk-or-v1-..." \
  -e API_KEY="your-api-key" \
  docuchat-ai
```

**Docker Build Stages:**

| Stage | Base Image | Purpose |
|-------|-----------|---------|
| `frontend-builder` | `node:18-alpine` | Compiles React/TypeScript → static assets |
| Runtime | `python:3.11-slim` | Serves FastAPI + built frontend via static file mount |

---

## 📊 Performance & Accuracy

### Benchmarks

| Metric | Value |
|--------|-------|
| **Average Query Latency** | ~2.5s (including LLM API call) |
| **Document Processing Speed** | ~0.3s per 1000 characters |
| **BM25 Search Latency** | <50ms for 1000+ chunks |
| **Relevance Accuracy** | 85–92% (based on manual evaluation) |
| **Max File Size** | 50MB per document (configurable) |
| **Supported Chunk Size** | 2000 chars with 400-char overlap |

### How Accuracy Works

- **BM25 + TF-IDF Scoring**: Sparse retrieval using Okapi BM25 with inverse document frequency boosting
- **Context Window**: Top 5 most relevant chunks (~5000 tokens) sent to LLM
- **Hallucination Prevention**: LLM system prompt instructs answering *only* from provided context
- **Confidence Scores**: Each source citation includes a relevance score (0.0–1.0)
- **Token Tracking**: Response token usage recorded for cost monitoring

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'chromadb'` | Run `pip install -r requirements.txt` to install all dependencies |
| Frontend can't connect to API | Ensure backend is running on port 8000. Set `VITE_API_URL` in `frontend/.env` if needed |
| Railway deployment shows "0 Variables" | Add environment variables in the Railway dashboard **Variables** tab, then redeploy |
| LLM responses are slow | Try a faster model on OpenRouter (e.g., `anthropic/claude-instant-v1`) |
| `DATABASE_URL` not found | Ensure `.env` file exists in the project root with valid Supabase credentials |
| Document upload fails | Check file size (<50MB) and format (PDF, DOCX, XLSX, CSV, TXT only) |
| Charts not rendering | Ensure the LLM response contains valid chart data JSON. Check browser console for errors |

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Development Guidelines

- Follow **PEP 8** for Python code
- Use **ESLint / Prettier** for TypeScript/JavaScript
- Write **tests** for new features
- Update **documentation** for any API or schema changes
- Use **type hints** in Python and **TypeScript interfaces** in frontend

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) — High-performance Python web framework
- [rank_bm25](https://github.com/dorianbrown/rank_bm25) — BM25 retrieval algorithm
- [OpenRouter](https://openrouter.ai/) — LLM API gateway
- [Supabase](https://supabase.com/) — PostgreSQL backend-as-a-service
- [Recharts](https://recharts.org/) — React charting library
- [Material-UI](https://mui.com/) — React component library
- [Railway](https://railway.app/) — Cloud deployment platform

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Soberrex/DocuChartAI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Soberrex/DocuChartAI/discussions)

---

<div align="center">

**Made with ❤️ by [Soberrex](https://github.com/Soberrex)**

⭐ Star this repo if you found it helpful!

</div>
