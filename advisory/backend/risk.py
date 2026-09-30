"""Client risk profiling and call risk levels.

A client answers 7 questions (each option scores 1–4, total 7–28). The score maps
to a profile, and each profile is suited to certain call risk levels. A call's risk
level comes from the stock's measured volatility, not from opinion.
"""

QUESTIONS = [
    ("What is your age?", ["60 or above", "45 to 60", "30 to 45", "Under 30"]),
    ("How long can you stay invested?", ["Less than 1 year", "1 to 3 years", "3 to 5 years", "More than 5 years"]),
    ("How much investing experience do you have?", ["None", "Only FDs or mutual funds", "Stocks for 1–3 years", "Stocks or F&O for 3+ years"]),
    ("How stable is your income?", ["Irregular", "Somewhat stable", "Stable", "Very stable, with surplus"]),
    ("What share of your savings will you invest in stocks?", ["More than 50%", "25% to 50%", "10% to 25%", "Less than 10%"]),
    ("Your portfolio falls 20% in a month. What do you do?", ["Sell everything", "Sell some", "Hold", "Buy more"]),
    ("What is your main goal?", ["Protect my capital", "Regular income", "Balanced growth", "Maximum growth"]),
]

PROFILES = [  # (max score, profile, suited risk levels, description)
    (13, "Conservative", ["Low"], "You prefer stability. Calls on steadier stocks suit you best."),
    (21, "Moderate", ["Low", "Medium"], "You accept some ups and downs for better growth."),
    (28, "Aggressive", ["Low", "Medium", "High"], "You can handle large swings in pursuit of higher returns."),
]
LEVELS = ["Low", "Medium", "High"]


def score(answers: list[int]) -> dict:
    total = sum(a + 1 for a in answers)  # option index 0–3 → 1–4 points
    for max_score, profile, suited, description in PROFILES:
        if total <= max_score:
            return {"score": total, "max_score": 28, "profile": profile, "suited_levels": suited,
                    "description": description}
    raise ValueError("score out of range")


def risk_level(annual_vol_pct: float, setup: str | None = None) -> str:
    """Low < 20% a year, Medium 20–28%, High above 28%. Counter-trend setups go one level up."""
    idx = 0 if annual_vol_pct < 20 else 1 if annual_vol_pct < 28 else 2
    if setup == "OVERSOLD_BOUNCE":
        idx = min(idx + 1, 2)
    return LEVELS[idx]
