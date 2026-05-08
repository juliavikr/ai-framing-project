"""
scrape_eu_debates.py — Scrape EU Parliament verbatim plenary debate records (CRE docs).

Generates CRE document URLs from known EP 9th-term plenary session dates (2020-2024)
and fetches each directly from europarl.europa.eu. Keeps only debate items that mention
AI topics.

Actor: EU Commission  |  context: policy  |  platform: regulatory_doc

Usage:
    python src/scraping/scrape_eu_debates.py
    python src/scraping/scrape_eu_debates.py --limit 300
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Optional

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import ACTORS, DATA_RAW
from src.scraping.scrape_individuals import (
    DELAY, extract_date, extract_text, fetch, load_seen_urls, make_session, save_doc,
)

EP_BASE = "https://www.europarl.europa.eu"

# ── Known EP 9th-term plenary session dates (2020-2024) ───────────────────────
# Strasbourg sessions (4 days) and Brussels mini-plenaries (2 days).
# Each date = one CRE document page.

EP_PLENARY_DATES: list[str] = [
    # 2020
    "2020-01-13", "2020-01-14", "2020-01-15", "2020-01-16",
    "2020-02-10", "2020-02-11", "2020-02-12", "2020-02-13",
    "2020-03-09", "2020-03-10", "2020-03-11", "2020-03-12",
    "2020-04-16", "2020-04-17",
    "2020-05-13", "2020-05-14", "2020-05-15",
    "2020-06-17", "2020-06-18", "2020-06-19",
    "2020-07-08", "2020-07-09", "2020-07-10",
    "2020-09-14", "2020-09-15", "2020-09-16", "2020-09-17",
    "2020-10-05", "2020-10-06", "2020-10-07", "2020-10-08",
    "2020-10-19", "2020-10-20", "2020-10-21", "2020-10-22",
    "2020-11-23", "2020-11-24", "2020-11-25", "2020-11-26",
    "2020-12-14", "2020-12-15", "2020-12-16", "2020-12-17",
    # 2021
    "2021-01-11", "2021-01-12", "2021-01-13", "2021-01-14",
    "2021-02-08", "2021-02-09", "2021-02-10", "2021-02-11",
    "2021-03-08", "2021-03-09", "2021-03-10", "2021-03-11",
    "2021-03-24", "2021-03-25",
    "2021-04-26", "2021-04-27", "2021-04-28", "2021-04-29",
    "2021-05-17", "2021-05-18", "2021-05-19", "2021-05-20",
    "2021-06-07", "2021-06-08", "2021-06-09", "2021-06-10",
    "2021-06-23", "2021-06-24",
    "2021-07-05", "2021-07-06", "2021-07-07", "2021-07-08",
    "2021-09-13", "2021-09-14", "2021-09-15", "2021-09-16",
    "2021-10-04", "2021-10-05", "2021-10-06", "2021-10-07",
    "2021-10-18", "2021-10-19", "2021-10-20", "2021-10-21",
    "2021-11-22", "2021-11-23", "2021-11-24", "2021-11-25",
    "2021-12-13", "2021-12-14", "2021-12-15", "2021-12-16",
    # 2022
    "2022-01-17", "2022-01-18", "2022-01-19", "2022-01-20",
    "2022-02-14", "2022-02-15", "2022-02-16", "2022-02-17",
    "2022-03-07", "2022-03-08", "2022-03-09", "2022-03-10",
    "2022-03-23", "2022-03-24",
    "2022-04-04", "2022-04-05", "2022-04-06", "2022-04-07",
    "2022-05-09", "2022-05-10", "2022-05-11", "2022-05-12",
    "2022-06-06", "2022-06-07", "2022-06-08", "2022-06-09",
    "2022-06-22", "2022-06-23",
    "2022-07-04", "2022-07-05", "2022-07-06", "2022-07-07",
    "2022-09-12", "2022-09-13", "2022-09-14", "2022-09-15",
    "2022-10-03", "2022-10-04", "2022-10-05", "2022-10-06",
    "2022-10-17", "2022-10-18", "2022-10-19", "2022-10-20",
    "2022-11-21", "2022-11-22", "2022-11-23", "2022-11-24",
    "2022-12-12", "2022-12-13", "2022-12-14", "2022-12-15",
    # 2023
    "2023-01-16", "2023-01-17", "2023-01-18", "2023-01-19",
    "2023-02-01", "2023-02-02",
    "2023-02-13", "2023-02-14", "2023-02-15", "2023-02-16",
    "2023-03-06", "2023-03-07", "2023-03-08", "2023-03-09",
    "2023-03-22", "2023-03-23",
    "2023-04-17", "2023-04-18", "2023-04-19", "2023-04-20",
    "2023-05-08", "2023-05-09", "2023-05-10", "2023-05-11",
    "2023-05-31", "2023-06-01",
    "2023-06-12", "2023-06-13", "2023-06-14", "2023-06-15",  # AI Act!
    "2023-07-10", "2023-07-11", "2023-07-12", "2023-07-13",
    "2023-09-11", "2023-09-12", "2023-09-13", "2023-09-14",
    "2023-10-02", "2023-10-03", "2023-10-04", "2023-10-05",
    "2023-10-18", "2023-10-19",
    "2023-11-20", "2023-11-21", "2023-11-22", "2023-11-23",
    "2023-12-11", "2023-12-12", "2023-12-13", "2023-12-14",
    # 2024 (9th term ends after May 2024 elections)
    "2024-01-15", "2024-01-16", "2024-01-17", "2024-01-18",
    "2024-01-31", "2024-02-01",
    "2024-02-05", "2024-02-06", "2024-02-07", "2024-02-08",
    "2024-02-26", "2024-02-27", "2024-02-28", "2024-02-29",
    "2024-03-11", "2024-03-12", "2024-03-13", "2024-03-14",  # AI Act final vote!
    "2024-04-22", "2024-04-23", "2024-04-24", "2024-04-25",
    "2024-05-22", "2024-05-23",
]

# Keyword filter: only save debate items that clearly discuss AI
AI_KEYWORDS = re.compile(
    r"\b(artificial intelligence|machine learning|AI regulation|AI act|"
    r"digital regulation|algorithm|automated decision|data governance|"
    r"large language model|foundation model|generative AI|AI safety|"
    r"biometric|facial recognition|deep fake|autonomous weapon)\b",
    re.I,
)

MIN_WORDS = 300


# ── URL generation ─────────────────────────────────────────────────────────────

def make_cre_url(date: str) -> str:
    """Build a CRE-9 document URL for the given YYYY-MM-DD date."""
    return f"{EP_BASE}/doceo/document/CRE-9-{date}_EN.html"


# ── Date extraction ────────────────────────────────────────────────────────────

def date_from_url(url: str) -> str:
    """Pull YYYY-MM-DD from CRE URL slug (CRE-9-2023-10-04-...)."""
    m = re.search(r"CRE-\d+-(\d{4}-\d{2}-\d{2})", url)
    return m.group(1) if m else "unknown"


# ── Main ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Scrape EU Parliament verbatim plenary debate records."
    )
    p.add_argument("--limit", type=int, default=400,
                   help="Maximum documents to save (default: 400)")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    actor = "EU Commission"
    out_dir = DATA_RAW / ACTORS[actor]["raw_subdir"] / "policy"
    out_dir.mkdir(parents=True, exist_ok=True)
    seen = load_seen_urls(out_dir)

    session = make_session()

    # Generate all candidate CRE document URLs from known plenary dates
    all_urls = [make_cre_url(d) for d in EP_PLENARY_DATES]
    unseen   = [u for u in all_urls if u not in seen]
    print(f"  {len(EP_PLENARY_DATES)} plenary dates → {len(unseen)} URLs not yet saved (limit: {args.limit})")

    saved = 0
    skipped_no_ai = 0
    skipped_short = 0
    not_found     = 0

    for url in unseen:
        if saved >= args.limit:
            break

        time.sleep(DELAY)
        soup = fetch(session, url)
        if soup is None:
            not_found += 1
            continue

        text = extract_text(soup)
        if len(text.split()) < MIN_WORDS:
            skipped_short += 1
            continue

        if not AI_KEYWORDS.search(text):
            skipped_no_ai += 1
            continue

        date = extract_date(soup)
        if date == "unknown":
            date = date_from_url(url)

        doc = {
            "url":      url,
            "date":     date,
            "text":     text,
            "actor":    actor,
            "context":  "policy",
            "platform": "regulatory_doc",
        }
        save_doc(doc, out_dir)
        seen.add(url)
        saved += 1
        print(f"    saved  {url.split('/')[-1][:55]}  ({len(text.split()):,} words,  {date})")

    print(
        f"\nSaved: {saved}"
        f"  |  Skipped (no AI keywords): {skipped_no_ai}"
        f"  |  Skipped (too short): {skipped_short}"
        f"  |  Not found / blocked: {not_found}"
    )


if __name__ == "__main__":
    main()
