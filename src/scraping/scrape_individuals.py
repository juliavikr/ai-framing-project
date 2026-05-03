"""
scrape_individuals.py — Scrapes documents for individual actors from their configured sources.

Saves one JSON per document to data/raw/{raw_subdir}/ with fields:
    url, date, text, actor, context, platform

Usage:
    python src/scraping/scrape_individuals.py --actor "Sam Altman" --context commercial --limit 400
"""

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import ACTORS, DATA_RAW

# ── Constants ──────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
DELAY = 1          # seconds between HTTP requests
MIN_TEXT_LEN = 200  # discard pages shorter than this (nav pages, 404s, etc.)

# Maps a fragment that can appear in a config source string → (base_url, platform).
# All blog-style sources that can be crawled with the generic link collector.
SOURCE_REGISTRY: dict[str, tuple[str, str]] = {
    # ── Commercial ─────────────────────────────────────────────────────────────
    "blog.samaltman.com":          ("https://blog.samaltman.com",                              "blog"),
    "darioamodei.com":             ("https://darioamodei.com",                                 "blog"),
    "anthropic.com/news":          ("https://www.anthropic.com/news",                          "press_release"),
    "anthropic.com/research":      ("https://www.anthropic.com/research",                      "research_paper"),
    "blogs.nvidia.com":            ("https://blogs.nvidia.com",                                "blog"),
    "deepmind.google/blog":        ("https://deepmind.google/blog",                            "blog"),
    "ai.meta.com":                 ("https://ai.meta.com/blog",                                "blog"),
    "xai blog":                    ("https://x.ai/blog",                                       "blog"),
    "blogs.microsoft.com":         ("https://blogs.microsoft.com/blog/author/satya-nadella",   "blog"),
    "microsoft.com/en-us/satyana": ("https://www.microsoft.com/en-us/satyanadella",            "blog"),
    # ── Policy ─────────────────────────────────────────────────────────────────
    "anthropic.com/policy":        ("https://www.anthropic.com/policy",                        "regulatory_doc"),
    "on-the-issues":               ("https://blogs.microsoft.com/on-the-issues",               "regulatory_doc"),
    "nvidia.com/en-us/government": ("https://www.nvidia.com/en-us/government",                 "regulatory_doc"),
    "aisi.gov.uk":                 ("https://www.aisi.gov.uk",                                 "regulatory_doc"),
    # ── Public ─────────────────────────────────────────────────────────────────
    "deepmind.google/research":    ("https://deepmind.google/research",                        "research_paper"),
    "nvidianews":                  ("https://nvidianews.nvidia.com",                           "press_release"),
    "worklab":                     ("https://www.microsoft.com/en-us/worklab",                 "interview"),
}

# Source strings we recognise but cannot scrape with this script.
# Each tuple is (pattern, reason).
UNSUPPORTED: list[tuple[str, str]] = [
    ("podcast",              "needs transcript API"),
    ("earnings call",        "needs transcript API"),
    ("earnings calls",       "needs transcript API"),
    ("gtc keynote",          "no public URL — add transcripts manually"),
    ("stanford",             "event page, not a document archive"),
    ("stratechery",          "paywalled"),
    ("csis",                 "event page"),
    ("senate banking",       "use scrape_policy.py"),
    ("house foreign",        "use scrape_policy.py"),
    ("house committee",      "use scrape_policy.py"),
    ("congressional",        "use scrape_policy.py"),
    ("senate.gov",           "use scrape_policy.py"),
    ("congress.gov",         "use scrape_policy.py"),
    ("house judiciary",      "use scrape_policy.py"),
    ("senate testimony",     "use scrape_policy.py"),
    ("uk parliament",        "use scrape_policy.py"),
    ("ai safety summit",     "use scrape_policy.py"),
    ("cfr",                  "event org — add specific URLs manually"),
    ("linkedin.com",         "blocked — requires login"),
    ("long-form x posts",    "needs Twitter/X API"),
    ("press interviews",     "too vague — add URLs manually"),
    ("press",                "too vague — add URLs manually"),
    ("nature interview",     "paywalled"),
    ("nobel prize",          "single event — add manually"),
    ("acquired",             "needs transcript API"),
    ("lex fridman",          "needs transcript API"),
    ("dwarkesh",             "needs transcript API — add actor-specific episode URLs manually"),
    ("wsj",                  "paywalled"),
    ("bloomberg",            "paywalled"),
    ("davos",                "event page, add manually"),
    ("microsoft build",      "event page, add manually"),
    ("keynote transcript",   "event page, add manually"),
    ("policy submission",    "submit via scrape_policy.py or add manually"),
]


