# TradeSmart Advisory (test build)

Client-facing advisory app: stock recommendations with live prices, plus market news.
**Sample data only.** Disclaimer: The securities are quoted as an example and not as a recommendation.

- Backend: FastAPI + SQLite (`advisory.db`, created and seeded with 24 sample calls on first start)
- Prices: Yahoo Finance via `yfinance`, cached 5 min; falls back to dummy prices if Yahoo is unreachable
- News: Economic Times / Moneycontrol / Livemint RSS (headline + link only), cached 10 min; dummy fallback
- Frontend: Vite + plain JS, styled with TradeSmart design tokens (`frontend/tokens.css`)

Runs on its own ports, so it can run alongside the watchlist: backend **8001**, frontend **5180**.

## Backend (terminal 1)

```
cd advisory/backend
uv sync
uv run uvicorn main:app --reload --port 8001
```

## Frontend (terminal 2)

```
cd advisory/frontend
npm install
npm run dev
```

Open http://localhost:5180. The top-right badge shows whether prices are LIVE or DUMMY.

To re-issue the sample calls at today's prices, stop the backend, delete `backend/advisory.db`, and start it again.

## API

- `GET /api/recommendations?action=BUY|SELL|HOLD` — list + summary + price source
- `GET /api/recommendations/{id}` — one call
- `GET /api/news` — headlines
