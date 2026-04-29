"""
scrape_policy.py — Scrapes policy and public contexts for policymaker actors.

Saves one JSON per document to data/raw/policymakers/{subdir}/{context}/
with fields: url, date, text, actor, context, platform

Usage:
    python src/scraping/scrape_policy.py --actor "EU Commission"
    python src/scraping/scrape_policy.py --actor "US Congress" --limit 400
    python src/scraping/scrape_policy.py --actor "UK DSIT" --delay 3 --source-timeout 600
    python src/scraping/scrape_policy.py --actor "White House OSTP" --wayback --context policy
    python src/scraping/scrape_policy.py --actor "EU Commission" --context policy
"""

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import ACTORS, DATA_RAW

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
DELAY = 1.5
MIN_TEXT_LEN = 300
SOURCE_TIMEOUT = 240  # seconds per source block


# ── File utilities ─────────────────────────────────────────────────────────────

def url_to_filename(url: str) -> str:
    """12-char MD5 hex used as the JSON filename."""
    return hashlib.md5(url.encode()).hexdigest()[:12] + ".json"


def load_seen_urls(output_dir: Path) -> set[str]:
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
        resp = session.get(url, timeout=timeout, allow_redirects=True)
        if resp.status_code in (403, 404, 410):
            print(f"    ! HTTP {resp.status_code}: {url}")
            return None
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except requests.RequestException as exc:
        print(f"    ! fetch failed: {url}  ({exc})")
        return None


def fetch_json(
    session: requests.Session,
    url: str,
    params: Optional[list] = None,
) -> Optional[dict]:
    """GET a JSON endpoint. `params` should be a list of (key, value) tuples."""
    try:
        resp = session.get(url, params=params, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        print(f"    ! JSON fetch failed: {url}  ({exc})")
        return None


def probe_status(session: requests.Session, url: str) -> int:
    """Return HTTP status code for a URL, or 0 on network error."""
    try:
        resp = session.get(url, timeout=10, allow_redirects=True)
        return resp.status_code
    except Exception:
        return 0


# ── Content extraction ─────────────────────────────────────────────────────────

def extract_text(soup: BeautifulSoup) -> str:
    for tag in soup(["nav", "header", "footer", "script", "style",
                     "aside", "noscript", "iframe", "form", "button"]):
        tag.decompose()
    content = (
        soup.find("article")
        or soup.find(attrs={"role": "main"})
        or soup.find("main")
        or soup.find("div", class_=re.compile(r"\b(post|entry|content|article|body|text)\b", re.I))
        or soup.find("body")
    )
    raw = content.get_text(" ", strip=True) if content else soup.get_text(" ", strip=True)
    return re.sub(r" {2,}", " ", raw).strip()


_MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}


def extract_date(soup: BeautifulSoup) -> str:
    t = soup.find("time", attrs={"datetime": True})
    if t:
        return str(t["datetime"])[:10]

    for prop in ("article:published_time", "datePublished", "og:updated_time",
                 "article:modified_time", "DC.date", "dcterms.issued"):
        meta = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
        if meta and meta.get("content"):
            return str(meta["content"])[:10]

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict):
                for key in ("datePublished", "dateCreated", "dateModified"):
                    if key in data:
                        return str(data[key])[:10]
        except (json.JSONDecodeError, AttributeError):
            pass

    m = re.search(
        r"\b(\d{1,2})\s+(January|February|March|April|May|June|"
        r"July|August|September|October|November|December)\s+(20\d{2})\b",
        soup.get_text(),
    )
    if m:
        day, month_str, year = m.group(1), m.group(2).lower(), m.group(3)
        return f"{year}-{_MONTH_NAMES[month_str]:02d}-{int(day):02d}"

    return "unknown"


# ── Generic link crawler ───────────────────────────────────────────────────────

_NAV_RE = re.compile(
    r"/(tag|category|author|feed|rss|wp-content|cdn|signin|login"
    r"|register|subscribe|privacy|terms)(/|$)",
    re.I,
)
_SKIP_EXT_RE = re.compile(r"\.(atom|rss|xml|zip|png|jpg|jpeg|gif|css|js)$", re.I)


