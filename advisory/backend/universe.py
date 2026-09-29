"""The 24 NSE stocks this demo covers.

base: a rough price used only to build dummy history when Yahoo is unreachable.
vol: daily volatility for that dummy history (so stocks differ in risk).
aliases: names used to tag news headlines. Short acronyms match case-sensitively.
exclude: phrases that contain an alias but mean a different company.
"""

UNIVERSE = {
    "RELIANCE":   {"name": "Reliance Industries", "sector": "Energy", "base": 1420, "vol": 0.014, "aliases": ["Reliance", "RIL"],
                  "exclude": ["Reliance Power", "Reliance Infra", "Reliance Capital", "Reliance Communications", "Reliance Home", "Reliance Retail"]},
    "TCS":        {"name": "Tata Consultancy Services", "sector": "IT", "base": 3150, "vol": 0.013, "aliases": ["TCS", "Tata Consultancy"]},
    "HDFCBANK":   {"name": "HDFC Bank", "sector": "Banking", "base": 980, "vol": 0.011, "aliases": ["HDFC Bank"]},
    "ICICIBANK":  {"name": "ICICI Bank", "sector": "Banking", "base": 1410, "vol": 0.012, "aliases": ["ICICI Bank"]},
    "INFY":       {"name": "Infosys", "sector": "IT", "base": 1520, "vol": 0.015, "aliases": ["Infosys", "Infy"]},
    "SBIN":       {"name": "State Bank of India", "sector": "Banking", "base": 820, "vol": 0.016, "aliases": ["SBI", "State Bank"],
                  "exclude": ["SBI Card", "SBI Life"]},
    "BHARTIARTL": {"name": "Bharti Airtel", "sector": "Telecom", "base": 1900, "vol": 0.013, "aliases": ["Airtel", "Bharti"]},
    "ITC":        {"name": "ITC", "sector": "FMCG", "base": 410, "vol": 0.010, "aliases": ["ITC"]},
    "LT":         {"name": "Larsen & Toubro", "sector": "Infrastructure", "base": 3600, "vol": 0.014, "aliases": ["L&T", "Larsen"]},
    "HINDUNILVR": {"name": "Hindustan Unilever", "sector": "FMCG", "base": 2400, "vol": 0.010, "aliases": ["HUL", "Hindustan Unilever"]},
    "KOTAKBANK":  {"name": "Kotak Mahindra Bank", "sector": "Banking", "base": 2050, "vol": 0.013, "aliases": ["Kotak"]},
    "AXISBANK":   {"name": "Axis Bank", "sector": "Banking", "base": 1150, "vol": 0.015, "aliases": ["Axis Bank"]},
    "BAJFINANCE": {"name": "Bajaj Finance", "sector": "NBFC", "base": 900, "vol": 0.020, "aliases": ["Bajaj Finance"]},
    "MARUTI":     {"name": "Maruti Suzuki", "sector": "Auto", "base": 12500, "vol": 0.014, "aliases": ["Maruti"]},
    "SUNPHARMA":  {"name": "Sun Pharmaceutical", "sector": "Pharma", "base": 1700, "vol": 0.013, "aliases": ["Sun Pharma"]},
    "TITAN":      {"name": "Titan Company", "sector": "Consumer", "base": 3400, "vol": 0.015, "aliases": ["Titan"]},
    "ASIANPAINT": {"name": "Asian Paints", "sector": "Consumer", "base": 2350, "vol": 0.013, "aliases": ["Asian Paints"]},
    "ULTRACEMCO": {"name": "UltraTech Cement", "sector": "Cement", "base": 11800, "vol": 0.014, "aliases": ["UltraTech"]},
    "NTPC":       {"name": "NTPC", "sector": "Power", "base": 340, "vol": 0.016, "aliases": ["NTPC"]},
    "POWERGRID":  {"name": "Power Grid Corporation", "sector": "Power", "base": 295, "vol": 0.013, "aliases": ["Power Grid", "POWERGRID"]},
    "TATASTEEL":  {"name": "Tata Steel", "sector": "Metals", "base": 150, "vol": 0.022, "aliases": ["Tata Steel"]},
    "M&M":        {"name": "Mahindra & Mahindra", "sector": "Auto", "base": 3150, "vol": 0.017, "aliases": ["M&M", "Mahindra & Mahindra", "Mahindra and Mahindra"]},
    "HCLTECH":    {"name": "HCL Technologies", "sector": "IT", "base": 1550, "vol": 0.015, "aliases": ["HCL Tech", "HCLTech"]},
    "WIPRO":      {"name": "Wipro", "sector": "IT", "base": 250, "vol": 0.016, "aliases": ["Wipro"]},
}
