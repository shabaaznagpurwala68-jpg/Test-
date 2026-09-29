"""Market headlines from public RSS feeds, with a dummy fallback.

RSS is published for syndication; we show only headline, source, time and a link
back to the original article — never the article body.
"""

import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import feedparser

FEEDS = [
    ("Economic Times", "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"),
    ("Moneycontrol", "https://www.moneycontrol.com/rss/marketreports.xml"),
    ("Livemint", "https://www.livemint.com/rss/markets"),
]
CACHE_TTL = 600
MAX_ITEMS = 30
_cache: dict = {"at": 0.0, "items": None, "source": None}

SAMPLE_HEADLINES = [
    "Sample: Nifty ends higher led by banking and IT stocks",
    "Sample: FIIs turn net buyers for the third straight session",
    "Sample: RBI keeps repo rate unchanged, maintains stance",
    "Sample: Auto sales rise on festive season demand",
    "Sample: Crude oil slips; oil marketing companies gain",
    "Sample: Rupee steady against the dollar in early trade",
    "Sample: Mid-cap index outperforms benchmark this week",
    "Sample: IT stocks watch US inflation data closely",
]


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
        items.append({"title": e.title.strip(), "link": link, "source": source, "published": published})
    return items


def _safe_read(feed: tuple[str, str]) -> list[dict]:
    try:
        return _read(*feed)
    except Exception:
        return []


def _dummy() -> list[dict]:
    now = datetime.now(timezone.utc)
    return [
        {"title": h, "link": None, "source": "Sample", "published": (now - timedelta(minutes=35 * i)).isoformat()}
        for i, h in enumerate(SAMPLE_HEADLINES)
    ]


def get_news() -> tuple[list[dict], str]:
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
