"""Instruments this demo covers.

STOCKS: 50 large-cap NSE stocks, approximately the Nifty 50 (the index is rebalanced
every six months, so the live list may differ slightly).
  base / vol: rough price and daily volatility, used ONLY to build dummy history
              when Yahoo is unreachable.
  aliases:    names used to tag news headlines; all-caps acronyms match case-sensitively.
  exclude:    phrases that contain an alias but mean a different company.

INDICES: Indian and global indices plus macro instruments for the Markets tab.
"""

def _s(name, sector, base, vol, aliases, exclude=()):
    return {"name": name, "sector": sector, "base": base, "vol": vol, "aliases": list(aliases), "exclude": list(exclude)}


STOCKS = {
    "ADANIENT":   _s("Adani Enterprises", "Conglomerate", 2400, 0.022, ["Adani Enterprises", "Adani Ent"]),
    "ADANIPORTS": _s("Adani Ports & SEZ", "Infrastructure", 1400, 0.019, ["Adani Ports"]),
    "APOLLOHOSP": _s("Apollo Hospitals", "Healthcare", 7000, 0.015, ["Apollo Hospitals"]),
    "ASIANPAINT": _s("Asian Paints", "Consumer", 2350, 0.013, ["Asian Paints"]),
    "AXISBANK":   _s("Axis Bank", "Banking", 1150, 0.015, ["Axis Bank"]),
    "BAJAJ-AUTO": _s("Bajaj Auto", "Auto", 8500, 0.014, ["Bajaj Auto"]),
    "BAJFINANCE": _s("Bajaj Finance", "NBFC", 900, 0.020, ["Bajaj Finance"]),
    "BAJAJFINSV": _s("Bajaj Finserv", "NBFC", 2000, 0.016, ["Bajaj Finserv"]),
    "BEL":        _s("Bharat Electronics", "Defence", 400, 0.020, ["Bharat Electronics", "BEL"]),
    "BHARTIARTL": _s("Bharti Airtel", "Telecom", 1900, 0.013, ["Airtel", "Bharti"]),
    "CIPLA":      _s("Cipla", "Pharma", 1500, 0.013, ["Cipla"]),
    "COALINDIA":  _s("Coal India", "Mining", 390, 0.016, ["Coal India"]),
    "DRREDDY":    _s("Dr. Reddy's Laboratories", "Pharma", 1250, 0.014, ["Dr Reddy", "Dr. Reddy"]),
    "EICHERMOT":  _s("Eicher Motors", "Auto", 5500, 0.016, ["Eicher", "Royal Enfield"]),
    "ETERNAL":    _s("Eternal (Zomato)", "Consumer Tech", 300, 0.025, ["Eternal", "Zomato", "Blinkit"]),
    "GRASIM":     _s("Grasim Industries", "Cement", 2750, 0.014, ["Grasim"]),
    "HCLTECH":    _s("HCL Technologies", "IT", 1550, 0.015, ["HCL Tech", "HCLTech"]),
    "HDFCBANK":   _s("HDFC Bank", "Banking", 980, 0.011, ["HDFC Bank"]),
    "HDFCLIFE":   _s("HDFC Life Insurance", "Insurance", 770, 0.015, ["HDFC Life"]),
    "HEROMOTOCO": _s("Hero MotoCorp", "Auto", 5000, 0.016, ["Hero MotoCorp", "Hero Moto"]),
    "HINDALCO":   _s("Hindalco Industries", "Metals", 700, 0.019, ["Hindalco"]),
    "HINDUNILVR": _s("Hindustan Unilever", "FMCG", 2400, 0.010, ["HUL", "Hindustan Unilever"]),
    "ICICIBANK":  _s("ICICI Bank", "Banking", 1410, 0.012, ["ICICI Bank"]),
    "INDIGO":     _s("InterGlobe Aviation (IndiGo)", "Aviation", 5700, 0.018, ["IndiGo", "InterGlobe"]),
    "INFY":       _s("Infosys", "IT", 1520, 0.015, ["Infosys", "Infy"]),
    "ITC":        _s("ITC", "FMCG", 410, 0.010, ["ITC"], ["ITC Hotels"]),
    "JIOFIN":     _s("Jio Financial Services", "NBFC", 310, 0.020, ["Jio Financial", "Jio Finance"]),
    "JSWSTEEL":   _s("JSW Steel", "Metals", 1050, 0.018, ["JSW Steel"]),
    "KOTAKBANK":  _s("Kotak Mahindra Bank", "Banking", 2050, 0.013, ["Kotak"]),
    "LT":         _s("Larsen & Toubro", "Infrastructure", 3600, 0.014, ["L&T", "Larsen"], ["L&T Finance", "L&T Technology"]),
    "M&M":        _s("Mahindra & Mahindra", "Auto", 3150, 0.017, ["M&M", "Mahindra & Mahindra", "Mahindra and Mahindra"]),
    "MARUTI":     _s("Maruti Suzuki", "Auto", 12500, 0.014, ["Maruti"]),
    "MAXHEALTH":  _s("Max Healthcare", "Healthcare", 1150, 0.019, ["Max Healthcare"]),
    "NESTLEIND":  _s("Nestle India", "FMCG", 1200, 0.011, ["Nestle"]),
    "NTPC":       _s("NTPC", "Power", 340, 0.016, ["NTPC"], ["NTPC Green"]),
    "ONGC":       _s("Oil & Natural Gas Corp", "Energy", 240, 0.017, ["ONGC"]),
    "POWERGRID":  _s("Power Grid Corporation", "Power", 295, 0.013, ["Power Grid", "POWERGRID"]),
    "RELIANCE":   _s("Reliance Industries", "Energy", 1420, 0.014, ["Reliance", "RIL"],
                     ["Reliance Power", "Reliance Infra", "Reliance Capital", "Reliance Communications", "Reliance Home"]),
    "SBILIFE":    _s("SBI Life Insurance", "Insurance", 1800, 0.014, ["SBI Life"]),
    "SBIN":       _s("State Bank of India", "Banking", 820, 0.016, ["SBI", "State Bank"], ["SBI Card", "SBI Life"]),
    "SHRIRAMFIN": _s("Shriram Finance", "NBFC", 650, 0.021, ["Shriram Finance"]),
    "SUNPHARMA":  _s("Sun Pharmaceutical", "Pharma", 1700, 0.013, ["Sun Pharma"]),
    "TATACONSUM": _s("Tata Consumer Products", "FMCG", 1100, 0.015, ["Tata Consumer"]),
    "TATASTEEL":  _s("Tata Steel", "Metals", 150, 0.022, ["Tata Steel"]),
    "TCS":        _s("Tata Consultancy Services", "IT", 3150, 0.013, ["TCS", "Tata Consultancy"]),
    "TECHM":      _s("Tech Mahindra", "IT", 1500, 0.017, ["Tech Mahindra", "TechM"]),
    "TITAN":      _s("Titan Company", "Consumer", 3400, 0.015, ["Titan"]),
    "TRENT":      _s("Trent", "Retail", 5200, 0.024, ["Trent"]),
    "ULTRACEMCO": _s("UltraTech Cement", "Cement", 11800, 0.014, ["UltraTech"]),
    "WIPRO":      _s("Wipro", "IT", 250, 0.016, ["Wipro"]),
}

