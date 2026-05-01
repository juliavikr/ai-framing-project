"""
scrape_newsapi.py — Collect public-context documents via NewsAPI and podcast archives.

Two complementary approaches:

  1. NewsAPI  — query news articles where each actor is quoted/featured in mass
               media (interviews, announcements, op-eds). Requires NEWS_API_KEY
               in .env. Paid Developer tier recommended for full date range;
               free tier only covers the last 30 days.

  2. Podcasts — scrape full HTML transcript pages from Lex Fridman
               (lexfridman.com) and Dwarkesh Patel (dwarkeshpatel.com);
               keep only episodes whose title mentions the actor. Individual
               actors only. No API key required.

All output is saved to data/raw/{actor_raw_subdir}/ with context=public, in the
same one-JSON-per-document format as the other scrapers.

Usage:
    python src/scraping/scrape_newsapi.py --actor "Sam Altman" --limit 150
    python src/scraping/scrape_newsapi.py --all --limit 100
    python src/scraping/scrape_newsapi.py --actor "Dario Amodei" --from-date 2022-01-01
    python src/scraping/scrape_newsapi.py --all --podcasts-only
    python src/scraping/scrape_newsapi.py --all --news-only
"""

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import date
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import ACTORS, DATA_RAW, NEWS_API_KEY

# ── Constants ──────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
DELAY = 1.5           # seconds between HTTP requests
MIN_TEXT_LEN = 300    # discard pages shorter than this
NEWSAPI_URL = "https://newsapi.org/v2/everything"

# Domains that paywall or heavily truncate content — skip URL fetch
PAYWALL_DOMAINS = frozenset({
    "wsj.com", "ft.com", "economist.com", "bloomberg.com",
    "thetimes.co.uk", "telegraph.co.uk", "hbr.org",
    "theathletic.com", "newyorker.com",
})

# Actors' own domains — content here is commercial/policy, not public
ACTOR_OWNED_DOMAINS = frozenset({
    "openai.com", "anthropic.com", "deepmind.google",
    "ai.meta.com", "about.fb.com", "blogs.microsoft.com",
    "microsoft.com", "nvidia.com", "blogs.nvidia.com",
    "nvidianews.nvidia.com", "blog.samaltman.com", "darioamodei.com",
})

# ── Per-actor NewsAPI search queries ──────────────────────────────────────────
# Queries are tuned to surface public media appearances (interviews, keynotes,
# op-eds) rather than product announcements or internal communications.

ACTOR_QUERIES: dict[str, str] = {
    "Sam Altman":
        '"Sam Altman" AND (AI OR "artificial intelligence" OR OpenAI)',
    "Dario Amodei":
        '"Dario Amodei" AND (AI OR "artificial intelligence" OR Anthropic)',
    "Jensen Huang":
        '"Jensen Huang" AND (AI OR "artificial intelligence" OR Nvidia)',
    "Satya Nadella":
        '"Satya Nadella" AND (AI OR "artificial intelligence" OR Microsoft)',
    "Mark Zuckerberg":
        '"Mark Zuckerberg" AND (AI OR "artificial intelligence" OR Meta)',
    "Demis Hassabis":
        '"Demis Hassabis" AND (AI OR "artificial intelligence" OR DeepMind)',
    "OpenAI":
        'OpenAI AND ("artificial intelligence" OR ChatGPT OR "language model")',
    "Anthropic":
        'Anthropic AND (Claude OR "language model" OR "AI safety")',
    "Google DeepMind":
        '("Google DeepMind" OR DeepMind) AND ("artificial intelligence" OR Gemini OR AlphaFold)',
    "Meta AI":
        '"Meta AI" AND ("artificial intelligence" OR LLaMA OR Llama)',
    "Microsoft":
        'Microsoft AND ("artificial intelligence" OR Copilot OR "AI model" OR "Azure AI")',
    "Nvidia":
        'Nvidia AND ("artificial intelligence" OR GPU OR "AI chip" OR "data center")',
    "EU Commission":
        '("European Commission" OR "EU Commission") AND ("artificial intelligence" OR "AI Act" OR "AI regulation")',
    "US Congress":
        '(Senate OR Congress OR "House of Representatives") AND ("artificial intelligence" OR "AI legislation")',
    "UK DSIT":
        '("DSIT" OR "AI Safety Institute" OR "AISI") AND ("artificial intelligence" OR "AI regulation")',
    "White House OSTP":
        '("White House" OR OSTP) AND ("artificial intelligence" OR "AI executive order" OR "AI policy")',
}

