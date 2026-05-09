"""
compute_kappa.py — Compute Cohen's Kappa inter-annotator agreement.

Reads both completed annotation xlsx sheets, merges on sentence_id (inner join),
computes per-label and overall Kappa, saves results, and prints disagreements.

Usage:
    python src/annotation/compute_kappa.py
    python src/annotation/compute_kappa.py \
        --a data/annotation/annotation_sheet_person_a.xlsx \
        --b data/annotation/annotation_sheet_person_b.xlsx
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import openpyxl
from sklearn.metrics import cohen_kappa_score

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import DATA_ANNOTATION, OUTPUTS_TABLES, KAPPA_THRESHOLD

LABEL_COLS = [
    "Innovation_Progress",
    "Economic_Benefit",
    "Risk_Harm",
    "Regulation_Governance",
    "Existential_AGI",
    "None",
]

LABEL_DISPLAY = {
    "Innovation_Progress":   "Innovation/Progress",
    "Economic_Benefit":      "Economic Benefit",
    "Risk_Harm":             "Risk/Harm",
    "Regulation_Governance": "Regulation/Governance",
    "Existential_AGI":       "Existential/AGI",
    "None":                  "None",
}


# ── xlsx reader (openpyxl direct — avoids pandas version constraint) ───────────

def read_annotation_sheet(path: Path) -> pd.DataFrame:
    """Read annotation xlsx into a DataFrame; treat blank cells as 0."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if not rows:
        raise ValueError(f"Empty workbook: {path}")

    headers = [str(h).strip() if h is not None else "" for h in rows[0]]
    data = []
    for row in rows[1:]:
        data.append([cell for cell in row])

    df = pd.DataFrame(data, columns=headers)

    # Normalise label columns: blank/None → 0, anything else → int
    for col in LABEL_COLS:
        if col not in df.columns:
            raise ValueError(f"Expected column '{col}' not found in {path.name}.\n"
                             f"Columns present: {list(df.columns)}")
        def _to_binary(v):
            if v is None:
                return 0
            s = str(v).strip()
            if s in ("", "None", "nan"):
                return 0
            try:
                return int(float(s))
            except (ValueError, TypeError):
                return 0

        df[col] = df[col].apply(_to_binary)

    required = ["sentence_id", "sentence_text", "actor", "context", "date"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing column '{col}' in {path.name}")

    df["sentence_id"] = df["sentence_id"].astype(str).str.strip()
    return df


# ── Kappa computation ──────────────────────────────────────────────────────────

def compute_agreement_pct(y_a, y_b) -> float:
    return float(np.mean(np.array(y_a) == np.array(y_b)) * 100)


def compute_kappa_table(merged: pd.DataFrame) -> pd.DataFrame:
    records = []
    for col in LABEL_COLS:
        y_a = merged[f"{col}_a"].tolist()
        y_b = merged[f"{col}_b"].tolist()

        # sklearn raises if only one class present in both; handle gracefully
        try:
            kappa = cohen_kappa_score(y_a, y_b)
        except ValueError:
            kappa = float("nan")

        pct = compute_agreement_pct(y_a, y_b)
        records.append({
            "label":       col,
            "display":     LABEL_DISPLAY[col],
            "kappa":       kappa,
            "agreement_pct": pct,
        })

    valid_kappas = [r["kappa"] for r in records if not np.isnan(r["kappa"])]
    overall_kappa = float(np.mean(valid_kappas)) if valid_kappas else float("nan")
    all_y_a = []
    all_y_b = []
    for col in LABEL_COLS:
        all_y_a.extend(merged[f"{col}_a"].tolist())
        all_y_b.extend(merged[f"{col}_b"].tolist())
    overall_pct = compute_agreement_pct(all_y_a, all_y_b)

    records.append({
        "label":         "OVERALL",
        "display":       "OVERALL",
        "kappa":         overall_kappa,
        "agreement_pct": overall_pct,
    })
    return pd.DataFrame(records)


# ── Disagreement analysis ──────────────────────────────────────────────────────

def find_disagreements(merged: pd.DataFrame) -> pd.DataFrame:
    """Return sentences where A and B disagree on at least one label."""
    rows = []
    for _, row in merged.iterrows():
        diffs = []
        for col in LABEL_COLS:
            va, vb = int(row[f"{col}_a"]), int(row[f"{col}_b"])
            if va != vb:
                diffs.append(f"{LABEL_DISPLAY[col]}: A={va} B={vb}")
        if diffs:
            rows.append({
                "sentence_id":   row["sentence_id"],
                "actor":         row["actor_a"],
                "context":       row["context_a"],
                "date":          row["date_a"],
                "sentence_text": str(row["sentence_text_a"])[:200],
                "disagreements": "; ".join(diffs),
                "n_disagreements": len(diffs),
            })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("n_disagreements", ascending=False).reset_index(drop=True)
    return df


# ── Printing helpers ───────────────────────────────────────────────────────────

def print_kappa_table(kt: pd.DataFrame) -> None:
    w_label, w_kappa, w_pct = 25, 7, 13
    sep = f"{'─' * w_label}-+-{'─' * w_kappa}-+-{'─' * w_pct}"
    hdr = f"{'Label':<{w_label}} | {'Kappa':>{w_kappa}} | {'Agreement %':>{w_pct}}"
    print(f"\n{sep}\n{hdr}\n{sep}")
    for _, row in kt.iterrows():
        if row["label"] == "OVERALL":
            print(sep)
        kappa_str = f"{row['kappa']:.2f}" if not np.isnan(row['kappa']) else "  n/a"
        pct_str   = f"{row['agreement_pct']:.0f}%"
        print(f"{row['display']:<{w_label}} | {kappa_str:>{w_kappa}} | {pct_str:>{w_pct}}")
    print(sep)


def print_disagreements(disag: pd.DataFrame, n: int = 20) -> None:
    if disag.empty:
        print("\nNo disagreements found — perfect agreement on all shared sentences.")
        return
    print(f"\n── Top {min(n, len(disag))} disagreements (of {len(disag)} total) ──\n")
    for i, row in disag.head(n).iterrows():
        print(f"[{i+1:>2}] {row['actor']} | {row['context']} | {row['date']}")
        print(f"     {row['sentence_text']}")
        print(f"     ↳ {row['disagreements']}")
        print()


# ── Main ───────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Compute Cohen's Kappa for annotation agreement.")
    p.add_argument("--a", default=str(DATA_ANNOTATION / "annotation_sheet_person_a.xlsx"),
                   help="Path to Person A's annotation sheet")
    p.add_argument("--b", default=str(DATA_ANNOTATION / "annotation_sheet_person_b.xlsx"),
                   help="Path to Person B's annotation sheet")
    return p.parse_args()


def main():
    args = parse_args()
    path_a = Path(args.a)
    path_b = Path(args.b)

    for p in (path_a, path_b):
        if not p.exists():
            print(f"Error: annotation sheet not found: {p}")
            sys.exit(1)

    print(f"Reading {path_a.name} …")
    df_a = read_annotation_sheet(path_a)
    print(f"  {len(df_a)} rows, {df_a[LABEL_COLS].sum().sum():.0f} total labels marked")

    print(f"Reading {path_b.name} …")
    df_b = read_annotation_sheet(path_b)
    print(f"  {len(df_b)} rows, {df_b[LABEL_COLS].sum().sum():.0f} total labels marked")

    # Inner join on sentence_id — Kappa requires shared sentences
    merged = df_a.merge(df_b, on="sentence_id", suffixes=("_a", "_b"))
    n_shared = len(merged)

    if n_shared == 0:
        print(
            "\nError: no shared sentence_ids found between the two sheets.\n"
            "Kappa requires both annotators to label the same sentences.\n"
            "Make sure both annotators worked from the same gold set, or\n"
            "create an overlap batch and re-run."
        )
        sys.exit(1)

    n_only_a = len(df_a) - n_shared
    n_only_b = len(df_b) - n_shared
    print(f"\nShared sentences : {n_shared}")
    if n_only_a:
        print(f"Only in A        : {n_only_a} (excluded from Kappa)")
    if n_only_b:
        print(f"Only in B        : {n_only_b} (excluded from Kappa)")

    if n_shared < 50:
        print(f"\nWarning: only {n_shared} shared sentences. Kappa estimates will be unreliable.")
        print("Aim for at least 50–100 shared sentences.\n")

    # Kappa table
    kt = compute_kappa_table(merged)
    print_kappa_table(kt)

    # Verdict
    overall_row = kt[kt["label"] == "OVERALL"].iloc[0]
    overall_kappa = overall_row["kappa"]
    if np.isnan(overall_kappa):
        print("\nVerdict: INCONCLUSIVE — could not compute Kappa (check label variance)")
    elif overall_kappa >= KAPPA_THRESHOLD:
        print(f"\nVerdict: PASS ✓  (κ = {overall_kappa:.2f} ≥ {KAPPA_THRESHOLD})")
        print("  → Proceed to full LLM labeling.")
    else:
        print(f"\nVerdict: FAIL ✗  (κ = {overall_kappa:.2f} < {KAPPA_THRESHOLD})")
        print("  → Review disagreements below, revise annotation guidelines, and re-annotate.")

    # Save CSV
    OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)
    out_csv = OUTPUTS_TABLES / "kappa_results.csv"
    save_df = kt[["display", "kappa", "agreement_pct"]].rename(columns={
        "display": "label", "agreement_pct": "agreement_pct"
    })
    save_df["kappa"] = save_df["kappa"].round(4)
    save_df["agreement_pct"] = save_df["agreement_pct"].round(1)
    save_df.to_csv(out_csv, index=False)
    print(f"\nSaved → {out_csv}")

    # Disagreements
    disag = find_disagreements(merged)
    print_disagreements(disag, n=20)

    if not disag.empty:
        disag_csv = OUTPUTS_TABLES / "kappa_disagreements.csv"
        disag.to_csv(disag_csv, index=False)
        print(f"All {len(disag)} disagreements saved → {disag_csv}")


if __name__ == "__main__":
    main()
