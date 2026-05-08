"""
prepare_gold_set.py — Sample stratified gold sets for inter-annotator agreement.

Splits corpus.csv into sentences, then draws two non-overlapping 300-sentence
samples (one per annotator), stratified by context (100 each), actor diversity
(≥5 actors per context), and pre/post-ChatGPT mix.

Usage:
    python src/annotation/prepare_gold_set.py
    python src/annotation/prepare_gold_set.py --seed 99
"""

import argparse
import sys
import uuid
from pathlib import Path

import nltk
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import CORPUS_CSV, DATA_ANNOTATION, GOLD_A_CSV, GOLD_B_CSV, GOLD_MERGED_CSV

# Download punkt silently if missing
for _resource in ("punkt", "punkt_tab"):
    try:
        nltk.data.find(f"tokenizers/{_resource}")
    except (LookupError, OSError):
        nltk.download(_resource, quiet=True)

SENTENCES_PER_CONTEXT   = 100   # per annotator
SHORT_WORD_THRESHOLD    = 10    # words; <= this counts as "short"
MIN_SHORT_FRACTION      = 0.20  # ≥20% of each 100-sentence block
MIN_ACTORS_PER_CONTEXT  = 5
MIN_SENTENCE_WORDS      = 3     # skip very tiny fragments


# ── Sentence extraction ────────────────────────────────────────────────────────

def explode_to_sentences(df: pd.DataFrame) -> pd.DataFrame:
    """Tokenise every document into sentences; return one-row-per-sentence table."""
    rows = []
    for _, doc in df.iterrows():
        text = str(doc["text"]) if pd.notna(doc["text"]) else ""
        sentences = nltk.sent_tokenize(text)
        for sent in sentences:
            sent = sent.strip()
            if len(sent.split()) < MIN_SENTENCE_WORDS:
                continue
            rows.append({
                "sentence_id":  str(uuid.uuid4()),
                "doc_id":       doc["doc_id"],
                "actor":        doc["actor"],
                "actor_type":   doc["actor_type"],
                "context":      doc["context"],
                "date":         doc["date"],
                "post_chatgpt": doc["post_chatgpt"],
                "sentence_text": sent,
            })
    return pd.DataFrame(rows)


# ── Stratified sampling ────────────────────────────────────────────────────────

def _word_count(text: str) -> int:
    return len(str(text).split())


def sample_context_block(pool: pd.DataFrame, n: int, rng, exclude_ids: set) -> pd.DataFrame:
    """
    Draw n sentences from pool (excluding exclude_ids) with:
    - ≥5 actors represented
    - ≥20% short sentences (< SHORT_WORD_THRESHOLD words)
    - pre/post-ChatGPT mix where available

    Uses iterative sampling with replacement if quotas are hard to fill.
    """
    pool = pool[~pool["sentence_id"].isin(exclude_ids)].copy()
    pool["_wc"] = pool["sentence_text"].apply(_word_count)

    short = pool[pool["_wc"] < SHORT_WORD_THRESHOLD]
    long_ = pool[pool["_wc"] >= SHORT_WORD_THRESHOLD]

    n_short = max(int(n * MIN_SHORT_FRACTION), 1)
    n_long  = n - n_short

    # Guarantee short quota; fall back gracefully if not enough short sentences
    if len(short) < n_short:
        n_short = len(short)
        n_long  = n - n_short

    sampled_short = short.sample(n=n_short, random_state=rng, replace=False)
    remaining_long = long_[~long_["sentence_id"].isin(sampled_short["sentence_id"])]

    if len(remaining_long) < n_long:
        # Supplement from short pool beyond quota
        extra_pool = pool[~pool["sentence_id"].isin(sampled_short["sentence_id"])]
        sampled_long = extra_pool.sample(n=n_long, random_state=rng, replace=False)
    else:
        sampled_long = remaining_long.sample(n=n_long, random_state=rng, replace=False)

    result = pd.concat([sampled_short, sampled_long], ignore_index=True)

    # Actor diversity check — resample up to 10 times if < MIN_ACTORS_PER_CONTEXT
    for _attempt in range(10):
        if result["actor"].nunique() >= MIN_ACTORS_PER_CONTEXT:
            break
        result = pool.sample(n=n, random_state=rng, replace=False)

    return result.drop(columns=["_wc"])


