"""
build_corpus.py — Build corpus.csv from raw JSON files and validate schema/balance.

Usage:
    python src/processing/build_corpus.py                  # build corpus.csv
    python src/processing/build_corpus.py --balance-report # report only, no CSV write
    python src/processing/build_corpus.py --validate-only  # schema check, no CSV write
"""

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Optional

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import (
    ACTORS, BALANCE_RULES, CHATGPT_LAUNCH_DATE, CONTEXTS,
    CORPUS_COLUMNS, CORPUS_CSV, DATA_RAW, PLATFORMS,
)

RAW_SUBDIRS = [
    DATA_RAW / "individuals",
    DATA_RAW / "companies",
    DATA_RAW / "policymakers",
]


# ── Ingest ─────────────────────────────────────────────────────────────────────

def load_raw_docs() -> list[dict]:
    """Walk all raw subdirectories and load every *.json doc."""
    docs = []
    for subdir in RAW_SUBDIRS:
        if not subdir.exists():
            continue
        for actor_dir in subdir.iterdir():
            if actor_dir.name.startswith("_"):  # skip _excluded/
                continue
            for fpath in actor_dir.rglob("*.json"):
                try:
                    docs.append(json.loads(fpath.read_text(encoding="utf-8")))
                except (json.JSONDecodeError, OSError) as e:
                    print(f"  WARN  skip {fpath.name}: {e}")
    return docs


def enrich_doc(doc: dict) -> Optional[dict]:
    """
    Validate and enrich a raw doc dict into a corpus row.
    Returns None if the doc should be dropped.
    """
    actor = doc.get("actor", "")
    if actor not in ACTORS:
        print(f"  WARN  unknown actor '{actor}' — dropping")
        return None

    meta = ACTORS[actor]
    context = doc.get("context", "")
    if context not in CONTEXTS:
        print(f"  WARN  unknown context '{context}' for {actor} — dropping")
        return None

    platform = doc.get("platform", "")
    if platform not in PLATFORMS:
        platform = "press_release"  # safe fallback rather than drop

    text = doc.get("text", "").strip()
    if not text:
        return None

    date_str = doc.get("date", "unknown")
    try:
        post_chatgpt = int(date_str >= CHATGPT_LAUNCH_DATE) if date_str != "unknown" else 0
    except Exception:
        post_chatgpt = 0

    return {
        "doc_id":      str(uuid.uuid4()),
        "actor":       actor,
        "actor_type":  meta["type"],
        "positioning": meta["positioning"],
        "context":     context,
        "platform":    platform,
        "date":        date_str,
        "post_chatgpt": post_chatgpt,
        "word_count":  len(text.split()),
        "text":        text,
    }


def build_dataframe() -> pd.DataFrame:
    """Load, enrich, deduplicate, and return corpus DataFrame."""
    raw = load_raw_docs()
    print(f"Raw docs loaded: {len(raw)}")

    enriched = []
    dropped = 0
    for doc in raw:
        row = enrich_doc(doc)
        if row is None:
            dropped += 1
        else:
            enriched.append(row)
    print(f"Enriched: {len(enriched)}  |  Dropped: {dropped}")

    df = pd.DataFrame(enriched, columns=CORPUS_COLUMNS)

    # Dedup by (actor, date, first-200-chars of text)
    df["_dedup_key"] = df["actor"] + "|" + df["date"] + "|" + df["text"].str[:200]
    before = len(df)
    df = df.drop_duplicates(subset="_dedup_key").drop(columns="_dedup_key")
    after = len(df)
    if before > after:
        print(f"Deduped: removed {before - after} duplicate rows")

    return df.reset_index(drop=True)


# ── Balance report ─────────────────────────────────────────────────────────────

def balance_report(df: pd.DataFrame) -> None:
    """Print a formatted balance report to stdout."""
    n = len(df)
    rules = BALANCE_RULES

    print("\n" + "=" * 60)
    print(f"  BALANCE REPORT  —  {n:,} documents")
    print("=" * 60)

    # ── Total ──────────────────────────────────────────────────────────────────
    min_total = rules["min_total_docs"]
    status = "✓" if n >= min_total else "✗"
    pct = n / min_total * 100
    print(f"\n[{status}] Total docs: {n:,} / {min_total:,} ({pct:.1f}%)")

    # ── Actor share ────────────────────────────────────────────────────────────
    max_share = rules["max_single_actor_share"]
    actor_counts = df["actor"].value_counts()
    biggest_actor = actor_counts.index[0]
    biggest_share = actor_counts.iloc[0] / n
    status = "✓" if biggest_share <= max_share else "✗"
    print(f"\n[{status}] Max single-actor share: {biggest_actor} {biggest_share:.1%} (limit {max_share:.0%})")

    print("\n  Actor breakdown:")
    for actor, cnt in actor_counts.items():
        flag = " ←" if cnt / n > max_share else ""
        print(f"    {actor:<22} {cnt:>5}  ({cnt/n:.1%}){flag}")

    # ── Context share ──────────────────────────────────────────────────────────
    min_ctx = rules["min_context_share"]
    ctx_counts = df["context"].value_counts()
    print(f"\n  Context breakdown:")
    for ctx in CONTEXTS:
        cnt = ctx_counts.get(ctx, 0)
        share = cnt / n if n else 0
        status = "✓" if share >= min_ctx else "✗"
        print(f"  [{status}] {ctx:<12} {cnt:>5}  ({share:.1%}, min {min_ctx:.0%})")

    # ── Actor-type split ───────────────────────────────────────────────────────
    type_targets = rules["target_type_split"]
    type_counts = df["actor_type"].value_counts()
    print(f"\n  Actor-type split (targets: ind 35%, co 35%, pm 30%):")
    for atype, target in type_targets.items():
        cnt = type_counts.get(atype, 0)
        share = cnt / n if n else 0
        status = "✓" if abs(share - target) <= 0.08 else "✗"
        print(f"  [{status}] {atype:<15} {cnt:>5}  ({share:.1%}, target {target:.0%})")

    # ── Min docs per actor per context ─────────────────────────────────────────
    min_d = rules["min_docs_per_actor_per_context"]
    print(f"\n  Per-actor per-context coverage (min {min_d} each, policymakers exempt for commercial):")
    fails = []
    for actor, meta in ACTORS.items():
        for ctx in CONTEXTS:
            if meta["type"] == "policymaker" and ctx == "commercial":
                continue
            cnt = len(df[(df["actor"] == actor) & (df["context"] == ctx)])
            if cnt < min_d:
                fails.append(f"    {actor} / {ctx}: {cnt}")
    if fails:
        print(f"  ✗  {len(fails)} actor/context pairs below {min_d} docs:")
        for f in fails:
            print(f)
    else:
        print(f"  ✓  All actor/context pairs meet minimum")

    print("\n" + "=" * 60 + "\n")


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build corpus.csv from raw JSON files.")
    p.add_argument("--balance-report", action="store_true",
                   help="Print balance report and exit without writing CSV")
    p.add_argument("--validate-only", action="store_true",
                   help="Validate schema and print stats; do not write CSV")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    df = build_dataframe()

    if args.balance_report or args.validate_only:
        balance_report(df)
        return

    CORPUS_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CORPUS_CSV, index=False)
    print(f"Wrote {len(df):,} rows → {CORPUS_CSV}")
    balance_report(df)


if __name__ == "__main__":
    main()
