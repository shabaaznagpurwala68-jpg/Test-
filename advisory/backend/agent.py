"""Ask AI: a local Ollama model that answers stock questions by calling tools.

Price sources, in order:
  1. TradeSmart API (Noren v2): only when TS_CLIENT_ID and TS_ACCESS_TOKEN are set (see ts_login.py)
  2. NSE's official MCP server (cm-market): 1-3 min delayed, no login
  3. This app's Yahoo cache: ~15 min delayed
Fundamentals come from this app's own scorecard (sample values, live price).

The model only words the answer; every number comes from a tool, and the disclaimer is added here.
OLLAMA_URL and OLLAMA_MODEL override the defaults.
"""

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

from fundamentals import evaluate_all
from market import get_market, quote
from universe import STOCKS

MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.5:4b")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/api/chat"
DISCLAIMER = "Educational information, not investment advice."
MAX_STEPS = 6
IST = timezone(timedelta(hours=5, minutes=30))


def _post(url: str, body: bytes, headers: dict, timeout: float = 20):
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8"), r.headers


class NseMcp:
    """Minimal Streamable-HTTP MCP client for NSE's live-snapshot server."""
    URL = "https://mcp.nseindia.in/cmmkt/mcp"
    HEADERS = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}

    def __init__(self):
        self.session = None
        self._id = 0

    def _rpc(self, method: str, params: dict | None = None, notify: bool = False):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        if not notify:
            self._id += 1
            msg["id"] = self._id
        headers = dict(self.HEADERS, **({"Mcp-Session-Id": self.session} if self.session else {}))
        text, resp_headers = _post(self.URL, json.dumps(msg).encode(), headers, timeout=40)
        if method == "initialize":
            self.session = resp_headers.get("Mcp-Session-Id")
        if notify:
            return None
        if not text.lstrip().startswith("{"):  # SSE framing: the JSON is on the data line
            text = next(line[5:] for line in text.splitlines() if line.startswith("data:"))
        return json.loads(text)

    def _connect(self):
        self._rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "tradesmart-advisory", "version": "0.1"}})
        self._rpc("notifications/initialized", notify=True)

    def call(self, tool: str, args: dict) -> dict:
        for attempt in range(2):
            try:
                if not self.session:
                    self._connect()
                res = self._rpc("tools/call", {"name": tool, "arguments": args})
                break
            except urllib.error.HTTPError:
                self.session = None  # expired session: reconnect once
                if attempt:
                    raise
        if "error" in res:
            raise RuntimeError(res["error"].get("message"))
        text = res["result"]["content"][0]["text"]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"text": text}


class TradeSmart:
    """TradeSmart Noren v2 REST client. Needs an access token from ts_login.py."""
    BASE = "https://v2api.tradesmartonline.in/NorenWClientAPIv2"

    def __init__(self):
        self.uid = os.environ.get("TS_CLIENT_ID")
        self.token = os.environ.get("TS_ACCESS_TOKEN")
        self._tokens: dict[str, str] = {}  # NSE symbol -> contract token

    @property
    def enabled(self) -> bool:
        return bool(self.uid and self.token)

    def _call(self, endpoint: str, payload: dict) -> dict:
        body = ("jData=" + json.dumps({"uid": self.uid, **payload})).encode()
        text, _ = _post(f"{self.BASE}/{endpoint}", body, {"Authorization": f"Bearer {self.token}"}, timeout=10)
        data = json.loads(text)
        if isinstance(data, dict) and data.get("stat") == "Not_Ok":
            raise RuntimeError(f"TradeSmart {endpoint}: {data.get('emsg')}")
        return data

    def quote(self, symbol: str) -> dict:
        if symbol not in self._tokens:
            hits = self._call("SearchScrip", {"exch": "NSE", "stext": symbol}).get("values", [])
            match = next((h for h in hits if h.get("exch") == "NSE" and h.get("tsym") == f"{symbol}-EQ"), None)
            if match is None:
                raise RuntimeError(f"TradeSmart: no NSE EQ contract for {symbol}")
            self._tokens[symbol] = match["token"]
        q = self._call("GetQuotes", {"exch": "NSE", "token": self._tokens[symbol]})
        num = lambda k: float(q[k]) if q.get(k) not in (None, "") else None  # noqa: E731
        price, prev = num("lp"), num("c")
        return {"price_inr": price, "prev_close": prev,
                "change_pct": round((price - prev) / prev * 100, 2) if price and prev else None,
                "open": num("o"), "high": num("h"), "low": num("l"), "volume": q.get("v"),
                "week52_high": num("wk52_h"), "week52_low": num("wk52_l"), "as_of": q.get("lut"),
                "source": "TradeSmart API (real-time)"}


