"""SAMPLE fundamental data for the 50 stocks — for demonstration only.

Approximately in line with recent reported figures, but NOT sourced, audited or current.
There is no reliable free feed of Indian fundamentals; a live product would load these
from a licensed data vendor. PE and PB are NOT stored: they are recalculated from the
live price, using EPS and book value per share derived below.

Columns:
  pe, pb    ratios at the dummy base price (used only to derive EPS and book value)
  roe, roce return on equity / capital employed, %   (roce None for financials)
  de        debt-to-equity                            (None for financials)
  roa       return on assets, % — financials only
  rev3      3-year revenue CAGR, %
  eps3      3-year EPS CAGR, %                        (None = not meaningful, e.g. turnaround)
  dy        dividend yield at the base price, %
  prom      promoter holding, %                       (0 = no identifiable promoter)
  pledge    promoter shares pledged, % of promoter holding
  mcap      market cap at the base price, ₹ crore
"""

from universe import STOCKS

_ROWS = {
    #             pe    pb   roe  roce  de    roa  rev3 eps3  dy   prom pledge  mcap
    "ADANIENT":   (45,  4.5, 10,  11,  1.4,  None, 20,  25,  0.1, 72, 1.0,  280000),
    "ADANIPORTS": (26,  5.0, 18,  14,  0.9,  None, 22,  20,  0.5, 66, 0.5,  300000),
    "APOLLOHOSP": (70, 11.0, 16,  17,  0.8,  None, 14,  28,  0.3, 29, 2.0,  100000),
    "ASIANPAINT": (55, 12.0, 22,  29,  0.1,  None,  5,   2,  1.2, 53, 0.0,  225000),
    "AXISBANK":   (13,  1.8, 16,  None, None, 1.8, 20,  30,  0.1,  8, 0.0,  355000),
    "BAJAJ-AUTO": (30,  8.0, 28,  36,  0.1,  None, 15,  18,  2.2, 55, 0.0,  237000),
    "BAJFINANCE": (32,  5.8, 19,  None, None, 4.2, 28,  25,  0.5, 54, 0.0,  560000),
    "BAJAJFINSV": (33,  4.0, 13,  None, None, 2.0, 25,  18,  0.05, 60, 0.0, 320000),
    "BEL":        (50, 13.0, 27,  36,  0.0,  None, 14,  25,  0.6, 51, 0.0,  290000),
    "BHARTIARTL": (45,  9.0, 25,  16,  1.4,  None, 12,  60,  0.5, 53, 0.0, 1150000),
    "CIPLA":      (23,  3.9, 17,  22,  0.02, None,  9,  20,  1.0, 30, 0.0,  120000),
    "COALINDIA":  (7,   2.7, 38,  50,  0.1,  None,  5,  15,  6.5, 63, 0.0,  240000),
    "DRREDDY":    (18,  3.2, 19,  23,  0.06, None, 13,  20,  0.6, 27, 0.0,  104000),
    "EICHERMOT":  (34,  7.5, 23,  28,  0.02, None, 20,  30,  1.2, 49, 0.0,  150000),
    "ETERNAL":    (400, 12.0, 3,   3,  0.05, None, 60, None, 0.0,  0, 0.0,  290000),
    "GRASIM":     (40,  1.8,  5,   7,  1.0,  None, 15,  -5,  0.4, 43, 0.0,  185000),
    "HCLTECH":    (24,  6.0, 24,  31,  0.1,  None, 10,   9,  3.8, 61, 0.0,  420000),
    "HDFCBANK":   (20,  2.7, 14,  None, None, 1.8, 30,  15,  1.1,  0, 0.0, 1500000),
    "HDFCLIFE":   (80,  9.0, 11,  None, None, 0.6, 18,  12,  0.3, 50, 0.0,  165000),
    "HEROMOTOCO": (20,  4.7, 23,  31,  0.05, None,  8,  15,  3.4, 35, 0.0,  100000),
    "HINDALCO":   (10,  1.4, 14,  13,  0.6,  None, 12,  12,  0.7, 35, 0.0,  155000),
    "HINDUNILVR": (52, 11.0, 21,  28,  0.02, None,  8,   8,  1.8, 62, 0.0,  560000),
    "ICICIBANK":  (19,  3.2, 17,  None, None, 2.3, 25,  30,  0.8,  0, 0.0, 1000000),
    "INDIGO":     (28, 30.0, 45,  20,  3.5,  None, 35, None, 0.2, 49, 0.0,  220000),
    "INFY":       (24,  7.5, 30,  38,  0.1,  None, 11,   9,  2.8, 14, 0.0,  630000),
    "ITC":        (25,  7.0, 28,  37,  0.0,  None,  9,  11,  3.5,  0, 0.0,  515000),
    "JIOFIN":     (110, 1.3, 1.2, None, None, 1.0, 20,   5,  0.2, 47, 0.0,  200000),
    "JSWSTEEL":   (35,  3.0,  8,  11,  1.1,  None, 18, -10,  0.7, 45, 4.0,  255000),
    "KOTAKBANK":  (20,  2.6, 13,  None, None, 2.4, 20,  20,  0.1, 26, 0.0,  410000),
    "LT":         (32,  5.0, 16,  15,  1.1,  None, 17,  22,  0.9,  0, 0.0,  495000),
    "M&M":        (28,  5.5, 18,  17,  1.3,  None, 22,  30,  0.7, 18, 0.0,  390000),
    "MARUTI":     (26,  4.0, 16,  21,  0.0,  None, 22,  45,  1.1, 58, 0.0,  395000),
    "MAXHEALTH":  (90, 10.0, 14,  15,  0.2,  None, 20,  25,  0.1, 24, 0.0,  110000),
    "NESTLEIND":  (70, 55.0, 90, 110,  0.2,  None, 10,  12,  1.3, 63, 0.0,  230000),
    "NTPC":       (15,  1.9, 13,  10,  1.4,  None, 12,  12,  2.4, 51, 0.0,  330000),
    "ONGC":       (8,   0.9, 12,  13,  0.4,  None, 10,  15,  5.0, 59, 0.0,  300000),
    "POWERGRID":  (17,  3.0, 18,  13,  1.4,  None,  5,   5,  3.7, 51, 0.0,  275000),
    "RELIANCE":   (24,  2.2,  9,  10,  0.4,  None, 12,   6,  0.4, 50, 0.0, 1920000),
    "SBILIFE":    (70, 10.0, 14,  None, None, 0.5, 15,  16,  0.2, 55, 0.0,  180000),
    "SBIN":       (9,   1.5, 18,  None, None, 1.1, 18,  40,  1.9, 57, 0.0,  730000),
    "SHRIRAMFIN": (13,  2.1, 16,  None, None, 3.2, 18,  20,  1.5, 25, 0.0,  122000),
    "SUNPHARMA":  (36,  5.5, 16,  19,  0.05, None, 11,  18,  0.9, 54, 0.0,  408000),
    "TATACONSUM": (80,  5.5,  7,   9,  0.1,  None, 12,  12,  0.8, 34, 0.0,  109000),
    "TATASTEEL":  (50,  2.2,  4,   8,  1.0,  None,  3, -30,  2.4, 33, 0.0,  187000),
    "TCS":        (24, 12.0, 52,  64,  0.1,  None, 10,  10,  1.8, 72, 0.0, 1140000),
    "TECHM":      (38,  5.5, 14,  19,  0.1,  None,  5,  -8,  3.0, 35, 0.0,  147000),
    "TITAN":      (85, 25.0, 32,  22,  1.2,  None, 22,  18,  0.3, 53, 0.0,  302000),
    "TRENT":      (110, 35.0, 30, 28,  0.4,  None, 50,  80,  0.1, 37, 0.0,  185000),
    "ULTRACEMCO": (50,  5.0, 10,  12,  0.3,  None, 12,   8,  0.6, 60, 0.0,  340000),
    "WIPRO":      (20,  3.3, 16,  19,  0.2,  None,  3,   4,  2.4, 72, 0.0,  262000),
}

FUNDAMENTALS = {}
for sym, (pe, pb, roe, roce, de, roa, rev3, eps3, dy, prom, pledge, mcap) in _ROWS.items():
    base = STOCKS[sym]["base"]
    FUNDAMENTALS[sym] = {
        "eps": base / pe,                   # trailing EPS, ₹
        "bvps": base / pb,                  # book value per share, ₹
        "dps": base * dy / 100,             # dividend per share, ₹
        "shares_cr": mcap / base,           # shares outstanding, crore
        "roe": roe, "roce": roce, "de": de, "roa": roa,
        "rev_cagr3": rev3, "eps_cagr3": eps3,
        "promoter": prom, "pledge": pledge,
    }

assert set(FUNDAMENTALS) == set(STOCKS), "every stock needs sample fundamentals"
