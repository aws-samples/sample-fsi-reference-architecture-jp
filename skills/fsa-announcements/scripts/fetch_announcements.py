#!/usr/bin/env python3
"""Fetch announcements from the Financial Services Agency of Japan (FSA).

Sources:
- News RSS feed (https://www.fsa.go.jp/fsaNewsListAll_rss2.xml) for the latest
  ~15 entries with the freshest pubDate timestamps.
- recent{YYYY}.html archive pages (back to 2021) for date-range queries that
  must reach further than the RSS window.

Design points:
- Standard library only.
- On-disk cache is OFF by default. Pass --cache-dir <path> to enable HTTP
  caching with conditional GET (ETag / Last-Modified). This default suits
  environments such as financial institutions that disallow third-party
  scripts writing to local disk.
- Date filter is mandatory (--start-date) with --end-date defaulting to today.
- HTML parsing uses html.parser with structural anchors and reads category
  text from the <span> body so that future labelNN class-name churn does not
  silently break the parser.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import email.utils
import hashlib
import html
import json
import logging
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

LOG = logging.getLogger("fsa")

USER_AGENT = (
    "fsi-reference-arch-jp/fsa-announcements "
    "(+https://gitlab.aws.dev/aws-jp-sa-fsi/fsi-reference-architecture-jp)"
)
RSS_URL = "https://www.fsa.go.jp/fsaNewsListAll_rss2.xml"
RECENT_URL_TEMPLATE = "https://www.fsa.go.jp/recent/recent{year}.html"
RECENT_OLDEST_YEAR = 2021
SITE_BASE = "https://www.fsa.go.jp"
JST = dt.timezone(dt.timedelta(hours=9), name="JST")


# ---------------------------------------------------------------------------
# HTTP with optional on-disk cache (ETag / Last-Modified, opt-in via cache_dir)
# ---------------------------------------------------------------------------


def _cache_paths(cache_dir: Path, url: str) -> tuple[Path, Path]:
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return cache_dir / f"{key}.body", cache_dir / f"{key}.meta.json"


def http_get(
    url: str,
    cache_dir: Path | None = None,
    timeout: int = 30,
    max_attempts: int = 3,
) -> bytes:
    scheme = urllib.parse.urlparse(url).scheme
    if scheme not in ("http", "https"):
        raise ValueError(f"unsupported URL scheme '{scheme}': {url}")
    headers: dict[str, str] = {"User-Agent": USER_AGENT}
    body_path: Path | None = None
    meta_path: Path | None = None

    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        body_path, meta_path = _cache_paths(cache_dir, url)
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text("utf-8"))
                if etag := meta.get("etag"):
                    headers["If-None-Match"] = etag
                if last_mod := meta.get("last_modified"):
                    headers["If-Modified-Since"] = last_mod
            except Exception as e:
                LOG.debug("ignoring unreadable cache metadata %s: %s", meta_path, e)

    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            # scheme validated above (http/https only)
            req = urllib.request.Request(url, headers=headers)  # noqa: S310
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
                body = resp.read()
                if body_path is not None and meta_path is not None:
                    body_path.write_bytes(body)
                    meta_path.write_text(
                        json.dumps(
                            {
                                "url": url,
                                "etag": resp.headers.get("ETag"),
                                "last_modified": resp.headers.get("Last-Modified"),
                                "content_type": resp.headers.get("Content-Type"),
                                "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                            },
                            ensure_ascii=False,
                        ),
                        "utf-8",
                    )
                return body
        except urllib.error.HTTPError as e:
            if e.code == 304 and body_path is not None and body_path.exists():
                LOG.debug("304 from %s, using cache", url)
                return body_path.read_bytes()
            last_err = e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = e
        if attempt < max_attempts:
            time.sleep(2 ** (attempt - 1))
    if last_err is None:
        raise RuntimeError(f"failed to fetch {url} but no error was recorded")
    raise last_err


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Announcement:
    """Normalized announcement entry."""

    source: str  # "rss" | "recent"
    published: dt.date  # JST calendar date
    category: str | None  # e.g. "報道発表"
    title: str
    url: str

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "published": self.published.isoformat(),
            "category": self.category,
            "title": self.title,
            "url": self.url,
        }


# ---------------------------------------------------------------------------
# RSS parsing
# ---------------------------------------------------------------------------


# RSS title prefix categories (manually-observed, not exhaustive). Only used to
# split the RSS title into (category, body); recent.html provides authoritative
# categories so RSS-prefix mismatches are non-fatal.
_RSS_CATEGORY_PREFIXES = (
    "報道発表",
    "記者会見",
    "審議会等",
    "国際関係",
    "イベント",
    "刊行物",
    "採用",
    "調達",
    "その他",
)


def _parse_pubdate_jst(pubdate: str) -> dt.date:
    """Parse RSS pubDate. FSA emits 'JST' (not RFC 822) so we substitute +0900."""
    s = pubdate.strip()
    s = re.sub(r"\bJST\b\s*$", "+0900", s)
    parsed = email.utils.parsedate_to_datetime(s)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=JST)
    return parsed.astimezone(JST).date()


def _split_rss_title(title: str) -> tuple[str | None, str]:
    """Strip a known category prefix like '報道発表,...' off the title."""
    for prefix in _RSS_CATEGORY_PREFIXES:
        if title.startswith(prefix + ","):
            return prefix, title[len(prefix) + 1 :].lstrip()
    return None, title


_ITEM_RE = re.compile(r"<item>(.*?)</item>", re.DOTALL)
_TAG_RE = re.compile(r"<(\w+)\b[^>]*>(.*?)</\1>", re.DOTALL)


def parse_rss(xml_bytes: bytes) -> list[Announcement]:
    """Minimal RSS 2.0 item extractor for the FSA news feed."""
    text = xml_bytes.decode("utf-8")
    items = _ITEM_RE.findall(text)
    out: list[Announcement] = []
    for raw in items:
        fields = {tag: html.unescape(body.strip()) for tag, body in _TAG_RE.findall(raw)}
        title = fields.get("title", "").strip()
        link = fields.get("link", "").strip()
        pub = fields.get("pubDate", "").strip()
        if not (title and link and pub):
            continue
        try:
            published = _parse_pubdate_jst(pub)
        except Exception as e:
            LOG.warning("skipping RSS item with unparseable pubDate %r: %s", pub, e)
            continue
        category, body = _split_rss_title(title)
        out.append(
            Announcement(
                source="rss",
                published=published,
                category=category,
                title=body,
                url=link,
            )
        )
    return out


# ---------------------------------------------------------------------------
# recent{YYYY}.html parsing
# ---------------------------------------------------------------------------


_WAREKI_ERA_OFFSETS = {
    "令和": 2018,  # 令和元年 = 2019 = 2018 + 1
    "平成": 1988,  # 平成元年 = 1989
    "昭和": 1925,  # 昭和元年 = 1926
}
_KANSUJI = {
    "〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "元": 1,
}


def _normalize_digits(s: str) -> str:
    # Convert full-width digits and basic kansuji to half-width
    out: list[str] = []
    for ch in s:
        if ch in _KANSUJI:
            out.append(str(_KANSUJI[ch]))
        elif "０" <= ch <= "９":
            out.append(str(ord(ch) - ord("０")))
        else:
            out.append(ch)
    return "".join(out)


_WAREKI_RE = re.compile(
    r"(令和|平成|昭和)\s*([\d元]+)\s*年\s*([\d]+)\s*月\s*([\d]+)\s*日"
)


def parse_wareki_date(text: str) -> dt.date | None:
    """Parse '令和X年Y月Z日' (with kansuji / full-width digits tolerated)."""
    norm = _normalize_digits(text)
    m = _WAREKI_RE.search(norm)
    if not m:
        return None
    era, era_year, mm, dd = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
    era_year_int = 1 if era_year == "元" else int(era_year)
    year = _WAREKI_ERA_OFFSETS[era] + era_year_int
    try:
        return dt.date(year, mm, dd)
    except ValueError:
        return None


class _RecentParser(HTMLParser):
    """Extracts announcement <li> entries from recent{YYYY}.html.

    Strategy (to survive UI churn):
    - We do NOT depend on the labelNN class number; we read category text
      from any <span class="label_en ..."> inside an <li>.
    - We anchor on <ul class="listtype04 longType"> first, but also fall back
      to scanning every <li> that contains a wareki date + a <span class="label_en">
      + an <a href> if no anchored <ul> is found. This lets the parser cope with
      a future class-name rename.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_anchor_ul = False
        self._ul_depth = 0
        self._anchor_ul_depth: int | None = None
        self._li_buf: list[str] | None = None
        self._li_depth = 0
        self._li_start_in_anchor_ul: bool = False
        self.entries_in_anchor: list[str] = []
        self.entries_global: list[str] = []  # every <li> regardless of <ul>
        self.anchor_ul_count = 0

    def _is_target_ul(self, attrs: list[tuple[str, str | None]]) -> bool:
        for k, v in attrs:
            if k == "class" and v:
                tokens = v.split()
                if "listtype04" in tokens and "longType" in tokens:
                    return True
        return False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "ul":
            self._ul_depth += 1
            if self._is_target_ul(attrs) and self._anchor_ul_depth is None:
                self._anchor_ul_depth = self._ul_depth
                self._in_anchor_ul = True
                self.anchor_ul_count += 1
        elif tag == "li":
            if self._li_buf is None:
                self._li_buf = []
                self._li_depth = 1
                self._li_start_in_anchor_ul = self._in_anchor_ul
                self._li_buf.append("<li>")
                return
            else:
                self._li_depth += 1
        if self._li_buf is not None:
            attr_str = "".join(f' {k}="{v}"' if v is not None else f" {k}" for k, v in attrs)
            self._li_buf.append(f"<{tag}{attr_str}>")

    def handle_endtag(self, tag: str) -> None:
        if tag == "li" and self._li_buf is not None:
            self._li_buf.append("</li>")
            self._li_depth -= 1
            if self._li_depth == 0:
                blob = "".join(self._li_buf)
                self.entries_global.append(blob)
                if self._li_start_in_anchor_ul:
                    self.entries_in_anchor.append(blob)
                self._li_buf = None
            return
        if self._li_buf is not None:
            self._li_buf.append(f"</{tag}>")
        if tag == "ul":
            if self._anchor_ul_depth is not None and self._ul_depth == self._anchor_ul_depth:
                self._anchor_ul_depth = None
                self._in_anchor_ul = False
            self._ul_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._li_buf is not None:
            self._li_buf.append(data)


