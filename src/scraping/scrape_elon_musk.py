"""
scrape_elon_musk.py — Multi-source scraper for Elon Musk documents.

Sources:
  1. rev.com  (PUBLIC)     — transcript pages, AI-filtered (3+ mentions)
  2. EDGAR Tesla 8-K       (COMMERCIAL) — quarterly earnings press releases
  3. x.ai/news             (COMMERCIAL) — attempted; logs 403 gracefully
  4. congress.gov          (POLICY)     — attempted; logs 403 gracefully

Usage:
    python src/scraping/scrape_elon_musk.py [--sources rev edgar xai congress]
"""

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import ACTORS, DATA_RAW

# ── Constants ──────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
DELAY = 1

ACTOR      = "Elon Musk"
TESLA_CIK  = "0001318605"

# ── Helpers ────────────────────────────────────────────────────────────────────

def url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]

def load_seen(output_dir: Path) -> set[str]:
    seen: set[str] = set()
    for f in output_dir.glob("*.json"):
        try:
            doc = json.loads(f.read_text())
            if "url" in doc:
                seen.add(doc["url"])
        except (json.JSONDecodeError, OSError):
            pass
    return seen

def save(doc: dict, output_dir: Path) -> None:
    path = output_dir / (url_hash(doc["url"]) + ".json")
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2))

def fetch(session: requests.Session, url: str) -> Optional[BeautifulSoup]:
    try:
        r = session.get(url, timeout=15)
        if r.status_code == 404:
            return None
        if r.status_code in (403, 429, 503):
            print(f"    ! {r.status_code} — {url}")
            return None
        r.raise_for_status()
        return BeautifulSoup(r.text, "lxml")
    except requests.RequestException as e:
        print(f"    ! fetch error: {url} — {e}")
        return None

def extract_text(soup: BeautifulSoup) -> str:
    for tag in soup(["nav", "header", "footer", "script", "style",
                     "aside", "noscript", "iframe", "form"]):
        tag.decompose()
    main = (soup.find("article")
            or soup.find(attrs={"role": "main"})
            or soup.find("main")
            or soup.find("div", class_=re.compile(r"\b(post|content|entry|body|text)\b", re.I))
            or soup.find("body"))
    raw = main.get_text(" ", strip=True) if main else soup.get_text(" ", strip=True)
    return re.sub(r" {2,}", " ", raw).strip()

MONTH_RE = re.compile(
    r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
    r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\s+(\d{1,2}),?\s+(\d{4})"
)

def parse_date_text(text: str, fallback: str = "unknown") -> str:
    m = MONTH_RE.search(text)
    if m:
        try:
            return datetime.strptime(
                f"{m.group(1)[:3]} {m.group(2)} {m.group(3)}", "%b %d %Y"
            ).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return fallback[:10] if fallback and fallback != "unknown" else "unknown"

def ai_count(text: str) -> int:
    """Count occurrences of 'AI' (word-boundary) or 'artificial intelligence'."""
    return len(re.findall(r"\bAI\b|artificial intelligence", text, re.I))


# ── Source 1: rev.com (PUBLIC) ─────────────────────────────────────────────────

# Known Elon Musk transcript URLs discovered from rev.com/sitemap.xml
REV_MUSK_URLS = [
    "https://www.rev.com/transcripts/ai-safety-panel-with-elon-musk-max-tegmark-greg-brockman-and-benjamin-netanyahu-transcript",
    "https://www.rev.com/transcripts/bill-gates-talks-divorce-jeffrey-epstein-elon-musk-5-03-22-transcript",
    "https://www.rev.com/transcripts/dealbook-summit-2023-elon-musk-interview-transcript",
    "https://www.rev.com/transcripts/elon-musk-and-benjamin-netanyahu-discuss-ai-anti-semitism-and-charging-fees-for-x-transcript",
    "https://www.rev.com/transcripts/elon-musk-and-donald-trump-interview",
    "https://www.rev.com/transcripts/elon-musk-fox-interview",
    "https://www.rev.com/transcripts/elon-musk-interview-with-don-lemon",
    "https://www.rev.com/transcripts/elon-musk-interview-with-the-bbc-4-11-23-transcript",
    "https://www.rev.com/transcripts/elon-musk-launches-new-a-i-chatbot-grok-transcript",
    "https://www.rev.com/transcripts/elon-musk-speaks-at-post-inauguration-celebration",
    "https://www.rev.com/transcripts/far-right-nationalist-giorgia-meloni-elected-as-italys-first-female-prime-minister-transcript",
    "https://www.rev.com/transcripts/fc-barcelona-president-joan-laporta-press-conference-on-lionel-messi-leaving-the-club-transcript",
    "https://www.rev.com/transcripts/florida-governor-ron-desantis-announces-2024-presidential-run-on-twitter-spaces-with-elon-musk-transcript",
    "https://www.rev.com/transcripts/joe-rogan-elon-musk-podcast-transcript-may-7-2020",
    "https://www.rev.com/transcripts/musk-and-doge-on-brett-baier",
    "https://www.rev.com/transcripts/musk-speaks-at-town-hall-in-pennsylvania",
    "https://www.rev.com/transcripts/musk-speaks-at-wef",
    "https://www.rev.com/transcripts/musk-town-hall-in-wisconsin",
    "https://www.rev.com/transcripts/tesla-ceo-elon-musk-at-qatar-economic-forum-6-21-22-transcript",
    "https://www.rev.com/transcripts/tesla-cybertruck-event-transcript-elon-musk-unveils-cybertruck",
    "https://www.rev.com/transcripts/trump-and-meloni-at-the-white-house",
    "https://www.rev.com/transcripts/trump-and-musk-on-federal-workforce",
    "https://www.rev.com/transcripts/trump-and-musk-on-hannity",
    "https://www.rev.com/transcripts/trump-and-musk-press-conference",
    "https://www.rev.com/transcripts/trump-and-musk-speak-at-butler-rally",
    "https://www.rev.com/transcripts/trump-pleads-not-guilty-to-34-felony-counts-of-falsification-of-business-records-transcript",
]

