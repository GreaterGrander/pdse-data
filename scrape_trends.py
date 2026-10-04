#!/usr/bin/env python3
"""
Scrapes Google Trends interest scores for a list of public-domain characters,
rescales every batch of 5 onto one consistent 0-100 scale using a shared
anchor term, and writes/updates data.json in the repo root.

Run manually:  pip install pytrends  &&  python scrape_trends.py
Run on a schedule via .github/workflows/update-trends.yml

If pytrends throws errors (Google changes its backend occasionally), swap to:
  pip install pytrends-modern
and change the import below to: from pytrends_modern import TrendReq
"""

import json
import time
import sys
from pathlib import Path

try:
    from pytrends.request import TrendReq
except ImportError:
    sys.exit("Install pytrends first: pip install pytrends")

DATA_FILE = Path(__file__).parent / "data.json"
HISTORY_LENGTH = 14          # keep the last N data points per character
ANCHOR = "Sherlock Holmes"   # steady, well-known term used to rescale batches
GEO = "US"                   # set to "" for worldwide
SLEEP_BETWEEN_REQUESTS = 8   # seconds between requests, be polite to avoid 429s

# (symbol, exact search term) -- add more rows here to scale past 18 characters.
# Keep symbols unique and under 5 chars to match the board's ticker style.
CHARACTERS = [
    ("SHLK", "Sherlock Holmes"),
    ("DRAC", "Dracula"),
    ("FRNK", "Frankenstein's monster"),
    ("ALIC", "Alice in Wonderland"),
    ("PETR", "Peter Pan"),
    ("ROBH", "Robin Hood"),
    ("ZORR", "Zorro"),
    ("TARZ", "Tarzan"),
    ("HYDE", "Mr Hyde"),
    ("SNOW", "Snow White"),
    ("CNDR", "Cinderella"),
    ("PINO", "Pinocchio"),
    ("QUAS", "Quasimodo"),
    ("PHAN", "Phantom of the Opera"),
    ("AHAB", "Captain Ahab"),
    ("HOOK", "Captain Hook"),
    ("MHAT", "Mad Hatter"),
    ("DQUI", "Don Quixote"),
]


def chunks(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def fetch_scores():
    pytrends = TrendReq(hl="en-US", tz=360)
    others = [c for c in CHARACTERS if c[1] != ANCHOR]
    batches = list(chunks(others, 4))  # 4 others + anchor = 5 terms per request

    reference_anchor_value = None
    scores = {}

    for batch in batches:
        terms = [ANCHOR] + [name for _, name in batch]
        pytrends.build_payload(terms, timeframe="now 7-d", geo=GEO)
        df = pytrends.interest_over_time()
        if df.empty:
            print(f"No data for batch: {terms}")
            continue

        latest = df.iloc[-1]
        anchor_value = max(latest[ANCHOR], 1)  # avoid divide-by-zero

        if reference_anchor_value is None:
            reference_anchor_value = anchor_value
            scale = 1.0
        else:
            scale = reference_anchor_value / anchor_value

        for symbol, name in batch:
            scores[symbol] = round(latest[name] * scale, 1)

        time.sleep(SLEEP_BETWEEN_REQUESTS)

    anchor_symbol = next(sym for sym, name in CHARACTERS if name == ANCHOR)
    scores[anchor_symbol] = round(reference_anchor_value, 1) if reference_anchor_value else 0

    return scores


def update_history(scores):
    if DATA_FILE.exists():
        existing = json.loads(DATA_FILE.read_text())
        history = {row[0]: row[2] for row in existing}
    else:
        history = {}

    out = []
    for symbol, name in CHARACTERS:
        hist = history.get(symbol, [])
        hist.append(scores.get(symbol, hist[-1] if hist else 0))
        hist = hist[-HISTORY_LENGTH:]
        out.append([symbol, name, hist])

    DATA_FILE.write_text(json.dumps(out, indent=2))
    print(f"Wrote {len(out)} characters to {DATA_FILE}")


if __name__ == "__main__":
    scores = fetch_scores()
    update_history(scores)