def _page_links(
    soup: BeautifulSoup,
    base_url: str,
    domain: str,
    url_must_contain: str = "",
) -> set[str]:
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    links: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = str(a["href"]).strip().split("?")[0].split("#")[0]
        if href.startswith("/"):
            href = origin + href
        href = re.sub(r"^http://", "https://", href).rstrip("/")
        if domain not in href:
            continue
        if href == base_url.rstrip("/"):
            continue
        if _NAV_RE.search(href):
            continue
        if _SKIP_EXT_RE.search(href):
            continue
        if url_must_contain and url_must_contain not in href:
            continue
        links.add(href)
    return links


def crawl_paginated(
    session: requests.Session,
    base_url: str,
    platform: str,
    actor: str,
    context: str,
    limit: int,
    seen_urls: set[str],
    output_dir: Path,
    max_pages: int = 30,
    page_param: str = "page",
    url_must_contain: str = "",
) -> int:
    """
    Crawl a paginated listing page and scrape individual article pages.
    Tries ?{page_param}={n} and /page/{n}/ pagination styles.
    Returns number of documents saved.
    """
    domain = urlparse(base_url).netloc
    candidates: set[str] = set()

    soup = fetch(session, base_url)
    if soup:
        candidates.update(_page_links(soup, base_url, domain, url_must_contain))

    page = 1
    no_new = 0
    while len(candidates) < limit * 3 and no_new < 3 and page <= max_pages:
        time.sleep(DELAY)
        found_new = False
        for page_url in (
            f"{base_url}?{page_param}={page}",
            f"{base_url}/page/{page}/",
        ):
            ps = fetch(session, page_url)
            if ps is None:
                continue
            fresh = _page_links(ps, base_url, domain, url_must_contain) - candidates
            if fresh:
                candidates.update(fresh)
                found_new = True
            break  # got a 200 response; don't try the other pattern

        no_new = 0 if found_new else no_new + 1
        page += 1

    print(f"    Candidate URLs: {len(candidates)} from {base_url}")

    saved = 0
    t0 = time.monotonic()
    for url in sorted(candidates):
        if saved >= limit:
            break
        if time.monotonic() - t0 > SOURCE_TIMEOUT:
            print(f"    ! source timeout ({SOURCE_TIMEOUT}s) — stopping")
            break
        if url in seen_urls:
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
        save_doc(doc, output_dir)
        seen_urls.add(url)
        saved += 1

    return saved


def scrape_url_list(
    session: requests.Session,
    url_date_pairs: list[tuple[str, str]],
    platform: str,
    actor: str,
    context: str,
    limit: int,
    seen_urls: set[str],
    output_dir: Path,
) -> int:
    """Fetch and save a pre-collected list of (url, date) pairs. Returns n saved."""
    saved = 0
    t0 = time.monotonic()
    for url, prefetch_date in url_date_pairs:
        if saved >= limit:
            break
        if time.monotonic() - t0 > SOURCE_TIMEOUT:
            print(f"    ! timeout ({SOURCE_TIMEOUT}s) — stopping")
            break
        if url in seen_urls:
            continue
        time.sleep(DELAY)
        soup = fetch(session, url)
        if soup is None:
            continue
        text = extract_text(soup)
        if len(text) < MIN_TEXT_LEN:
            continue
        date = prefetch_date if prefetch_date and prefetch_date != "unknown" else extract_date(soup)
        doc = {
            "url": url,
            "date": date,
            "text": text,
            "actor": actor,
            "context": context,
            "platform": platform,
        }
        save_doc(doc, output_dir)
        seen_urls.add(url)
        saved += 1
    return saved


# ── gov.uk Search JSON API ─────────────────────────────────────────────────────