_LABEL_RE = re.compile(
    r'<span\s+class="[^"]*\blabel_en\b[^"]*">\s*([^<]+?)\s*</span>'
)
_HREF_RE = re.compile(r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
_TAG_STRIP_RE = re.compile(r"<[^>]+>")


def _normalize_url(href: str) -> str:
    if href.startswith(("http://", "https://")):
        return href
    if href.startswith("/"):
        return SITE_BASE + href
    # Other relative forms shouldn't appear in recent.html, but be safe.
    return SITE_BASE + "/" + href.lstrip("./")


def _parse_li(blob: str) -> Announcement | None:
    date = parse_wareki_date(blob)
    if date is None:
        return None
    cat_match = _LABEL_RE.search(blob)
    category = cat_match.group(1).strip() if cat_match else None
    a_match = _HREF_RE.search(blob)
    if a_match is None:
        return None
    href = html.unescape(a_match.group(1))
    title = _TAG_STRIP_RE.sub("", a_match.group(2)).strip()
    if not (title and href):
        return None
    return Announcement(
        source="recent",
        published=date,
        category=category,
        title=title,
        url=_normalize_url(href),
    )


def parse_recent_html(html_bytes: bytes, *, year: int, min_entries: int = 50) -> list[Announcement]:
    """Parse recent{YYYY}.html. Raise if the result is suspiciously small."""
    parser = _RecentParser()
    parser.feed(html_bytes.decode("utf-8"))
    entries = parser.entries_in_anchor
    used = "anchor_ul"
    if not entries:
        # Fallback: any <li> at all. Helpful if the class names ever change.
        entries = parser.entries_global
        used = "fallback_global_li"

    out: list[Announcement] = []
    for blob in entries:
        ann = _parse_li(blob)
        if ann is not None:
            out.append(ann)

    LOG.debug(
        "recent%s.html: anchor_ul=%d, anchor_lis=%d, global_lis=%d, parsed=%d (mode=%s)",
        year,
        parser.anchor_ul_count,
        len(parser.entries_in_anchor),
        len(parser.entries_global),
        len(out),
        used,
    )
    if len(out) < min_entries:
        raise RuntimeError(
            f"recent{year}.html parsed only {len(out)} entries "
            f"(threshold={min_entries}). The page structure may have changed."
        )
    return out


# ---------------------------------------------------------------------------
# Filtering / merging
# ---------------------------------------------------------------------------


def filter_by_date(
    items: Iterable[Announcement], start: dt.date, end: dt.date
) -> list[Announcement]:
    return [a for a in items if start <= a.published <= end]


def dedupe_by_url(items: Iterable[Announcement]) -> list[Announcement]:
    """De-dupe by URL, preferring 'recent' (richer category) over 'rss'."""
    by_url: dict[str, Announcement] = {}
    for a in items:
        existing = by_url.get(a.url)
        if existing is None:
            by_url[a.url] = a
            continue
        # recent wins; otherwise keep first
        if existing.source == "rss" and a.source == "recent":
            by_url[a.url] = a
    return list(by_url.values())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_iso_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch FSA announcements from the news RSS feed and the "
            "recent{YYYY}.html archive pages."
        )
    )
    parser.add_argument(
        "--start-date",
        type=_parse_iso_date,
        required=True,
        help="Inclusive start date (YYYY-MM-DD, JST calendar).",
    )
    parser.add_argument(
        "--end-date",
        type=_parse_iso_date,
        default=dt.datetime.now(JST).date(),
        help="Inclusive end date (YYYY-MM-DD, JST calendar). Default: today.",
    )
    parser.add_argument(
        "--source",
        choices=("rss", "recent", "both"),
        default="both",
        help="Which source(s) to query. Default: both (RSS deduped against recent).",
    )
    parser.add_argument(
        "--category",
        action="append",
        default=None,
        help=(
            "Filter by category (repeatable). Examples: 報道発表, 記者会見, "
            "審議会等, 国際関係, イベント, 刊行物, 採用, 調達, その他"
        ),
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help=(
            "Optional directory for ETag / Last-Modified cache. "
            "If omitted, no files are written (default for restricted environments)."
        ),
    )
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="Emit per-source counts to stderr (helpful when the FSA HTML structure changes).",
    )
    parser.add_argument(
        "--log-level",
        default=os.environ.get("FSA_LOG_LEVEL", "WARNING"),
        help="DEBUG / INFO / WARNING / ERROR. Default: WARNING.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.WARNING),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )

    if args.start_date > args.end_date:
        print("--start-date must be <= --end-date", file=sys.stderr)
        return 2

    items: list[Announcement] = []

    if args.source in ("rss", "both"):
        try:
            xml_bytes = http_get(RSS_URL, cache_dir=args.cache_dir)
            rss_items = parse_rss(xml_bytes)
        except Exception as e:
            LOG.error("RSS fetch/parse failed: %s", e)
            rss_items = []
        if args.diagnose:
            print(f"[diagnose] rss: {len(rss_items)} items", file=sys.stderr)
        items.extend(filter_by_date(rss_items, args.start_date, args.end_date))

    if args.source in ("recent", "both"):
        years = range(args.start_date.year, args.end_date.year + 1)
        for year in years:
            if year < RECENT_OLDEST_YEAR:
                LOG.warning(
                    "recent%s.html does not exist (oldest available is %d). Skipping.",
                    year,
                    RECENT_OLDEST_YEAR,
                )
                continue
            url = RECENT_URL_TEMPLATE.format(year=year)
            try:
                html_bytes = http_get(url, cache_dir=args.cache_dir)
                year_items = parse_recent_html(html_bytes, year=year)
            except Exception as e:
                LOG.error("recent%s.html fetch/parse failed: %s", year, e)
                continue
            if args.diagnose:
                print(f"[diagnose] recent{year}: {len(year_items)} items", file=sys.stderr)
            items.extend(filter_by_date(year_items, args.start_date, args.end_date))

    items = dedupe_by_url(items)

    if args.category:
        wanted = set(args.category)
        items = [a for a in items if a.category in wanted]

    items.sort(key=lambda a: (a.published, a.title), reverse=True)

    json.dump(
        [a.to_dict() for a in items],
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
