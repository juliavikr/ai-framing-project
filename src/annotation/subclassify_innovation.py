"""
subclassify_innovation.py — Sub-classify Innovation/Progress sentences.

Filters labeled_sentences.csv to Innovation_Progress = 1, then calls
Claude Haiku to assign one of 5 sub-categories per sentence.

Sub-categories:
  health_biotech  — medicine, cancer, biology, longevity, drug discovery, healthcare
  climate_energy  — climate, clean energy, sustainability, environment
  scientific      — general scientific discovery, research breakthroughs
  productivity    — work efficiency, task automation, business productivity
  other_progress  — any other progress claim

Outputs:
  data/annotation/innovation_subclassified.csv
  outputs/tables/innovation_subclassification.csv  (actor-level summary)
  Adds innovation_subcategory_dominant column to labeled_documents.csv

Usage:
    python src/annotation/subclassify_innovation.py
    python src/annotation/subclassify_innovation.py --limit 50   # test mode
    python src/annotation/subclassify_innovation.py --resume     # skip already-done sentences
    python src/annotation/subclassify_innovation.py --finalize   # skip API, just build summaries
"""

import argparse
import csv
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import (
    ANTHROPIC_API_KEY,
    DATA_ANNOTATION,
    LLM_MODEL,
    OUTPUTS_TABLES,
)

INPUT_CSV      = DATA_ANNOTATION  / "labeled_sentences.csv"
OUTPUT_CSV     = DATA_ANNOTATION  / "innovation_subclassified.csv"
SUMMARY_CSV    = OUTPUTS_TABLES   / "innovation_subclassification.csv"
DOCUMENTS_CSV  = DATA_ANNOTATION  / "labeled_documents.csv"
FAILED_LOG     = DATA_ANNOTATION  / "subclassify_failed.log"

SUBCATEGORIES = ["health_biotech", "climate_energy", "scientific", "productivity", "other_progress"]

BATCH_SIZE       = 20
MAX_TOKENS       = 1100  # 20 items × ~40 tokens each (UUID tokenizes expensively) = ~785 actual
INTER_CALL_DELAY = 0.3
MAX_RETRIES      = 3
RETRY_DELAY      = 5.0

OUTPUT_COLS = ["sentence_id", "doc_id", "actor", "context", "sentence_text", "innovation_subcategory"]

SYSTEM_PROMPT = """\
Classify each sentence into exactly ONE sub-category of Innovation/Progress framing in AI discourse.

Categories:
- health_biotech: mentions medicine, cancer, biology, longevity, drug discovery, healthcare, disease
- climate_energy: mentions climate, clean energy, sustainability, environment, carbon, renewable
- scientific: mentions scientific discovery, research breakthroughs, knowledge advancement (not specific domain)
- productivity: mentions work efficiency, task automation, business productivity, economic transformation
- other_progress: any other progress claim that does not fit the above categories

Return ONLY compact JSON, no newlines: [{"id": "<id>", "subcategory": "health_biotech"}, ...]"""


def call_haiku(client: anthropic.Anthropic, batch: list) -> str:
    user_msg = json.dumps(batch, ensure_ascii=False)
    resp = client.messages.create(
        model=LLM_MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    return resp.content[0].text.strip()


def parse_response(raw: str, expected_ids: list) -> dict:
    clean = re.sub(r"^```[a-z]*\n?", "", raw.strip(), flags=re.MULTILINE)
    clean = re.sub(r"\n?```$", "", clean.strip())
    data  = json.loads(clean)
    result = {}
    for item in data:
        sid = str(item.get("id", ""))
        sub = item.get("subcategory", "other_progress")
        result[sid] = sub if sub in SUBCATEGORIES else "other_progress"
    for sid in expected_ids:
        if sid not in result:
            result[sid] = "other_progress"
    return result


def label_batch_with_retry(client, batch, batch_num):
    expected_ids = [b["id"] for b in batch]
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw = call_haiku(client, batch)
            return parse_response(raw, expected_ids)
        except Exception as exc:
            last_err = exc
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
    with open(FAILED_LOG, "a") as f:
        ids_str = ", ".join(expected_ids[:3]) + ("…" if len(expected_ids) > 3 else "")
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] batch {batch_num}: "
                f"{type(last_err).__name__}: {last_err} | ids: {ids_str}\n")
    return {sid: "other_progress" for sid in expected_ids}


