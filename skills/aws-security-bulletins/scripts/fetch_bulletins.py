#!/usr/bin/env python3
"""Fetch AWS Security Bulletins from the public API or retrieve individual bulletin details."""

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
from html.parser import HTMLParser

LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARN").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.WARN),
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger(__name__)

BASE_URL = "https://aws.amazon.com"
API_PATH = "/api/dirs/items/search"
DIRECTORY_ID = (
    "product-categories-security-identity-compliance-security-cards-interactive-security-bulletins"
)
BULLETIN_URL_PREFIX = f"{BASE_URL}/security/security-bulletins/"
TAG_NS_SEVERITY = "GLOBAL#local-tags-security-bulletins-flag"
MAX_RETRIES = 3
PAGE_SIZE = 100


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _request_with_retry(url: str) -> bytes:
    """GET with exponential backoff (max 3 attempts)."""
    scheme = urllib.parse.urlparse(url).scheme
    if scheme not in ("http", "https"):
        raise ValueError(f"unsupported URL scheme '{scheme}': {url}")
    for attempt in range(MAX_RETRIES):
        try:
            log.info("GET %s (attempt %d)", url, attempt + 1)
            req = urllib.request.Request(  # noqa: S310 - scheme validated above
                url,
                headers={
                    "Accept": "application/json, text/html, */*",
                    "User-Agent": "aws-security-bulletins-skill/1.0",
                },
            )
            with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 - scheme validated above  # nosec B310
                return resp.read()
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            wait = 2**attempt
            log.warning("Request failed (%s), retrying in %ds…", exc, wait)
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(wait)
    raise RuntimeError("unreachable")


# ---------------------------------------------------------------------------
# List / search mode
# ---------------------------------------------------------------------------


def _extract_severity(tags: list) -> str:
    for t in tags:
        if t.get("tagNamespaceId") == TAG_NS_SEVERITY and t["name"] not in ("aws", "amazon"):
            return t["name"]
    return ""


def _to_full_url(cta_link: str) -> str:
    if cta_link.startswith("http"):
        return cta_link
    return BASE_URL + cta_link


def fetch_list(start_date: str, end_date: str, keywords: list[str] | None) -> list[dict]:
    """Return bulletin items, optionally filtered by keywords (OR, case-insensitive)."""
    all_items: list[dict] = []
    page = 0
    while True:
        url = (
            f"{BASE_URL}{API_PATH}"
            f"?item.directoryId={DIRECTORY_ID}"
            f"&sort_by=item.additionalFields.publishedDate"
            f"&sort_order=desc"
            f"&size={PAGE_SIZE}"
            f"&item.locale=en_US"
            f"&page={page}"
        )
        log.info("Fetching page %d", page)
        data = json.loads(_request_with_retry(url))
        items = data.get("items", [])
        if not items:
            break
        for entry in items:
            item = entry["item"]
            af = item.get("additionalFields", {})
            pub = af.get("publishedDate", "")
            if pub and start_date and pub < start_date:
                # Past the window – stop pagination
                return _apply_keyword_filter(all_items, keywords)
            if pub and end_date and pub > end_date:
                continue
            all_items.append(
                {
                    "locale": item.get("locale", ""),
                    "bulletinId": af.get("namePerson", item.get("name", "")),
                    "title": af.get("title", ""),
                    "publishedDate": pub,
                    "severity": _extract_severity(entry.get("tags", [])),
                    "url": _to_full_url(af.get("ctaLink", "")),
                }
            )
        total_hits = data.get("metadata", {}).get("totalHits", 0)
        if (page + 1) * PAGE_SIZE >= total_hits:
            break
        page += 1
    return _apply_keyword_filter(all_items, keywords)


def _apply_keyword_filter(items: list[dict], keywords: list[str] | None) -> list[dict]:
    if not keywords:
        return items
    kw_lower = [k.lower() for k in keywords]
    return [i for i in items if any(k in i["title"].lower() for k in kw_lower)]


# ---------------------------------------------------------------------------
# Detail mode
# ---------------------------------------------------------------------------


