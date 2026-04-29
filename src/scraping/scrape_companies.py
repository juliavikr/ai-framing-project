"""
scrape_companies.py — Scrapes all contexts for company actors.

Saves one JSON per document to data/raw/companies/{subdir}/{context}/ with fields:
    url, date, text, actor, context, platform

Usage:
    python src/scraping/scrape_companies.py --actor openai
    python src/scraping/scrape_companies.py --actor anthropic --limit 400
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
from src.config import ACTORS, CONTEXTS, DATA_RAW

# ── Constants ──────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
DELAY = 1
MIN_TEXT_LEN = 200
SOURCE_TIMEOUT = 180  # seconds; skip a source that takes longer than this

# Slug → ACTORS key (so CLI is lowercase-friendly)
SLUG_MAP: dict[str, str] = {
    "openai":          "OpenAI",
    "anthropic":       "Anthropic",
    "google_deepmind": "Google DeepMind",
    "meta_ai":         "Meta AI",
    "microsoft":       "Microsoft",
    "nvidia":          "Nvidia",
}

# Fragment that can appear in a config source string → (base_url, platform).
# More-specific (longer) patterns must come BEFORE shorter patterns that share a prefix
# so that the first-match wins correctly.
SOURCE_REGISTRY: dict[str, tuple[str, str]] = {
    # ── OpenAI ─────────────────────────────────────────────────────────────────
    "openai.com/government":     ("https://openai.com/government",      "regulatory_doc"),
    "openai.com/research":       ("https://openai.com/research",        "research_paper"),
    "openai.com/blog":           ("https://openai.com/blog",            "blog"),
    "openai.com/news":           ("https://openai.com/news",            "press_release"),
    # ── Anthropic ──────────────────────────────────────────────────────────────
    "anthropic.com/research":    ("https://www.anthropic.com/research", "research_paper"),
    "anthropic.com/policy":      ("https://www.anthropic.com/policy",   "regulatory_doc"),
    "anthropic.com/news":        ("https://www.anthropic.com/news",     "press_release"),
    # ── Google DeepMind ────────────────────────────────────────────────────────
    "deepmind.google/research":  ("https://deepmind.google/research",   "research_paper"),
    "deepmind.google/blog":      ("https://deepmind.google/blog",       "blog"),
    # ── Meta AI ────────────────────────────────────────────────────────────────
    "about.fb.com/tag":          ("https://about.fb.com/tag/artificial-intelligence", "blog"),
    "about.fb.com/policy":       ("https://about.fb.com/news",          "regulatory_doc"),
    "about.fb.com/news":         ("https://about.fb.com/news",          "press_release"),
    "ai.meta.com/blog":          ("https://ai.meta.com/blog",           "blog"),
    # ── Microsoft ──────────────────────────────────────────────────────────────
    "microsoft.com/responsible-ai": ("https://blogs.microsoft.com/on-the-issues", "regulatory_doc"),
    "blogs.microsoft.com/on-the-issues": ("https://blogs.microsoft.com/on-the-issues", "regulatory_doc"),
    "microsoft.com/en-us/research": ("https://www.microsoft.com/en-us/research/blog", "blog"),
    "blogs.microsoft.com/ai":    ("https://blogs.microsoft.com/ai",     "blog"),
    # ── Nvidia ─────────────────────────────────────────────────────────────────
    "nvidia.com/en-us/government": ("https://www.nvidia.com/en-us/government",  "regulatory_doc"),
    "nvidia.com/en-us/newsroom":   ("https://www.nvidia.com/en-us/newsroom",    "press_release"),
    "nvidia.com/en-us/research":   ("https://www.nvidia.com/en-us/research",    "research_paper"),
    "nvidianews.nvidia.com":       ("https://nvidianews.nvidia.com",            "press_release"),
    "blogs.nvidia.com":            ("https://blogs.nvidia.com",                 "blog"),
}

UNSUPPORTED: list[tuple[str, str]] = [
    ("regulatory submissions", "formal submissions — add URLs manually"),
    ("press releases",         "too vague — specify URL or use company news page"),
    ("research announcements", "too vague — add URLs manually"),
    ("ai principles",          "landing page — add specific doc URLs manually"),
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

    ph = soup.find(class_="posthaven-formatted-date", attrs={"data-unix-time": True})
    if ph:
        try:
            ts = int(ph["data-unix-time"])
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        except (ValueError, OSError):
            pass

    t = soup.find("time", attrs={"datetime": True})
    if t:
        return str(t["datetime"])[:10]

    for prop in ("article:published_time", "datePublished", "og:updated_time",
                 "article:modified_time"):
        meta = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
        if meta and meta.get("content"):
            return str(meta["content"])[:10]

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

_NAV_PATTERN = re.compile(
    r"/(tag|category|author|feed|rss|page|wp-content|cdn|search|about|contact"
    r"|signin|login|register|subscribe|privacy|terms|archive)(/|$)",
    re.I,
)
_SKIP_EXTENSIONS = re.compile(r"\.(atom|rss|xml|pdf|zip|png|jpg|jpeg|gif|css|js)$", re.I)


def _normalise_url(url: str) -> str:
    url = re.sub(r"^http://", "https://", url)
    return url.rstrip("/")


def _origin(url: str) -> str:
    """Return scheme + host only (e.g. https://deepmind.google)."""
    m = re.match(r"(https?://[^/]+)", url)
    return m.group(1) if m else url


def _extract_post_links(soup: BeautifulSoup, base_url: str, domain: str) -> set[str]:
    origin = _origin(base_url)
    links: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = str(a["href"]).strip().split("?")[0].split("#")[0]
        if href.startswith("/"):
            href = origin + href
        href = _normalise_url(href)
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
    session: requests.Session, base_url: str, want: int, max_pages: int = 25
) -> list[str]:
    """Crawl paginated blog listings; returns up to want*3 candidate post URLs."""
    domain = re.sub(r"https?://", "", base_url).split("/")[0]
    found: set[str] = set()

    soup = fetch(session, base_url)
    if soup:
        found.update(_extract_post_links(soup, base_url, domain))

    page = 2
    no_new = 0
    while len(found) < want * 3 and no_new < 3 and page <= max_pages:
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

    if page > max_pages:
        print(f"    [max_pages={max_pages} reached; stopping pagination]")

    return list(found)