def govuk_search(
    session: requests.Session,
    org_slug: str,
    query: str,
    content_supergroup: Optional[str] = None,
    max_results: int = 500,
    document_type: Optional[str] = None,
) -> list[tuple[str, str]]:
    """
    Query gov.uk search JSON API for a given organisation and keyword.
    Returns list of (full_url, date_str).
    """
    results: list[tuple[str, str]] = []
    count = 50
    start = 0

    while len(results) < max_results:
        params = [
            ("filter_organisations[]", org_slug),
            ("q", query),
            ("count", str(count)),
            ("start", str(start)),
            ("fields[]", "link"),
            ("fields[]", "public_timestamp"),
        ]
        if content_supergroup:
            params.append(("filter_content_purpose_supergroup[]", content_supergroup))
        if document_type:
            params.append(("filter_content_store_document_type[]", document_type))

        data = fetch_json(session, "https://www.gov.uk/api/search.json", params=params)
        if data is None:
            break

        batch = data.get("results", [])
        if not batch:
            break

        for item in batch:
            link = item.get("link", "")
            if not link:
                continue
            url = f"https://www.gov.uk{link}" if link.startswith("/") else link
            date = str(item.get("public_timestamp", "unknown"))[:10]
            results.append((url, date))

        total = data.get("total", 0)
        if isinstance(total, dict):
            total = total.get("value", 0)
        start += len(batch)
        if start >= min(int(total), max_results):
            break
        time.sleep(DELAY)

    return results


# ── EU Commission ──────────────────────────────────────────────────────────────

_EU_POLICY_SOURCES: list[tuple[str, str, str]] = [
    # (url, platform, url_must_contain)
    ("https://digital-strategy.ec.europa.eu/en/news", "regulatory_doc", ""),
    ("https://digital-strategy.ec.europa.eu/en/policies/artificial-intelligence", "regulatory_doc", ""),
    ("https://commission.europa.eu/strategy-and-policy/priorities-2019-2024/"
     "europe-fit-digital-age/european-approach-artificial-intelligence_en",
     "regulatory_doc", ""),
    ("https://www.europarl.europa.eu/news/en/press-room", "regulatory_doc", ""),
]

_EU_PUBLIC_SOURCES: list[tuple[str, str, str]] = [
    ("https://ec.europa.eu/commission/presscorner/home/en", "speech", "detail"),
    ("https://audiovisual.ec.europa.eu/en/video", "speech", ""),
]


def scrape_eu_commission(
    session: requests.Session,
    context: str,
    limit: int,
    output_dir: Path,
    seen_urls: set[str],
    actor_name: str,
) -> int:
    saved = 0
    sources = _EU_POLICY_SOURCES if context == "policy" else _EU_PUBLIC_SOURCES

    for url, platform, must_contain in sources:
        if saved >= limit:
            break
        print(f"\n  EU Commission source: {url}")
        n = crawl_paginated(
            session, url, platform, actor_name, context,
            limit - saved, seen_urls, output_dir,
            url_must_contain=must_contain,
        )
        saved += n
        print(f"  → {n} saved (running total: {saved})")

    return saved


# ── UK DSIT ────────────────────────────────────────────────────────────────────

_AISI_SOURCES = [
    "https://www.aisi.gov.uk/work",
    "https://www.aisi.gov.uk/research",
    "https://www.aisi.gov.uk/updates",
]


def scrape_uk_dsit(
    session: requests.Session,
    context: str,
    limit: int,
    output_dir: Path,
    seen_urls: set[str],
    actor_name: str,
) -> int:
    saved = 0

    if context == "policy":
        print("  gov.uk API → DSIT + 'artificial intelligence' …")
        links = govuk_search(
            session,
            org_slug="department-for-science-innovation-and-technology",
            query="artificial intelligence",
            max_results=limit * 2,
        )
        print(f"  gov.uk API: {len(links)} results")
        n = scrape_url_list(
            session, links, "regulatory_doc",
            actor_name, context, limit, seen_urls, output_dir,
        )
        saved += n
        print(f"  gov.uk saved: {n}")

        for aisi_url in _AISI_SOURCES:
            if saved >= limit:
                break
            print(f"\n  AISI: {aisi_url}")
            n = crawl_paginated(
                session, aisi_url, "regulatory_doc",
                actor_name, context, limit - saved, seen_urls, output_dir,
            )
            saved += n
            print(f"  → {n} from AISI (total: {saved})")

    elif context == "public":
        print("  gov.uk API → DSIT speeches on AI …")
        # Use document_type filter (not supergroup) — correct param for speech content
        links = govuk_search(
            session,
            org_slug="department-for-science-innovation-and-technology",
            query="artificial intelligence",
            content_supergroup=None,
            max_results=limit * 2,
            document_type="speech",
        )
        print(f"  gov.uk API: {len(links)} speech results")
        n = scrape_url_list(
            session, links, "speech",
            actor_name, context, limit, seen_urls, output_dir,
        )
        saved += n
        print(f"  gov.uk speeches saved: {n}")

    return saved


