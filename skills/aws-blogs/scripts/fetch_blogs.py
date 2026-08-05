#!/usr/bin/env python3
"""Fetch AWS blog posts via the public AWS blog directory API.

Modes:
  list   – Retrieve blog post summaries within a date range.
  detail – Retrieve full content for one or more blog posts by URL or ID.

All output is JSON on stdout.  Errors are JSON on stderr.
"""

import argparse
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARN").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.WARN),
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
API_BASE = (
    "https://aws.amazon.com/api/dirs/items/search"
    "?item.directoryId=blog-posts-v2"
    "&sort_by=item.dateCreated&sort_order=desc"
)
PAGE_SIZE = 100
MAX_RETRIES = 3
INITIAL_BACKOFF = 1  # seconds


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _emit_error(msg: str, code: int = 1) -> None:
    json.dump({"error": msg}, sys.stderr, ensure_ascii=False)
    sys.stderr.write("\n")
    sys.exit(code)


def _http_get(url: str) -> dict | list | str:
    """GET with exponential-backoff retry.  Returns parsed JSON."""
    scheme = urllib.parse.urlparse(url).scheme
    if scheme not in ("http", "https"):
        raise ValueError(f"unsupported URL scheme '{scheme}': {url}")
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.debug("GET %s (attempt %d)", url, attempt)
            req = urllib.request.Request(url, headers={"Accept": "application/json"})  # noqa: S310 - scheme validated above
            with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 - scheme validated above  # nosec B310
                return json.loads(resp.read().decode())
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            wait = INITIAL_BACKOFF * (2 ** (attempt - 1))
            log.warning(
                "Request failed (attempt %d/%d): %s – retrying in %ds",
                attempt,
                MAX_RETRIES,
                exc,
                wait,
            )
            if attempt == MAX_RETRIES:
                _emit_error(f"HTTP request failed after {MAX_RETRIES} retries: {exc}")
            time.sleep(wait)
    # unreachable
    _emit_error("Unexpected retry loop exit")


def _parse_date(s: str) -> datetime:
    """Parse ISO-ish date string to UTC datetime."""
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S+0000"):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue
    _emit_error(f"Cannot parse date: {s}")


def _in_range(item: dict, start: datetime | None, end: datetime | None) -> bool:
    raw = item.get("dateCreated", "")
    if not raw:
        return False
    dt = _parse_date(raw)
    if start and dt < start:
        return False
    if end and dt > end:
        return False
    return True


def _matches_keywords(item: dict, keywords: list[str]) -> bool:
    if not keywords:
        return True
    af = item.get("additionalFields", {})
    text = (af.get("title", "") + " " + af.get("excerpt", "")).lower()
    return any(kw.lower() in text for kw in keywords)


# ---------------------------------------------------------------------------
# List mode
# ---------------------------------------------------------------------------


def cmd_list(args: argparse.Namespace) -> None:
    locale = args.locale
    no_date_filter = getattr(args, "no_date_filter", False)
    start = None if no_date_filter else (_parse_date(args.start_date) if args.start_date else None)
    end_raw = None if no_date_filter else (args.end_date if args.end_date else None)
    end = _parse_date(end_raw) if end_raw else None
    # If end date has no time component, set to end of day
    if end and end.hour == 0 and end.minute == 0 and end.second == 0:
        end = end.replace(hour=23, minute=59, second=59)
    keywords = args.keywords or []

    log.info("list: locale=%s start=%s end=%s keywords=%s", locale, start, end, keywords)

    results: list[dict] = []
    page = 0
    while True:
        url = f"{API_BASE}&size={PAGE_SIZE}&item.locale={locale}&page={page}"
        data = _http_get(url)
        items = data.get("items", [])
        if not items:
            log.debug("No more items at page %d", page)
            break

        past_range = False
        for entry in items:
            item = entry["item"]
            if start and _parse_date(item["dateCreated"]) < start:
                past_range = True
                break
            if not _in_range(item, start, end):
                continue
            if not _matches_keywords(item, keywords):
                continue
            af = item.get("additionalFields", {})
            results.append(
                {
                    "locale": item.get("locale", locale),
                    "dateUpdated": item.get("dateUpdated", ""),
                    "title": af.get("title", ""),
                    "excerpt": af.get("excerpt", ""),
                    "url": af.get("link", ""),
                }
            )

        if past_range:
            break
        total_hits = data.get("metadata", {}).get("totalHits", 0)
        if (page + 1) * PAGE_SIZE >= total_hits:
            break
        page += 1

    json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    log.info("list: returned %d items", len(results))