# ── Source resolution ──────────────────────────────────────────────────────────

def resolve_source(source: str) -> Optional[tuple[str, str]]:
    """Map a config source string to (base_url, platform) or None."""
    src_lower = source.lower()
    for pattern, (url, platform) in SOURCE_REGISTRY.items():
        if pattern.lower() in src_lower:
            return url, platform
    return None


def unsupported_reason(source: str) -> Optional[str]:
    """Return skip reason if this source is explicitly unsupported."""
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
    """Scrape up to `limit` new docs from `base_url`. Returns (new_docs, n_skipped)."""
    print(f"    Collecting links from {base_url} …")
    candidates = collect_post_links(session, base_url, limit)
    print(f"    Found {len(candidates)} candidate URLs")

    # Timer starts after link-collection (already bounded by max_pages).
    t0 = time.monotonic()
    docs: list[dict] = []
    skipped = 0

    for url in candidates:
        if len(docs) >= limit:
            break
        if time.monotonic() - t0 > SOURCE_TIMEOUT:
            print(f"    ! source timeout ({SOURCE_TIMEOUT}s) — moving to next source")
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
            "url":      url,
            "date":     extract_date(soup),
            "text":     text,
            "actor":    actor,
            "context":  context,
            "platform": platform,
        }
        docs.append(doc)
        seen_urls.add(url)

    return docs, skipped


# ── Sitemap fallback for JS-rendered listing pages ─────────────────────────────

