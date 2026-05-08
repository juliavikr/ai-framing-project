"""
ingest_pdf.py — Ingest manually collected PDF documents into the raw corpus.

Reads every PDF listed in MANIFEST, extracts text with pdfplumber, and saves
a JSON doc to data/raw/{actor_subdir}/{context}/ using the standard schema.

Usage:
    python src/scraping/ingest_pdf.py
    python src/scraping/ingest_pdf.py --pdf-dir data/raw/_manual_pdfs
    python src/scraping/ingest_pdf.py --dry-run
"""

import argparse
import hashlib
import io
import json
import re
import sys
from pathlib import Path

import pdfplumber

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import ACTORS, DATA_RAW

MIN_WORDS = 200  # skip cover-page-only extractions

# ── Manifest ───────────────────────────────────────────────────────────────────
# Each entry: filename, actor (exact ACTORS key), context, platform, date.

MANIFEST: list[dict] = [
    # ── Individual testimony / policy ─────────────────────────────────────────
    {
        "filename": "sam_altman_policy_2023-05-16_senate_judiciary.pdf",
        "actor":    "Sam Altman",
        "context":  "policy",
        "platform": "testimony",
        "date":     "2023-05-16",
    },
    {
        "filename": "dario_amodei_policy_2023-07-25_senate_judiciary.pdf",
        "actor":    "Dario Amodei",
        "context":  "policy",
        "platform": "testimony",
        "date":     "2023-07-25",
    },
    {
        "filename": "dario_amodei_policy_2023-09-12_senate_judiciary.pdf",
        "actor":    "Dario Amodei",
        "context":  "policy",
        "platform": "testimony",
        "date":     "2023-09-12",
    },
    {
        "filename": "mark_zuckerberg_policy_2024-01-31_senate_judiciary.pdf",
        "actor":    "Mark Zuckerberg",
        "context":  "policy",
        "platform": "testimony",
        "date":     "2024-01-31",
    },
    {
        "filename": "demis_hassabis_policy_2023-10-24_uk_science_committee.pdf",
        "actor":    "Demis Hassabis",
        "context":  "policy",
        "platform": "testimony",
        "date":     "2023-10-24",
    },
    # ── Company policy submissions ─────────────────────────────────────────────
    {
        "filename": "anthropic_policy_2023-06-12_ntia_submission.pdf",
        "actor":    "Anthropic",
        "context":  "policy",
        "platform": "regulatory_doc",
        "date":     "2023-06-12",
    },
    {
        "filename": "openai_policy_2023-06-12_ntia_submission.pdf",
        "actor":    "OpenAI",
        "context":  "policy",
        "platform": "regulatory_doc",
        "date":     "2023-06-12",
    },
    {
        "filename": "microsoft_policy_2025-05-08_senate_commerce.pdf",
        "actor":    "Microsoft",
        "context":  "policy",
        "platform": "testimony",
        "date":     "2025-05-08",
    },
    # ── EU Commission regulatory docs ─────────────────────────────────────────
    {
        "filename": "eu_commission_policy_2019-04-08_ethics_guidelines_trustworthy_ai.pdf",
        "actor":    "EU Commission",
        "context":  "policy",
        "platform": "regulatory_doc",
        "date":     "2019-04-08",
    },
    {
        "filename": "eu_commission_policy_2020-02-19_white_paper_ai.pdf",
        "actor":    "EU Commission",
        "context":  "policy",
        "platform": "regulatory_doc",
        "date":     "2020-02-19",
    },
    {
        "filename": "eu_commission_policy_2024-06-13_ai_act_final.pdf",
        "actor":    "EU Commission",
        "context":  "policy",
        "platform": "regulatory_doc",
        "date":     "2024-06-13",
    },
    # ── White House OSTP policy docs ──────────────────────────────────────────
    {
        "filename": "white_house_ostp_policy_2022-10-04_ai_bill_of_rights.pdf",
        "actor":    "White House OSTP",
        "context":  "policy",
        "platform": "regulatory_doc",
        "date":     "2022-10-04",
    },
    {
        "filename": "white_house_ostp_policy_2023-10-30_executive_order_safe_ai.pdf",
        "actor":    "White House OSTP",
        "context":  "policy",
        "platform": "regulatory_doc",
        "date":     "2023-10-30",
    },
    {
        "filename": "white_house_ostp_policy_2023-05-04_national_ai_initiative.pdf",
        "actor":    "White House OSTP",
        "context":  "policy",
        "platform": "regulatory_doc",
        "date":     "2023-05-04",
    },
    # ── UK DSIT regulatory docs ───────────────────────────────────────────────
    {
        "filename": "uk_dsit_policy_2023-11-01_bletchley_declaration.pdf",
        "actor":    "UK DSIT",
        "context":  "policy",
        "platform": "regulatory_doc",
        "date":     "2023-11-01",
    },
    {
        "filename": "uk_dsit_policy_2023-03-29_ai_regulation_white_paper.pdf",
        "actor":    "UK DSIT",
        "context":  "policy",
        "platform": "regulatory_doc",
        "date":     "2023-03-29",
    },
    # ── US Congress ───────────────────────────────────────────────────────────
    {
        "filename": "us_congress_policy_2023-09-13_senate_ai_insight_forum.pdf",
        "actor":    "US Congress",
        "context":  "policy",
        "platform": "testimony",
        "date":     "2023-09-13",
    },
    # ── Individual public essays / speeches ───────────────────────────────────
    {
        "filename": "dario_amodei_public_2024-10-01_machines_of_loving_grace.pdf",
        "actor":    "Dario Amodei",
        "context":  "public",
        "platform": "speech",
        "date":     "2024-10-01",
    },
    {
        "filename": "sam_altman_public_2024-09-23_intelligence_age.pdf",
        "actor":    "Sam Altman",
        "context":  "public",
        "platform": "speech",
        "date":     "2024-09-23",
    },
    {
        "filename": "sam_altman_public_2021-03-16_moores_law_for_everything.pdf",
        "actor":    "Sam Altman",
        "context":  "public",
        "platform": "speech",
        "date":     "2021-03-16",
    },
    {
        "filename": "jensen_huang_public_2025-03-18_gtc_keynote.pdf",
        "actor":    "Jensen Huang",
        "context":  "public",
        "platform": "speech",
        "date":     "2025-03-18",
    },
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def url_from_filename(filename: str) -> str:
    """Synthetic stable URL used as doc identifier."""
    return f"manual_pdf://{filename}"


def filename_to_json_name(filename: str) -> str:
    stem = filename.replace(".pdf", "")
    h = hashlib.md5(stem.encode()).hexdigest()[:12]
    return f"{h}.json"


def extract_pdf_text(pdf_path: Path):
    """Extract and normalise text from a PDF file."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        raw = "\n".join(pages)
        return re.sub(r"\s+", " ", raw).strip() or None
    except Exception as exc:
        print(f"    ! pdfplumber error: {exc}")
        return None


# ── Main ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ingest manual PDFs into raw corpus.")
    p.add_argument("--pdf-dir", default="data/raw/_manual_pdfs",
                   help="Directory containing PDFs (default: data/raw/_manual_pdfs)")
    p.add_argument("--dry-run", action="store_true",
                   help="Extract and print stats but do not write JSON files")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    pdf_dir = Path(args.pdf_dir)

    if not pdf_dir.exists():
        print(f"Error: PDF directory '{pdf_dir}' not found.")
        sys.exit(1)

    col_w = (44, 20, 10, 8, 7, 20)
    sep = "─" * (sum(col_w) + len(col_w) * 2)
    hdr = (
        f"{'Filename':<{col_w[0]}}  {'Actor':<{col_w[1]}}  "
        f"{'Context':<{col_w[2]}}  {'Words':>{col_w[3]}}  "
        f"{'OK?':<{col_w[4]}}  {'Status':<{col_w[5]}}"
    )
    print(f"\n{sep}\n{hdr}\n{sep}")

    saved = 0
    skipped = 0
    missing = 0

    for entry in MANIFEST:
        fname   = entry["filename"]
        actor   = entry["actor"]
        context = entry["context"]

        pdf_path = pdf_dir / fname

        if not pdf_path.exists():
            print(
                f"{fname:<{col_w[0]}}  {actor:<{col_w[1]}}  "
                f"{context:<{col_w[2]}}  {'—':>{col_w[3]}}  "
                f"{'—':<{col_w[4]}}  FILE NOT FOUND"
            )
            missing += 1
            continue

        text = extract_pdf_text(pdf_path)
        if text is None:
            print(
                f"{fname:<{col_w[0]}}  {actor:<{col_w[1]}}  "
                f"{context:<{col_w[2]}}  {'—':>{col_w[3]}}  "
                f"{'✗':<{col_w[4]}}  extraction failed"
            )
            skipped += 1
            continue

        words = len(text.split())
        if words < MIN_WORDS:
            print(
                f"{fname:<{col_w[0]}}  {actor:<{col_w[1]}}  "
                f"{context:<{col_w[2]}}  {words:>{col_w[3]}}  "
                f"{'✗':<{col_w[4]}}  too short (<{MIN_WORDS} words)"
            )
            skipped += 1
            continue

        actor_cfg = ACTORS[actor]
        out_dir = DATA_RAW / actor_cfg["raw_subdir"] / context
        out_dir.mkdir(parents=True, exist_ok=True)

        url = url_from_filename(fname)
        json_path = out_dir / filename_to_json_name(fname)

        if json_path.exists():
            print(
                f"{fname:<{col_w[0]}}  {actor:<{col_w[1]}}  "
                f"{context:<{col_w[2]}}  {words:>{col_w[3]}}  "
                f"{'─':<{col_w[4]}}  already exists"
            )
            continue

        doc = {
            "url":      url,
            "date":     entry["date"],
            "text":     text,
            "actor":    actor,
            "context":  context,
            "platform": entry["platform"],
        }

        if not args.dry_run:
            json_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

        tag = "(dry-run)" if args.dry_run else "saved"
        print(
            f"{fname:<{col_w[0]}}  {actor:<{col_w[1]}}  "
            f"{context:<{col_w[2]}}  {words:>{col_w[3]}}  "
            f"{'✓':<{col_w[4]}}  {tag}"
        )
        saved += 1

    print(f"\n{sep}")
    print(f"Saved: {saved}  |  Skipped: {skipped}  |  Missing: {missing}")
    if args.dry_run:
        print("(dry-run — no files written)")
    print()


if __name__ == "__main__":
    main()
