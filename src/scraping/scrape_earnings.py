"""
scrape_earnings.py — Scrape Motley Fool earnings call transcripts.

Companies: Nvidia (NVDA), Meta (META), Microsoft (MSFT), Alphabet/Google (GOOGL)
Date range: Q1 2022 – Q4 2024 (~12 quarters × 4 companies = ~48 docs)
Saves to: data/raw/companies/{subdir}/commercial/

Usage:
    python src/scraping/scrape_earnings.py
    python src/scraping/scrape_earnings.py --company nvidia
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import ACTORS, DATA_RAW
from src.scraping.scrape_individuals import (
    DELAY, extract_text, fetch, load_seen_urls, make_session, save_doc,
)

FOOL_BASE = "https://www.fool.com"
FOOL_CATEGORY = "https://www.fool.com/earnings/call-transcripts/"
FOOL_SEARCH = "https://www.fool.com/search/?q={query}+earnings+call+transcript&filter=article"

MIN_WORDS = 500  # full earnings transcripts are 5k–20k words; < 500 = paywalled stub

COMPANY_REGISTRY: dict[str, dict] = {
    "nvidia": {
        "actor": "Nvidia",
        "ticker": "nvda",
        "keywords": ["nvidia-nvda", "nvidia", "nvda"],
    },
    "meta": {
        "actor": "Meta AI",
        "ticker": "meta",
        "keywords": ["meta-platforms-meta", "meta-platforms", "facebook"],
    },
    "microsoft": {
        "actor": "Microsoft",
        "ticker": "msft",
        "keywords": ["microsoft-msft", "microsoft", "msft"],
    },
    "alphabet": {
        "actor": "Google DeepMind",
        "ticker": "googl",
        "keywords": ["alphabet-googl", "alphabet-goog", "alphabet", "googl"],
    },
}

# Date range filter: keep transcripts from 2022-01-01 to 2025-01-01
DATE_FROM = "2022"
DATE_TO   = "2025"


# ── URL helpers ────────────────────────────────────────────────────────────────

def _is_transcript_url(href: str) -> bool:
    return "/earnings/call-transcripts/" in href and href.count("/") >= 7

def _in_date_range(href: str) -> bool:
    m = re.search(r"/(\d{4})/", href)
    if not m:
        return True  # unknown date, include and filter by content later
    return DATE_FROM <= m.group(1) < DATE_TO

def _date_from_url(url: str) -> str:
    m = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", url)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else "unknown"

def _normalise(href: str) -> str:
    href = href.split("?")[0].split("#")[0]
    if href.startswith("/"):
        return FOOL_BASE + href
    return href


# ── URL collection ─────────────────────────────────────────────────────────────

def collect_urls(session, keywords: list[str]) -> set[str]:
    """
    Scrape Motley Fool earnings category pages (up to 30 pages) to find
    transcript URLs matching the company keywords and date range.
    """
    found: set[str] = set()

    for page in range(1, 31):
        page_url = FOOL_CATEGORY if page == 1 else f"{FOOL_CATEGORY}?page={page}"
        soup = fetch(session, page_url)
        if soup is None:
            break

        prev = len(found)
        for a in soup.find_all("a", href=True):
            href = str(a["href"])
            if not _is_transcript_url(href):
                continue
            if not _in_date_range(href):
                continue
            href_lower = href.lower()
            if any(kw in href_lower for kw in keywords):
                found.add(_normalise(href))

        # Stop paging when we're getting nothing new or hit only old dates
        if len(found) == prev and page > 3:
            break
        time.sleep(DELAY)

    # Also try the Fool's search page for each keyword
    for kw in keywords[:1]:  # just the primary keyword to avoid too many requests
        search_url = FOOL_SEARCH.format(query=kw.replace("-", "+"))
        soup = fetch(session, search_url)
        if soup:
            for a in soup.find_all("a", href=True):
                href = str(a["href"])
                if _is_transcript_url(href) and _in_date_range(href):
                    href_lower = href.lower()
                    if any(k in href_lower for k in keywords):
                        found.add(_normalise(href))
        time.sleep(DELAY)

    return found


# ── Per-company scrape ─────────────────────────────────────────────────────────

def scrape_company(session, company_key: str) -> int:
    cfg = COMPANY_REGISTRY[company_key]
    actor = cfg["actor"]
    actor_subdir = ACTORS[actor]["raw_subdir"]
    out_dir = DATA_RAW / actor_subdir / "commercial"
    out_dir.mkdir(parents=True, exist_ok=True)
    seen = load_seen_urls(out_dir)

    print(f"\n  [{actor}] collecting candidate URLs ...")
    urls = collect_urls(session, cfg["keywords"])
    print(f"  [{actor}] {len(urls)} candidates found")

    saved = 0
    for url in sorted(urls):
        if url in seen:
            continue
        time.sleep(DELAY)
        soup = fetch(session, url)
        if soup is None:
            continue

        text = extract_text(soup)
        words = len(text.split())
        if words < MIN_WORDS:
            print(f"    skip (paywall stub, {words} words): {url.split('/')[-2][:50]}")
            continue

        date = _date_from_url(url)
        doc = {
            "url":      url,
            "date":     date,
            "text":     text,
            "actor":    actor,
            "context":  "commercial",
            "platform": "earnings_call",
        }
        save_doc(doc, out_dir)
        seen.add(url)
        saved += 1
        print(f"    saved  {url.split('/')[-2][:55]}  ({words:,} words,  {date})")

    return saved


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Scrape Motley Fool earnings call transcripts for Nvidia, Meta, Microsoft, Alphabet."
    )
    p.add_argument("--company", choices=list(COMPANY_REGISTRY.keys()), default=None,
                   help="Scrape one company only (default: all four)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    session = make_session()
    targets = [args.company] if args.company else list(COMPANY_REGISTRY.keys())
    total = 0
    for key in targets:
        n = scrape_company(session, key)
        total += n
        print(f"  → {key}: {n} new docs saved")
    print(f"\nTotal saved this run: {total}")


if __name__ == "__main__":
    main()
