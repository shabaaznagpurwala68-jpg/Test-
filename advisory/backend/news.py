"""Market headlines from public RSS feeds, with a dummy fallback.

RSS is published for syndication; we show only headline, source, time and a link
back to the original article — never the article body.
"""

import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import re

import feedparser

from universe import UNIVERSE

FEEDS = [
    ("Economic Times", "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"),
    ("Moneycontrol", "https://www.moneycontrol.com/rss/marketreports.xml"),
    ("Livemint", "https://www.livemint.com/rss/markets"),
]
CACHE_TTL = 600
MAX_ITEMS = 30
_cache: dict = {"at": 0.0, "items": None, "source": None}

SAMPLE_HEADLINES = [
    "Sample: Nifty ends higher led by HDFC Bank and Infosys",
    "Sample: FIIs turn net buyers for the third straight session",
    "Sample: Reliance shares rise after retail business update",
    "Sample: RBI keeps repo rate unchanged; SBI, Kotak edge up",
    "Sample: Maruti and M&M report higher festive season sales",
    "Sample: Tata Steel slips as global steel prices soften",
    "Sample: Rupee steady against the dollar in early trade",
    "Sample: TCS, Wipro in focus ahead of quarterly results",
]


def _alias_pattern(alias: str) -> re.Pattern:
    # Short all-caps acronyms (ITC, SBI, L&T) must match exactly; names match any case.
    flags = 0 if alias.upper() == alias else re.IGNORECASE
    return re.compile(rf"(?<![A-Za-z]){re.escape(alias)}(?![A-Za-z])", flags)


_PATTERNS = {sym: [_alias_pattern(a) for a in info["aliases"]] for sym, info in UNIVERSE.items()}
_EXCLUDE = {sym: [re.compile(re.escape(x), re.IGNORECASE) for x in info.get("exclude", [])]
            for sym, info in UNIVERSE.items()}


def tag(title: str) -> list[str]:
    """Which of our stocks a headline mentions."""
    found = []
    for sym, pats in _PATTERNS.items():
        text = title
        for x in _EXCLUDE[sym]:
            text = x.sub("", text)  # "Reliance Power" is not Reliance Industries
        if any(p.search(text) for p in pats):
            found.append(sym)
    return found


def _read(source: str, url: str) -> list[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (TradeSmart Advisory test)"})
    with urllib.request.urlopen(req, timeout=6) as resp:
        feed = feedparser.parse(resp.read())
    items = []
    for e in feed.entries:
        link = e.get("link", "")
        if not e.get("title") or not link.startswith(("http://", "https://")):
            continue
        t = e.get("published_parsed") or e.get("updated_parsed")
        published = datetime(*t[:6], tzinfo=timezone.utc).isoformat() if t else None
        title = e.title.strip()
        items.append({"title": title, "link": link, "source": source, "published": published, "symbols": tag(title)})
    return items


def _safe_read(feed: tuple[str, str]) -> list[dict]:
    try:
        return _read(*feed)
    except Exception:
        return []


def _dummy() -> list[dict]:
    now = datetime.now(timezone.utc)
    return [
        {"title": h, "link": None, "source": "Sample", "published": (now - timedelta(minutes=35 * i)).isoformat(),
         "symbols": tag(h)}
        for i, h in enumerate(SAMPLE_HEADLINES)
    ]


def get_news(symbol: str | None = None) -> tuple[list[dict], str]:
    items, source = _all_news()
    if symbol:
        items = [i for i in items if symbol in i["symbols"]]
    return items, source


def _all_news() -> tuple[list[dict], str]:
    if _cache["items"] is not None and time.time() - _cache["at"] < CACHE_TTL:
        return _cache["items"], _cache["source"]

    with ThreadPoolExecutor(len(FEEDS)) as pool:
        items = [i for batch in pool.map(_safe_read, FEEDS) for i in batch]

    if items:
        items.sort(key=lambda i: i["published"] or "", reverse=True)
        items, source = items[:MAX_ITEMS], "live"
    else:
        items, source = _dummy(), "dummy"

    _cache.update(at=time.time(), items=items, source=source)
    return items, source
