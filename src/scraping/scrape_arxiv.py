"""
scrape_arxiv.py — Fetch arXiv paper abstracts for Anthropic and OpenAI researchers.

Uses the open arXiv Atom API (no key required). Saves title + abstract as document text.
Author list covers researchers listed in the spec (Askell, Christiano, Schulman, Sutskever, etc.)

Usage:
    python src/scraping/scrape_arxiv.py
    python src/scraping/scrape_arxiv.py --actor anthropic
    python src/scraping/scrape_arxiv.py --max-per-query 200
"""

import argparse
import hashlib
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlencode

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import ACTORS, DATA_RAW

ARXIV_API  = "http://export.arxiv.org/api/query"
ARXIV_NS   = "http://www.w3.org/2005/Atom"
ARXIV_DELAY = 3  # arXiv asks for ≥3 s between API requests

DATE_FROM = "2019-01-01"  # ignore pre-2019 papers

# ── Query configs ──────────────────────────────────────────────────────────────
# Each config produces one API request per query string.
# 'affiliation_hint' keywords are used to filter results when affiliation is
# not directly available in the Atom feed (arXiv doesn't expose affiliation).

SEARCH_CONFIGS: list[dict] = [

    # ── Anthropic ──────────────────────────────────────────────────────────────
    # arXiv author search uses plain last name only (no underscore+initial format)
    {
        "actor":   "Anthropic",
        "context": "commercial",
        "query":   "(au:Amodei OR au:Askell OR au:Christiano OR au:Kaplan OR au:Clark) AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL)",
        "label":   "Anthropic core authors (AI/ML papers)",
    },
    {
        "actor":   "Anthropic",
        "context": "commercial",
        "query":   "(au:Ganguli OR au:Bai OR au:Perez OR au:Jones OR au:Hernandez) AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL)",
        "label":   "Anthropic alignment researchers",
    },
    # Institutional affiliation: papers where authors name "Anthropic" in the abstract
    {
        "actor":   "Anthropic",
        "context": "commercial",
        "query":   "abs:Anthropic AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL)",
        "label":   "Papers with Anthropic affiliation in abstract",
    },

    # ── OpenAI ─────────────────────────────────────────────────────────────────
    {
        "actor":   "OpenAI",
        "context": "commercial",
        "query":   "(au:Schulman OR au:Sutskever OR au:Ouyang OR au:Ziegler OR au:Radford) AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL)",
        "label":   "OpenAI core authors (AI/ML papers)",
    },
    {
        "actor":   "OpenAI",
        "context": "commercial",
        "query":   "(au:Hilton OR au:Leike OR au:Stiennon OR au:Wu) AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL)",
        "label":   "OpenAI alignment/RL authors",
    },
    # Institutional affiliation: papers naming "OpenAI" in abstract
    {
        "actor":   "OpenAI",
        "context": "commercial",
        "query":   "abs:OpenAI AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL)",
        "label":   "Papers with OpenAI affiliation in abstract",
    },

    # ── Google DeepMind ────────────────────────────────────────────────────────
    {
        "actor":   "Google DeepMind",
        "context": "commercial",
        "query":   "(au:Vinyals OR au:Silver OR au:Kavukcuoglu OR au:Legg OR au:Hassabis) AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL)",
        "label":   "DeepMind core authors",
    },
    {
        "actor":   "Google DeepMind",
        "context": "commercial",
        "query":   "(au:Jumper OR au:Tunyasuvunakool OR au:Evans OR au:Kohli) AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL)",
        "label":   "DeepMind AlphaFold / protein team",
    },
    {
        "actor":   "Google DeepMind",
        "context": "commercial",
        "query":   "abs:DeepMind AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL)",
        "label":   "Papers with DeepMind affiliation in abstract",
    },

    # ── Meta AI ────────────────────────────────────────────────────────────────
    {
        "actor":   "Meta AI",
        "context": "commercial",
        "query":   "(au:LeCun OR au:Pineau OR au:Bordes OR au:Collobert OR au:Bengio) AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL)",
        "label":   "Meta AI / FAIR core authors",
    },
    {
        "actor":   "Meta AI",
        "context": "commercial",
        "query":   "(au:Touvron OR au:Scao OR au:Lample OR au:Grave OR au:Joulin) AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL)",
        "label":   "Meta LLaMA / language model authors",
    },
    {
        "actor":   "Meta AI",
        "context": "commercial",
        "query":   'abs:"Meta AI" AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL)',
        "label":   "Papers with Meta AI affiliation in abstract",
    },

    # ── Microsoft ──────────────────────────────────────────────────────────────
    {
        "actor":   "Microsoft",
        "context": "commercial",
        "query":   "(au:Nori OR au:Kamar OR au:Fathi OR au:Amershi OR au:Weld) AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL)",
        "label":   "Microsoft Research AI/ML authors",
    },
    {
        "actor":   "Microsoft",
        "context": "commercial",
        "query":   "(au:Wei OR au:Bubeck OR au:Mensch OR au:Shen) AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL)",
        "label":   "Microsoft Phi / language model authors",
    },
    {
        "actor":   "Microsoft",
        "context": "commercial",
        "query":   'abs:"Microsoft Research" AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL)',
        "label":   "Papers with Microsoft Research affiliation in abstract",
    },

    # ── Nvidia ─────────────────────────────────────────────────────────────────
    {
        "actor":   "Nvidia",
        "context": "commercial",
        "query":   "(au:Catanzaro OR au:Shoeybi OR au:Narayanan OR au:Patwary OR au:Peng) AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL)",
        "label":   "Nvidia deep learning / Megatron authors",
    },
    {
        "actor":   "Nvidia",
        "context": "commercial",
        "query":   'abs:NVIDIA AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL)',
        "label":   "Papers with NVIDIA affiliation in abstract",
    },
]

