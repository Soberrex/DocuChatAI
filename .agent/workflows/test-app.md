---
description: How to test all API calls and UI functions in the DocuChat AI app
---

# Testing Workflow for DocuChat AI

## Prerequisites

// turbo-all

1. Make sure you are in the project root directory:
```
cd d:\ERPNext-Analyzer
```

2. Install Python dependencies:
```
pip install -r requirements.txt
```

3. Install frontend dependencies:
```
cd frontend && npm install && cd ..
```

---

## Step 1: Run Page Index Unit Tests

These test the core BM25 retrieval engine (no external services needed):

```
python -m pytest tests/test_page_index.py -v
```

**Expected:** All 18 tests pass. Tests cover:
- Index initialization (empty, with data)
- Adding chunks (single, multiple documents)
- Search relevance (BM25 ranking, filtering, edge cases)
- Deletion (document, session)
- Persistence (save/load, corruption recovery)

---

## Step 2: Run Indexer Tests

```
python -m pytest tests/test_indexer.py -v
```

**Expected:** Indexer initializes without loading ML models. Search returns None on empty index.

---

## Step 3: Run API Tests

These test the FastAPI endpoints (requires database to be configured):

```
python -m pytest tests/test_api.py -v --tb=short
```

**Expected:** Tests cover:
- Root endpoint returns API info
- Health check endpoint
- Authentication (missing/invalid API key)
- Search with valid/invalid queries
- Metrics endpoints (stats, recent queries)
- Rate limiting (normal usage)

---

## Step 4: Run All Tests Together

```
python -m pytest tests/ -v --tb=short
```

---

## Step 5: Test Backend Startup Time

```
python -c "import time; start=time.time(); from src.indexer import HybridIndexer; idx=HybridIndexer(); print(f'Startup time: {time.time()-start:.2f}s')"
```

**Expected:** Should be under 1 second (previously 30+ seconds with ML models).

---

## Step 6: Test Frontend Build

```
cd frontend && npm run build
```

**Expected:** Build completes with chunk splitting:
- `vendor-react` chunk (~150KB)
- `vendor-charts` chunk (~250KB)
- `vendor-motion` chunk (~200KB)
- Main app chunk (~50KB)

---

## Step 7: Test Frontend Dev Server

```
cd frontend && npm run dev
```

Then open the browser to `http://localhost:5173`:

1. **Loading skeleton** — Should appear instantly before React loads
2. **Theme toggle** — Click sun/moon icon, should switch dark/light
3. **Chat input** — Type message, should show demo response
4. **File upload** — Click paperclip, should open file dialog
5. **Sidebar** — Should show conversation list, click to switch

---

## Step 8: Test API Endpoints Manually

Start the backend:
```
python -m api.main
```

Test with curl:

```bash
# Health check
curl http://localhost:8000/health

# Root info
curl http://localhost:8000/

# Search (requires API key + indexed data)
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-test-key-12345" \
  -d '{"query": "test search"}'

# Stats
curl http://localhost:8000/stats \
  -H "X-API-Key: dev-test-key-12345"
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: rank_bm25` | Run `pip install rank_bm25` |
| Database connection error | Check `DATABASE_URL` in `.env` |
| Frontend proxy 502 | Start backend first: `python -m api.main` |
| Tests fail with import errors | Run from project root: `cd d:\ERPNext-Analyzer` |