# ── White House OSTP ───────────────────────────────────────────────────────────

_OSTP_POLICY_SOURCES: list[tuple[str, str]] = [
    # /ostp/news-updates/ is 404 under current admin — removed from list
    ("https://www.whitehouse.gov/briefing-room/presidential-actions/", "regulatory_doc"),
    ("https://www.whitehouse.gov/briefing-room/statements-releases/", "regulatory_doc"),
    ("https://ai.gov/", "regulatory_doc"),
    ("https://www.whitehouse.gov/ai/", "regulatory_doc"),
]

_OSTP_PUBLIC_SOURCES: list[tuple[str, str]] = [
    ("https://www.whitehouse.gov/briefing-room/speeches-remarks/", "speech"),
    ("https://www.whitehouse.gov/briefing-room/press-briefings/", "speech"),
]


def scrape_white_house_ostp(
    session: requests.Session,
    context: str,
    limit: int,
    output_dir: Path,
    seen_urls: set[str],
    actor_name: str,
) -> int:
    saved = 0
    sources = _OSTP_POLICY_SOURCES if context == "policy" else _OSTP_PUBLIC_SOURCES

    for url, platform in sources:
        if saved >= limit:
            break
        print(f"\n  WH OSTP source: {url}")
        # whitehouse.gov uses WordPress-style /page/{n}/ pagination
        n = crawl_paginated(
            session, url, platform, actor_name, context,
            limit - saved, seen_urls, output_dir,
            page_param="paged",
        )
        saved += n
        print(f"  → {n} saved (total: {saved})")

    return saved


# ── US Congress ────────────────────────────────────────────────────────────────

_COMMITTEE_SOURCES: list[tuple[str, str, str]] = [
    # (url, platform, url_must_contain)
    ("https://www.commerce.senate.gov/hearings", "testimony", "hearing"),
    ("https://www.judiciary.senate.gov/hearings", "testimony", "hearing"),
    ("https://www.help.senate.gov/hearings", "testimony", "hearing"),
    ("https://science.house.gov/hearings", "testimony", "hearing"),
    ("https://judiciary.house.gov/hearings", "testimony", "hearing"),
    ("https://intelligence.senate.gov/hearings", "testimony", "hearing"),
    ("https://www.foreign.senate.gov/hearings", "testimony", "hearing"),
]

_CONGRESS_PUBLIC_SOURCES: list[tuple[str, str]] = [
    ("https://www.commerce.senate.gov/press-releases", "speech"),
    ("https://www.judiciary.senate.gov/press-releases", "speech"),
    ("https://science.house.gov/press-releases", "speech"),
]

_CONGRESS_GOV_SEARCH = (
    "https://www.congress.gov/search"
    "?q=%7B%22source%22%3A%22congressional-record%22"
    "%2C%22search%22%3A%22artificial+intelligence%22%7D"
)
_GOVINFO_HEARINGS_URLS = [
    "https://www.govinfo.gov/app/collection/chrg/118",
    "https://www.govinfo.gov/app/collection/chrg/117",
]