# Name variants used for the relevance check (actor name must appear in article text).
# Keys are ACTORS dict keys; values are lowercase strings to look for.
ACTOR_NAME_VARIANTS: dict[str, list[str]] = {
    "Sam Altman":       ["sam altman"],
    "Dario Amodei":     ["dario amodei"],
    "Jensen Huang":     ["jensen huang"],
    "Satya Nadella":    ["satya nadella"],
    "Mark Zuckerberg":  ["mark zuckerberg", "zuckerberg"],
    "Demis Hassabis":   ["demis hassabis", "hassabis"],
    "OpenAI":           ["openai"],
    "Anthropic":        ["anthropic"],
    "Google DeepMind":  ["deepmind", "google deepmind"],
    "Meta AI":          ["meta ai", "meta's ai"],
    "Microsoft":        ["microsoft"],
    "Nvidia":           ["nvidia"],
    "EU Commission":    ["european commission", "eu commission"],
    "US Congress":      ["congress", "senate", "house of representatives"],
    "UK DSIT":          ["dsit", "ai safety institute", "aisi"],
    "White House OSTP": ["white house", "ostp"],
}

# ── Podcast transcript archives ────────────────────────────────────────────────
# Full HTML transcripts are available on these blog archives.
# We crawl the archive listing and keep pages whose title mentions the actor.
# (archive_url, domain_fragment, platform)

PODCAST_ARCHIVES = [
    ("https://lexfridman.com/blog/",      "lexfridman.com",   "interview"),
    ("https://www.dwarkeshpatel.com/podcast", "dwarkeshpatel.com", "interview"),
    ("https://www.acquired.fm/episodes",  "acquired.fm",       "interview"),
]

# ── URL / file utilities (same pattern as other scrapers) ─────────────────────

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
    path = output_dir / url_to_filename(doc["url"])
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


# ── HTTP helpers ───────────────────────────────────────────────────────────────

def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def fetch(session: requests.Session, url: str, timeout: int = 20) -> Optional[BeautifulSoup]:
    try:
        resp = session.get(url, timeout=timeout)
        if resp.status_code in (401, 403, 404, 429):
            return None
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except requests.RequestException as exc:
        print(f"    ! fetch failed: {url}  ({exc})")
        return None


# ── Content extraction (matches scrape_individuals.py exactly) ────────────────

def extract_text(soup: BeautifulSoup) -> str:
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


# ── Platform detection ─────────────────────────────────────────────────────────

_SPEECH_RE = re.compile(
    r"\b(speech|remarks|keynote|address|statement|testimony|testif|hearing)\b", re.I
)

def detect_platform(title: str, description: str = "") -> str:
    """Infer platform from article title / description."""
    if _SPEECH_RE.search(f"{title} {description}"):
        return "speech"
    return "interview"


# ── Domain utilities ───────────────────────────────────────────────────────────

def domain_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lstrip("www.")
    except Exception:
        return ""


def _is_blocked(url: str) -> bool:
    """True if URL is paywalled or belongs to an actor-owned domain."""
    d = domain_of(url)
    for block_set in (PAYWALL_DOMAINS, ACTOR_OWNED_DOMAINS):
        if any(d == p or d.endswith("." + p) for p in block_set):
            return True
    return False


# ── NewsAPI integration ────────────────────────────────────────────────────────

def _newsapi_fetch_page(
    api_key: str,
    query: str,
    from_date: Optional[str],
    to_date: Optional[str],
    page: int,
    page_size: int = 100,
) -> dict:
    """Single NewsAPI request; returns the parsed JSON response."""
    params: dict = {
        "q": query,
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": page_size,
        "page": page,
        "apiKey": api_key,
    }
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    try:
        resp = requests.get(NEWSAPI_URL, params=params, timeout=30)
        return resp.json()
    except Exception as exc:
        print(f"    ! NewsAPI request failed (page {page}): {exc}")
        return {}