nse = NseMcp()
ts = TradeSmart()


def _ist(utc_iso: str) -> str:
    """NSE MCP 'updatedAt' is UTC with nanoseconds; show it as IST."""
    dt = datetime.fromisoformat(utc_iso[:19]).replace(tzinfo=timezone.utc)
    return dt.astimezone(IST).strftime("%Y-%m-%d %H:%M IST")


# ---------- tools ----------

def find_symbol(query: str) -> dict:
    q = query.lower()
    hits = [{"symbol": s, "name": i["name"]} for s, i in STOCKS.items()
            if q in s.lower() or q in i["name"].lower() or any(q in a.lower() for a in i["aliases"])]
    return {"matches": hits[:5]} if hits else {
        "note": f"'{query}' is not in our Nifty 50 list; try get_quote with the exact NSE symbol"}


def get_quote(symbol: str) -> dict:
    sym = symbol.upper().strip()
    errors = []
    if ts.enabled:
        try:
            return {"symbol": sym, **ts.quote(sym)}
        except Exception as e:  # fall through to the next source
            errors.append(str(e))
    try:
        s = nse.call("cm_get_stock_quote", {"symbol": sym})["stock"]
        return {"symbol": sym, "price_inr": s["lastTradedPrice"], "prev_close": s["preClosePrice"],
                "change_pct": s["perChange"], "open": s["openPrice"], "high": s["highPrice"],
                "low": s["lowPrice"], "volume": s["volume"], "week52_high": s["fiftyTwoWeekHigh"],
                "week52_low": s["fiftyTwoWeekLow"], "as_of_ist": s["latestTimestamp"],
                "source": "NSE MCP (1-3 min delayed)"}
    except Exception as e:
        errors.append(f"NSE MCP: {e}")
    market, source = get_market()
    if sym in market:
        q = quote(market[sym])
        return {"symbol": sym, "price_inr": q["price"], "prev_close": q["prev_close"],
                "change_pct": round((q["price"] - q["prev_close"]) / q["prev_close"] * 100, 2),
                "as_of": market[sym][-1]["date"], "source": f"Yahoo ({source}, ~15 min delayed)"}
    return {"error": f"no quote for {sym}", "details": errors}


def get_index_quote(index_name: str) -> dict:
    try:
        return {**nse.call("cm_get_index_quote", {"indexName": index_name}), "source": "NSE MCP"}
    except Exception:  # that tool is sometimes slow; the all-indices snapshot has the core fields
        data = nse.call("cm_get_live_indices", {})
        rows = [r for group in data["indices"].values() for r in group]
        row = next((r for r in rows if r["indexName"].lower() == index_name.lower()), None)
        if row is None:
            return {"error": f"unknown index '{index_name}'", "some_valid_names": [r["indexName"] for r in rows[:15]]}
        return {**row, "as_of_ist": data["nseTimestamp"], "source": "NSE MCP"}


def get_market_movers(index: str = "") -> dict:
    data = nse.call("nse_get_market_movers", {"indexName": index, "limit": 5})
    slim = lambda rows: [{"symbol": r["symbol"], "price_inr": r["ltp"], "prev_close_inr": r["prev_price"],  # noqa: E731
                          "change_pct": r["perChange"]} for r in rows]
    return {"segment": data.get("segment"), "as_of": _ist(data["gainersUpdatedAt"]), "source": "NSE MCP",
            "gainers": slim(data["gainers"]), "losers": slim(data["losers"])}


def get_fundamentals(symbol: str) -> dict:
    sym = symbol.upper().strip()
    market, _ = get_market()
    item = next((i for i in evaluate_all(market)["items"] if i["symbol"] == sym), None)
    if item is None:
        return {"error": f"no fundamentals for {sym} (we cover the Nifty 50 only)"}
    keys = ("symbol", "name", "sector", "cmp", "pe", "pb", "eps", "div_yield", "mcap_cr", "roe", "roce",
            "de", "rev_cagr3", "eps_cagr3", "promoter", "pledge", "fair_value", "upside_pct", "verdict",
            "risk_level")
    out = {k: item[k] for k in keys}
    out["total_score_out_of_100"] = item["score"]
    out["pillar_scores_each_out_of_25"] = item["pillars"]
    out["source"] = "TradeSmart Advisory scorecard (sample fundamentals)"
    out["note"] = ("fair_value is capped at +30% of the current price, so upside_pct of 30 means 'at least 30'. "
                   "promoter=null means the company has no promoter group.")
    return out