class _BulletinHTMLExtractor(HTMLParser):
    """Extract structured fields from the embedded JSON in a bulletin page."""

    def __init__(self):
        super().__init__()
        self._in_script = False
        self._script_buf = ""
        self.fields: dict | None = None

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == "script" and attr_dict.get("type") == "application/json":
            self._in_script = True
            self._script_buf = ""

    def handle_data(self, data):
        if self._in_script:
            self._script_buf += data

    def handle_endtag(self, tag):
        if tag == "script" and self._in_script:
            self._in_script = False
            self._try_parse(self._script_buf)

    def _try_parse(self, raw: str):
        try:
            d = json.loads(raw)
            for item in d.get("data", {}).get("items", []):
                fields = item.get("fields", {})
                body = fields.get("itemLongLoc", "")
                heading = fields.get("itemHeading", "")
                if body and heading:
                    self.fields = fields
                    return
        except (json.JSONDecodeError, KeyError):
            pass


def _resolve_bulletin_url(identifier: str) -> str:
    """Accept a full URL or a bulletin ID like '2026-003-AWS' and return the canonical URL."""
    if identifier.startswith("http"):
        return identifier.rstrip("/") + "/"
    return f"{BULLETIN_URL_PREFIX}{identifier}/"


def fetch_detail(identifier: str) -> dict:
    """Fetch a single bulletin page and return structured JSON."""
    url = _resolve_bulletin_url(identifier)
    log.info("Fetching detail: %s", url)
    html_bytes = _request_with_retry(url)
    html_text = html_bytes.decode("utf-8", errors="replace")

    parser = _BulletinHTMLExtractor()
    parser.feed(html_text)

    if not parser.fields:
        return {"error": f"Could not extract bulletin content from {url}"}

    f = parser.fields
    body_html = f.get("itemLongLoc", "")
    heading = f.get("itemHeading", "")

    # Extract metadata from body HTML
    bulletin_id = ""
    published_date = ""
    severity = ""
    body_lower = body_html.lower()
    import re

    def _clean(s: str) -> str:
        return re.sub(r"&nbsp;|\xa0", " ", s).strip()

    if "bulletin id:" in body_lower:
        m = re.search(r"Bulletin ID:</b>[&nbsp;\s]*([^<]+)", body_html, re.IGNORECASE)
        if m:
            bulletin_id = _clean(m.group(1))
    if "publication date:" in body_lower:
        m = re.search(r"Publication Date:</b>[&nbsp;\s]*([^<]+)", body_html, re.IGNORECASE)
        if m:
            published_date = _clean(m.group(1))
    if "content type:" in body_lower:
        m = re.search(r"Content Type:</b>[&nbsp;\s]*([^<]+)", body_html, re.IGNORECASE)
        if m:
            severity = _clean(m.group(1))

    return {
        "bulletinId": bulletin_id or identifier,
        "title": heading,
        "publishedDate": published_date,
        "severity": severity,
        "body": body_html,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _default_start_date() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%dT00:00:00Z")


def _default_end_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT23:59:59Z")


def main():
    parser = argparse.ArgumentParser(description="AWS Security Bulletins fetcher")
    sub = parser.add_subparsers(dest="command", required=True)

    # list sub-command
    p_list = sub.add_parser("list", help="List / search bulletins")
    p_list.add_argument(
        "--start-date", default=None, help="Start date (ISO 8601). Default: 1 year ago"
    )
    p_list.add_argument("--end-date", default=None, help="End date (ISO 8601). Default: today")
    p_list.add_argument(
        "--no-date-filter", action="store_true", help="Disable date filtering entirely"
    )
    p_list.add_argument(
        "--keyword",
        nargs="*",
        default=None,
        help="Filter titles by keyword(s) (OR, case-insensitive)",
    )

    # detail sub-command
    p_detail = sub.add_parser("detail", help="Get detail of a single bulletin")
    p_detail.add_argument("identifier", help="Bulletin ID (e.g. AWS-2025-032) or full URL")

    args = parser.parse_args()

    try:
        if args.command == "list":
            sd = "" if args.no_date_filter else (args.start_date or _default_start_date())
            ed = "" if args.no_date_filter else (args.end_date or _default_end_date())
            result = fetch_list(sd, ed, args.keyword)
            json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        elif args.command == "detail":
            result = fetch_detail(args.identifier)
            json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    except Exception as exc:
        log.error("Fatal: %s", exc)
        json.dump({"error": str(exc)}, sys.stderr, ensure_ascii=False)
        sys.exit(1)


if __name__ == "__main__":
    main()