# key: (yahoo ticker, display name, group, dummy base, dummy daily vol)
INDICES = {
    "NIFTY50":   ("^NSEI", "Nifty 50", "India", 25000, 0.009),
    "SENSEX":    ("^BSESN", "Sensex", "India", 82000, 0.009),
    "BANKNIFTY": ("^NSEBANK", "Nifty Bank", "India", 55000, 0.011),
    "NIFTYIT":   ("^CNXIT", "Nifty IT", "India", 36000, 0.013),
    "INDIAVIX":  ("^INDIAVIX", "India VIX", "India", 13, 0.045),
    "SPX":       ("^GSPC", "S&P 500", "Global", 6400, 0.009),
    "NASDAQ":    ("^IXIC", "Nasdaq Composite", "Global", 21000, 0.012),
    "DOW":       ("^DJI", "Dow Jones", "Global", 45000, 0.008),
    "FTSE":      ("^FTSE", "FTSE 100", "Global", 9000, 0.008),
    "DAX":       ("^GDAXI", "DAX", "Global", 24000, 0.010),
    "NIKKEI":    ("^N225", "Nikkei 225", "Global", 42000, 0.012),
    "HANGSENG":  ("^HSI", "Hang Seng", "Global", 25000, 0.013),
    "USDINR":    ("INR=X", "USD/INR", "Macro", 87.5, 0.003),
    "BRENT":     ("BZ=F", "Brent Crude ($)", "Macro", 68, 0.018),
    "GOLD":      ("GC=F", "Gold ($/oz)", "Macro", 3500, 0.009),
    "US10Y":     ("^TNX", "US 10Y Yield (%)", "Macro", 4.2, 0.015),
    "DXY":       ("DX-Y.NYB", "Dollar Index", "Macro", 98, 0.004),
}


def yahoo_ticker(key: str) -> str:
    return INDICES[key][0] if key in INDICES else f"{key}.NS"