AI_MIN_COUNT = 3


def scrape_rev(session: requests.Session, output_dir: Path, seen: set[str]) -> list[dict]:
    """Scrape rev.com Musk transcripts, keeping only those with 3+ AI mentions."""
    print(f"\n[rev.com] {len(REV_MUSK_URLS)} candidate URLs → AI filter ≥{AI_MIN_COUNT}")
    docs: list[dict] = []
    skipped_ai = 0

    for url in REV_MUSK_URLS:
        if url in seen:
            continue
        time.sleep(DELAY)
        soup = fetch(session, url)
        if soup is None:
            continue

        text = extract_text(soup)
        ai_hits = ai_count(text)
        if ai_hits < AI_MIN_COUNT:
            skipped_ai += 1
            slug = url.split("/")[-1][:50]
            print(f"    skip (AI={ai_hits}) {slug}")
            continue

        # Date: rev.com puts it in plain text near top; try a meta tag first
        date = "unknown"
        for prop in ("article:published_time", "datePublished"):
            meta = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
            if meta and meta.get("content"):
                date = str(meta["content"])[:10]
                break
        if date == "unknown":
            date = parse_date_text(soup.get_text(" "))

        doc = {
            "url":      url,
            "date":     date,
            "text":     text,
            "actor":    ACTOR,
            "context":  "public",
            "platform": "interview",
        }
        docs.append(doc)
        seen.add(url)
        print(f"    saved (AI={ai_hits:3d}) {url.split('/')[-1][:60]}")

    print(f"  → rev.com: {len(docs)} saved, {skipped_ai} below AI threshold")
    return docs


# ── Source 2: EDGAR Tesla 8-K EX-99.1 (COMMERCIAL) ────────────────────────────

# Q1-2022 through Q1-2025: accession numbers matched from EDGAR submissions API.
# Each entry: (quarter_label, filing_date, accession_number)
TESLA_QUARTERS: list[tuple[str, str, str]] = [
    ("Q1-2022", "2022-04-20", "0001564590-22-014917"),
    ("Q2-2022", "2022-07-20", "0001564590-22-026048"),
    ("Q3-2022", "2022-10-19", "0001564590-22-034639"),
    ("Q4-2022", "2023-01-25", "0001564590-23-000799"),
    ("Q1-2023", "2023-04-19", "0001564590-23-005959"),
    ("Q2-2023", "2023-07-20", "0000950170-23-033695"),
    ("Q3-2023", "2023-10-18", "0001628280-23-034588"),
    ("Q4-2023", "2024-01-24", "0000950170-24-007073"),
    ("Q1-2024", "2024-04-23", "0000950170-24-046895"),
    ("Q2-2024", "2024-07-23", "0001628280-24-032603"),
    ("Q3-2024", "2024-10-23", "0001628280-24-043432"),
    ("Q4-2024", "2025-01-29", "0001628280-25-002993"),
    ("Q1-2025", "2025-04-22", "0001628280-25-018851"),
]

EDGAR_BASE    = "https://www.sec.gov/Archives/edgar/data/1318605"
EDGAR_HEADERS = {"User-Agent": "academic-research/1.0 contact@example.com"}
AI_COMMERCIAL_RE = re.compile(
    r"\bAI\b|artificial intelligence|Optimus|Full Self.Driving|FSD|Dojo|autonomous|"
    r"neural network|machine learning|robotaxi|humanoid",
    re.I,
)