# ── URL / file utilities ───────────────────────────────────────────────────────

def url_to_filename(url: str) -> str:
    """12-char MD5 hex used as the JSON filename."""
    return hashlib.md5(url.encode()).hexdigest()[:12] + ".json"


def load_seen_urls(output_dir: Path) -> set[str]:
    """Return URLs already persisted to disk so we can skip them."""
    seen: set[str] = set()
    for f in output_dir.glob("*.json"):
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
            if "url" in doc:
                seen.add(doc["url"])
        except (json.JSONDecodeError, OSError):
            pass
    return seen


def save_doc(doc: dict, output_dir: Path) -> None:
    """Write one document dict to a JSON file."""
    path = output_dir / url_to_filename(doc["url"])
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


# ── HTTP helpers ───────────────────────────────────────────────────────────────

def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def fetch(session: requests.Session, url: str) -> Optional[BeautifulSoup]:
    """GET a URL and return BeautifulSoup, or None on error / 404."""
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except requests.RequestException as exc:
        print(f"    ! fetch failed: {url}  ({exc})")
        return None


# ── Content extraction ─────────────────────────────────────────────────────────

def extract_text(soup: BeautifulSoup) -> str:
    """Return main body text, stripping nav / chrome."""
    for tag in soup(["nav", "header", "footer", "script", "style",
                     "aside", "noscript", "iframe", "form"]):
        tag.decompose()

    content = (
        soup.find("article")
        or soup.find(attrs={"role": "main"})
        or soup.find("main")
        or soup.find("div", class_=re.compile(
            r"\b(post|entry|content|article|body|text)\b", re.I
        ))
        or soup.find("body")
    )
    raw = content.get_text(" ", strip=True) if content else soup.get_text(" ", strip=True)
    return re.sub(r" {2,}", " ", raw).strip()


def extract_date(soup: BeautifulSoup) -> str:
    """Best-effort date extraction; returns YYYY-MM-DD or 'unknown'."""
    from datetime import datetime, timezone

    # Posthaven blogs: data-unix-time attribute on .posthaven-formatted-date
    ph = soup.find(class_="posthaven-formatted-date", attrs={"data-unix-time": True})
    if ph:
        try:
            ts = int(ph["data-unix-time"])
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        except (ValueError, OSError):
            pass

    # <time datetime="...">
    t = soup.find("time", attrs={"datetime": True})
    if t:
        return str(t["datetime"])[:10]

    # <meta property="article:published_time"> and friends
    for prop in ("article:published_time", "datePublished", "og:updated_time",
                 "article:modified_time"):
        meta = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
        if meta and meta.get("content"):
            return str(meta["content"])[:10]

    # JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            for key in ("datePublished", "dateCreated", "dateModified"):
                if key in data:
                    return str(data[key])[:10]
        except (json.JSONDecodeError, AttributeError):
            pass

    return "unknown"


# ── Post-link collector ────────────────────────────────────────────────────────

# URL path segments that indicate a listing / nav page, not a post.
_NAV_PATTERN = re.compile(
    r"/(tag|category|author|feed|rss|page|wp-content|cdn|search|about|contact"
    r"|signin|login|register|subscribe|privacy|terms|archive)(/|$)",
    re.I,
)
_SKIP_EXTENSIONS = re.compile(r"\.(atom|rss|xml|pdf|zip|png|jpg|jpeg|gif|css|js)$", re.I)


def _normalise_url(url: str) -> str:
    """Canonicalise to https and strip trailing slash."""
    url = re.sub(r"^http://", "https://", url)
    return url.rstrip("/")


def _origin(url: str) -> str:
    """Return scheme + host (e.g. https://deepmind.google) from any URL."""
    m = re.match(r"(https?://[^/]+)", url)
    return m.group(1) if m else url


def _extract_post_links(soup: BeautifulSoup, base_url: str, domain: str) -> set[str]:
    """Pull candidate post URLs out of a listing page."""
    origin = _origin(base_url)
    links: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = str(a["href"]).strip().split("?")[0].split("#")[0]
        if href.startswith("/"):
            href = origin + href  # use scheme+host, not full listing URL
        href = _normalise_url(href)
        # Keep only same-domain links that look like posts
        if domain not in href:
            continue
        if href in (_normalise_url(base_url), _normalise_url(base_url) + "/"):
            continue
        if _NAV_PATTERN.search(href):
            continue
        if _SKIP_EXTENSIONS.search(href):
            continue
        links.add(href)
    return links


