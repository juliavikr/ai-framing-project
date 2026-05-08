"""
scrape_ted.py — Scrape TED talk transcripts for AI-relevant speakers.

Fetches confirmed transcript pages at ted.com/talks/{slug}/transcript.
SSL verification is disabled (ted.com fails macOS cert chain verification).

Usage:
    python src/scraping/scrape_ted.py
"""

import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Optional

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import ACTORS, DATA_RAW
from src.scraping.scrape_individuals import DELAY, HEADERS, extract_text, load_seen_urls, save_doc

# ── Confirmed transcript pages ─────────────────────────────────────────────────

CONFIRMED_TALKS: list[dict] = [
    {
        "url":          "https://www.ted.com/talks/demis_hassabis_the_incredible_inventions_of_intuitive_ai/transcript",
        "actor":        "Demis Hassabis",
        "context":      "public",
        "platform":     "speech",
        "date_fallback": "2018-04-10",
    },
    {
        "url":          "https://www.ted.com/talks/sam_altman_on_the_future_of_ai_and_humanity/transcript",
        "actor":        "Sam Altman",
        "context":      "public",
        "platform":     "speech",
        "date_fallback": "2024-11-01",
    },
]

# ── Additional search slugs to try ────────────────────────────────────────────
# TED's search page is partially JS-rendered; we probe known slug patterns.

SEARCH_URLS: list[str] = [
    "https://www.ted.com/search?q=artificial+intelligence+future&language=en",
    "https://www.ted.com/search?q=AI+safety+alignment&language=en",
    "https://www.ted.com/search?q=large+language+models&language=en",
]

# Only keep talks by speakers who map to our actor registry
SPEAKER_ACTOR_MAP: dict[str, str] = {
    "sam altman":     "Sam Altman",
    "demis hassabis": "Demis Hassabis",
    "dario amodei":   "Dario Amodei",
    "jensen huang":   "Jensen Huang",
    "satya nadella":  "Satya Nadella",
    "mark zuckerberg":"Mark Zuckerberg",
}

MIN_WORDS = 300


# ── Fetch helpers ──────────────────────────────────────────────────────────────

def url_to_filename(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12] + ".json"


def fetch_ssl_bypass(url: str) -> Optional[BeautifulSoup]:
    """GET with SSL verification disabled (needed for ted.com on macOS)."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, verify=False)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except requests.RequestException as exc:
        print(f"    ! fetch failed: {url}  ({exc})")
        return None


def extract_ted_transcript(soup: BeautifulSoup) -> str:
    """Extract transcript text; TED wraps it in data-purpose='transcript-body'."""
    body = soup.find(attrs={"data-purpose": "transcript-body"})
    if body:
        return re.sub(r"\s+", " ", body.get_text(" ", strip=True)).strip()
    # Fallback: look for any div with 'transcript' in class name
    div = soup.find("div", class_=re.compile(r"transcript", re.I))
    if div:
        return re.sub(r"\s+", " ", div.get_text(" ", strip=True)).strip()
    return extract_text(soup)


def extract_ted_date(soup: BeautifulSoup, fallback: str) -> str:
    """Pull event date from TED page meta tags."""
    for prop in ("datePublished", "article:published_time"):
        meta = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
        if meta and meta.get("content"):
            return str(meta["content"])[:10]
    t = soup.find("time", attrs={"datetime": True})
    if t:
        return str(t["datetime"])[:10]
    return fallback


# ── Discover additional talk URLs via search ──────────────────────────────────

def discover_talk_urls(existing_urls: set[str]) -> list[dict]:
    """Search TED for additional AI talks and match to registry speakers."""
    found: list[dict] = []
    seen_urls = set(existing_urls)

    for search_url in SEARCH_URLS:
        time.sleep(DELAY)
        soup = fetch_ssl_bypass(search_url)
        if soup is None:
            continue

        for a in soup.find_all("a", href=True):
            href = str(a["href"])
            if "/talks/" not in href or "/transcript" in href:
                continue
            # Infer transcript URL
            slug = href.rstrip("/").split("/talks/")[-1].split("/")[0]
            transcript_url = f"https://www.ted.com/talks/{slug}/transcript"
            if transcript_url in seen_urls:
                continue

            # Try to find speaker name near this link
            speaker_text = ""
            parent = a.find_parent()
            if parent:
                speaker_text = parent.get_text(" ", strip=True).lower()

            for speaker, actor in SPEAKER_ACTOR_MAP.items():
                if speaker in speaker_text:
                    found.append({
                        "url":          transcript_url,
                        "actor":        actor,
                        "context":      "public",
                        "platform":     "speech",
                        "date_fallback": "unknown",
                    })
                    seen_urls.add(transcript_url)
                    break

    return found


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    total = 0

    # Load all confirmed talks first
    all_entries = list(CONFIRMED_TALKS)

    # Discover additional talks via search
    confirmed_urls = {e["url"] for e in all_entries}
    print("  Searching TED for additional AI talks ...")
    extra = discover_talk_urls(confirmed_urls)
    if extra:
        print(f"  Found {len(extra)} additional candidate talks")
        all_entries.extend(extra)
    else:
        print("  No additional talks found via search (JS-rendered)")

    for entry in all_entries:
        actor = entry["actor"]
        url   = entry["url"]
        out_dir = DATA_RAW / ACTORS[actor]["raw_subdir"] / "public"
        out_dir.mkdir(parents=True, exist_ok=True)
        seen = load_seen_urls(out_dir)

        if url in seen:
            print(f"  skip (exists): {url.split('/talks/')[-1][:60]}")
            continue

        print(f"  Fetching: {url.split('/talks/')[-1][:70]}")
        time.sleep(DELAY)
        soup = fetch_ssl_bypass(url)
        if soup is None:
            print(f"    ! fetch failed")
            continue

        text = extract_ted_transcript(soup)
        words = len(text.split())
        if words < MIN_WORDS:
            print(f"    ! too short ({words} words), skipping")
            continue

        date = extract_ted_date(soup, entry.get("date_fallback", "unknown"))

        doc = {
            "url":      url,
            "date":     date,
            "text":     text,
            "actor":    actor,
            "context":  "public",
            "platform": "speech",
        }
        save_doc(doc, out_dir)
        total += 1
        print(f"    → saved  ({words:,} words,  date {date})")

    print(f"\nTotal saved: {total}")


if __name__ == "__main__":
    main()