def load_done_ids() -> set:
    """Return sentence_ids already written to OUTPUT_CSV."""
    if not OUTPUT_CSV.exists():
        return set()
    done = set()
    with open(OUTPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            done.add(row["sentence_id"])
    return done


def append_rows(rows: list, write_header: bool) -> None:
    """Append a list of row dicts to OUTPUT_CSV."""
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLS)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def build_summaries():
    """Read OUTPUT_CSV and produce distribution + actor summary + documents update."""
    out_df = pd.read_csv(OUTPUT_CSV, dtype=str)

    print(f"\n── Sub-category distribution ({len(out_df):,} sentences) ──")
    for cat in SUBCATEGORIES:
        n   = (out_df["innovation_subcategory"] == cat).sum()
        pct = n / len(out_df) * 100
        print(f"  {cat:<20} {n:>5,}  ({pct:.1f}%)")

    print(f"\n── Actor summary (% of each actor's Innovation sentences) ──")
    actor_rows = []
    for actor, grp in out_df.groupby("actor"):
        total = len(grp)
        row = {"actor": actor, "n_innovation": total}
        for cat in SUBCATEGORIES:
            row[cat + "_pct"] = round((grp["innovation_subcategory"] == cat).sum() / total * 100, 1)
        actor_rows.append(row)

    summary = pd.DataFrame(actor_rows).sort_values("health_biotech_pct", ascending=False)
    OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)
    summary.to_csv(SUMMARY_CSV, index=False)

    header = f"{'Actor':<22} {'N':>5}  {'health%':>7} {'climate%':>8} {'sci%':>6} {'prod%':>6} {'other%':>7}"
    print(header)
    print("─" * len(header))
    for _, row in summary.iterrows():
        print(f"  {row['actor']:<20} {row['n_innovation']:>5}  "
              f"{row['health_biotech_pct']:>7.1f} {row['climate_energy_pct']:>8.1f} "
              f"{row['scientific_pct']:>6.1f} {row['productivity_pct']:>6.1f} "
              f"{row['other_progress_pct']:>7.1f}")
    print(f"\nSaved → {SUMMARY_CSV}")

    if DOCUMENTS_CSV.exists():
        dominant = (
            out_df.groupby("doc_id")["innovation_subcategory"]
            .agg(lambda x: x.value_counts().idxmax() if len(x) > 0 else None)
            .rename("innovation_subcategory_dominant")
            .reset_index()
        )
        docs = pd.read_csv(DOCUMENTS_CSV, dtype=str)
        if "innovation_subcategory_dominant" in docs.columns:
            docs = docs.drop(columns=["innovation_subcategory_dominant"])
        docs = docs.merge(dominant, on="doc_id", how="left")
        docs.to_csv(DOCUMENTS_CSV, index=False)
        print(f"Updated → {DOCUMENTS_CSV}  (added innovation_subcategory_dominant)")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--limit",    type=int, default=None,  help="Process only first N sentences (test)")
    p.add_argument("--resume",   action="store_true",      help="Skip already-classified sentences")
    p.add_argument("--finalize", action="store_true",      help="Skip API calls; build summaries from existing OUTPUT_CSV")
    return p.parse_args()


def main():
    args = parse_args()

    if args.finalize:
        if not OUTPUT_CSV.exists():
            print(f"Error: {OUTPUT_CSV} does not exist — nothing to finalize")
            sys.exit(1)
        print(f"Finalize mode — reading {OUTPUT_CSV}")
        build_summaries()
        return

    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY not set"); sys.exit(1)

    print(f"Loading labeled sentences …")
    df = pd.read_csv(INPUT_CSV, dtype=str)
    df["Innovation_Progress"] = pd.to_numeric(df["Innovation_Progress"], errors="coerce").fillna(0).astype(int)
    innov = df[df["Innovation_Progress"] == 1].copy().reset_index(drop=True)
    print(f"  {len(innov):,} Innovation/Progress sentences total")

    # ── Resume: skip already-done ──────────────────────────────────────────────
    done_ids = set()
    if args.resume:
        done_ids = load_done_ids()
        print(f"  Resume mode — {len(done_ids):,} already classified, skipping")
        innov = innov[~innov["sentence_id"].isin(done_ids)].reset_index(drop=True)
        print(f"  {len(innov):,} remaining")

    if args.limit:
        innov = innov.head(args.limit)
        print(f"  Test mode — using first {args.limit}")

    if len(innov) == 0:
        print("Nothing to do — all sentences already classified.")
        build_summaries()
        return

    # Write header only when starting fresh (output file doesn't exist or resume not requested)
    write_header = not OUTPUT_CSV.exists() or (not args.resume and len(done_ids) == 0)
    if not args.resume and OUTPUT_CSV.exists():
        OUTPUT_CSV.unlink()  # fresh run: remove stale file
        write_header = True

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    batch_num = 0
    n_written = 0
    start = time.time()

    for i in range(0, len(innov), BATCH_SIZE):
        chunk = innov.iloc[i : i + BATCH_SIZE]
        batch = [{"id": row["sentence_id"], "text": row["sentence_text"]} for _, row in chunk.iterrows()]
        batch_num += 1
        result = label_batch_with_retry(client, batch, batch_num)

        rows = []
        for _, row in chunk.iterrows():
            rows.append({
                "sentence_id":            row["sentence_id"],
                "doc_id":                 row["doc_id"],
                "actor":                  row["actor"],
                "context":                row["context"],
                "sentence_text":          row["sentence_text"],
                "innovation_subcategory": result.get(row["sentence_id"], "other_progress"),
            })

        append_rows(rows, write_header=(write_header and batch_num == 1))
        n_written += len(rows)

        if batch_num % 20 == 0 or batch_num == 1:
            elapsed = time.time() - start
            pct = (i + len(chunk)) / len(innov) * 100
            print(f"  Batch {batch_num} — {pct:.1f}% done  ({elapsed:.0f}s elapsed)  "
                  f"{n_written:,} written", flush=True)

        time.sleep(INTER_CALL_DELAY)

    elapsed_total = time.time() - start
    print(f"\nDone — {n_written:,} new sentences in {elapsed_total:.0f}s")

    # ── Cost estimate ─────────────────────────────────────────────────────────
    est_input  = batch_num * 400
    est_output = batch_num * 100
    cost = est_input / 1e6 * 0.80 + est_output / 1e6 * 4.00
    print(f"Estimated API cost this run: ${cost:.2f}  ({batch_num} batches)")

    if FAILED_LOG.exists():
        with open(FAILED_LOG) as f:
            failures = f.readlines()
        if failures:
            print(f"⚠  {len(failures)} failed batch(es) → {FAILED_LOG}")
        else:
            print("No failed batches ✓")
    else:
        print("No failed batches ✓")

    build_summaries()


if __name__ == "__main__":
    main()
