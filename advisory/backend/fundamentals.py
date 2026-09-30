"""Fundamental scorecard: 100 points across four pillars, each worth 25.

  Valuation    PE vs peer median (10) · PB vs peer median (7) · PEG (8)
  Quality      Non-financials: ROE (9) · ROCE (8) · Debt/Equity (8)
               Financials:     ROE (13) · ROA (12)   (debt is their raw material, so D/E doesn't apply)
  Growth       3-year revenue CAGR (12) · 3-year EPS CAGR (13)
  Shareholder  Dividend yield (8) · Promoter holding (8) · Promoter pledge (9)

Each factor scores on a straight line between a "zero points" level and a "full points" level.

Fair value = forward EPS × blended PE, where
  forward EPS = EPS × (1 + EPS growth, capped between 0% and 15%)
  blended PE  = ½ × peer-group median PE + ½ × the stock's own PE
Blending stops a low-PE stock from looking absurdly cheap just because its peers trade higher —
gaps like that usually have reasons the market already prices in (ownership, cyclicality, debt).
The target is capped at +30% of the current price for a 12-month view.

Verdict: PICK if score ≥ 75 and fair value is ≥ 15% above the price;
         WATCH if score ≥ 75 but the price already reflects most of the value;
         NEUTRAL for scores 50–74; WEAK below 50.
"""

from statistics import median

from fmt import inr
from fundamentals_data import FUNDAMENTALS
from indicators import annual_volatility
from market import quote
from risk import risk_level
from universe import STOCKS

PEER_GROUPS = {
    "Banking": "Financials", "NBFC": "Financials", "Insurance": "Financials",
    "IT": "IT", "Auto": "Auto",
    "FMCG": "Consumer", "Consumer": "Consumer", "Retail": "Consumer", "Consumer Tech": "Consumer",
    "Pharma": "Healthcare", "Healthcare": "Healthcare",
    "Energy": "Energy & Utilities", "Power": "Energy & Utilities", "Mining": "Energy & Utilities",
    "Metals": "Materials", "Cement": "Materials",
    "Infrastructure": "Industrials", "Defence": "Industrials", "Conglomerate": "Industrials",
    "Telecom": "Services", "Aviation": "Services",
}
PICK_SCORE, PICK_UPSIDE, TARGET_CAP, STOP_LOSS_PCT, MAX_MEANINGFUL_PE = 75, 15, 30, 15, 150


def _linear(value: float | None, zero_at: float, full_at: float, points: float) -> float:
    """Points on a straight line: 0 at `zero_at`, full at `full_at` (works in either direction)."""
    if value is None:
        return 0.0
    t = (value - zero_at) / (full_at - zero_at)
    return round(points * min(max(t, 0.0), 1.0), 2)


def _f(label, pillar, value, benchmark, points, maximum, note=None):
    return {"label": label, "pillar": pillar, "value": value, "benchmark": benchmark,
            "points": points, "max": maximum, "note": note}


def _pct(v, d=1):
    return "n/m" if v is None else f"{v:.{d}f}%"


