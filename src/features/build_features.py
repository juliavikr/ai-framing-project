"""
build_features.py — Prepare analysis dataset for regression.

Loads labeled_documents.csv (doc-level framing scores + metadata),
applies minimum quality filters, reports balance, and saves a clean
analysis_dataset.csv ready for regression.py and variance_analysis.py.

Usage:
    python src/features/build_features.py
    python src/features/build_features.py --min-sentences 5
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import (
    ACTORS,
    CONTEXTS,
    DATA_ANNOTATION,
    OUTPUTS_TABLES,
    REGRESSION_DVS,
)

LABELED_DOCS = DATA_ANNOTATION  / "labeled_documents.csv"
OUT_CSV      = OUTPUTS_TABLES   / "analysis_dataset.csv"
BALANCE_CSV  = OUTPUTS_TABLES   / "balance_report.csv"

FRAME_COLS = ["innovation_score", "economic_score", "risk_score",
              "regulation_score", "existential_score"]

REQUIRED_COLS = [
    "doc_id", "actor", "actor_type", "positioning", "context",
    "platform", "date", "post_chatgpt", "n_sentences",
] + FRAME_COLS


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--min-sentences", type=int, default=5,
                   help="Minimum n_sentences per doc to include (default: 5)")
    return p.parse_args()


def main():
    args = parse_args()

    print("Loading labeled_documents.csv …")
    df = pd.read_csv(LABELED_DOCS, dtype=str)

    # Cast numeric columns
    for col in ["post_chatgpt", "n_sentences", "word_count"] + FRAME_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        print(f"ERROR: missing columns: {missing}")
        sys.exit(1)

    total_raw = len(df)
    print(f"  {total_raw:,} documents loaded")

    # ── Filter: drop docs with too few sentences ───────────────────────────────
    df = df[df["n_sentences"] >= args.min_sentences].copy()
    print(f"  {len(df):,} kept after n_sentences >= {args.min_sentences} filter "
          f"(dropped {total_raw - len(df):,})")

    # ── Drop docs with unknown actor ───────────────────────────────────────────
    known = set(ACTORS.keys())
    unknown = df[~df["actor"].isin(known)]
    if len(unknown):
        print(f"  Dropping {len(unknown)} docs with unrecognised actor values")
        df = df[df["actor"].isin(known)]

    # ── Balance report ─────────────────────────────────────────────────────────
    OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)

    print(f"\n── Documents per actor × context ──")
    pivot = df.groupby(["actor", "context"]).size().unstack(fill_value=0)
    for ctx in CONTEXTS:
        if ctx not in pivot.columns:
            pivot[ctx] = 0
    pivot = pivot[CONTEXTS]
    pivot["total"] = pivot.sum(axis=1)
    print(pivot.to_string())

    # Flag pairs with fewer than 50 docs
    pair_counts = df.groupby(["actor", "context"]).size().reset_index(name="n_docs")
    thin_pairs = pair_counts[pair_counts["n_docs"] < 50]
    if len(thin_pairs):
        print(f"\n⚠  {len(thin_pairs)} actor/context pairs with < 50 docs "
              f"(excluded from interaction regressions):")
        for _, row in thin_pairs.iterrows():
            print(f"     {row['actor']} × {row['context']}: {row['n_docs']} docs")

    pivot.to_csv(BALANCE_CSV)
    print(f"\nBalance report → {BALANCE_CSV}")

    # ── Mean framing scores per actor × context ────────────────────────────────
    print(f"\n── Mean framing scores per context ──")
    ctx_means = df.groupby("context")[FRAME_COLS].mean()
    print(ctx_means.round(4).to_string())

    # ── Save ──────────────────────────────────────────────────────────────────
    df.to_csv(OUT_CSV, index=False)
    print(f"\nAnalysis dataset → {OUT_CSV}  ({len(df):,} documents)")
    print(f"Columns: {list(df.columns)}")


if __name__ == "__main__":
    main()