def scrape_newsapi(
    session: requests.Session,
    actor: str,
    actor_cfg: dict,
    api_key: str,
    from_date: Optional[str],
    to_date: Optional[str],
    limit: int,
    seen_urls: set[str],
) -> list[dict]:
    """
    Query NewsAPI for the actor, then fetch full article text from each URL.
    Returns a list of new document dicts.
    """
    query = ACTOR_QUERIES.get(actor)
    if not query:
        print(f"  No NewsAPI query defined for '{actor}' — skipping.")
        return []

    name_variants = ACTOR_NAME_VARIANTS.get(actor, [actor.lower()])

    print(f"  [NewsAPI] query: {query[:90]}...")

    # Collect article metadata across pages (max 5 pages × 100 = 500 candidates)
    api_articles: list[dict] = []
    for page in range(1, 6):
        data = _newsapi_fetch_page(api_key, query, from_date, to_date, page)
        if data.get("status") != "ok":
            msg = data.get("message", data.get("code", "unknown error"))
            print(f"  ! NewsAPI error: {msg}")
            break
        batch = data.get("articles", [])
        api_articles.extend(batch)
        total = data.get("totalResults", 0)
        if len(api_articles) >= total or len(batch) < 100:
            break
        time.sleep(DELAY)

    print(f"  → {len(api_articles)} candidates from NewsAPI")

    docs: list[dict] = []
    for article in api_articles:
        if len(docs) >= limit:
            break

        url = (article.get("url") or "").split("?")[0].rstrip("/")
        if not url or url in seen_urls:
            continue
        if _is_blocked(url):
            continue

        title = article.get("title") or ""
        description = article.get("description") or ""
        published_at = (article.get("publishedAt") or "")[:10]

        time.sleep(DELAY)
        soup = fetch(session, url)
        if soup is None:
            continue

        text = extract_text(soup)
        if len(text) < MIN_TEXT_LEN:
            continue

        # Relevance gate: actor name must appear in the article body
        text_lower = text.lower()
        if not any(v in text_lower for v in name_variants):
            continue

        doc_date = published_at or extract_date(soup)
        doc = {
            "url": url,
            "date": doc_date,
            "text": text,
            "actor": actor,
            "context": "public",
            "platform": detect_platform(title, description),
        }
        docs.append(doc)
        seen_urls.add(url)

    return docs


# ── Podcast transcript scraping ────────────────────────────────────────────────

_NAV_RE = re.compile(
    r"/(tag|category|author|feed|rss|page|wp-content|cdn|search|about|contact"
    r"|signin|login|register|subscribe|privacy|terms)(/|$)",
    re.I,
)
_SKIP_EXT_RE = re.compile(r"\.(atom|rss|xml|pdf|zip|png|jpg|jpeg|gif|css|js)$", re.I)


def _collect_episode_links(soup: BeautifulSoup, base_url: str, domain: str) -> set[str]:
    origin = "https://" + urlparse(base_url).netloc
    links: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = str(a["href"]).strip().split("?")[0].split("#")[0]
        if href.startswith("/"):
            href = origin + href
        href = href.rstrip("/")
        if domain not in href:
            continue
        if _NAV_RE.search(href):
            continue
        if _SKIP_EXT_RE.search(href):
            continue
        links.add(href)
    return links


def scrape_podcasts(
    session: requests.Session,
    actor: str,
    actor_cfg: dict,
    limit: int,
    seen_urls: set[str],
) -> list[dict]:
    """
    Scrape Lex Fridman, Dwarkesh, and Acquired transcript archives.
    Keeps only episode pages whose title mentions the actor's name.
    Individual actors only.
    """
    if actor_cfg["type"] != "individual":
        return []

    # Name parts used for title matching (first name, last name, full name)
    name_parts = [p.lower() for p in actor.split() if len(p) > 2]

    docs: list[dict] = []

    for archive_url, domain, platform in PODCAST_ARCHIVES:
        if len(docs) >= limit:
            break

        print(f"  [Podcast] {archive_url}")
        soup = fetch(session, archive_url)
        if soup is None:
            print(f"    ! Could not reach archive, skipping")
            continue

        links = _collect_episode_links(soup, archive_url, domain)

        # Try page 2 in case the listing paginates
        time.sleep(DELAY)
        for page_url in (f"{archive_url}/page/2", f"{archive_url}?page=2"):
            p2 = fetch(session, page_url)
            if p2:
                links.update(_collect_episode_links(p2, archive_url, domain))
                break

        print(f"    {len(links)} episode links found")

        for url in sorted(links):
            if len(docs) >= limit:
                break
            if url in seen_urls:
                continue

            # Cheap title-level filter before fetching the full page
            # (avoids fetching hundreds of irrelevant episodes)
            time.sleep(DELAY)
            page = fetch(session, url)
            if page is None:
                continue

            title_tag = page.find("title")
            title = title_tag.get_text().lower() if title_tag else ""
            h1_tag = page.find("h1")
            heading = h1_tag.get_text().lower() if h1_tag else ""

            if not any(part in title or part in heading for part in name_parts):
                continue

            text = extract_text(page)
            if len(text) < MIN_TEXT_LEN:
                continue

            # Final body-level relevance check
            if not any(part in text.lower() for part in name_parts):
                continue

            doc = {
                "url": url,
                "date": extract_date(page),
                "text": text,
                "actor": actor,
                "context": "public",
                "platform": platform,
            }
            docs.append(doc)
            seen_urls.add(url)
            print(f"    ✓ saved: {url[:80]}")

    return docs