def _score(sym: str, f: dict, pe: float | None, pb: float, peer_pe: float, peer_pb: float, dy: float) -> list[dict]:
    fin = STOCKS[sym]["sector"] in ("Banking", "NBFC", "Insurance")
    growth = f["eps_cagr3"]
    peg = pe / growth if pe and growth and growth > 0 else None
    pe_ok = pe is not None and pe <= MAX_MEANINGFUL_PE
    factors = [
        _f("PE vs peer median", "Valuation", "n/m" if not pe_ok else f"{pe:.1f}× vs {peer_pe:.1f}×",
           "≤ 0.7× peers = full, ≥ 1.2× = zero", _linear(pe / peer_pe, 1.2, 0.7, 10) if pe_ok else 0, 10,
           None if pe_ok else f"PE above {MAX_MEANINGFUL_PE}× or loss-making: not meaningful, scores zero"),
        _f("PB vs peer median", "Valuation", f"{pb:.1f}× vs {peer_pb:.1f}×",
           "≤ 0.7× peers = full, ≥ 1.2× = zero", _linear(pb / peer_pb, 1.2, 0.7, 7), 7),
        _f("PEG (PE ÷ EPS growth)", "Valuation", "n/m" if peg is None or not pe_ok else f"{peg:.2f}",
           "≤ 0.8 = full, ≥ 2.0 = zero", _linear(peg, 2.0, 0.8, 8) if pe_ok else 0, 8,
           None if peg is not None else "Needs positive EPS growth"),
    ]
    if fin:
        factors += [
            _f("Return on equity", "Quality", _pct(f["roe"]), "≥ 20% = full, ≤ 10% = zero", _linear(f["roe"], 10, 20, 13), 13),
            _f("Return on assets", "Quality", _pct(f["roa"], 2), "≥ 2% = full, ≤ 0.8% = zero", _linear(f["roa"], 0.8, 2.0, 12), 12,
               "Financials: ROA replaces ROCE and debt/equity"),
        ]
    else:
        factors += [
            _f("Return on equity", "Quality", _pct(f["roe"]), "≥ 20% = full, ≤ 10% = zero", _linear(f["roe"], 10, 20, 9), 9),
            _f("Return on capital employed", "Quality", _pct(f["roce"]), "≥ 20% = full, ≤ 10% = zero", _linear(f["roce"], 10, 20, 8), 8),
            _f("Debt / equity", "Quality", f"{f['de']:.2f}", "≤ 0.2 = full, ≥ 1.2 = zero", _linear(f["de"], 1.2, 0.2, 8), 8),
        ]
    factors += [
        _f("Revenue growth (3-yr CAGR)", "Growth", _pct(f["rev_cagr3"]), "≥ 15% = full, ≤ 3% = zero", _linear(f["rev_cagr3"], 3, 15, 12), 12),
        _f("EPS growth (3-yr CAGR)", "Growth", _pct(f["eps_cagr3"]), "≥ 15% = full, ≤ 3% = zero", _linear(f["eps_cagr3"], 3, 15, 13), 13,
           None if f["eps_cagr3"] is not None else "Not meaningful (turnaround from losses)"),
        _f("Dividend yield", "Shareholder", f"{dy:.2f}%", "≥ 2.5% = full, ≤ 0.3% = zero", _linear(dy, 0.3, 2.5, 8), 8),
        _f("Promoter holding", "Shareholder", "No promoter" if f["promoter"] == 0 else _pct(f["promoter"], 0),
           "≥ 50% = full, ≤ 25% = zero", 4.0 if f["promoter"] == 0 else _linear(f["promoter"], 25, 50, 8), 8,
           "Professionally managed with no promoter group: neutral half points" if f["promoter"] == 0 else None),
        _f("Promoter pledge", "Shareholder", _pct(f["pledge"]), "0% = full, ≥ 5% = zero", _linear(f["pledge"], 5, 0, 9), 9),
    ]
    return factors


def _verdict(score: float, upside: float | None) -> str:
    if score >= PICK_SCORE:
        return "PICK" if upside is not None and upside >= PICK_UPSIDE else "WATCH"
    return "NEUTRAL" if score >= 50 else "WEAK"