# For sites where the listing page is JS-rendered (0 links found by the generic
# crawler), we fall back to fetching the sitemap and filtering by URL path.
SITEMAP_FALLBACKS: dict[str, tuple[str, str]] = {
    # base_url → (sitemap_url, path_filter)
    "https://www.anthropic.com/policy":   ("https://www.anthropic.com/sitemap.xml", "/policy"),
    "https://www.anthropic.com/news":     ("https://www.anthropic.com/sitemap.xml", "/news"),
    "https://www.anthropic.com/research": ("https://www.anthropic.com/sitemap.xml", "/research"),
    "https://openai.com/blog":            ("https://openai.com/sitemap.xml",        "/blog"),
    "https://openai.com/research":        ("https://openai.com/sitemap.xml",        "/research"),
    "https://openai.com/news":            ("https://openai.com/sitemap.xml",        "/news"),
    "https://openai.com/government":      ("https://openai.com/sitemap.xml",        "/government"),
}


def collect_via_sitemap(session: requests.Session, sitemap_url: str, path_filter: str) -> list[str]:
    """Fetch a sitemap XML and return all <loc> URLs that contain path_filter."""
    try:
        resp = session.get(sitemap_url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"    ! sitemap fetch failed: {sitemap_url}  ({exc})")
        return []
    urls = re.findall(r"<loc>([^<]+)</loc>", resp.text)
    filtered = [u for u in urls if path_filter in u]
    print(f"    Sitemap: {len(urls)} total URLs → {len(filtered)} matching '{path_filter}'")
    return filtered


def scrape_source_with_fallback(
    session: requests.Session,
    base_url: str,
    platform: str,
    actor: str,
    context: str,
    limit: int,
    seen_urls: set[str],
) -> tuple[list[dict], int]:
    """
    Like scrape_source, but if 0 candidates are found and a sitemap fallback
    exists for this URL, retries via sitemap URL enumeration.
    """
    docs, skipped = scrape_source(session, base_url, platform, actor, context, limit, seen_urls)

    # Sitemap fallback when link-collector found nothing
    if not docs and base_url in SITEMAP_FALLBACKS:
        sitemap_url, path_filter = SITEMAP_FALLBACKS[base_url]
        print(f"    → 0 from link-collector; trying sitemap fallback …")
        candidates = collect_via_sitemap(session, sitemap_url, path_filter)
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
                "url":      url,
                "date":     extract_date(soup),
                "text":     text,
                "actor":    actor,
                "context":  context,
                "platform": platform,
            }
            docs.append(doc)
            seen_urls.add(url)

    return docs, skipped


# ── Sitemap-only scrape (bypasses JS listing pages) ───────────────────────────

# Maps actor slug → list of (sitemap_url, path_filter, context, platform)
SITEMAP_ONLY_CONFIG: dict[str, list[tuple[str, str, str, str]]] = {
    "anthropic": [
        ("https://www.anthropic.com/sitemap.xml", "/news",     "commercial", "press_release"),
        ("https://www.anthropic.com/sitemap.xml", "/research", "commercial", "research_paper"),
    ],
}


def run_sitemap_only(
    session: requests.Session,
    actor_name: str,
    actor_cfg: dict,
    slug: str,
    context_filter: Optional[str],
    limit: int,
) -> dict[str, int]:
    """
    Fetch sitemaps directly, skip JS listing pages entirely.
    Returns {context: n_saved}.
    """
    entries = SITEMAP_ONLY_CONFIG.get(slug, [])
    if not entries:
        print(f"No sitemap-only config for '{slug}'")
        return {}

    if context_filter:
        entries = [(s, p, c, pl) for s, p, c, pl in entries if c == context_filter]

    totals: dict[str, int] = {}

    for sitemap_url, path_filter, context, platform in entries:
        output_dir = DATA_RAW / actor_cfg["raw_subdir"] / context
        output_dir.mkdir(parents=True, exist_ok=True)
        seen_urls = load_seen_urls(output_dir)
        pre_existing = len(seen_urls)

        print(f"\n── SITEMAP  {sitemap_url}  filter={path_filter}  ctx={context}  (pre-existing: {pre_existing}) ──")
        candidates = collect_via_sitemap(session, sitemap_url, path_filter)

        saved = 0
        skipped = 0
        t0 = time.monotonic()

        for url in candidates:
            if saved >= limit:
                break
            if time.monotonic() - t0 > SOURCE_TIMEOUT:
                print(f"  ! timeout ({SOURCE_TIMEOUT}s) — stopping")
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
                "url":      url,
                "date":     extract_date(soup),
                "text":     text,
                "actor":    actor_name,
                "context":  context,
                "platform": platform,
            }
            save_doc(doc, output_dir)
            seen_urls.add(url)
            saved += 1

        total_on_disk = len(list(output_dir.glob("*.json")))
        print(f"  saved {saved}  |  skipped {skipped}  |  total on disk {total_on_disk}")
        totals[context] = totals.get(context, 0) + saved

    return totals


