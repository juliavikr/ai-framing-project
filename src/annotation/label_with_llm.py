"""
label_with_llm.py — Label all corpus sentences with an LLM (5 annotation frames).

Reads clean_sentences.csv, labels in batches via the Anthropic API, aggregates
sentence-level labels to document-level framing scores, and writes two output files:
  data/annotation/labeled_sentences.csv
  data/annotation/labeled_documents.csv

Usage:
    python src/annotation/label_with_llm.py --limit 50          # test run, 50 docs
    python src/annotation/label_with_llm.py                     # full corpus
    python src/annotation/label_with_llm.py --resume            # continue after crash
    python src/annotation/label_with_llm.py --input data/processed/corpus.csv
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import anthropic
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import (
    ANTHROPIC_API_KEY,
    CORPUS_CSV,
    DATA_ANNOTATION,
    LLM_BATCH_SIZE,
    LLM_MAX_TOKENS,
    LLM_MODEL,
)

CLEAN_SENTENCES_CSV   = DATA_ANNOTATION / "clean_sentences.csv"
LABELED_SENTENCES_CSV = DATA_ANNOTATION / "labeled_sentences.csv"
LABELED_DOCUMENTS_CSV = DATA_ANNOTATION / "labeled_documents.csv"
FAILED_BATCHES_LOG    = DATA_ANNOTATION / "failed_batches.log"

FRAMES = [
    "Innovation/Progress",
    "Economic Benefit",
    "Risk/Harm",
    "Regulation/Governance",
    "Existential/AGI",
]

FRAME_COLS = {
    "Innovation/Progress":   "Innovation_Progress",
    "Economic Benefit":      "Economic_Benefit",
    "Risk/Harm":             "Risk_Harm",
    "Regulation/Governance": "Regulation_Governance",
    "Existential/AGI":       "Existential_AGI",
}

SYSTEM_PROMPT = """\
You are a research assistant for a computational linguistics project studying how AI
industry actors frame artificial intelligence across different contexts.

You will receive a JSON array of sentences. For each sentence, assign ONE OR MORE of
these frames, or "None" if no frame applies:

1. Innovation/Progress   — AI as transformative; EXPLICIT claim about societal benefit
                           or meaningful scientific advance. Descriptive statements
                           about how AI works are NOT enough.
2. Economic Benefit      — EXPLICIT claim about jobs, revenue, productivity, or
                           national competitiveness. Product announcements do NOT qualify.
3. Risk/Harm             — CONCRETE near-term harms: bias, job loss, misuse,
                           surveillance. Vague concern does NOT qualify.
4. Regulation/Governance — EXPLICIT institutional mechanism: law, policy framework,
                           oversight body, compliance requirement, standards body.
5. Existential/AGI       — Long-term civilizational risk, AGI, superintelligence,
                           x-risk. Near-term risks go in Risk/Harm.
None                     — Procedural, descriptive, transitional, or administrative
                           sentences. When in doubt and the frame must be INFERRED
                           rather than stated, use None.

Return ONLY a valid JSON array, one object per sentence:
  [{"id": "<sentence_id>", "labels": ["Innovation/Progress"]}, ...]
For None: {"id": "<sentence_id>", "labels": ["None"]}
No preamble, no explanation, no markdown fences. Compact JSON only — no newlines or extra whitespace.
"""

INTER_CALL_DELAY = 0.3   # seconds between API calls
MAX_RETRIES      = 3
RETRY_DELAY      = 5.0   # seconds before retry


# ── API call ───────────────────────────────────────────────────────────────────

def call_llm(client: anthropic.Anthropic, batch: list) -> str:
    """Send a batch of {id, text} dicts to Haiku; return raw response text."""
    user_msg = json.dumps(batch, ensure_ascii=False)
    response = client.messages.create(
        model=LLM_MODEL,
        max_tokens=LLM_MAX_TOKENS,
        messages=[{"role": "user", "content": user_msg}],
        system=SYSTEM_PROMPT,
    )
    return response.content[0].text.strip()


def parse_response(raw: str, expected_ids: list[str]) -> dict[str, list[str]]:
    """Parse Claude's JSON response into {sentence_id: [labels]}. Robust to fencing."""
    # Strip markdown fences if present
    clean = re.sub(r"^```[a-z]*\n?", "", raw.strip(), flags=re.MULTILINE)
    clean = re.sub(r"\n?```$", "", clean.strip())

    data = json.loads(clean)
    result = {}
    for item in data:
        sid    = str(item.get("id", ""))
        labels = item.get("labels", ["None"])
        # Normalise: keep only valid frame names or None
        valid = [l for l in labels if l in FRAMES or l == "None"]
        result[sid] = valid if valid else ["None"]

    # Fill in any missing IDs as None (failsafe)
    for sid in expected_ids:
        if sid not in result:
            result[sid] = ["None"]
    return result