def collect_post_links(
    session: requests.Session,
    base_url: str,
    want: int,
) -> list[str]:
    """
    Crawl paginated blog listings and return candidate post URLs.
    Tries /page/N and ?page=N patterns; stops when pages are exhausted.
    Returns up to want * 3 candidates (caller filters to final limit).
    """
    domain = re.sub(r"https?://", "", base_url).split("/")[0]
    found: set[str] = set()

    soup = fetch(session, base_url)
    if soup:
        found.update(_extract_post_links(soup, base_url, domain))

    page = 2
    no_new = 0
    while len(found) < want * 3 and no_new < 3:
        time.sleep(DELAY)
        page_soup = None
        for page_url in (f"{base_url}/page/{page}", f"{base_url}?page={page}"):
            page_soup = fetch(session, page_url)
            if page_soup:
                break

        if page_soup is None:
            no_new += 1
        else:
            new = _extract_post_links(page_soup, base_url, domain) - found
            if new:
                found.update(new)
                no_new = 0
            else:
                no_new += 1
        page += 1

    return list(found)


# ── Source resolution ──────────────────────────────────────────────────────────

def resolve_source(source: str) -> Optional[tuple[str, str]]:
    """
    Map a source string from config to (base_url, platform).
    Returns None if the source is recognised but not URL-scrapable.
    """
    src_lower = source.lower()
    for pattern, (url, platform) in SOURCE_REGISTRY.items():
        if pattern.lower() in src_lower:
            return url, platform
    return None


def unsupported_reason(source: str) -> Optional[str]:
    """Return the skip reason if this source is explicitly unsupported."""
    src_lower = source.lower()
    for pattern, reason in UNSUPPORTED:
        if pattern in src_lower:
            return reason
    return None


# ── Core scraping loop ─────────────────────────────────────────────────────────

def scrape_source(
    session: requests.Session,
    base_url: str,
    platform: str,
    actor: str,
    context: str,
    limit: int,
    seen_urls: set[str],
) -> tuple[list[dict], int]:
    """
    Scrape up to `limit` new docs from `base_url`.
    Returns (new_docs, n_duplicates_skipped).
    """
    print(f"    Collecting links from {base_url} …")
    candidates = collect_post_links(session, base_url, limit)
    print(f"    Found {len(candidates)} candidate URLs")

    docs: list[dict] = []
    skipped = 0

    for url in candidates:
        if len(docs) >= limit:
            break
        if url in seen_urls:
            skipped += 1
            continue

        time.sleep(DELAY)
        soup = fetch(session, url)
        if soup is None:
            continue

        text = extract_text(soup)
        if len(text) < MIN_TEXT_LEN:
            continue

        doc = {
            "url": url,
            "date": extract_date(soup),
            "text": text,
            "actor": actor,
            "context": context,
            "platform": platform,
        }
        docs.append(doc)
        seen_urls.add(url)

    return docs, skipped


# ── Wayback Machine CDX ────────────────────────────────────────────────────────

CDX_API = "http://web.archive.org/cdx/search/cdx"
SOURCE_TIMEOUT = 240  # seconds per source block

# actor_name → list of (url_pattern, from_ts, to_ts, context, platform)
WAYBACK_CONFIG_INDIVIDUALS: dict[str, list[tuple[str, str, str, str, str]]] = {
    "Sam Altman": [
        ("judiciary.senate.gov/hearings/*",  "20220101", "", "policy", "testimony"),
        ("commerce.senate.gov/hearings/*",   "20220101", "", "policy", "testimony"),
    ],
    "Dario Amodei": [
        ("judiciary.senate.gov/hearings/*",  "20220101", "", "policy", "testimony"),
        ("commerce.senate.gov/hearings/*",   "20220101", "", "policy", "testimony"),
    ],
    "Mark Zuckerberg": [
        ("judiciary.senate.gov/hearings/*",  "20220101", "", "policy", "testimony"),
        ("commerce.senate.gov/hearings/*",   "20220101", "", "policy", "testimony"),
        ("judiciary.house.gov/hearings/*",   "20220101", "", "policy", "testimony"),
    ],
    "Jensen Huang": [
        ("banking.senate.gov/hearings/*",    "20220101", "", "policy", "testimony"),
        ("csis.org/events/*",               "20220101", "", "policy", "speech"),
    ],
    "Demis Hassabis": [
        ("committees.parliament.uk/oralevidence/*", "20220101", "", "policy", "testimony"),
        ("csis.org/events/*",                       "20220101", "", "policy", "speech"),
    ],
    "Satya Nadella": [
        ("judiciary.senate.gov/hearings/*",  "20220101", "", "policy", "testimony"),
        ("commerce.senate.gov/hearings/*",   "20220101", "", "policy", "testimony"),
    ],
}