# ── Wayback Machine CDX scraper ────────────────────────────────────────────────

CDX_API = "http://web.archive.org/cdx/search/cdx"

# Maps actor slug → list of (url_pattern, context, platform)
WAYBACK_CONFIG: dict[str, list[tuple[str, str, str]]] = {
    "openai": [
        ("openai.com/blog/*",            "commercial", "blog"),
        ("openai.com/research/*",        "commercial", "research_paper"),
        ("openai.com/index/gpt*",        "commercial", "blog"),
        ("openai.com/index/dall*",       "commercial", "blog"),
        ("openai.com/index/chatgpt*",    "commercial", "blog"),
        ("openai.com/index/introducing*", "commercial", "blog"),
        ("openai.com/index/openai*",     "commercial", "press_release"),
        ("openai.com/index/*",           "policy",     "regulatory_doc"),
        ("openai.com/news/*",            "public",     "press_release"),
    ],
}


def cdx_query(session: requests.Session, url_pattern: str, limit: int = 500) -> list[tuple[str, str]]:
    """
    Query Wayback CDX API.
    Returns list of (original_url, timestamp) for status-200 captures,
    deduplicated by URL key (one capture per unique URL).
    """
    params = {
        "url":      url_pattern,
        "output":   "json",
        "fl":       "original,timestamp",
        "filter":   "statuscode:200",
        "collapse": "urlkey",
        "limit":    str(limit),
    }
    try:
        resp = session.get(CDX_API, params=params, timeout=30)
        resp.raise_for_status()
        rows = resp.json()
    except Exception as exc:
        print(f"  ! CDX query failed for {url_pattern}: {exc}")
        return []

    # First row is the header ["original","timestamp"]
    if not rows or rows[0] == ["original", "timestamp"]:
        rows = rows[1:]
    return [(r[0], r[1]) for r in rows if len(r) == 2]


def fetch_wayback(session: requests.Session, original_url: str, timestamp: str) -> Optional[BeautifulSoup]:
    """Fetch a Wayback snapshot; returns BeautifulSoup or None."""
    wb_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
    return fetch(session, wb_url)


def parse_wayback_date(timestamp: str) -> str:
    """Convert YYYYMMDDHHMMSS → YYYY-MM-DD."""
    if len(timestamp) >= 8:
        return f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}"
    return "unknown"