def label_batch_with_retry(
    client: anthropic.Anthropic,
    batch: list,
    batch_num: int,
) -> dict:
    """Label one batch; retry up to MAX_RETRIES times. Log failures."""
    expected_ids = [b["id"] for b in batch]
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw = call_llm(client, batch)
            return parse_response(raw, expected_ids)
        except Exception as exc:
            last_err = exc
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
            continue

    # All retries failed — log and return None for all sentences
    with open(FAILED_BATCHES_LOG, "a") as f:
        ids_str = ", ".join(expected_ids[:3]) + ("…" if len(expected_ids) > 3 else "")
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] batch {batch_num}: "
                f"{type(last_err).__name__}: {last_err} | ids: {ids_str}\n")
    return {sid: ["None"] for sid in expected_ids}


# ── Row builder ────────────────────────────────────────────────────────────────

def build_sentence_row(sent: pd.Series, labels: list[str]) -> dict:
    row = {
        "sentence_id":  sent["sentence_id"],
        "doc_id":       sent["doc_id"],
        "actor":        sent["actor"],
        "actor_type":   sent["actor_type"],
        "context":      sent["context"],
        "date":         sent["date"],
        "sentence_text": sent["sentence_text"],
        "raw_labels":   json.dumps(labels),
        "is_none":      int(labels == ["None"]),
    }
    for frame, col in FRAME_COLS.items():
        row[col] = int(frame in labels)
    return row


# ── Document-level aggregation ─────────────────────────────────────────────────