# Keyword allowlists: skip a Wayback doc if none of the actor's keywords appear in text.
WAYBACK_KEYWORD_INDIVIDUALS: dict[str, list[str]] = {
    "Sam Altman":      ["sam altman", "openai"],
    "Dario Amodei":    ["dario amodei", "amodei", "anthropic"],
    "Mark Zuckerberg": ["zuckerberg", "mark zuckerberg"],
    "Jensen Huang":    ["jensen huang", "nvidia"],
    "Demis Hassabis":  ["demis hassabis", "hassabis", "deepmind"],
    "Satya Nadella":   ["satya nadella", "nadella", "microsoft"],
}


def cdx_query(
    session: requests.Session,
    url_pattern: str,
    from_ts: str = "",
    to_ts: str = "",
    limit: int = 500,
) -> list[tuple[str, str]]:
    """Query Wayback CDX. Returns (original_url, timestamp) pairs, deduped by urlkey."""
    params = [
        ("url",      url_pattern),
        ("output",   "json"),
        ("fl",       "original,timestamp"),
        ("filter",   "statuscode:200"),
        ("collapse", "urlkey"),
        ("limit",    str(limit)),
    ]
    if from_ts:
        params.append(("from", from_ts))
    if to_ts:
        params.append(("to", to_ts))
    try:
        resp = session.get(CDX_API, params=params, timeout=30)
        resp.raise_for_status()
        rows = resp.json()
    except Exception as exc:
        print(f"  ! CDX query failed for {url_pattern}: {exc}")
        return []
    if not rows or rows[0] == ["original", "timestamp"]:
        rows = rows[1:]
    return [(r[0], r[1]) for r in rows if len(r) == 2]


def fetch_wayback(
    session: requests.Session, original_url: str, timestamp: str
) -> Optional[BeautifulSoup]:
    """Fetch a Wayback snapshot; returns BeautifulSoup or None."""
    wb_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
    return fetch(session, wb_url)


def parse_wayback_date(timestamp: str) -> str:
    """Convert YYYYMMDDHHMMSS → YYYY-MM-DD."""
    if len(timestamp) >= 8:
        return f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}"
    return "unknown"


