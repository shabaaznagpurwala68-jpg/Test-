"""Dummy recommendations for testing. None of this is research or advice.

Levels are stored as % offsets from the entry price. At first startup the entry is
set to the live price when Yahoo is reachable (so target/stop loss make sense against
today's market), otherwise to the dummy base price below.
"""

from datetime import date, timedelta

from db import get_conn
from market import get_prices

# symbol, name, sector, action, dummy base price, target %, stop-loss %, horizon, rationale
SEED = [
    ("RELIANCE", "Reliance Industries", "Energy", "BUY", 1420, 12, -6, "6 months", "Sample: retail and telecom segments driving earnings visibility."),
    ("TCS", "Tata Consultancy Services", "IT", "BUY", 3150, 10, -5, "6 months", "Sample: steady deal wins and stable margins."),
    ("HDFCBANK", "HDFC Bank", "Banking", "BUY", 980, 11, -5, "9 months", "Sample: loan growth recovering with stable asset quality."),
    ("ICICIBANK", "ICICI Bank", "Banking", "BUY", 1410, 10, -5, "6 months", "Sample: consistent return ratios and deposit growth."),
    ("INFY", "Infosys", "IT", "HOLD", 1520, 7, -6, "6 months", "Sample: guidance steady; wait for clearer demand trend."),
    ("SBIN", "State Bank of India", "Banking", "BUY", 820, 14, -7, "12 months", "Sample: valuation comfort with improving credit costs."),
    ("BHARTIARTL", "Bharti Airtel", "Telecom", "BUY", 1900, 12, -6, "9 months", "Sample: tariff actions supporting ARPU growth."),
    ("ITC", "ITC", "FMCG", "HOLD", 410, 6, -5, "6 months", "Sample: defensive pick; limited near-term triggers."),
    ("LT", "Larsen & Toubro", "Infrastructure", "BUY", 3600, 13, -6, "12 months", "Sample: strong order book across segments."),
    ("HINDUNILVR", "Hindustan Unilever", "FMCG", "SELL", 2400, -8, 5, "3 months", "Sample: volume growth slowing; margin pressure."),
    ("KOTAKBANK", "Kotak Mahindra Bank", "Banking", "BUY", 2050, 10, -5, "9 months", "Sample: balance sheet strength and improving growth."),
    ("AXISBANK", "Axis Bank", "Banking", "BUY", 1150, 12, -6, "9 months", "Sample: integration benefits flowing into earnings."),
    ("BAJFINANCE", "Bajaj Finance", "NBFC", "BUY", 900, 15, -7, "12 months", "Sample: AUM growth with diversified product mix."),
    ("MARUTI", "Maruti Suzuki", "Auto", "BUY", 12500, 11, -5, "9 months", "Sample: new launches and export momentum."),
    ("SUNPHARMA", "Sun Pharmaceutical", "Pharma", "BUY", 1700, 10, -5, "6 months", "Sample: specialty portfolio scaling in the US."),
    ("TITAN", "Titan Company", "Consumer", "HOLD", 3400, 6, -5, "6 months", "Sample: quality franchise, valuation already rich."),
    ("ASIANPAINT", "Asian Paints", "Consumer", "SELL", 2350, -9, 5, "3 months", "Sample: rising competition in decorative paints."),
    ("ULTRACEMCO", "UltraTech Cement", "Cement", "BUY", 11800, 12, -6, "12 months", "Sample: capacity additions and pricing discipline."),
    ("NTPC", "NTPC", "Power", "BUY", 340, 14, -7, "12 months", "Sample: renewable capacity pipeline adds growth."),
    ("POWERGRID", "Power Grid Corporation", "Power", "HOLD", 295, 6, -5, "6 months", "Sample: stable dividends; limited upside from here."),
    ("TATASTEEL", "Tata Steel", "Metals", "SELL", 150, -10, 6, "3 months", "Sample: weak global steel prices weigh on margins."),
    ("M&M", "Mahindra & Mahindra", "Auto", "BUY", 3150, 13, -6, "9 months", "Sample: SUV and tractor demand remain strong."),
    ("HCLTECH", "HCL Technologies", "IT", "BUY", 1550, 10, -5, "6 months", "Sample: services growth leading large-cap IT peers."),
    ("WIPRO", "Wipro", "IT", "SELL", 250, -8, 5, "3 months", "Sample: revenue growth lagging peers."),
]


def tick(x: float) -> float:
    """Round to the NSE tick size of ₹0.05."""
    return round(round(x * 20) / 20, 2)


def seed_if_empty() -> None:
    with get_conn() as conn:
        if conn.execute("SELECT COUNT(*) FROM recommendations").fetchone()[0]:
            return
        prices, _ = get_prices({s[0]: s[4] for s in SEED})
        today = date.today()
        for i, (sym, name, sector, action, base, tgt_pct, sl_pct, horizon, why) in enumerate(SEED):
            entry = tick(prices[sym]["prev_close"])
            conn.execute(
                """INSERT INTO recommendations
                   (symbol, name, sector, action, entry, target, stop_loss, horizon, rationale, issued_on)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (sym, name, sector, action, entry,
                 tick(entry * (1 + tgt_pct / 100)), tick(entry * (1 + sl_pct / 100)),
                 horizon, why, (today - timedelta(days=i)).isoformat()),
            )
