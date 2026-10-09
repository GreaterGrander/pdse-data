#!/usr/bin/env python3
"""
Pulls real daily Wikipedia pageview counts for a list of public-domain
characters from the official, free, keyless Wikimedia Pageviews API, and
writes/updates data.json in the repo root.

No API key, no pip installs, no rate-limit workarounds needed -- just
Python's standard library. This is the MVP-simple version.
"""

import json
import math
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data.json"
HISTORY_DAYS = 14   # how many days of daily pageviews to pull per character

# Wikimedia asks every API client to identify itself with a real User-Agent.
# Put a real contact (your site URL or email) here before running.
USER_AGENT = "PDSE-Bot/1.0 (greaterandgrander@gmail.com)"

# (symbol, exact Wikipedia article title) -- add more rows to scale past 18.
# Titles must match the article exactly as it appears in the en.wikipedia.org
# URL (with spaces instead of underscores). If a title is wrong, that row
# just falls back to a flat line instead of breaking the whole run.
CHARACTERS = [
    ("SHLK", "Sherlock Holmes"),
    ("DRAC", "Dracula"),
    ("FRNK", "Frankenstein's monster"),
    ("DRFR", "Victor Frankenstein"),
    ("ALIC", "Alice (Wonderland)"),
    ("PETR", "Peter Pan"),
    ("ROBH", "Robin Hood"),
    ("ZORR", "Zorro"),
    ("TARZ", "Tarzan"),
    ("HYDE", "Mr. Hyde"),
    ("SNOW", "Snow White"),
    ("CNDR", "Cinderella"),
    ("PINO", "Pinocchio"),
    ("QUAS", "Quasimodo"),
    ("PHAN", "Erik (The Phantom of the Opera)"),
    ("AHAB", "Captain Ahab"),
    ("HOOK", "Captain Hook"),
    ("MHAT", "Mad Hatter"),
    ("DQUI", "Don Quixote"),
    ("ATLA", "Atlas (mythology)"),
    ("ELBE", "Elizabeth Bennet"),
    ("MRDA", "Mr. Darcy"),
    ("BENN", "Bennet family"),
    ("GEWI", "George Wickham"),
    ("WICO", "Mr William Collins"),
    ("LCDB", "Lady Catherine de Bourgh"),
    ("ISHM", "Ishmael (Moby-Dick)"),
    ("MOBY", "Moby_Dick_(whale)"),
    ("WHIT", "White Rabbit"),
    ("CATP", "Caterpillar (Alice's Adventures in Wonderland)"),
    ("CHES", "Cheshire Cat"),
    ("HARE", "March Hare"),
    ("QUEN", "Queen of Hearts (Alice's Adventures in Wonderland)"),
]


def fetch_pageviews(article):
    """Returns a list of daily view counts for the last HISTORY_DAYS days."""
    end = datetime.utcnow().date() - timedelta(days=1)  # yesterday (today is incomplete)
    start = end - timedelta(days=HISTORY_DAYS - 1)
    title = urllib.parse.quote(article.replace(" ", "_"), safe="")
    url = (
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        f"en.wikipedia/all-access/user/{title}/daily/"
        f"{start.strftime('%Y%m%d')}/{end.strftime('%Y%m%d')}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
        return [item["views"] for item in data.get("items", [])]
    except Exception as e:
        print(f"Failed to fetch '{article}': {e}")
        return []


def to_index(views):
    """Compresses raw daily view counts onto a 0-100-ish scale so the
    board's existing price formula (unchanged) still looks right."""
    return min(99, round(math.sqrt(max(views, 0))))


def main():
    out = []
    for symbol, article in CHARACTERS:
        raw = fetch_pageviews(article)
        hist = [to_index(v) for v in raw] if raw else [10] * HISTORY_DAYS
        out.append([symbol, article, hist])
        time.sleep(0.5)  # polite pause; nowhere near Wikimedia's limits

    DATA_FILE.write_text(json.dumps(out, indent=2))
    print(f"Wrote {len(out)} characters to {DATA_FILE}")


if __name__ == "__main__":
    main()