def run_wayback_individuals(
    session: requests.Session,
    actor_name: str,
    actor_cfg: dict,
    limit: int,
    context_filter: Optional[str],
) -> dict[str, int]:
    """Scrape an individual actor's blocked policy sources via Wayback CDX.
    Returns {context: n_saved}."""
    entries = WAYBACK_CONFIG_INDIVIDUALS.get(actor_name, [])
    if not entries:
        print(f"No Wayback config for '{actor_name}'")
        return {}

    if context_filter:
        entries = [e for e in entries if e[3] == context_filter]

    keywords = WAYBACK_KEYWORD_INDIVIDUALS.get(actor_name)
    output_dir = DATA_RAW / actor_cfg["raw_subdir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    seen_urls = load_seen_urls(output_dir)

    totals: dict[str, int] = {}

    for url_pattern, from_ts, to_ts, context, platform in entries:
        print(f"\n── WAYBACK  {url_pattern}  {from_ts}–{to_ts}  ctx={context}  "
              f"(seen: {len(seen_urls)}) ──")
        captures = cdx_query(session, url_pattern, from_ts, to_ts, limit=limit * 3)
        print(f"  CDX returned {len(captures)} captures")

        saved = 0
        skipped = 0
        t0 = time.monotonic()

        for original_url, timestamp in captures:
            if saved >= limit:
                break
            if time.monotonic() - t0 > SOURCE_TIMEOUT:
                print(f"  ! timeout ({SOURCE_TIMEOUT}s) — stopping")
                break
            if original_url in seen_urls:
                skipped += 1
                continue
            time.sleep(DELAY)
            soup = fetch_wayback(session, original_url, timestamp)
            if soup is None:
                continue
            text = extract_text(soup)
            if len(text) < MIN_TEXT_LEN:
                continue
            if keywords and not any(kw in text.lower() for kw in keywords):
                continue
            doc = {
                "url":      original_url,
                "date":     parse_wayback_date(timestamp),
                "text":     text,
                "actor":    actor_name,
                "context":  context,
                "platform": platform,
            }
            save_doc(doc, output_dir)
            seen_urls.add(original_url)
            saved += 1

        total_on_disk = len(list(output_dir.glob("*.json")))
        print(f"  saved {saved}  |  skipped {skipped}  |  total on disk {total_on_disk}")
        totals[context] = totals.get(context, 0) + saved

    return totals


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Scrape documents for an individual actor from their configured sources."
    )
    p.add_argument(
        "--actor",
        required=True,
        help='Exact actor name from ACTORS dict, e.g. "Sam Altman"',
    )
    p.add_argument(
        "--context",
        choices=["commercial", "policy", "public"],
        default=None,
        help="Context to scrape (required in standard mode; optional filter with --wayback)",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=400,
        help="Maximum total documents to collect (default: 400)",
    )
    p.add_argument(
        "--wayback",
        action="store_true",
        help="Scrape via Wayback Machine CDX (for blocked policy sources)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if args.actor not in ACTORS:
        valid = [k for k, v in ACTORS.items() if v["type"] == "individual"]
        print(f"Error: '{args.actor}' not in ACTORS. Valid individual actors:")
        for name in valid:
            print(f"  {name}")
        sys.exit(1)

    actor_cfg = ACTORS[args.actor]
    if actor_cfg["type"] != "individual":
        print(f"Error: '{args.actor}' is not an individual actor (type={actor_cfg['type']}).")
        sys.exit(1)

    session = make_session()

    # ── Wayback mode ───────────────────────────────────────────────────────────
    if args.wayback:
        print(f"\n{'='*55}")
        print(f"Actor:   {args.actor}  |  WAYBACK CDX  |  limit {args.limit}")
        print(f"{'='*55}")
        totals = run_wayback_individuals(session, args.actor, actor_cfg, args.limit, args.context)
        grand_total = sum(totals.values())
        print(f"\n{'─'*55}")
        print(f"  {args.actor} — WAYBACK DONE")
        print(f"{'─'*55}")
        for ctx, n in totals.items():
            target = actor_cfg["contexts"].get(ctx, 0)
            pct = n / target * 100 if target else 0
            print(f"  {ctx:<12} {n:>4} / {target:<4}  ({pct:.0f}%)")
        print(f"  {'TOTAL':<12} {grand_total:>4}")
        print(f"{'─'*55}\n")
        return

    # ── Standard mode ──────────────────────────────────────────────────────────
    if args.context is None:
        print("Error: --context is required in standard mode (omit only with --wayback)")
        sys.exit(1)

    sources: list[str] = actor_cfg["sources"].get(args.context, [])
    if not sources:
        print(f"No sources configured for {args.actor} / {args.context}.")
        sys.exit(0)

    output_dir: Path = DATA_RAW / actor_cfg["raw_subdir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    seen_urls = load_seen_urls(output_dir)
    pre_existing = len(seen_urls)

    print(f"\n{'='*55}")
    print(f"Actor:   {args.actor}")
    print(f"Context: {args.context}  |  Limit: {args.limit}")
    print(f"Output:  {output_dir}")
    print(f"Pre-existing docs: {pre_existing}")
    print(f"{'='*55}\n")

    total_saved = 0
    total_skipped = 0

    for source in sources:
        remaining = args.limit - total_saved
        if remaining <= 0:
            break

        resolved = resolve_source(source)
        if resolved is None:
            reason = unsupported_reason(source) or "no URL mapping — add to SOURCE_REGISTRY"
            print(f"  SKIP  '{source}'  →  {reason}")
            continue

        base_url, platform = resolved
        print(f"  SOURCE  '{source}'  →  {base_url}  [{platform}]")

        new_docs, skipped = scrape_source(
            session,
            base_url,
            platform,
            actor=args.actor,
            context=args.context,
            limit=remaining,
            seen_urls=seen_urls,
        )

        for doc in new_docs:
            save_doc(doc, output_dir)

        total_saved += len(new_docs)
        total_skipped += skipped
        print(f"    → saved {len(new_docs)}  |  duplicates skipped {skipped}\n")

    total_on_disk = len(list(output_dir.glob("*.json")))
    print(f"{'─'*55}")
    print(f"Saved this run : {total_saved}")
    print(f"Duplicates skip: {total_skipped}")
    print(f"Total on disk  : {total_on_disk}  (in {output_dir})")
    print(f"{'─'*55}")


if __name__ == "__main__":
    main()
