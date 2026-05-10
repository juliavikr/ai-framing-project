"""
variance_analysis.py — Actor-level cross-context framing variance (H3).

Tests H3: Individual actors show greater cross-context framing variance
than institutions (companies + policymakers).

For each actor, computes the mean framing score per context, then takes
the standard deviation across contexts as a measure of adaptation.
Produces a variance table, bar chart, and Welch t-test comparing
individuals vs institutions.

Usage:
    python src/models/variance_analysis.py
    python src/models/variance_analysis.py --dv innovation_score
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import (
    CONTEXTS,
    FIGURE_DPI,
    INDIVIDUALS,
    OUTPUTS_FIGURES,
    OUTPUTS_TABLES,
    REGRESSION_DVS,
)

DATASET_CSV = OUTPUTS_TABLES / "analysis_dataset.csv"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--dv", default="all", help="Framing score column, or 'all' (default: all)")
    p.add_argument("--min-context-docs", type=int, default=10,
                   help="Min docs per actor×context to include that cell (default: 10)")
    return p.parse_args()


def compute_variance(df: pd.DataFrame, dv: str, min_docs: int) -> pd.DataFrame:
    """
    Per-actor, compute mean framing score in each context, then
    return the std across contexts as cross-context variance.
    Actors without >= 2 contexts meeting min_docs threshold are excluded.
    """
    rows = []
    for actor, grp in df.groupby("actor"):
        ctx_means = {}
        for ctx in CONTEXTS:
            sub = grp[grp["context"] == ctx]
            if len(sub) >= min_docs:
                ctx_means[ctx] = sub[dv].mean()
        if len(ctx_means) < 2:
            continue
        actor_type = grp["actor_type"].iloc[0]
        row = {
            "actor":      actor,
            "actor_type": actor_type,
            "is_individual": int(actor_type == "individual"),
            "n_contexts": len(ctx_means),
        }
        for ctx in CONTEXTS:
            row[f"mean_{ctx}"] = ctx_means.get(ctx, float("nan"))
        row["cross_context_std"] = pd.Series(list(ctx_means.values())).std(ddof=1)
        row["n_docs"] = len(grp)
        rows.append(row)
    return pd.DataFrame(rows).sort_values("cross_context_std", ascending=False)


def plot_variance(var_df: pd.DataFrame, dv: str) -> Path:
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = var_df["actor_type"].map(
        {"individual": "#2166ac", "company": "#4dac26", "policymaker": "#d01c8b"}
    )
    ax.bar(var_df["actor"], var_df["cross_context_std"], color=colors, edgecolor="white")
    ax.set_xlabel("Actor")
    ax.set_ylabel(f"Cross-context std ({dv})")
    ax.set_title(f"Cross-context framing variance — {dv}")
    plt.xticks(rotation=40, ha="right", fontsize=8)

    from matplotlib.patches import Patch
    legend = [
        Patch(color="#2166ac", label="Individual"),
        Patch(color="#4dac26", label="Company"),
        Patch(color="#d01c8b", label="Policymaker"),
    ]
    ax.legend(handles=legend, loc="upper right", fontsize=8)
    plt.tight_layout()

    OUTPUTS_FIGURES.mkdir(parents=True, exist_ok=True)
    out = OUTPUTS_FIGURES / f"variance_{dv}.png"
    fig.savefig(out, dpi=FIGURE_DPI)
    plt.close(fig)
    return out


def h3_test(var_df: pd.DataFrame, dv: str) -> None:
    ind  = var_df[var_df["is_individual"] == 1]["cross_context_std"].dropna()
    inst = var_df[var_df["is_individual"] == 0]["cross_context_std"].dropna()
    if len(ind) < 2 or len(inst) < 2:
        print("  Not enough actors for t-test")
        return
    t, p = stats.ttest_ind(ind, inst, equal_var=False)
    print(f"\n  H3 test ({dv}):  individuals mean={ind.mean():.4f}  "
          f"vs  institutions mean={inst.mean():.4f}")
    print(f"  Welch t-test: t={t:.3f}  p={p:.4f}  "
          f"({'H3 SUPPORTED ✓' if p < 0.05 and ind.mean() > inst.mean() else 'H3 NOT supported'})")


def run_dv(df: pd.DataFrame, dv: str, min_docs: int) -> None:
    print(f"\n{'='*60}")
    print(f"  DV: {dv}")
    var_df = compute_variance(df, dv, min_docs)

    if var_df.empty:
        print("  No actors with >= 2 contexts — skipping")
        return

    print(var_df[["actor", "actor_type", "n_contexts",
                  "mean_commercial", "mean_policy", "mean_public",
                  "cross_context_std"]].round(4).to_string(index=False))

    h3_test(var_df, dv)

    out_csv = OUTPUTS_TABLES / f"variance_{dv}.csv"
    var_df.to_csv(out_csv, index=False)
    print(f"\n  Table → {out_csv}")

    fig_path = plot_variance(var_df, dv)
    print(f"  Figure → {fig_path}")


def main():
    args = parse_args()

    if not DATASET_CSV.exists():
        print(f"ERROR: {DATASET_CSV} not found — run build_features.py first")
        sys.exit(1)

    df = pd.read_csv(DATASET_CSV, dtype=str)
    score_cols = [c for c in df.columns if c.endswith("_score")]
    for col in score_cols + ["post_chatgpt", "n_sentences"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    target_dvs = REGRESSION_DVS if args.dv == "all" else [args.dv]
    for dv in target_dvs:
        if dv not in df.columns:
            print(f"Warning: {dv} not in dataset — skipping")
            continue
        run_dv(df, dv, args.min_context_docs)

    print(f"\nDone. Figures → {OUTPUTS_FIGURES}/variance_*.png")
    print(f"Tables → {OUTPUTS_TABLES}/variance_*.csv")


if __name__ == "__main__":
    main()