def run_wayback(
    session: requests.Session,
    actor_name: str,
    actor_cfg: dict,
    slug: str,
    context_filter: Optional[str],
    limit: int,
) -> dict[str, int]:
    """
    Scrape OpenAI (or any Wayback-configured actor) via CDX API.
    Returns {context: n_saved}.
    """
    entries = WAYBACK_CONFIG.get(slug, [])
    if not entries:
        print(f"No Wayback config for '{slug}'")
        return {}

    if context_filter:
        entries = [(p, c, pl) for p, c, pl in entries if c == context_filter]

    totals: dict[str, int] = {}

    for url_pattern, context, platform in entries:
        output_dir = DATA_RAW / actor_cfg["raw_subdir"] / context
        output_dir.mkdir(parents=True, exist_ok=True)
        seen_urls = load_seen_urls(output_dir)
        pre_existing = len(seen_urls)

        print(f"\n── WAYBACK  {url_pattern}  ctx={context}  (pre-existing: {pre_existing}) ──")
        captures = cdx_query(session, url_pattern, limit=max(limit * 3, 1000))
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
            word_count = len(text.split())
            if word_count < 300:
                continue
            date = parse_wayback_date(timestamp)
            doc = {
                "url":      original_url,
                "date":     date,
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
        description="Scrape all contexts for a company actor."
    )
    p.add_argument(
        "--actor",
        required=True,
        choices=list(SLUG_MAP.keys()),
        help="Company slug: openai | anthropic | google_deepmind | meta_ai | microsoft | nvidia",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Max docs per context (default: 500)",
    )
    p.add_argument(
        "--context",
        choices=["commercial", "policy", "public"],
        default=None,
        help="Restrict to a single context (default: all)",
    )
    p.add_argument(
        "--sitemap-only",
        action="store_true",
        help="Bypass JS listing pages; fetch URLs direct from sitemap",
    )
    p.add_argument(
        "--wayback",
        action="store_true",
        help="Scrape via Wayback Machine CDX API (for blocked sites like OpenAI)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    actor_name = SLUG_MAP[args.actor]
    actor_cfg  = ACTORS[actor_name]

    if actor_cfg["type"] != "company":
        print(f"Error: '{actor_name}' is not a company actor.")
        sys.exit(1)

    session = make_session()

    # ── Special modes ──────────────────────────────────────────────────────────
    if args.sitemap_only:
        print(f"\n{'='*60}")
        print(f"Company: {actor_name}  |  SITEMAP-ONLY  |  limit {args.limit}")
        print(f"{'='*60}")
        run_sitemap_only(session, actor_name, actor_cfg, args.actor, args.context, args.limit)
        return

    if args.wayback:
        print(f"\n{'='*60}")
        print(f"Company: {actor_name}  |  WAYBACK CDX  |  limit {args.limit}")
        print(f"{'='*60}")
        run_wayback(session, actor_name, actor_cfg, args.actor, args.context, args.limit)
        return

    # ── Standard mode ──────────────────────────────────────────────────────────
    contexts_to_run = [args.context] if args.context else list(CONTEXTS)

    print(f"\n{'='*60}")
    print(f"Company: {actor_name}  |  limit {args.limit}/context")
    print(f"{'='*60}")

    context_totals: dict[str, int] = {}

    for context in contexts_to_run:
        sources: list[str] = actor_cfg["sources"].get(context, [])
        if not sources:
            context_totals[context] = 0
            continue

        output_dir = DATA_RAW / actor_cfg["raw_subdir"] / context
        output_dir.mkdir(parents=True, exist_ok=True)
        seen_urls = load_seen_urls(output_dir)
        pre_existing = len(seen_urls)

        print(f"\n── {context.upper()}  (pre-existing: {pre_existing}) ──")

        ctx_saved = 0
        ctx_skipped = 0

        for source in sources:
            remaining = args.limit - ctx_saved
            if remaining <= 0:
                break

            resolved = resolve_source(source)
            if resolved is None:
                reason = unsupported_reason(source) or "no URL mapping — add to SOURCE_REGISTRY"
                print(f"  SKIP  '{source}'  →  {reason}")
                continue

            base_url, platform = resolved
            print(f"  SOURCE  '{source}'  →  {base_url}  [{platform}]")

            new_docs, skipped = scrape_source_with_fallback(
                session, base_url, platform,
                actor=actor_name, context=context,
                limit=remaining, seen_urls=seen_urls,
            )

            for doc in new_docs:
                save_doc(doc, output_dir)

            ctx_saved   += len(new_docs)
            ctx_skipped += skipped
            print(f"    → saved {len(new_docs)}  |  duplicates skipped {skipped}")

        context_totals[context] = ctx_saved
        total_on_disk = len(list(output_dir.glob("*.json")))
        print(f"  ── {context}: saved {ctx_saved}, total on disk {total_on_disk}")

    # ── Summary ────────────────────────────────────────────────────────────────
    grand_total = sum(context_totals.values())
    print(f"\n{'─'*60}")
    print(f"  {actor_name} — DONE")
    print(f"{'─'*60}")
    for ctx, n in context_totals.items():
        target = actor_cfg["contexts"].get(ctx, 0)
        pct = n / target * 100 if target else 0
        print(f"  {ctx:<12} {n:>4} / {target:<4}  ({pct:.0f}%)")
    print(f"  {'TOTAL':<12} {grand_total:>4} / {actor_cfg['target']:<4}")
    print(f"{'─'*60}\n")


if __name__ == "__main__":
    main()