TOOLS_IMPL = {"find_symbol": find_symbol, "get_quote": get_quote, "get_index_quote": get_index_quote,
              "get_market_movers": get_market_movers, "get_fundamentals": get_fundamentals}


def _tool(name: str, desc: str, params: dict, required: bool = True) -> dict:
    return {"type": "function", "function": {"name": name, "description": desc, "parameters": {
        "type": "object", "properties": {k: {"type": "string", "description": v} for k, v in params.items()},
        "required": list(params) if required else []}}}


TOOLS = [
    _tool("find_symbol", "Look up the NSE symbol for a company name.", {"query": "Company name or part of it"}),
    _tool("get_quote", "Live price, day change, day range, volume and 52-week range for any NSE stock.",
          {"symbol": "Exact NSE symbol, e.g. RELIANCE"}),
    _tool("get_index_quote", "Live value and change of an NSE index.",
          {"index_name": "Exact NSE index name, e.g. 'NIFTY 50', 'NIFTY BANK', 'INDIA VIX'"}),
    _tool("get_market_movers", "Today's top gainers and losers.",
          {"index": "'' for all NSE stocks, or NIFTY, BANKNIFTY, NIFTYNEXT50"}, required=False),
    _tool("get_fundamentals", "PE, PB, ROE, growth, promoter holding, scorecard, fair value and verdict "
          "for a Nifty 50 stock.", {"symbol": "NSE symbol, e.g. TCS"}),
]

SYSTEM = ("You are TradeSmart's research assistant for Indian stocks. Use the tools for every number; never "
          "guess prices or ratios. If you don't know a company's symbol, call find_symbol first. Answer "
          "concisely, quote figures in INR, copy numbers exactly as the tools give them, and say which source "
          "and timestamp the price came from. Decline questions unrelated to Indian markets.")


def _chat_stream(messages: list[dict]):
    """Yields ("delta", text) as the reply streams in, then ("done", full_message)."""
    body = json.dumps({"model": MODEL, "messages": messages, "tools": TOOLS, "stream": True, "think": False})
    req = urllib.request.Request(OLLAMA_URL, data=body.encode(), headers={"Content-Type": "application/json"})
    content, tool_calls = "", []
    with urllib.request.urlopen(req, timeout=300) as r:
        for line in r:
            if not line.strip():
                continue
            chunk = json.loads(line)
            msg = chunk.get("message", {})
            if msg.get("content"):
                content += msg["content"]
                yield "delta", msg["content"]
            tool_calls += msg.get("tool_calls") or []
            if chunk.get("done"):
                break
    yield "done", {"role": "assistant", "content": content, "tool_calls": tool_calls}


def ask(question: str, history: list[dict] | None = None):
    """Runs the tool loop, yielding events for the UI:
    {"type": "tool", ...} per tool call, {"type": "delta", "text"} while the answer streams,
    then {"type": "answer", "text", "seconds"} or {"type": "error", "text"}."""
    messages = [{"role": "system", "content": SYSTEM}, *(history or []), {"role": "user", "content": question}]
    t0 = time.time()
    try:
        for _ in range(MAX_STEPS):
            msg = None
            for kind, value in _chat_stream(messages):
                if kind == "delta":
                    yield {"type": "delta", "text": value}
                else:
                    msg = value
            messages.append(msg)
            if not msg["tool_calls"]:
                yield {"type": "answer", "text": msg["content"].strip(), "disclaimer": DISCLAIMER,
                       "seconds": round(time.time() - t0, 1)}
                return
            for c in msg["tool_calls"]:
                name, args = c["function"]["name"], c["function"].get("arguments") or {}
                try:
                    result = TOOLS_IMPL[name](**args)
                except Exception as e:
                    result = {"error": f"{name} failed: {e}"}
                yield {"type": "tool", "name": name, "args": args,
                       "source": result.get("source"), "error": result.get("error")}
                messages.append({"role": "tool", "tool_name": name, "content": json.dumps(result)})
        yield {"type": "error", "text": "The assistant took too many steps. Try a simpler question."}
    except urllib.error.URLError as e:
        yield {"type": "error", "text": f"Can't reach the AI model at {OLLAMA_URL} ({e.reason}). Is Ollama running?"}