def _get_ex991_url(acc: str) -> Optional[str]:
    """Find the EX-99.1 document URL from a Tesla 8-K filing index.

    Uses a dedicated session with SEC-compliant User-Agent (browser UA is rejected).
    """
    acc_path = acc.replace("-", "")
    idx_url = f"{EDGAR_BASE}/{acc_path}/{acc}-index.htm"
    time.sleep(0.5)
    try:
        r = requests.get(idx_url, headers=EDGAR_HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"      index {r.status_code}: {idx_url[-60:]}")
            return None
        soup = BeautifulSoup(r.text, "lxml")
        for row in soup.find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cells) >= 2 and cells[1] == "EX-99.1":
                link = row.find("a")
                if link:
                    return "https://www.sec.gov" + link["href"]
    except requests.RequestException as e:
        print(f"      ! index fetch error: {e}")
    return None


def scrape_edgar(session: requests.Session, output_dir: Path, seen: set[str]) -> list[dict]:
    """Scrape Tesla 8-K EX-99.1 exhibits — quarterly AI/FSD/Optimus highlights."""
    print(f"\n[EDGAR] {len(TESLA_QUARTERS)} Tesla quarterly 8-K filings")
    docs: list[dict] = []

    for quarter, date, acc in TESLA_QUARTERS:
        # Synthetic URL used as the dedup key / doc identifier
        doc_url = f"https://www.sec.gov/edgar/tesla-{quarter.lower()}-ex991"
        if doc_url in seen:
            print(f"    skip (dup) {quarter}")
            continue

        ex991_url = _get_ex991_url(acc)
        if ex991_url is None:
            print(f"    ! could not find EX-99.1 for {quarter}")
            continue

        time.sleep(DELAY)
        try:
            r = requests.get(ex991_url, headers=EDGAR_HEADERS, timeout=15)
            if r.status_code != 200:
                print(f"    ! {r.status_code} fetching exhibit: {ex991_url[-55:]}")
                continue
            soup = BeautifulSoup(r.text, "lxml")
        except requests.RequestException as e:
            print(f"    ! exhibit fetch error {quarter}: {e}")
            continue

        # Extract all text, then keep only paragraphs/sentences with AI keywords
        full_text = soup.get_text(" ", strip=True)
        full_text = re.sub(r" {2,}", " ", full_text)

        # Filter to sentences/clauses mentioning AI/FSD/Optimus/autonomous
        sentences = re.split(r"(?<=[.!?])\s+", full_text)
        ai_sentences = [s for s in sentences if AI_COMMERCIAL_RE.search(s)]

        if len(ai_sentences) < 3:
            print(f"    skip (too few AI sentences: {len(ai_sentences)}) {quarter}")
            continue

        ai_text = " ".join(ai_sentences)
        doc = {
            "url":      doc_url,
            "date":     date,
            "text":     ai_text,
            "actor":    ACTOR,
            "context":  "commercial",
            "platform": "press_release",
            "source_exhibit": ex991_url,
            "quarter": quarter,
        }
        docs.append(doc)
        seen.add(doc_url)
        ai_hits = len(AI_COMMERCIAL_RE.findall(ai_text))
        print(f"    saved {quarter}  ({date})  AI-hits={ai_hits}  sentences={len(ai_sentences)}")

    print(f"  → EDGAR: {len(docs)} quarterly docs saved")
    return docs


# ── Source 3: x.ai/news (COMMERCIAL) ──────────────────────────────────────────

XAI_NEWS_PATHS = [
    "https://x.ai/news/grok-4",
    "https://x.ai/news/grok-3",
    "https://x.ai/news/grok-2",
    "https://x.ai/news/grok",
    "https://x.ai/news/colossus",
    "https://x.ai/news/api",
    "https://x.ai/news/aurora",
]


def scrape_xai(session: requests.Session, output_dir: Path, seen: set[str]) -> list[dict]:
    """Attempt x.ai/news pages. Logs 403 gracefully."""
    print(f"\n[x.ai/news] attempting {len(XAI_NEWS_PATHS)} known press release paths")
    docs: list[dict] = []
    blocked = 0

    for url in XAI_NEWS_PATHS:
        if url in seen:
            continue
        time.sleep(DELAY)
        try:
            r = session.get(url, timeout=15)
            if r.status_code == 403:
                blocked += 1
                continue
            if r.status_code != 200:
                print(f"    ! {r.status_code} — {url}")
                continue
            soup = BeautifulSoup(r.text, "lxml")
            text = extract_text(soup)
            if len(text) < 200:
                continue
            doc = {
                "url":      url,
                "date":     parse_date_text(soup.get_text(" ")),
                "text":     text,
                "actor":    ACTOR,
                "context":  "commercial",
                "platform": "press_release",
            }
            docs.append(doc)
            seen.add(url)
            print(f"    saved {url}")
        except requests.RequestException as e:
            print(f"    ! {url} — {e}")

    if blocked:
        print(f"  → x.ai: {blocked} URLs returned 403 (Cloudflare) — skipped")
    print(f"  → x.ai: {len(docs)} docs saved")
    return docs


