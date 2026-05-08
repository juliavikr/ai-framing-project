"""
scrape_transcripts.py — Fetch interview transcripts for all 6 individual actors.

Method 1 (web): direct scrape of Lex Fridman, Dwarkesh Patel, and Acquired
                transcript pages using requests + BeautifulSoup.
Method 2 (youtube): YouTube Transcript API fallback for additional interviews.

Usage:
    python src/scraping/scrape_transcripts.py --method all
    python src/scraping/scrape_transcripts.py --method web
    python src/scraping/scrape_transcripts.py --method youtube
    python src/scraping/scrape_transcripts.py --actor "Dario Amodei"
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
    DELAY,
    extract_date,
    extract_text,
    fetch,
    load_seen_urls,
    make_session,
    save_doc,
    url_to_filename,
)

MIN_WORD_COUNT_YT = 2000  # skip YouTube transcripts shorter than this

# ── Web transcript registry ────────────────────────────────────────────────────
# Each entry: url, actor, context, platform, date_fallback (YYYY-MM-DD).
# date_fallback is used when the page carries no parseable date tag.

WEB_REGISTRY: list[dict] = [

    # ── Lex Fridman ────────────────────────────────────────────────────────────
    {
        "url": "https://lexfridman.com/sam-altman-2-transcript",
        "actor": "Sam Altman",
        "context": "public",
        "platform": "interview",
        "date_fallback": "2024-03-22",
    },
    {
        "url": "https://lexfridman.com/dario-amodei-transcript",
        "actor": "Dario Amodei",
        "context": "public",
        "platform": "interview",
        "date_fallback": "2024-11-11",
    },
    {
        "url": "https://lexfridman.com/jensen-huang-transcript",
        "actor": "Jensen Huang",
        "context": "public",
        "platform": "interview",
        "date_fallback": "2024-01-29",
    },
    {
        "url": "https://lexfridman.com/mark-zuckerberg-3-transcript",
        "actor": "Mark Zuckerberg",
        "context": "public",
        "platform": "interview",
        "date_fallback": "2023-09-28",
    },
    {
        "url": "https://lexfridman.com/demis-hassabis-2-transcript",
        "actor": "Demis Hassabis",
        "context": "public",
        "platform": "interview",
        "date_fallback": "2025-01-27",
    },
    # ── Dwarkesh Patel ─────────────────────────────────────────────────────────
    {
        "url": "https://www.dwarkeshpatel.com/p/dario-amodei",
        "actor": "Dario Amodei",
        "context": "public",
        "platform": "interview",
        "date_fallback": "2024-04-08",
    },
    {
        "url": "https://www.dwarkeshpatel.com/p/mark-zuckerberg",
        "actor": "Mark Zuckerberg",
        "context": "public",
        "platform": "interview",
        "date_fallback": "2024-04-04",
    },
    {
        "url": "https://www.dwarkeshpatel.com/p/satya-nadella",
        "actor": "Satya Nadella",
        "context": "public",
        "platform": "interview",
        "date_fallback": "2025-02-19",
    },
    {
        "url": "https://www.dwarkeshpatel.com/p/jensen-huang",
        "actor": "Jensen Huang",
        "context": "public",
        "platform": "interview",
        "date_fallback": "2024-06-14",
    },


    # ── Nobel Prize lecture ────────────────────────────────────────────────────
    {
        "url": "https://www.nobelprize.org/uploads/2024/12/hassabis-lecture.pdf",
        "actor": "Demis Hassabis",
        "context": "public",
        "platform": "speech",
        "date_fallback": "2024-12-08",
        "pdf": True,
    },

    # ── Dwarkesh Patel additional episodes ────────────────────────────────────
    {
        "url": "https://www.dwarkeshpatel.com/p/demis-hassabis",
        "actor": "Demis Hassabis",
        "context": "public",
        "platform": "interview",
        "date_fallback": "2024-09-01",
    },
    {
        "url": "https://www.dwarkeshpatel.com/p/mark-zuckerberg-2",
        "actor": "Mark Zuckerberg",
        "context": "public",
        "platform": "interview",
        "date_fallback": "2025-04-01",
    },
]

# ── YouTube video registry ─────────────────────────────────────────────────────
# Fields: video_id, actor, context, platform, date (YYYY-MM-DD).

VIDEO_REGISTRY: list[dict] = [

    # Sam Altman
    {"video_id": "qCVAzmUOMCQ", "actor": "Sam Altman",      "context": "public",     "platform": "interview", "date": "2023-05-23"},  # Bloomberg
    {"video_id": "L_Guz73e6fw", "actor": "Sam Altman",      "context": "public",     "platform": "interview", "date": "2024-01-18"},  # Davos WEF
    {"video_id": "xXCBz_8aPcg", "actor": "Sam Altman",      "context": "public",     "platform": "interview", "date": "2023-11-29"},  # DealBook

    # Dario Amodei
    {"video_id": "vTvTaRMPqzs", "actor": "Dario Amodei",    "context": "public",     "platform": "interview", "date": "2024-11-11"},  # Lex Fridman #452
    {"video_id": "xaZhCMEOFoE", "actor": "Dario Amodei",    "context": "policy",     "platform": "speech",    "date": "2024-05-22"},  # Senate Commerce

    # Jensen Huang
    {"video_id": "ObA8jh0HpMg", "actor": "Jensen Huang",    "context": "public",     "platform": "speech",    "date": "2024-01-29"},  # WEF Davos
    {"video_id": "cEg8cOx7UZk", "actor": "Jensen Huang",    "context": "public",     "platform": "interview", "date": "2023-09-13"},  # Goldman Sachs
    {"video_id": "toTFpCdcZpM", "actor": "Jensen Huang",    "context": "commercial", "platform": "speech",    "date": "2024-06-02"},  # Computex keynote

    # Mark Zuckerberg
    {"video_id": "MJMnBEYZB1E", "actor": "Mark Zuckerberg", "context": "public",     "platform": "interview", "date": "2024-04-04"},  # Stratechery
    {"video_id": "lbOPAWbJbcE", "actor": "Mark Zuckerberg", "context": "policy",     "platform": "testimony", "date": "2024-01-31"},  # Senate hearing

    # Demis Hassabis
    {"video_id": "ybmXmNFuuGM", "actor": "Demis Hassabis",  "context": "public",     "platform": "interview", "date": "2024-01-16"},  # WEF Davos
    {"video_id": "CJFHs7s2wuY", "actor": "Demis Hassabis",  "context": "public",     "platform": "speech",    "date": "2024-12-08"},  # Nobel lecture

    # Satya Nadella
    {"video_id": "mjjALDnLQbw", "actor": "Satya Nadella",   "context": "public",     "platform": "interview", "date": "2024-01-16"},  # WEF Davos
    {"video_id": "GHDkWsL3KdU", "actor": "Satya Nadella",   "context": "public",     "platform": "interview", "date": "2023-11-29"},  # DealBook
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _actor_dir(actor: str) -> Path:
    """Return (and create) the data/raw output dir for an individual actor."""
    out = DATA_RAW / ACTORS[actor]["raw_subdir"]
    out.mkdir(parents=True, exist_ok=True)
    return out


def _display_url(url: str) -> str:
    """Strip scheme + www for compact table output (max 58 chars)."""
    short = re.sub(r"^https?://(www\.)?", "", url)
    return short[:58] + "…" if len(short) > 58 else short


def _display_source(entry: dict) -> str:
    """Human-readable source label from a registry entry."""
    if entry.get("video_id"):
        return f"yt:{entry['video_id']}"
    return _display_url(entry["url"])


# ── PDF fetch ─────────────────────────────────────────────────────────────────

def fetch_pdf_text(session, url: str) -> Optional[str]:
    """Download a PDF and extract full text with pdfplumber."""
    try:
        import io
        import pdfplumber
    except ImportError:
        print("ERROR: pdfplumber not installed. Run: pip install pdfplumber")
        sys.exit(1)

    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        text = re.sub(r"\s+", " ", "\n".join(pages)).strip()
        return text if text else None
    except Exception as exc:
        print(f"    ! PDF fetch failed: {url}  ({exc})")
        return None


# ── YouTube transcript fetch ───────────────────────────────────────────────────

def fetch_youtube_transcript(video_id: str) -> Optional[str]:
    """
    Fetch English transcript from YouTube, preferring manual over auto-generated.
    Returns joined plain text (no timestamps), or None if unavailable.
    """
    try:
        from youtube_transcript_api import (
            NoTranscriptFound,
            TranscriptsDisabled,
            YouTubeTranscriptApi,
        )
    except ImportError:
        print("ERROR: youtube-transcript-api not installed. Run: pip install youtube-transcript-api")
        sys.exit(1)

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            t = transcript_list.find_manually_created_transcript(["en"])
        except NoTranscriptFound:
            t = transcript_list.find_generated_transcript(["en"])
        chunks = t.fetch()
        parts = []
        for chunk in chunks:
            # Support both object-style (>=0.6.3) and dict-style chunk formats
            parts.append(chunk.text if hasattr(chunk, "text") else chunk.get("text", ""))
        return re.sub(r"\s+", " ", " ".join(parts)).strip()
    except TranscriptsDisabled:
        print(f"    ! transcripts disabled for {video_id}")
        return None
    except NoTranscriptFound:
        print(f"    ! no English transcript for {video_id}")
        return None
    except Exception as exc:
        print(f"    ! YouTube fetch failed for {video_id}: {exc}")
        return None


# ── Method 1: web scraping ─────────────────────────────────────────────────────

def run_web(actor_filter: Optional[str], session) -> list[dict]:
    """
    Scrape all WEB_REGISTRY entries (optionally filtered to one actor).
    Returns a list of result dicts for the final report.
    """
    entries = [e for e in WEB_REGISTRY if actor_filter is None or e["actor"] == actor_filter]
    results: list[dict] = []

    for entry in entries:
        actor = entry["actor"]
        url = entry["url"]
        source_label = _display_url(url)
        out_dir = _actor_dir(actor)
        seen = load_seen_urls(out_dir)

        if url in seen:
            results.append({"actor": actor, "source": source_label, "words": "—", "status": "already exists"})
            continue

        print(f"  WEB  {actor:20s}  {url}")
        time.sleep(DELAY)

        if entry.get("pdf"):
            text = fetch_pdf_text(session, url)
            if text is None:
                results.append({"actor": actor, "source": source_label, "words": "—", "status": "fetch failed"})
                continue
            date = entry["date_fallback"]
        else:
            soup = fetch(session, url)
            if soup is None:
                results.append({"actor": actor, "source": source_label, "words": "—", "status": "fetch failed"})
                continue
            text = extract_text(soup)
            date = extract_date(soup)
            if date == "unknown":
                date = entry["date_fallback"]

        doc = {
            "url": url,
            "date": date,
            "text": text,
            "actor": actor,
            "context": entry["context"],
            "platform": entry["platform"],
        }
        save_doc(doc, out_dir)
        word_count = len(text.split())
        results.append({"actor": actor, "source": source_label, "words": word_count, "status": "saved"})
        print(f"    → {word_count:,} words  |  date {date}")

    return results


# ── Method 2: YouTube Transcript API ──────────────────────────────────────────

def run_youtube(actor_filter: Optional[str]) -> tuple[list[dict], list[str]]:
    """
    Fetch all VIDEO_REGISTRY transcripts (optionally filtered to one actor).
    Returns (result dicts for report, list of failed video_ids).
    """
    entries = [e for e in VIDEO_REGISTRY if actor_filter is None or e["actor"] == actor_filter]
    results: list[dict] = []
    failed_ids: list[str] = []

    for entry in entries:
        actor = entry["actor"]
        vid = entry["video_id"]
        source_label = f"yt:{vid}"
        out_dir = _actor_dir(actor)
        out_path = out_dir / f"yt_{vid}.json"

        if out_path.exists():
            results.append({"actor": actor, "source": source_label, "words": "—", "status": "already exists"})
            continue

        print(f"  YT   {actor:20s}  {vid}  ({entry['context']} / {entry['platform']})")
        text = fetch_youtube_transcript(vid)

        if text is None:
            results.append({"actor": actor, "source": source_label, "words": "—", "status": "no transcript"})
            failed_ids.append(vid)
            continue

        word_count = len(text.split())
        if word_count < MIN_WORD_COUNT_YT:
            results.append({"actor": actor, "source": source_label, "words": word_count,
                            "status": f"too short (<{MIN_WORD_COUNT_YT} words)"})
            continue

        doc = {
            "url": f"https://www.youtube.com/watch?v={vid}",
            "date": entry["date"],
            "text": text,
            "actor": actor,
            "context": entry["context"],
            "platform": entry["platform"],
        }
        out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        results.append({"actor": actor, "source": source_label, "words": word_count, "status": "saved"})
        print(f"    → {word_count:,} words  |  date {entry['date']}")
        time.sleep(DELAY)

    return results, failed_ids


# ── Report ─────────────────────────────────────────────────────────────────────

def print_report(results: list[dict], failed_ids: list[str]) -> None:
    """Print actor × source × word count × status summary table."""
    C = (20, 60, 8, 24)
    sep = "─" * (sum(C) + 6)
    header = f"{'Actor':<{C[0]}}  {'Source':<{C[1]}}  {'Words':>{C[2]}}  {'Status':<{C[3]}}"

    print(f"\n{sep}")
    print(header)
    print(sep)

    saved = 0
    for r in results:
        words_str = f"{r['words']:,}" if isinstance(r["words"], int) else str(r["words"])
        print(f"{r['actor']:<{C[0]}}  {r['source']:<{C[1]}}  {words_str:>{C[2]}}  {r['status']:<{C[3]}}")
        if r["status"] == "saved":
            saved += 1

    print(sep)
    print(f"Total new documents added : {saved}")
    if failed_ids:
        print(f"Failed video IDs (no transcript): {', '.join(failed_ids)}")
    print()


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Fetch interview transcripts for individual actors via web scrape or YouTube API."
    )
    p.add_argument(
        "--method",
        choices=["all", "web", "youtube"],
        default="all",
        help="Which method(s) to run (default: all)",
    )
    p.add_argument(
        "--actor",
        default=None,
        help='Limit to one actor, e.g. "Dario Amodei"',
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if args.actor is not None:
        if args.actor not in ACTORS:
            valid = [k for k, v in ACTORS.items() if v["type"] == "individual"]
            print(f"Error: '{args.actor}' not found. Valid individual actors:")
            for name in valid:
                print(f"  {name}")
            sys.exit(1)
        if ACTORS[args.actor]["type"] != "individual":
            print(f"Error: '{args.actor}' is type '{ACTORS[args.actor]['type']}', not 'individual'.")
            sys.exit(1)

    session = make_session()
    all_results: list[dict] = []
    all_failed: list[str] = []

    if args.method in ("all", "web"):
        print(f"\n{'='*60}")
        print("METHOD 1 — Web transcript scraping")
        print(f"{'='*60}\n")
        web_results = run_web(args.actor, session)
        all_results.extend(web_results)

    if args.method in ("all", "youtube"):
        print(f"\n{'='*60}")
        print("METHOD 2 — YouTube Transcript API")
        print(f"{'='*60}\n")
        yt_results, failed = run_youtube(args.actor)
        all_results.extend(yt_results)
        all_failed.extend(failed)

    print_report(all_results, all_failed)


if __name__ == "__main__":
    main()