def aggregate_to_documents(
    sent_df: pd.DataFrame,
    corpus_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute per-document framing scores from sentence-level labels."""
    meta_cols = [
        "doc_id", "actor", "actor_type", "positioning", "context",
        "platform", "date", "post_chatgpt", "word_count",
    ]

    agg = (
        sent_df
        .groupby("doc_id")
        .agg(
            n_sentences        = ("sentence_id", "count"),
            innovation_score   = ("Innovation_Progress", "mean"),
            economic_score     = ("Economic_Benefit",    "mean"),
            risk_score         = ("Risk_Harm",           "mean"),
            regulation_score   = ("Regulation_Governance","mean"),
            existential_score  = ("Existential_AGI",     "mean"),
            none_pct           = ("is_none",             "mean"),
        )
        .reset_index()
    )

    meta = corpus_df[meta_cols].drop_duplicates("doc_id")
    doc_df = meta.merge(agg, on="doc_id", how="left")

    # Docs with no clean sentences get n_sentences=0, scores=NaN
    doc_df["n_sentences"] = doc_df["n_sentences"].fillna(0).astype(int)
    return doc_df


# ── Print helpers ──────────────────────────────────────────────────────────────

def print_label_distribution(sent_df: pd.DataFrame, title: str = "Label distribution") -> None:
    total = len(sent_df)
    print(f"\n── {title} ({total:,} sentences) ──")
    for frame, col in FRAME_COLS.items():
        n   = sent_df[col].sum()
        pct = n / total * 100 if total else 0
        print(f"  {frame:<25} {n:>6,}  ({pct:.1f}%)")
    n_none = sent_df["is_none"].sum()
    print(f"  {'None':<25} {n_none:>6,}  ({n_none/total*100:.1f}%)")


def print_example_sentences(sent_df: pd.DataFrame, n: int = 10) -> None:
    print(f"\n── {n} example labeled sentences ──")
    sample = sent_df[sent_df["is_none"] == 0].head(n)
    for i, row in enumerate(sample.itertuples(), 1):
        labels = json.loads(row.raw_labels)
        text   = row.sentence_text[:120]
        print(f"\n[{i}] {row.actor} | {row.context}")
        print(f"    {text}")
        print(f"    → {', '.join(labels)}")


def print_top_docs(doc_df: pd.DataFrame, score_col: str, label: str, n: int = 5) -> None:
    top = (
        doc_df[doc_df["n_sentences"] > 0]
        .nlargest(n, score_col)[["actor", "context", "date", score_col, "n_sentences"]]
    )
    print(f"\n── Top {n} by {label} ──")
    for row in top.itertuples():
        score = getattr(row, score_col)
        print(f"  {row.actor:<22} {row.context:<12} {str(row.date):<12} "
              f"{score:.3f}  ({row.n_sentences} sents)")


# ── Main ───────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Label corpus sentences with Claude.")
    p.add_argument("--input",  default=str(CORPUS_CSV),
                   help="Path to corpus.csv (for document metadata)")
    p.add_argument("--sentences", default=str(CLEAN_SENTENCES_CSV),
                   help="Path to clean_sentences.csv")
    p.add_argument("--limit",  type=int, default=None,
                   help="Process only first N documents (test mode)")
    p.add_argument("--resume", action="store_true",
                   help="Skip already-labeled sentence_ids")
    p.add_argument("--batch-size", type=int, default=LLM_BATCH_SIZE,
                   help=f"Sentences per API call (default: {LLM_BATCH_SIZE})")
    return p.parse_args()


def main():
    args = parse_args()

    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY not set in .env")
        sys.exit(1)

    # ── Load data ──────────────────────────────────────────────────────────────
    print(f"Loading corpus metadata from {args.input} …")
    corpus_df = pd.read_csv(args.input, dtype=str)
    print(f"  {len(corpus_df):,} documents")

    print(f"Loading sentences from {args.sentences} …")
    sents_df = pd.read_csv(args.sentences, dtype=str)
    print(f"  {len(sents_df):,} sentences, {sents_df['doc_id'].nunique():,} docs")

    # ── Resume logic ───────────────────────────────────────────────────────────
    done_ids: set = set()
    write_header = True
    if args.resume and LABELED_SENTENCES_CSV.exists():
        done_df  = pd.read_csv(LABELED_SENTENCES_CSV, dtype=str, usecols=["sentence_id"])
        done_ids = set(done_df["sentence_id"].tolist())
        write_header = False
        print(f"Resuming — {len(done_ids):,} sentences already labeled, skipping")

    # ── Select docs to process ─────────────────────────────────────────────────
    doc_order = list(sents_df["doc_id"].unique())
    if args.limit:
        doc_order = doc_order[: args.limit]
        print(f"Test mode — processing first {args.limit} documents")

    total_docs = len(doc_order)

    # Filter out already-done docs (resume mode: skip if ALL sentences done)
    if done_ids:
        def doc_fully_done(doc_id):
            doc_sents = sents_df[sents_df["doc_id"] == doc_id]["sentence_id"]
            return doc_sents.isin(done_ids).all()
        doc_order = [d for d in doc_order if not doc_fully_done(d)]
        print(f"  {total_docs - len(doc_order)} docs already complete, "
              f"{len(doc_order)} remaining")

    # ── API client ─────────────────────────────────────────────────────────────
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # ── Label loop ─────────────────────────────────────────────────────────────
    DATA_ANNOTATION.mkdir(parents=True, exist_ok=True)
    out_file    = open(LABELED_SENTENCES_CSV, "a" if args.resume else "w", encoding="utf-8")
    batch_num   = 0
    total_sents = 0
    start_time  = time.time()

    # Write CSV header
    col_order = (
        ["sentence_id", "doc_id", "actor", "actor_type", "context", "date",
         "sentence_text", "raw_labels", "is_none"]
        + list(FRAME_COLS.values())
    )
    if write_header:
        out_file.write(",".join(col_order) + "\n")

    pending_batch: list[dict] = []
    pending_meta:  list[pd.Series] = []

    def flush_batch():
        nonlocal batch_num, total_sents
        if not pending_batch:
            return
        batch_num += 1
        labels_map = label_batch_with_retry(client, pending_batch, batch_num)
        for sent in pending_meta:
            sid    = sent["sentence_id"]
            labels = labels_map.get(sid, ["None"])
            row    = build_sentence_row(sent, labels)
            line   = ",".join(
                '"' + str(row.get(c, "")).replace('"', '""') + '"'
                for c in col_order
            )
            out_file.write(line + "\n")
        out_file.flush()
        total_sents += len(pending_batch)
        pending_batch.clear()
        pending_meta.clear()
        time.sleep(INTER_CALL_DELAY)

    for doc_idx, doc_id in enumerate(doc_order):
        doc_sents = sents_df[sents_df["doc_id"] == doc_id]

        for _, sent_row in doc_sents.iterrows():
            sid = sent_row["sentence_id"]
            if sid in done_ids:
                continue
            pending_batch.append({"id": sid, "text": sent_row["sentence_text"]})
            pending_meta.append(sent_row)
            if len(pending_batch) >= args.batch_size:
                flush_batch()

        # Progress every 100 docs
        docs_done = doc_idx + 1
        if docs_done % 100 == 0 or docs_done == total_docs:
            elapsed = time.time() - start_time
            pct     = docs_done / total_docs * 100
            eta_s   = (elapsed / docs_done) * (total_docs - docs_done) if docs_done else 0
            elapsed_str = str(timedelta(seconds=int(elapsed)))
            eta_str     = str(timedelta(seconds=int(eta_s)))
            print(f"Labeled {docs_done}/{total_docs} docs ({pct:.1f}%) — "
                  f"elapsed: {elapsed_str}  ETA: {eta_str}")

    flush_batch()  # remaining sentences
    out_file.close()

    elapsed_total = str(timedelta(seconds=int(time.time() - start_time)))
    print(f"\nDone — {total_docs} docs, {total_sents} sentences in {elapsed_total}")

    # ── Load results and report ────────────────────────────────────────────────
    print("\nLoading labeled sentences for summary …")
    result_df = pd.read_csv(LABELED_SENTENCES_CSV, dtype=str)
    for col in list(FRAME_COLS.values()) + ["is_none"]:
        result_df[col] = pd.to_numeric(result_df[col], errors="coerce").fillna(0).astype(int)

    print_label_distribution(result_df)
    print_example_sentences(result_df, n=10)

    # Failed batches
    if FAILED_BATCHES_LOG.exists():
        with open(FAILED_BATCHES_LOG) as f:
            failures = f.readlines()
        if failures:
            print(f"\n⚠  {len(failures)} failed batch(es) logged → {FAILED_BATCHES_LOG}")
        else:
            print("\nNo failed batches ✓")
    else:
        print("\nNo failed batches ✓")

    # ── Aggregate to documents ─────────────────────────────────────────────────
    print("\nAggregating to document level …")
    doc_df = aggregate_to_documents(result_df, corpus_df)
    doc_df.to_csv(LABELED_DOCUMENTS_CSV, index=False)
    print(f"Saved → {LABELED_DOCUMENTS_CSV}  ({len(doc_df):,} rows)")

    print_top_docs(doc_df, "risk_score",       "risk_score")
    print_top_docs(doc_df, "innovation_score", "innovation_score")

    # Score sanity check
    score_cols = ["innovation_score", "economic_score", "risk_score",
                  "regulation_score", "existential_score"]
    for col in score_cols:
        vals = doc_df[col].dropna()
        ok   = vals.between(0, 1).all()
        print(f"  {col:<22} min={vals.min():.3f}  max={vals.max():.3f}  "
              f"{'✓' if ok else '✗ OUT OF RANGE'}")


if __name__ == "__main__":
    main()
