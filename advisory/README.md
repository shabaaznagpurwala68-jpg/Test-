# TradeSmart Advisory (test build)

Client-facing advisory demo: fundamental and technical picks with the reasoning behind each, a markets
dashboard with valuation ratios, a 12-month track record of the technical method, market news tagged by
stock, and client risk profiling.
**Sample build.** Disclaimer: The securities are quoted as an example and not as a recommendation.

Everything here is free: prices from Yahoo Finance via `yfinance`, news from public RSS feeds,
charts from TradingView Lightweight Charts (Apache-2.0), fonts and logo from the TradeSmart Design System.

## What's inside

| Tab | What it does |
|---|---|
| **Fundamental** | A 100-point scorecard for all 50 stocks: Valuation (PE and PB vs peer median, PEG), Quality (ROE, ROCE, D/E; ROE and ROA for financials), Growth (3-yr revenue and EPS CAGR), Shareholder (dividend yield, promoter holding, pledge). PICK = score ≥ 75 and ≥ 15% below fair value. Each stock shows its full scorecard, fair-value maths and peer group. **Fundamentals are sample values**; PE, PB, yield and market cap use the live price. |
| **Technical** | Three setups (Trend Breakout, MACD Momentum, Oversold Bounce) scan 50 stocks (≈ Nifty 50) after each close. A call is issued only when every rule passes. Each call shows its checklist ("why this stock"), the formula behind its levels, and a chart with 20/50/200-DMA, RSI and MACD. |
| **Markets** | Indian and global indices, USD/INR, crude, gold, US 10Y, Dollar Index; breadth; 9 scanners; a sortable stock screener; valuation ratios (aggregate PE/PB/yield of the 50, peer-group medians, and PE, PB, EPS, ROE, ROCE, D/E, yield, growth, promoter holding per stock). |
| **Track record** | The same setups replayed over the last 12 months: win rate, P&L on ₹1 lakh per call after ₹15 × 2 brokerage, equity curve, results by setup and sector. |
| **News** | ET / Moneycontrol / Livemint headlines (headline + link only), tagged by stock. |
| **Learn** | Blog with 6 sample posts (Market Events, Guides, and a Weekly Wrap built from the app's own data), a reading view with shareable links (`#learn/<slug>`), and **The Smart Weekly** newsletter: sign-ups stored in SQLite, plus a preview of this week's issue generated from the app's data. Emails are not sent in this demo. To add a post, append it to `backend/blog_posts.py`. |
| **My risk profile** | 7-question quiz → Conservative / Moderate / Aggressive; calls are marked suited or not. |

**Technical levels:** entry = close; stop loss = entry − 2 × ATR(14); target = entry + 2 × risk (1:2); 60-day limit.
**Fundamental levels:** fair value = forward EPS × blended PE (½ peer median + ½ own PE), forward EPS growth capped
at 15%; target = fair value capped at +30%; stop loss 15%; 12 months. Trade levels are shown for picks only.

Runs on its own ports, so it can run alongside the watchlist: backend **8001**, frontend **5180**.

## Backend (terminal 1)

```
cd advisory/backend
uv sync
uv run uvicorn main:app --reload --port 8001
```

The first start downloads ~2 years of daily prices for 50 stocks and 17 indices and replays 12 months of
calls — allow up to a minute or two.

## Frontend (terminal 2)

```
cd advisory/frontend
npm install
npm run dev
```

Open http://localhost:5180. The top-right badge shows whether prices are LIVE or DUMMY.

## Data rules

- Calls are stored in `backend/advisory.db` and never rewritten: new days are scanned as they arrive,
  and open calls close when price touches target or stop loss (stop loss assumed if a day touches both).
- A track record built on dummy data is rebuilt automatically once live data is available, and dummy
  data is never mixed into a live track record.
- Calls are issued only on completed candles (after 3:30 pm IST for the current day).
- The database rebuilds itself when its structure changes between versions. To start over manually,
  stop the backend and delete `backend/advisory.db`.

## API

- `GET /api/fundamentals`, `GET /api/fundamentals/{symbol}` — scorecards, fair value, peers
- `GET /api/setups` — setup definitions + 12-month stats
- `GET /api/calls?status=open|closed|all&setup=TREND_BREAKOUT|MACD_MOMENTUM|OVERSOLD_BOUNCE`
- `GET /api/calls/{id}`, `/api/calls/{id}/chart`, `/api/calls/{id}/explain`
- `GET /api/chart/{symbol-or-index}?days=180` — candles + indicators
- `GET /api/markets` — indices, breadth, scanners, stock screener
- `GET /api/performance` — track record
- `GET /api/news?symbol=RELIANCE`
- `GET /api/posts?category=…`, `GET /api/posts/{slug}`, `GET /api/newsletter/latest`, `POST /api/newsletter/subscribe`
- `GET /api/risk/questions`, `POST /api/risk/score`
