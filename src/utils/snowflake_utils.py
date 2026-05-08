"""
snowflake_utils.py — Snowflake connection, corpus upload, and query helpers.

Usage:
    python src/utils/snowflake_utils.py --load data/processed/corpus.csv
    python src/utils/snowflake_utils.py --balance
    python src/utils/snowflake_utils.py --query "SELECT COUNT(*) FROM CORPUS"
"""

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import CORPUS_COLUMNS, SNOWFLAKE_CONFIG, SNOWFLAKE_TABLE


# ── Connection ─────────────────────────────────────────────────────────────────

def get_connection():
    """Return an open Snowflake connection using credentials from SNOWFLAKE_CONFIG.

    Raises ValueError if any required credential is missing from the environment.
    """
    import snowflake.connector  # import here so the module loads without the package

    required = ("account", "user", "password")
    missing = [k for k in required if not SNOWFLAKE_CONFIG.get(k)]
    if missing:
        raise ValueError(
            f"Missing Snowflake credentials: {', '.join(missing).upper()}. "
            "Set them as environment variables (e.g. in .env)."
        )

    return snowflake.connector.connect(
        account=SNOWFLAKE_CONFIG["account"],
        user=SNOWFLAKE_CONFIG["user"],
        password=SNOWFLAKE_CONFIG["password"],
        warehouse=SNOWFLAKE_CONFIG["warehouse"],
        database=SNOWFLAKE_CONFIG["database"],
        schema=SNOWFLAKE_CONFIG["schema"],
    )


# ── Load corpus ────────────────────────────────────────────────────────────────

def load_corpus(csv_path: str) -> None:
    """Read corpus.csv, validate schema, and upload to Snowflake via write_pandas."""
    from snowflake.connector.pandas_tools import write_pandas

    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"corpus CSV not found: {path}")

    print(f"Reading {path} …")
    df = pd.read_csv(path, dtype=str)

    # Validate all required columns are present
    missing_cols = [c for c in CORPUS_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"corpus.csv is missing columns: {missing_cols}")

    # Drop any extra columns; keep canonical order
    df = df[CORPUS_COLUMNS].copy()

    # Convert date to datetime (keeps Snowflake DATE type happy)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Snowflake write_pandas requires uppercase column names
    df.columns = [c.upper() for c in df.columns]

    conn = get_connection()
    print(f"Connected → {SNOWFLAKE_CONFIG['database']}.{SNOWFLAKE_CONFIG['schema']}.{SNOWFLAKE_TABLE}")

    # Ensure the table exists with the right schema
    _ensure_table(conn)

    print(f"Uploading {len(df):,} rows …")
    t0 = time.time()
    success, nchunks, nrows, _ = write_pandas(
        conn,
        df,
        table_name=SNOWFLAKE_TABLE,
        database=SNOWFLAKE_CONFIG["database"],
        schema=SNOWFLAKE_CONFIG["schema"],
        overwrite=True,
        auto_create_table=False,
    )
    elapsed = time.time() - t0

    if success:
        print(f"✓ Uploaded {nrows:,} rows in {nchunks} chunk(s) — {elapsed:.1f}s")
    else:
        print(f"✗ Upload failed after {elapsed:.1f}s")

    conn.close()


def _ensure_table(conn) -> None:
    """Create CORPUS table if it doesn't exist, matching the corpus schema exactly."""
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {SNOWFLAKE_TABLE} (
        DOC_ID       VARCHAR(36)    NOT NULL,
        ACTOR        VARCHAR(100)   NOT NULL,
        ACTOR_TYPE   VARCHAR(20)    NOT NULL,
        POSITIONING  VARCHAR(20)    NOT NULL,
        CONTEXT      VARCHAR(20)    NOT NULL,
        PLATFORM     VARCHAR(30)    NOT NULL,
        DATE         DATE,
        POST_CHATGPT SMALLINT,
        WORD_COUNT   INTEGER,
        TEXT         TEXT
    )
    """
    with conn.cursor() as cur:
        cur.execute(ddl)


# ── Query ──────────────────────────────────────────────────────────────────────

def query(sql: str) -> pd.DataFrame:
    """Run any SQL string against Snowflake and return a pandas DataFrame."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
        return pd.DataFrame(rows, columns=cols)
    finally:
        conn.close()


# ── Balance check ──────────────────────────────────────────────────────────────

def run_balance_check() -> None:
    """Print actor, context, and actor-type breakdowns from the Snowflake table."""
    conn = get_connection()
    try:
        _print_query(conn, "Actor breakdown",
            f"""SELECT ACTOR, COUNT(*) AS DOCS
                FROM {SNOWFLAKE_TABLE}
                GROUP BY ACTOR
                ORDER BY DOCS DESC""")

        _print_query(conn, "Context breakdown",
            f"""SELECT CONTEXT, COUNT(*) AS DOCS,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS PCT
                FROM {SNOWFLAKE_TABLE}
                GROUP BY CONTEXT
                ORDER BY DOCS DESC""")

        _print_query(conn, "Actor-type breakdown",
            f"""SELECT ACTOR_TYPE, COUNT(*) AS DOCS
                FROM {SNOWFLAKE_TABLE}
                GROUP BY ACTOR_TYPE
                ORDER BY DOCS DESC""")
    finally:
        conn.close()


def _print_query(conn, title: str, sql: str) -> None:
    with conn.cursor() as cur:
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    print(f"\n── {title} ──")
    print(df.to_string(index=False))


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Snowflake utilities: load corpus, run balance check, or run a query."
    )
    parser.add_argument("--load",    help="Path to corpus.csv to upload")
    parser.add_argument("--balance", action="store_true", help="Print balance check from Snowflake")
    parser.add_argument("--query",   help="SQL string to run and print")
    args = parser.parse_args()

    if args.load:
        load_corpus(args.load)
    if args.balance:
        run_balance_check()
    if args.query:
        print(query(args.query))

    if not any([args.load, args.balance, args.query]):
        parser.print_help()
