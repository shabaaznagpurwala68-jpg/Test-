# TradeSmart Advisory (test build)

Client-facing advisory app: stock recommendations with live prices and charts, a track record,
market news tagged by stock, and client risk profiling.
**Sample data only.** Disclaimer: The securities are quoted as an example and not as a recommendation.

- Backend: FastAPI + SQLite (`advisory.db`, created on first start)
- Sample calls: ~60 calls replayed over the last 12 months against actual daily prices; open calls
  are checked on every refresh and closed permanently when target, stop loss or horizon is reached
- Prices: 13 months of daily candles from Yahoo Finance via `yfinance`, cached 5 min; falls back to a
  deterministic dummy history if Yahoo is unreachable
- Track record: win rate, P&L on ₹1 lakh per call after ₹15 × 2 brokerage, equity curve, by sector/type
- Charts: TradingView Lightweight Charts (Apache-2.0) with entry/target/stop-loss lines
- News: Economic Times / Moneycontrol / Livemint RSS (headline + link only), tagged by stock; dummy fallback
- Risk profile: 7-question quiz → Conservative / Moderate / Aggressive; call risk from measured volatility
- "Explain this call simply": rule-based text built from the call's numbers (no AI, no cost)
- Frontend: Vite + plain JS modules in `frontend/src/`, styled with TradeSmart design tokens

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

To regenerate the sample calls (for example, after the first start ran in dummy mode), stop the backend,
delete `backend/advisory.db`, and start it again. The database also rebuilds itself automatically when
its structure changes between versions.

## API

- `GET /api/recommendations?status=open|closed|all&action=BUY|SELL|HOLD` — calls + summary
- `GET /api/recommendations/{id}` — one call
- `GET /api/recommendations/{id}/candles` — daily candles around the call
- `GET /api/recommendations/{id}/explain` — plain-language explanation
- `GET /api/performance` — track record
- `GET /api/news?symbol=RELIANCE` — headlines (optionally for one stock)
- `GET /api/risk/questions`, `POST /api/risk/score` — risk profiling