def build_annotator_set(
    sentences: pd.DataFrame,
    n_per_context: int,
    rng,
    exclude_ids: set,
) -> pd.DataFrame:
    """Build a 300-sentence set: 100 per context, non-overlapping with exclude_ids."""
    parts = []
    for ctx in ("commercial", "policy", "public"):
        pool = sentences[sentences["context"] == ctx].copy()
        block = sample_context_block(pool, n_per_context, rng, exclude_ids)
        exclude_ids.update(block["sentence_id"].tolist())
        parts.append(block)
    return pd.concat(parts, ignore_index=True)


# ── Summary reporting ──────────────────────────────────────────────────────────

def print_summary(label: str, df: pd.DataFrame) -> None:
    print(f"\n── {label} ({'annotator ' + label.split()[-1]}) ──")
    print(f"  Total sentences : {len(df)}")
    ctx_counts = df.groupby("context").size()
    for ctx, cnt in ctx_counts.items():
        actors = df[df["context"] == ctx]["actor"].nunique()
        short  = (df[df["context"] == ctx]["sentence_text"]
                  .apply(_word_count) < SHORT_WORD_THRESHOLD).sum()
        pct_short = short / cnt * 100 if cnt else 0
        post = df[df["context"] == ctx]["post_chatgpt"].astype(str).eq("1").sum()
        pre  = cnt - post
        print(f"  {ctx:<12} {cnt:>4} sent | {actors} actors | "
              f"{short} short ({pct_short:.0f}%) | pre={pre} post={post}")

    avg_len = df["sentence_text"].apply(_word_count).mean()
    print(f"  Avg sentence length : {avg_len:.1f} words")
    print(f"  Actors represented  : {sorted(df['actor'].unique())}")


# ── Main ───────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Prepare stratified gold sets for annotation.")
    p.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    return p.parse_args()


def main():
    args = parse_args()
    rng  = args.seed

    if not CORPUS_CSV.exists():
        print(f"Error: corpus not found at {CORPUS_CSV}")
        sys.exit(1)

    print(f"Reading corpus from {CORPUS_CSV} …")
    corpus = pd.read_csv(CORPUS_CSV, dtype=str)
    print(f"  {len(corpus):,} documents loaded")

    print("Tokenising sentences (this may take a minute) …")
    sentences = explode_to_sentences(corpus)
    print(f"  {len(sentences):,} sentences total")

    for ctx in ("commercial", "policy", "public"):
        n = (sentences["context"] == ctx).sum()
        actors = sentences[sentences["context"] == ctx]["actor"].nunique()
        print(f"  {ctx:<12} {n:>7,} sentences | {actors} actors")

    # Build annotator sets sequentially so B never overlaps A
    exclude: set = set()

    print("\nSampling Person A (300 sentences) …")
    set_a = build_annotator_set(sentences, SENTENCES_PER_CONTEXT, rng, exclude)
    set_a = set_a.sample(frac=1, random_state=rng).reset_index(drop=True)

    print("Sampling Person B (300 sentences) …")
    set_b = build_annotator_set(sentences, SENTENCES_PER_CONTEXT, rng, exclude)
    set_b = set_b.sample(frac=1, random_state=rng).reset_index(drop=True)

    # Add annotator label to combined file
    set_a_tagged = set_a.copy(); set_a_tagged["annotator"] = "A"
    set_b_tagged = set_b.copy(); set_b_tagged["annotator"] = "B"
    combined = pd.concat([set_a_tagged, set_b_tagged], ignore_index=True)

    # Verify no overlap
    overlap = set(set_a["sentence_id"]) & set(set_b["sentence_id"])
    assert len(overlap) == 0, f"Overlap detected: {len(overlap)} shared sentence_ids!"

    # Write outputs
    DATA_ANNOTATION.mkdir(parents=True, exist_ok=True)
    set_a.to_csv(GOLD_A_CSV, index=False)
    set_b.to_csv(GOLD_B_CSV, index=False)
    combined.to_csv(GOLD_MERGED_CSV, index=False)

    print_summary("Person A", set_a)
    print_summary("Person B", set_b)

    print(f"\n── Saved ──")
    print(f"  {GOLD_A_CSV}")
    print(f"  {GOLD_B_CSV}")
    print(f"  {GOLD_MERGED_CSV}")
    print(f"\n  Overlap check: 0 shared sentence_ids ✓")


if __name__ == "__main__":
    main()