def evaluate_all(market: dict[str, list[dict]]) -> dict:
    """Scorecard, fair value and verdict for every stock, using live prices for PE / PB / yield."""
    base = {}
    for sym, f in FUNDAMENTALS.items():
        q = quote(market[sym])
        price = q["price"]
        base[sym] = {
            "price": price,
            "change_pct": round((price - q["prev_close"]) / q["prev_close"] * 100, 2),
            "pe": price / f["eps"] if f["eps"] > 0 else None,
            "pb": price / f["bvps"],
            "dy": f["dps"] / price * 100,
            "mcap_cr": price * f["shares_cr"],
            "group": PEER_GROUPS[STOCKS[sym]["sector"]],
        }

    groups: dict[str, dict] = {}
    for g in set(PEER_GROUPS.values()):
        members = [s for s, b in base.items() if b["group"] == g]
        pes = [base[s]["pe"] for s in members if base[s]["pe"] and base[s]["pe"] <= MAX_MEANINGFUL_PE]
        groups[g] = {"group": g, "stocks": len(members), "median_pe": round(median(pes), 1),
                     "median_pb": round(median(base[s]["pb"] for s in members), 1),
                     "median_roe": round(median(FUNDAMENTALS[s]["roe"] for s in members), 1)}

    items = []
    for sym, b in base.items():
        f, info, g = FUNDAMENTALS[sym], STOCKS[sym], groups[b["group"]]
        factors = _score(sym, f, b["pe"], b["pb"], g["median_pe"], g["median_pb"], b["dy"])
        pillars = {p: round(sum(x["points"] for x in factors if x["pillar"] == p), 1)
                   for p in ("Valuation", "Quality", "Growth", "Shareholder")}
        total = round(sum(pillars.values()), 1)

        fair = uncapped = upside = None
        if b["pe"] and b["pe"] <= MAX_MEANINGFUL_PE:
            growth = min(max(f["eps_cagr3"] or 0, 0), 15)
            fwd_eps = f["eps"] * (1 + growth / 100)
            blended_pe = (g["median_pe"] + b["pe"]) / 2
            uncapped = fwd_eps * blended_pe
            fair = min(uncapped, b["price"] * (1 + TARGET_CAP / 100))
            upside = round((fair / b["price"] - 1) * 100, 2)

        vol = annual_volatility([x["close"] for x in market[sym]])
        items.append({
            "symbol": sym, "name": info["name"], "sector": info["sector"], "peer_group": b["group"],
            "cmp": b["price"], "change_pct": b["change_pct"],
            "pe": b["pe"] and round(b["pe"], 1), "pb": round(b["pb"], 2), "eps": round(f["eps"], 2),
            "bvps": round(f["bvps"], 2), "div_yield": round(b["dy"], 2), "mcap_cr": round(b["mcap_cr"]),
            "roe": f["roe"], "roce": f["roce"], "de": f["de"], "roa": f["roa"],
            "rev_cagr3": f["rev_cagr3"], "eps_cagr3": f["eps_cagr3"],
            "promoter": f["promoter"], "pledge": f["pledge"],
            "score": total, "pillars": pillars, "factors": factors,
            "fair_value": fair and round(fair, 2), "fair_value_uncapped": uncapped and round(uncapped, 2),
            "upside_pct": upside, "verdict": _verdict(round(total), upside),  # the whole-number score users see
            "stop_loss": round(b["price"] * (1 - STOP_LOSS_PCT / 100), 2),
            "volatility": vol, "risk_level": risk_level(vol),
        })
    items.sort(key=lambda x: -x["score"])

    # Aggregate PE of all 50 = total market cap ÷ total earnings (what an index PE measures).
    earnings = sum(it["mcap_cr"] / it["pe"] for it in items if it["pe"])
    mcap = sum(it["mcap_cr"] for it in items)
    book = sum(it["mcap_cr"] / it["pb"] for it in items)
    dividends = sum(it["mcap_cr"] * it["div_yield"] / 100 for it in items)
    aggregate = {"pe": round(mcap / earnings, 1), "pb": round(mcap / book, 2),
                 "div_yield": round(dividends / mcap * 100, 2), "mcap_cr": round(mcap)}
    return {"items": items, "peer_groups": sorted(groups.values(), key=lambda x: x["group"]), "aggregate": aggregate}


def narrative(item: dict) -> list[str]:
    """Plain-language summary built from the scorecard. Rule-based: it only restates the numbers."""
    # Strongest and weakest factors, heavier-weighted factors first when shares tie.
    ranked = sorted(item["factors"], key=lambda x: (x["points"] / x["max"], x["max"]), reverse=True)
    strengths = [x for x in ranked if x["points"] / x["max"] >= 0.8][:3]
    weaknesses = [x for x in reversed(ranked) if x["points"] / x["max"] <= 0.3][:3]
    p = item["pillars"]
    out = [f"{item['name']} scores {item['score']:.0f} out of 100 — valuation {p['Valuation']:.0f}/25, quality "
           f"{p['Quality']:.0f}/25, growth {p['Growth']:.0f}/25, shareholder {p['Shareholder']:.0f}/25."]
    if strengths:
        out.append("Strengths: " + "; ".join(f"{x['label']} {x['value']}" for x in strengths) + ".")
    if weaknesses:
        out.append("Weak spots: " + "; ".join(f"{x['label']} {x['value']}" for x in weaknesses) + ".")
    if item["fair_value"]:
        capped = item["fair_value_uncapped"] > item["fair_value"] + 0.01
        out.append(f"Fair value works out to {inr(item['fair_value'])} against a price of {inr(item['cmp'])} "
                   f"({item['upside_pct']:+.1f}%)" + (f" — capped at +{TARGET_CAP}% for a 12-month view." if capped else "."))
    else:
        out.append("A fair value can't be calculated meaningfully: earnings are too small relative to the price.")
    out.append({
        "PICK": f"Verdict: PICK — the business scores at least {PICK_SCORE} and the price is at least "
                f"{PICK_UPSIDE}% below fair value.",
        "WATCH": "Verdict: WATCH — a strong business, but the price already reflects most of its value. "
                 "A lower price would make it a pick.",
        "NEUTRAL": "Verdict: NEUTRAL — a mixed scorecard; not strong enough to recommend on fundamentals alone.",
        "WEAK": "Verdict: WEAK — too many factors score poorly to recommend it on fundamentals.",
    }[item["verdict"]])
    return out
