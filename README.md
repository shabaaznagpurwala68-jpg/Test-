# Stock Watchlist (test project)

FastAPI + SQLite backend, Vite + plain JS frontend. The Vite dev server proxies `/api` to the backend on port 8000.

## Backend (terminal 1)

```bash
cd "1st Project Test TradeSmart/backend"
uv sync
uv run uvicorn main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

## Frontend (terminal 2)

```bash
cd "1st Project Test TradeSmart/frontend"
npm install
npm run dev
```

Open http://localhost:5173

---

A second project, **TradeSmart Advisory**, lives in [`advisory/`](advisory/README.md).