def scrape_us_congress(
    session: requests.Session,
    context: str,
    limit: int,
    output_dir: Path,
    seen_urls: set[str],
    actor_name: str,
) -> int:
    saved = 0

    if context == "policy":
        # Strategy 1: Senate/House committee hearing pages
        for url, platform, must_contain in _COMMITTEE_SOURCES:
            if saved >= limit:
                break
            print(f"\n  Committee: {url}")
            n = crawl_paginated(
                session, url, platform, actor_name, context,
                limit - saved, seen_urls, output_dir,
                url_must_contain=must_contain,
            )
            saved += n
            print(f"  → {n} hearings (total: {saved})")

        # Strategy 2: congress.gov if accessible
        if saved < limit:
            status = probe_status(session, "https://www.congress.gov/")
            if status == 200:
                print(f"\n  congress.gov accessible (HTTP {status}) — trying CR search …")
                n = crawl_paginated(
                    session, _CONGRESS_GOV_SEARCH, "testimony",
                    actor_name, context, limit - saved, seen_urls, output_dir,
                )
                saved += n
                print(f"  → {n} from congress.gov CR search (total: {saved})")
            elif status == 403:
                print(f"\n  congress.gov returned 403 — trying congressional-record fallback …")
                cr_url = (
                    "https://www.congress.gov/congressional-record/search"
                    "?q=%7B%22search%22%3A%22artificial+intelligence%22%7D"
                )
                n = crawl_paginated(
                    session, cr_url, "testimony",
                    actor_name, context, limit - saved, seen_urls, output_dir,
                )
                saved += n
                if saved < limit:
                    print(f"\n  congressional-record fallback returned {n} — trying govinfo.gov …")
                    for gi_url in _GOVINFO_HEARINGS_URLS:
                        if saved >= limit:
                            break
                        n2 = crawl_paginated(
                            session, gi_url, "testimony",
                            actor_name, context, limit - saved, seen_urls, output_dir,
                        )
                        saved += n2
                        print(f"  → {n2} from {gi_url} (total: {saved})")
            else:
                print(f"\n  congress.gov returned HTTP {status} — skipping")

    elif context == "public":
        for url, platform in _CONGRESS_PUBLIC_SOURCES:
            if saved >= limit:
                break
            print(f"\n  Congress public: {url}")
            n = crawl_paginated(
                session, url, platform, actor_name, context,
                limit - saved, seen_urls, output_dir,
            )
            saved += n
            print(f"  → {n} saved (total: {saved})")

    return saved


# ── Wayback Machine CDX ────────────────────────────────────────────────────────

CDX_API = "http://web.archive.org/cdx/search/cdx"

# actor_name → list of (url_pattern, from_ts, to_ts, context, platform)
# Timestamps are YYYYMMDD strings (or empty for no bound).
WAYBACK_CONFIG_POLICY: dict[str, list[tuple[str, str, str, str, str]]] = {
    "White House OSTP": [
        ("whitehouse.gov/ostp/*", "20210120", "20250120", "policy", "regulatory_doc"),
        ("whitehouse.gov/ai/*",   "20210120", "20250120", "policy", "regulatory_doc"),
    ],
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
    wb_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
    return fetch(session, wb_url)


def parse_wayback_date(timestamp: str) -> str:
    if len(timestamp) >= 8:
        return f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}"
    return "unknown"


def run_wayback_policy(
    session: requests.Session,
    actor_name: str,
    actor_cfg: dict,
    limit: int,
    context_filter: Optional[str],
) -> dict[str, int]:
    """Scrape a policymaker actor via Wayback CDX. Returns {context: n_saved}."""
    entries = WAYBACK_CONFIG_POLICY.get(actor_name, [])
    if not entries:
        print(f"No Wayback config for '{actor_name}'")
        return {}

    if context_filter:
        entries = [e for e in entries if e[3] == context_filter]

    totals: dict[str, int] = {}

    for url_pattern, from_ts, to_ts, context, platform in entries:
        output_dir = DATA_RAW / actor_cfg["raw_subdir"] / context
        output_dir.mkdir(parents=True, exist_ok=True)
        seen_urls = load_seen_urls(output_dir)
        pre_existing = len(seen_urls)

        print(f"\n── WAYBACK  {url_pattern}  {from_ts}–{to_ts}  ctx={context}  "
              f"(pre-existing: {pre_existing}) ──")
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


# ── Actor dispatcher ───────────────────────────────────────────────────────────