# ── Source 4: congress.gov (POLICY) ────────────────────────────────────────────

CONGRESS_URLS = [
    "https://www.congress.gov/event/118th-congress/senate-event/LC65609/detail",
    "https://www.judiciary.senate.gov/imo/media/doc/2023-05-16-testimony-altman.pdf",
]


def scrape_congress(session: requests.Session, output_dir: Path, seen: set[str]) -> list[dict]:
    """Attempt congress.gov AI hearing pages. Logs 403 gracefully."""
    print(f"\n[congress.gov] attempting {len(CONGRESS_URLS)} hearing pages")
    docs: list[dict] = []
    blocked = 0

    for url in CONGRESS_URLS:
        if url in seen:
            continue
        time.sleep(DELAY)
        try:
            r = session.get(url, timeout=15)
            if r.status_code == 403:
                blocked += 1
                continue
            if r.status_code != 200:
                print(f"    ! {r.status_code} — {url}")
                continue
            soup = BeautifulSoup(r.text, "lxml")
            text = extract_text(soup)
            if "Musk" not in text or len(text) < 500:
                continue
            doc = {
                "url":      url,
                "date":     parse_date_text(soup.get_text(" ")),
                "text":     text,
                "actor":    ACTOR,
                "context":  "policy",
                "platform": "testimony",
            }
            docs.append(doc)
            seen.add(url)
            print(f"    saved {url}")
        except requests.RequestException as e:
            print(f"    ! {url} — {e}")

    if blocked:
        print(f"  → congress.gov: {blocked} URLs returned 403 — skipped")
        print(f"    NOTE: congress.gov blocks automated scraping. Policy docs need manual download.")
    print(f"  → congress.gov: {len(docs)} docs saved")
    return docs


# ── Main ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Multi-source scraper for Elon Musk documents.")
    p.add_argument(
        "--sources",
        nargs="+",
        choices=["rev", "edgar", "xai", "congress"],
        default=["rev", "edgar", "xai", "congress"],
        help="Which sources to run (default: all)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    actor_cfg = ACTORS[ACTOR]
    output_dir = DATA_RAW / actor_cfg["raw_subdir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    seen = load_seen(output_dir)
    pre_existing = len(seen)

    print(f"\n{'='*60}")
    print(f"Actor:  {ACTOR}  |  Target: {actor_cfg['target']} docs")
    print(f"Output: {output_dir}")
    print(f"Pre-existing: {pre_existing} docs")
    print(f"Sources: {args.sources}")
    print(f"{'='*60}")

    session = requests.Session()
    session.headers.update(HEADERS)

    all_docs: list[dict] = []

    if "rev" in args.sources:
        docs = scrape_rev(session, output_dir, seen)
        for d in docs:
            save(d, output_dir)
        all_docs.extend(docs)

    if "edgar" in args.sources:
        docs = scrape_edgar(session, output_dir, seen)
        for d in docs:
            save(d, output_dir)
        all_docs.extend(docs)

    if "xai" in args.sources:
        docs = scrape_xai(session, output_dir, seen)
        for d in docs:
            save(d, output_dir)
        all_docs.extend(docs)

    if "congress" in args.sources:
        docs = scrape_congress(session, output_dir, seen)
        for d in docs:
            save(d, output_dir)
        all_docs.extend(docs)

    # ── Summary ──────────────────────────────────────────────────────────────
    total = len(list(output_dir.glob("*.json")))
    by_context: dict[str, int] = {}
    for f in output_dir.glob("*.json"):
        try:
            ctx = json.loads(f.read_text()).get("context", "?")
            by_context[ctx] = by_context.get(ctx, 0) + 1
        except (json.JSONDecodeError, OSError):
            pass

    print(f"\n{'─'*60}")
    print(f"Saved this run : {len(all_docs)}")
    print(f"Total on disk  : {total}")
    print(f"By context     : {by_context}")
    targets = actor_cfg["contexts"]
    print(f"Targets        : commercial={targets['commercial']}  "
          f"policy={targets['policy']}  public={targets['public']}")
    print(f"{'─'*60}")


if __name__ == "__main__":
    main()