MIN_ABSTRACT_WORDS = 50  # skip empty / ultra-short abstracts


# ── Helpers ────────────────────────────────────────────────────────────────────

def url_to_filename(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12] + ".json"


def normalise_arxiv_id(raw_id: str) -> str:
    """Strip version suffix and normalise to https://arxiv.org/abs/{id}."""
    raw_id = raw_id.strip()
    raw_id = re.sub(r"v\d+$", "", raw_id)
    if raw_id.startswith("http"):
        # e.g. http://arxiv.org/abs/2303.08774  →  https://arxiv.org/abs/2303.08774
        return re.sub(r"^http://", "https://", raw_id)
    return f"https://arxiv.org/abs/{raw_id}"


def query_arxiv(query: str, max_results: int = 150, start: int = 0) -> list[dict]:
    """Call arXiv Atom API and return a list of paper metadata dicts."""
    params = {
        "search_query": query,
        "start":        start,
        "max_results":  max_results,
        "sortBy":       "submittedDate",
        "sortOrder":    "descending",
    }
    url = ARXIV_API + "?" + urlencode(params)
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
    except Exception as exc:
        print(f"    ! arXiv API error: {exc}")
        return []

    ns = ARXIV_NS
    papers: list[dict] = []
    for entry in root.findall(f"{{{ns}}}entry"):
        arxiv_id_el  = entry.find(f"{{{ns}}}id")
        title_el     = entry.find(f"{{{ns}}}title")
        summary_el   = entry.find(f"{{{ns}}}summary")
        published_el = entry.find(f"{{{ns}}}published")

        if arxiv_id_el is None or summary_el is None:
            continue

        raw_id   = arxiv_id_el.text or ""
        title    = re.sub(r"\s+", " ", (title_el.text   or "").strip()) if title_el   is not None else ""
        abstract = re.sub(r"\s+", " ", "".join(summary_el.itertext()).strip()) if summary_el is not None else ""
        date     = "".join(published_el.itertext()).strip()[:10]            if published_el is not None else "unknown"

        papers.append({
            "url":      normalise_arxiv_id(raw_id),
            "title":    title,
            "abstract": abstract,
            "date":     date,
        })

    return papers


# ── Main ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Fetch arXiv abstracts for AI lab researchers."
    )
    p.add_argument("--actor", default=None,
                   help="Limit to one actor by name fragment (default: all)")
    p.add_argument("--max-per-query", type=int, default=150,
                   help="Max results per API query (default: 150)")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    # Collect all unique actor keys from SEARCH_CONFIGS
    all_actors = list(dict.fromkeys(cfg["actor"] for cfg in SEARCH_CONFIGS))

    # Build per-actor output dirs and load seen URLs
    actor_dirs: dict[str, tuple[Path, set[str]]] = {}
    from src.scraping.scrape_individuals import load_seen_urls
    for actor_key in all_actors:
        context = next(c["context"] for c in SEARCH_CONFIGS if c["actor"] == actor_key)
        out_dir = DATA_RAW / ACTORS[actor_key]["raw_subdir"] / context
        out_dir.mkdir(parents=True, exist_ok=True)
        seen = load_seen_urls(out_dir)
        actor_dirs[actor_key] = (out_dir, seen)

    # Global dedup set so the same paper isn't saved for both actors
    seen_global: set[str] = set()
    for _, (_, seen) in actor_dirs.items():
        seen_global.update(seen)

    total = 0

    for cfg in SEARCH_CONFIGS:
        actor = cfg["actor"]
        if args.actor and args.actor.lower() not in actor.lower():
            continue

        out_dir, seen = actor_dirs[actor]
        print(f"\n  [{actor}] {cfg['label']}")
        print(f"    query: {cfg['query'][:80]}")

        papers = query_arxiv(cfg["query"], max_results=args.max_per_query)
        print(f"    returned {len(papers)} entries from API")
        time.sleep(ARXIV_DELAY)

        saved = 0
        for paper in papers:
            url = paper["url"]
            if url in seen_global:
                continue
            if paper["date"] != "unknown" and paper["date"] < DATE_FROM:
                continue

            text = paper["title"] + "\n\n" + paper["abstract"]
            if len(text.split()) < MIN_ABSTRACT_WORDS:
                continue

            doc = {
                "url":      url,
                "date":     paper["date"],
                "text":     text,
                "actor":    actor,
                "context":  cfg["context"],
                "platform": "research_paper",
            }
            fname = out_dir / url_to_filename(url)
            fname.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
            seen_global.add(url)
            saved += 1

        total += saved
        print(f"    saved {saved} new papers")

    print(f"\nTotal saved this run: {total}")


if __name__ == "__main__":
    main()