_ACTOR_SCRAPERS = {
    "EU Commission":    scrape_eu_commission,
    "UK DSIT":          scrape_uk_dsit,
    "White House OSTP": scrape_white_house_ostp,
    "US Congress":      scrape_us_congress,
}


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Scrape policy and public contexts for policymaker actors."
    )
    p.add_argument(
        "--actor",
        required=True,
        choices=list(_ACTOR_SCRAPERS.keys()),
        help="Policymaker actor name (exact, with spaces)",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Max new docs per context (default: 500)",
    )
    p.add_argument(
        "--context",
        choices=["policy", "public"],
        default=None,
        help="Restrict to a single context (default: all)",
    )
    p.add_argument(
        "--delay",
        type=float,
        default=None,
        help="Override inter-request delay in seconds (default: 1.5)",
    )
    p.add_argument(
        "--source-timeout",
        type=int,
        default=None,
        dest="source_timeout",
        help="Override per-source timeout in seconds (default: 240)",
    )
    p.add_argument(
        "--wayback",
        action="store_true",
        help="Scrape via Wayback Machine CDX (for actors with WAYBACK_CONFIG_POLICY entries)",
    )
    return p.parse_args()


def main() -> None:
    global DELAY, SOURCE_TIMEOUT
    args = parse_args()

    if args.delay is not None:
        DELAY = args.delay
    if args.source_timeout is not None:
        SOURCE_TIMEOUT = args.source_timeout

    actor_name = args.actor
    actor_cfg = ACTORS[actor_name]
    scraper_fn = _ACTOR_SCRAPERS[actor_name]

    if actor_cfg["type"] != "policymaker":
        print(f"Error: '{actor_name}' is not a policymaker actor.")
        sys.exit(1)

    session = make_session()

    # ── Wayback mode ───────────────────────────────────────────────────────────
    if args.wayback:
        print(f"\n{'='*60}")
        print(f"Policymaker: {actor_name}  |  WAYBACK CDX  |  limit {args.limit}")
        print(f"{'='*60}")
        totals = run_wayback_policy(session, actor_name, actor_cfg, args.limit, args.context)
        grand_total = sum(totals.values())
        print(f"\n{'─'*60}")
        print(f"  {actor_name} — WAYBACK DONE")
        print(f"{'─'*60}")
        for ctx, n in totals.items():
            target = actor_cfg["contexts"].get(ctx, 0)
            pct = n / target * 100 if target else 0
            print(f"  {ctx:<12} {n:>4} / {target:<4}  ({pct:.0f}%)")
        print(f"  {'TOTAL':<12} {grand_total:>4}")
        print(f"{'─'*60}\n")
        return

    contexts_to_run = [args.context] if args.context else ["policy", "public"]

    print(f"\n{'='*60}")
    print(f"Policymaker: {actor_name}  |  limit {args.limit}/context  |  delay {DELAY}s  |  timeout {SOURCE_TIMEOUT}s")
    print(f"{'='*60}")

    context_totals: dict[str, int] = {}

    for context in contexts_to_run:
        target = actor_cfg["contexts"].get(context, 0)
        if target == 0:
            print(f"\n── {context.upper()} — no target for {actor_name}, skipping ──")
            continue

        output_dir = DATA_RAW / actor_cfg["raw_subdir"] / context
        output_dir.mkdir(parents=True, exist_ok=True)
        seen_urls = load_seen_urls(output_dir)
        pre_existing = len(seen_urls)

        print(f"\n── {context.upper()}  (pre-existing: {pre_existing} / target: {target}) ──")

        n = scraper_fn(session, context, args.limit, output_dir, seen_urls, actor_name)
        context_totals[context] = n
        total_on_disk = len(list(output_dir.glob("*.json")))
        print(f"\n  {context}: new={n}  |  on disk={total_on_disk}  |  target={target}")

    # ── Summary ────────────────────────────────────────────────────────────────
    grand_total = sum(context_totals.values())
    print(f"\n{'─'*60}")
    print(f"  {actor_name} — DONE")
    print(f"{'─'*60}")
    for ctx, n in context_totals.items():
        target = actor_cfg["contexts"].get(ctx, 0)
        pct = n / target * 100 if target else 0
        print(f"  {ctx:<12} {n:>4} / {target:<4}  ({pct:.0f}%)")
    print(f"  {'TOTAL':<12} {grand_total:>4}")
    print(f"{'─'*60}\n")


if __name__ == "__main__":
    main()