# ── Per-actor runner ───────────────────────────────────────────────────────────

def run_actor(
    actor: str,
    api_key: Optional[str],
    from_date: str,
    to_date: str,
    limit: int,
    news_only: bool,
    podcasts_only: bool,
) -> int:
    """Run both sources for one actor. Returns total docs saved this run."""
    if actor not in ACTORS:
        print(f"  Unknown actor: '{actor}'")
        return 0

    actor_cfg = ACTORS[actor]
    output_dir: Path = DATA_RAW / actor_cfg["raw_subdir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    seen_urls = load_seen_urls(output_dir)

    print(f"\n{'='*60}")
    print(f"Actor:   {actor}  ({actor_cfg['type']})")
    print(f"Output:  {output_dir}")
    print(f"Pre-existing: {len(seen_urls)} docs on disk")
    print(f"{'='*60}")

    session = make_session()
    total_saved = 0

    # ── Approach 1: NewsAPI ────────────────────────────────────────────────────
    if not podcasts_only:
        if api_key:
            news_docs = scrape_newsapi(
                session, actor, actor_cfg, api_key,
                from_date, to_date,
                limit=limit,
                seen_urls=seen_urls,
            )
            for doc in news_docs:
                save_doc(doc, output_dir)
            total_saved += len(news_docs)
            print(f"  NewsAPI saved: {len(news_docs)}")
        else:
            print("  ! NEWS_API_KEY not set in .env — skipping NewsAPI")

    # ── Approach 2: Podcast archives (individual actors only) ─────────────────
    remaining = limit - total_saved
    if not news_only and remaining > 0:
        pod_docs = scrape_podcasts(session, actor, actor_cfg, remaining, seen_urls)
        for doc in pod_docs:
            save_doc(doc, output_dir)
        total_saved += len(pod_docs)
        print(f"  Podcasts saved: {len(pod_docs)}")

    print(f"{'─'*60}")
    print(f"Saved this run : {total_saved}")
    print(f"Total on disk  : {len(list(output_dir.glob('*.json')))}")
    return total_saved


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Collect public-context docs via NewsAPI and podcast transcript archives."
    )
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--actor",
        help='Exact actor name from ACTORS dict (e.g. "Sam Altman")',
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Run for every actor in ACTORS",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Max new public docs to collect per actor (default: 100)",
    )
    p.add_argument(
        "--from-date",
        default="2020-01-01",
        metavar="YYYY-MM-DD",
        help="Earliest NewsAPI article date (default: 2020-01-01; free tier ignores this)",
    )
    p.add_argument(
        "--to-date",
        default=str(date.today()),
        metavar="YYYY-MM-DD",
        help="Latest NewsAPI article date (default: today)",
    )
    p.add_argument(
        "--news-only",
        action="store_true",
        help="Skip podcast archives; use NewsAPI only",
    )
    p.add_argument(
        "--podcasts-only",
        action="store_true",
        help="Skip NewsAPI; scrape podcast archives only",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if args.news_only and args.podcasts_only:
        print("Error: --news-only and --podcasts-only are mutually exclusive.")
        sys.exit(1)

    api_key: Optional[str] = NEWS_API_KEY
    if not api_key and not args.podcasts_only:
        print(
            "Warning: NEWS_API_KEY not set in .env — NewsAPI queries will be skipped.\n"
            "Set NEWS_API_KEY in .env or use --podcasts-only."
        )

    actors_to_run: list[str] = list(ACTORS.keys()) if args.all else [args.actor]

    grand_total = 0
    for actor in actors_to_run:
        saved = run_actor(
            actor=actor,
            api_key=api_key,
            from_date=args.from_date,
            to_date=args.to_date,
            limit=args.limit,
            news_only=args.news_only,
            podcasts_only=args.podcasts_only,
        )
        grand_total += saved

    if args.all:
        print(f"\n{'='*60}")
        print(f"Grand total saved: {grand_total} public docs")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
