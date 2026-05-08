"""
scrape_hearings.py — Fetch Congress.gov AI hearing PDFs (US Congress, policy/testimony).

Fetches 4 confirmed hearing PDFs directly, then searches congress.gov for more.
Uses pdfplumber for text extraction.

Usage:
    python src/scraping/scrape_hearings.py
"""

import hashlib
import io
import json
import re
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import ACTORS, DATA_RAW
from src.scraping.scrape_individuals import DELAY, HEADERS, fetch, make_session

# ── Confirmed accessible hearing PDFs ─────────────────────────────────────────
# Dates estimated from Congress.gov metadata; exact date is in PDF content.

CONFIRMED_PDFS: list[dict] = [
    {
        "url":  "https://www.congress.gov/118/chrg/CHRG-118hhrg55220/CHRG-118hhrg55220.pdf",
        "date": "2023-05-16",
        "note": "118th Congress House hearing on AI",
    },
    {
        "url":  "https://www.congress.gov/118/chrg/CHRG-118shrg59704/CHRG-118shrg59704.pdf",
        "date": "2023-09-12",
        "note": "118th Congress Senate Commerce AI hearing",
    },
    {
        "url":  "https://www.congress.gov/117/chrg/CHRG-117shrg45562/CHRG-117shrg45562.pdf",
        "date": "2021-06-09",
        "note": "117th Congress Senate hearing on AI",
    },
    {
        "url":  "https://www.congress.gov/117/chrg/CHRG-117hhrg44024/CHRG-117hhrg44024.pdf",
        "date": "2021-03-25",
        "note": "117th Congress House hearing on AI",
    },
]

# congress.gov search — returns HTML listing of hearing documents
# Note: most congress.gov search is JS-rendered; these static search URLs sometimes work
CGOV_SEARCH_URLS: list[str] = [
    "https://www.congress.gov/search?q=%7B%22source%22%3A%22hearings%22%2C%22search%22%3A%22artificial+intelligence%22%7D&pageSize=25",
    "https://www.congress.gov/search?q=%7B%22source%22%3A%22hearings%22%2C%22search%22%3A%22AI+safety%22%7D&pageSize=25",
]

MIN_WORDS = 500


# ── Helpers ────────────────────────────────────────────────────────────────────

def url_to_filename(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12] + ".json"


def fetch_pdf_text(session, url: str) -> Optional[str]:
    """Download and extract text from a PDF URL using pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        print("ERROR: pdfplumber not installed. Run: pip install pdfplumber")
        sys.exit(1)

    try:
        resp = session.get(url, timeout=60)
        resp.raise_for_status()
        with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
        text = re.sub(r"\s+", " ", "\n".join(pages)).strip()
        return text if len(text.split()) >= MIN_WORDS else None
    except Exception as exc:
        print(f"    ! PDF failed: {url.split('/')[-1]}  ({exc})")
        return None


def collect_extra_pdf_urls(session) -> list[dict]:
    """Try congress.gov search pages to discover additional hearing PDF links."""
    found: list[dict] = []
    pdf_pattern = re.compile(
        r"https://www\.congress\.gov/\d+/chrg/CHRG-\d+[a-z]+\d+/CHRG-\d+[a-z]+\d+\.pdf",
        re.I,
    )
    for search_url in CGOV_SEARCH_URLS:
        soup = fetch(session, search_url)
        if soup is None:
            continue
        for a in soup.find_all("a", href=True):
            href = str(a["href"])
            if not href.startswith("http"):
                href = "https://www.congress.gov" + href
            if pdf_pattern.match(href):
                found.append({"url": href, "date": "unknown"})
        time.sleep(DELAY)
    return found


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    actor = "US Congress"
    out_dir = DATA_RAW / ACTORS[actor]["raw_subdir"] / "policy"
    out_dir.mkdir(parents=True, exist_ok=True)
    existing = {f.name for f in out_dir.glob("*.json")}

    session = make_session()
    total = 0

    all_entries = CONFIRMED_PDFS.copy()

    print("  Searching congress.gov for additional hearing PDFs ...")
    extra = collect_extra_pdf_urls(session)
    new_extra = [e for e in extra if url_to_filename(e["url"]) not in existing]
    if new_extra:
        print(f"  Found {len(new_extra)} additional PDF URLs from search")
        all_entries.extend(new_extra)
    else:
        print("  No additional PDFs found via search (JS-rendered or blocked)")

    print(f"\n  Fetching {len(all_entries)} hearing PDFs ...")
    for entry in all_entries:
        url  = entry["url"]
        fname = url_to_filename(url)
        if fname in existing:
            print(f"  skip (exists): {url.split('/')[-1]}")
            continue

        print(f"  Fetching: {url.split('/')[-1]}")
        time.sleep(DELAY)
        text = fetch_pdf_text(session, url)
        if text is None:
            continue

        doc = {
            "url":      url,
            "date":     entry["date"],
            "text":     text,
            "actor":    actor,
            "context":  "policy",
            "platform": "testimony",
        }
        out_path = out_dir / fname
        out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        existing.add(fname)
        total += 1
        print(f"    → saved  ({len(text.split()):,} words)")

    print(f"\nTotal saved: {total}")


if __name__ == "__main__":
    main()
