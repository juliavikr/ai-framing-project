"""
regression.py — OLS regression models for framing analysis.

Runs three models for a given dependent variable (framing score):

  Model 1 (baseline):     Frame ~ Context + PostChatGPT
  Model 2 (main):         Frame ~ Actor + Context + Actor×Context
  Model 3 (full controls):Frame ~ ActorType + Context + Positioning + Platform + PostChatGPT

Reference levels: context=commercial, actor_type=company, positioning=capability,
                  platform=blog (alphabetically first among platform values; set explicitly
                  via pd.Categorical ordering for context and actor_type, implicit for platform).

Usage:
    python src/models/regression.py --dv risk_score
    python src/models/regression.py --dv innovation_score
    python src/models/regression.py --dv regulation_score
    python src/models/regression.py --dv risk_score --min-pair-docs 50
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import OUTPUTS_TABLES, REGRESSION_DVS

DATASET_CSV = OUTPUTS_TABLES / "analysis_dataset.csv"

VALID_DVS = REGRESSION_DVS + ["economic_score", "existential_score"]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--dv", required=True, choices=VALID_DVS,
                   help="Dependent variable (framing score column)")
    p.add_argument("--min-pair-docs", type=int, default=50,
                   help="Minimum docs per actor×context pair for Model 2 (default: 50)")
    return p.parse_args()


def load_data(dv: str) -> pd.DataFrame:
    if not DATASET_CSV.exists():
        print(f"ERROR: {DATASET_CSV} not found — run build_features.py first")
        sys.exit(1)
    df = pd.read_csv(DATASET_CSV, dtype=str)
    for col in [dv, "post_chatgpt", "n_sentences"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=[dv, "context", "actor", "actor_type",
                            "positioning", "platform", "post_chatgpt"])
    # Set reference levels explicitly so results are interpretable
    df["context"]     = pd.Categorical(df["context"],
                                        categories=["commercial", "policy", "public"])
    df["actor_type"]  = pd.Categorical(df["actor_type"],
                                        categories=["company", "individual", "policymaker"])
    df["positioning"] = pd.Categorical(df["positioning"],
                                        categories=["capability", "safety",
                                                    "infrastructure", "regulator"])
    df["post_chatgpt"] = df["post_chatgpt"].astype(int)
    return df


def save_results(result, model_name: str, dv: str) -> None:
    out_path = OUTPUTS_TABLES / f"regression_{dv}_{model_name}.csv"
    summary = result.summary2().tables[1]
    summary.to_csv(out_path)
    print(f"  Saved → {out_path}")


def print_summary(result, model_name: str) -> None:
    print(f"\n{'─'*60}")
    print(f"  {model_name}   N={int(result.nobs):,}   R²={result.rsquared:.4f}   "
          f"adj-R²={result.rsquared_adj:.4f}   F={result.fvalue:.2f}   p={result.f_pvalue:.4f}")
    tbl = result.summary2().tables[1]
    sig = tbl[tbl["P>|t|"] < 0.05].copy()
    if len(sig):
        print(f"  Significant predictors (p < 0.05):")
        for idx, row in sig.iterrows():
            stars = "***" if row["P>|t|"] < 0.001 else ("**" if row["P>|t|"] < 0.01 else "*")
            print(f"    {idx:<45} β={row['Coef.']:+.4f}  {stars}")
    else:
        print("  No significant predictors at p < 0.05")


def main():
    args = parse_args()
    dv = args.dv

    OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)
    df = load_data(dv)
    print(f"Loaded {len(df):,} documents  |  DV: {dv}")
    print(f"Context distribution:\n{df['context'].value_counts().to_string()}")

    # ── Model 1: Does context predict framing? ─────────────────────────────────
    formula1 = f"{dv} ~ C(context) + post_chatgpt"
    m1 = smf.ols(formula1, data=df).fit()
    print_summary(m1, "Model 1 — Context + PostChatGPT")
    save_results(m1, "m1", dv)

    # ── Model 2: Strategic adaptation ─────────────────────────────────────────
    # Keep only actor×context pairs with enough docs for reliable estimates,
    # then restrict to actors that still appear in >= 2 contexts so that
    # interaction terms are estimable.
    pair_n = df.groupby(["actor", "context"], observed=True).size().reset_index(name="n")
    sufficient = pair_n[pair_n["n"] >= args.min_pair_docs][["actor", "context"]]
    df2 = df.merge(sufficient, on=["actor", "context"], how="inner").copy()

    ctx_per_actor = df2.groupby("actor", observed=True)["context"].nunique()
    single_ctx = sorted(ctx_per_actor[ctx_per_actor < 2].index)
    df2 = df2[~df2["actor"].isin(single_ctx)].copy()

    dropped_pairs = pair_n[pair_n["n"] < args.min_pair_docs][["actor", "context", "n"]]
    if not dropped_pairs.empty:
        print(f"\n  Model 2: excluded thin pairs (< {args.min_pair_docs} docs):")
        for _, r in dropped_pairs.iterrows():
            print(f"    {r['actor']} × {r['context']}: {int(r['n'])} docs")
    if single_ctx:
        print(f"  Model 2: also excluded (only 1 context remaining): {single_ctx}")
    print(f"  Model 2 actors: {sorted(df2['actor'].unique())}")
    print(f"  Model 2 N = {len(df2):,}")

    formula2 = f"{dv} ~ C(actor) + C(context) + C(actor):C(context)"
    m2 = smf.ols(formula2, data=df2).fit()
    print_summary(m2, "Model 2 — Actor + Context + Actor×Context")
    save_results(m2, "m2", dv)

    # Interaction F-test: are any Actor×Context terms jointly significant?
    try:
        interaction_terms = [t for t in m2.model.exog_names
                             if "actor" in t.lower() and "context" in t.lower() and ":" in t]
        if interaction_terms:
            ftest = m2.f_test([f"{t} = 0" for t in interaction_terms])
            print(f"\n  Actor×Context joint F-test: F={ftest.statistic[0][0]:.3f}  "
                  f"p={ftest.pvalue:.4f}  "
                  f"({'SIGNIFICANT ✓' if ftest.pvalue < 0.05 else 'not significant'})")
    except Exception:
        pass  # joint test is optional; skip if it fails

    # ── Model 3: Full controls ─────────────────────────────────────────────────
    formula3 = (f"{dv} ~ C(actor_type) + C(context) + C(positioning) "
                f"+ C(platform) + post_chatgpt")
    m3 = smf.ols(formula3, data=df).fit()
    print_summary(m3, "Model 3 — ActorType + Context + Positioning + Platform + PostChatGPT")
    save_results(m3, "m3", dv)

    print(f"\nAll Model 1–3 results saved to {OUTPUTS_TABLES}/regression_{dv}_m*.csv")


if __name__ == "__main__":
    main()