# ---------------------------------------------------------------------------
# Detail mode
# ---------------------------------------------------------------------------


def _resolve_id_to_entry(blog_id: str, locale: str) -> dict | None:
    """Search API pages to find an entry matching the given ID."""
    page = 0
    while True:
        url = f"{API_BASE}&size={PAGE_SIZE}&item.locale={locale}&page={page}"
        data = _http_get(url)
        items = data.get("items", [])
        if not items:
            return None
        for entry in items:
            if entry["item"]["id"] == blog_id:
                return entry
        total_hits = data.get("metadata", {}).get("totalHits", 0)
        if (page + 1) * PAGE_SIZE >= total_hits:
            return None
        page += 1


def _resolve_url_to_entry(blog_url: str, locale: str) -> dict | None:
    """Search API pages to find an entry matching the given URL."""
    page = 0
    while True:
        url = f"{API_BASE}&size={PAGE_SIZE}&item.locale={locale}&page={page}"
        data = _http_get(url)
        items = data.get("items", [])
        if not items:
            return None
        for entry in items:
            af = entry["item"].get("additionalFields", {})
            if af.get("link", "") == blog_url:
                return entry
        total_hits = data.get("metadata", {}).get("totalHits", 0)
        if (page + 1) * PAGE_SIZE >= total_hits:
            return None
        page += 1


def cmd_detail(args: argparse.Namespace) -> None:
    locale = args.locale
    identifiers = args.identifiers
    log.info("detail: locale=%s identifiers=%s", locale, identifiers)

    results: list[dict] = []
    # Simple in-memory cache: id/url -> entry
    cache: dict[str, dict | None] = {}

    for ident in identifiers:
        ident = ident.strip()
        if not ident:
            continue

        if ident in cache:
            entry = cache[ident]
        elif ident.startswith("blog-posts-v2#"):
            entry = _resolve_id_to_entry(ident, locale)
            cache[ident] = entry
        elif ident.startswith("https://aws.amazon.com/blogs/") or ident.startswith(
            "https://aws.amazon.com/jp/blogs/"
        ):
            entry = _resolve_url_to_entry(ident, locale)
            cache[ident] = entry
        else:
            log.warning("Unrecognised identifier format: %s", ident)
            results.append({"error": f"Unrecognised identifier: {ident}"})
            continue

        if entry is None:
            results.append({"error": f"Not found: {ident}"})
            continue

        item = entry["item"]
        af = item.get("additionalFields", {})
        results.append(
            {
                "locale": item.get("locale", locale),
                "dateCreated": item.get("dateCreated", ""),
                "dateUpdated": item.get("dateUpdated", ""),
                "title": af.get("title", ""),
                "url": af.get("link", ""),
                "content": af.get("content", ""),
            }
        )

    json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    log.info("detail: returned %d items", len(results))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    one_month_ago = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")

    parser = argparse.ArgumentParser(description="Fetch AWS blog posts")
    sub = parser.add_subparsers(dest="mode", required=True)

    # --- list ---
    p_list = sub.add_parser("list", help="List blog post summaries")
    p_list.add_argument("--locale", required=True, choices=["en_US", "ja_JP"])
    p_list.add_argument(
        "--no-date-filter",
        action="store_true",
        help="Ignore date range and retrieve all available posts",
    )
    p_list.add_argument(
        "--start-date", default=one_month_ago, help="Start date (YYYY-MM-DD). Default: 30 days ago"
    )
    p_list.add_argument("--end-date", default=today, help="End date (YYYY-MM-DD). Default: today")
    p_list.add_argument("--keywords", nargs="*", help="Filter by keywords (OR, case-insensitive)")

    # --- detail ---
    p_detail = sub.add_parser("detail", help="Get full content of blog posts")
    p_detail.add_argument("--locale", required=True, choices=["en_US", "ja_JP"])
    p_detail.add_argument(
        "identifiers", nargs="+", help="Blog post URLs or IDs (blog-posts-v2#<uuid>)"
    )

    args = parser.parse_args()
    if args.mode == "list":
        cmd_list(args)
    elif args.mode == "detail":
        cmd_detail(args)


if __name__ == "__main__":
    main()
