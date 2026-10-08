"""Learn tab: blog posts, the Weekly Wrap, and the newsletter issue — built from the app's own data.

The Weekly Wrap post and the newsletter are generated from the same numbers the other tabs
show (breadth, scanners, new calls, track record, picks), so they write themselves each week.
"""

from datetime import date, timedelta

from blog_posts import POSTS
from fmt import inr

DISCLAIMER = "Disclaimer: The securities are quoted as an example and not as a recommendation."
PLAN_LINE = "Trade @ ₹15 per executed order."


def _pct(v: float) -> str:
    return ("+" if v > 0 else "−" if v < 0 else "") + f"{abs(v):.2f}%"


def _meta(p: dict) -> dict:
    return {k: p[k] for k in ("slug", "category", "title", "excerpt", "read_min")} | {
        "date": (date.today() - timedelta(days=p["days_ago"])).isoformat(), "featured": p.get("featured", False)}


def weekly_wrap(markets: dict, calls: list[dict], perf: dict) -> dict:
    b = markets["breadth"]
    idx = {x["key"]: x for x in markets["indices"]}
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    new_calls = [c for c in calls if c["issued_on"] >= week_ago]
    scans = {s["key"]: s for s in markets["scanners"]}
    body = [
        ("p", "Your quick look at the week, built from the same numbers you see across the app. Sample content."),
        ("h", "Indices"),
        ("ul", [f"{idx[k]['name']}: {idx[k]['last']:,.2f} ({_pct(idx[k]['chg_1w'])} this week)"
                for k in ("NIFTY50", "SENSEX", "BANKNIFTY", "INDIAVIX") if k in idx]),
        ("h", "Market breadth"),
        ("p", f"{b['advances']} of our {b['total']} stocks rose on the last day and {b['declines']} fell. "
              f"{b['above_sma200_pct']}% trade above their 200-day average — "
              f"{'a healthy long-term picture' if b['above_sma200_pct'] >= 50 else 'a sign of a weak market underneath'}."),
        ("h", "Scanner highlights"),
        ("ul", [f"{s['title']}: {', '.join(i['symbol'] for i in s['items'][:4]) or 'none today'}"
                for k, s in scans.items() if k in ("HIGH_52W", "RSI_OVERSOLD", "GOLDEN_CROSS", "VOLUME_SURGE")]),
        ("h", "Technical calls"),
        ("p", f"{len(new_calls)} new call{'s' if len(new_calls) != 1 else ''} this week. Over the last 12 months the "
              f"three setups closed {perf['stats']['calls']} calls with a {perf['stats']['win_rate']}% win rate."),
        ("callout", "Every call shows the rules it passed and how its levels were set — open the Technical tab."),
    ]
    return {"slug": "this-week-in-markets", "category": "Weekly Wrap", "title": "This Week in Markets (Sample)",
            "excerpt": "Indices, breadth, scanner highlights and new technical calls — built from the app's data.",
            "date": date.today().isoformat(), "read_min": 2, "featured": False, "body": body}


def all_posts(markets: dict, calls: list[dict], perf: dict) -> list[dict]:
    posts = [_meta(p) | {"body": p["body"]} for p in POSTS] + [weekly_wrap(markets, calls, perf)]
    return sorted(posts, key=lambda p: p["date"], reverse=True)


def newsletter_issue(markets: dict, calls: list[dict], perf: dict, fundamentals: dict, posts: list[dict]) -> dict:
    b, s = markets["breadth"], perf["stats"]
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    open_calls = [c for c in calls if c["status"] == "OPEN"]
    new_calls = [c for c in open_calls if c["issued_on"] >= week_ago] or open_calls[:3]
    picks = [i for i in fundamentals["items"] if i["verdict"] == "PICK"][:3]
    nifty = next((x for x in markets["indices"] if x["key"] == "NIFTY50"), None)
    return {
        "name": "The Smart Weekly",
        "subject": f"The Smart Weekly: {len(new_calls)} new calls, {b['above_sma200_pct']:.0f}% of stocks in an uptrend",
        "preheader": "Your week in markets, in five minutes.",
        "date": date.today().isoformat(),
        "sections": [
            {"title": "The market in one line",
             "lines": [f"Nifty 50 {nifty['last']:,.2f} ({_pct(nifty['chg_1w'])} this week). "
                       f"{b['advances']} advances, {b['declines']} declines; {b['above_sma200_pct']}% of our 50 stocks above "
                       f"their 200-day average." if nifty else ""]},
            {"title": "New technical calls",
             "lines": [f"{c['symbol']} — {c['setup_name']}: entry {inr(c['entry'])}, target {inr(c['target'])}, "
                       f"stop loss {inr(c['stop_loss'])}" for c in new_calls[:3]]},
            {"title": "Top fundamental picks",
             "lines": [f"{i['symbol']} — score {i['score']:.0f}/100, fair value {inr(i['fair_value'])} "
                       f"({_pct(i['upside_pct'])})" for i in picks]},
            {"title": "Track record, last 12 months",
             "lines": [f"{s['calls']} closed calls · {s['win_rate']}% profitable · average win {_pct(s['avg_win_pct'])}, "
                       f"average loss {_pct(s['avg_loss_pct'])}"]},
            {"title": "Worth reading",
             "lines": [p["title"] for p in posts[:3]], "slugs": [p["slug"] for p in posts[:3]]},
        ],
        "footer": [PLAN_LINE, DISCLAIMER, "Sample issue for demonstration.",
                   "www.tradesmartonline.in l +91 022-61208000"],
    }
