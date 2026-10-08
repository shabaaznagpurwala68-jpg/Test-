"""SAMPLE blog posts for the Learn tab — demonstration content only.

Posts are written as evergreen explainers: they describe how events work, not what
happened on a particular day, so nothing here states a market fact that could go stale
or be wrong. To add a post, append a dict to POSTS. Body blocks:
  ("p", text) paragraph · ("h", text) sub-heading · ("ul", [items]) bullet list ·
  ("callout", text) highlighted key point.
The Weekly Wrap post's body is built from live app data in blog.py, not stored here.
"""

POSTS = [
    {
        "slug": "rbi-policy-day",
        "category": "Market Events",
        "title": "RBI Policy Day: What It Means For You",
        "excerpt": "One rate decision moves banks, borrowers and the whole market. Here's how it reaches your portfolio.",
        "days_ago": 2,
        "read_min": 4,
        "featured": True,
        "body": [
            ("p", "Every two months, the Reserve Bank of India's Monetary Policy Committee meets and decides the repo rate — the rate at which banks borrow from the RBI. It sounds technical. It isn't. That one number travels through the whole economy, and through your portfolio."),
            ("h", "How a rate decision travels"),
            ("ul", [
                "Banks' cost of money changes, so loan and deposit rates follow — your home-loan EMI included.",
                "Cheaper money tends to support spending and company earnings; costlier money cools both.",
                "Bond yields react first, and stock valuations take their cue from bond yields.",
            ]),
            ("h", "Who usually feels it most"),
            ("p", "Rate-sensitive sectors move first: banks and NBFCs (their lending margins), real estate and autos (buyers borrow to purchase), and capital-heavy businesses such as infrastructure and power."),
            ("callout", "The decision itself is often expected. Markets react to the surprise — and to the RBI's tone about what comes next."),
            ("h", "What to watch on the day"),
            ("ul", [
                "The repo rate decision: cut, hike or hold.",
                "The stance (accommodative, neutral or withdrawal of accommodation) — it signals the next move.",
                "The inflation and GDP forecasts in the policy statement.",
            ]),
            ("p", "Smart move: don't trade the headline in the first minutes. Volatility spikes and spreads widen. Let the market digest the statement, then act on your plan."),
        ],
    },
    {
        "slug": "results-season-5-numbers",
        "category": "Market Events",
        "title": "Results Season: 5 Numbers Worth Watching",
        "excerpt": "Quarterly results arrive in a flood. These five numbers tell you most of the story in minutes.",
        "days_ago": 5,
        "read_min": 5,
        "body": [
            ("p", "Listed companies publish quarterly results within 45 days of a quarter ending (60 days for the final quarter of the year). For a few weeks, hundreds of companies report. Here's how to read one in five minutes."),
            ("h", "1. Revenue growth"),
            ("p", "Compare with the same quarter last year (year-on-year), not just the previous quarter — many businesses are seasonal."),
            ("h", "2. Operating margin"),
            ("p", "Revenue can grow while profits shrink. A rising operating margin means the company is keeping more of every rupee it earns."),
            ("h", "3. EPS versus expectations"),
            ("p", "Prices move on surprises. A good result that the market already expected can still see the stock fall."),
            ("h", "4. Guidance"),
            ("p", "What management says about the next few quarters often matters more than the quarter just gone."),
            ("h", "5. Management commentary"),
            ("p", "Read the investor presentation or call notes for demand trends, pricing power and costs."),
            ("callout", "Our Fundamental scorecard uses several of these: revenue and EPS growth, return on equity and capital, and debt."),
        ],
    },
    {
        "slug": "muhurat-trading-explained",
        "category": "Market Events",
        "title": "Muhurat Trading, Explained in 2 Minutes",
        "excerpt": "A one-hour session on Diwali, a long tradition, and a few things every trader should know.",
        "days_ago": 8,
        "read_min": 2,
        "body": [
            ("p", "On Diwali, the stock exchanges open for a special session of about an hour, called Muhurat Trading. It marks the start of a new Samvat — the Hindu calendar year — and many investors place a token buy as an auspicious start."),
            ("h", "How it works"),
            ("ul", [
                "The exchanges announce the exact timing a few weeks before Diwali.",
                "It is a normal trading session: trades carry the usual settlement obligations.",
                "Volumes are usually thin, so prices can jump on small orders.",
            ]),
            ("callout", "Thin volume means wide spreads. Use limit orders, not market orders, in the Muhurat session."),
            ("p", "Tradition is a good reason to invest for the long term. It isn't a reason to change your plan for an hour."),
        ],
    },
    {
        "slug": "expiry-day-explained",
        "category": "Guides",
        "title": "Expiry Day Explained: Why Markets Get Choppy",
        "excerpt": "Futures and options contracts end on fixed days. Here's why prices swing as the clock runs down.",
        "days_ago": 11,
        "read_min": 4,
        "body": [
            ("p", "Every futures and options (F&O) contract has an expiry date. On that day, open positions are settled and the contract stops trading. Index options have weekly expiries; stock futures and options expire monthly. Check the exchange's current expiry calendar — the days have changed in recent years."),
            ("h", "Why expiry days get choppy"),
            ("ul", [
                "Traders close or roll positions to the next contract, adding a burst of orders.",
                "Option sellers defend strike prices with big open interest, which can pin the index near those levels.",
                "Time value of options falls fastest in the final hours, so option prices move sharply.",
            ]),
            ("h", "Stock F&O are settled by delivery"),
            ("p", "Open stock futures and in-the-money stock options held to expiry are settled physically: you may have to take or give delivery of the shares. Make sure you have the funds or shares, or close the position before expiry."),
            ("callout", "Not planning to take delivery? Square off or roll over stock F&O positions before expiry day."),
            ("p", "Expiry isn't something to fear. Know the date, know your positions, and size your trades for a day that can swing both ways."),
        ],
    },
    {
        "slug": "how-we-score-a-stock",
        "category": "Guides",
        "title": "How We Score a Stock Out of 100",
        "excerpt": "Valuation, quality, growth and shareholder factors — the scorecard behind our Fundamental picks.",
        "days_ago": 15,
        "read_min": 4,
        "body": [
            ("p", "Every one of the 50 stocks we cover gets the same 100-point scorecard. Same rules, same benchmarks, no exceptions. Here's what goes into it."),
            ("h", "Four pillars, 25 points each"),
            ("ul", [
                "Valuation — is the price reasonable? PE and PB compared with peers, and PEG (PE divided by EPS growth).",
                "Quality — does the business earn well on its money? ROE, ROCE and debt. Banks and NBFCs use ROE and ROA instead.",
                "Growth — is it getting bigger? Three-year revenue and EPS growth.",
                "Shareholder — is it fair to you? Dividend yield, promoter holding and promoter pledge.",
            ]),
            ("h", "From score to pick"),
            ("p", "A stock becomes a PICK only when it scores at least 75 AND trades at least 15% below our fair value. A high score alone isn't enough — a great company can be priced too high. Those go on the WATCH list."),
            ("callout", "Open any stock on the Fundamental tab to see every factor, its benchmark and the points it earned."),
        ],
    },
]
