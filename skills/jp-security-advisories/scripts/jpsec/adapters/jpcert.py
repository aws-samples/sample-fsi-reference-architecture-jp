"""JPCERT/CC adapter — RSS for list, HTML scraping for detail."""

from __future__ import annotations

import re
import defusedxml.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ..filters import filter_items
from ..http_cache import http_get
from ..ids import extract_ids
from ._base import ListQuery

NS = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rss": "http://purl.org/rss/1.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
}

FEED_URLS = {
    "jpcert": "https://www.jpcert.or.jp/rss/jpcert.rdf",
    "jpcert-all": "https://www.jpcert.or.jp/rss/jpcert-all.rdf",
}


def classify(link: str) -> str:
    p = urlparse(link)
    path = p.path or ""
    netloc = p.netloc or ""
    if "/at/" in path:
        return "alert"
    if "/wr/" in path:
        return "weekly-report"
    if "/tsubame/" in path:
        return "tsubame"
    if "/newsflash/" in path:
        return "news"
    if "blogs.jpcert.or.jp" in netloc:
        return "blog"
    return "other"


def parse_feed(xml_bytes: bytes, source: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_bytes)
    out: list[dict[str, Any]] = []
    for it in root.findall("rss:item", NS):
        title = (it.findtext("rss:title", default="", namespaces=NS) or "").strip()
        link = (it.findtext("rss:link", default="", namespaces=NS) or "").strip()
        date = (it.findtext("dc:date", default="", namespaces=NS) or "").strip()
        desc = (it.findtext("rss:description", default="", namespaces=NS) or "").strip()

        rec: dict[str, Any] = {
            "source": source,
            "category": classify(link),
            "title": title,
            "link": link,
            "date": date,
            "description": desc[:500] if desc else None,
        }
        cves, jids = extract_ids(f"{title}\n{desc}")
        if cves:
            rec["cves"] = cves
        if jids:
            rec["jvn_ids"] = jids
        out.append(rec)
    return out


# ---- Detail HTML extraction ------------------------------------------------


class _TextExtractor(HTMLParser):
    SKIP_TAGS = {"script", "style", "nav", "footer", "header", "noscript", "form"}
    BLOCK_TAGS = {
        "p", "div", "br", "li", "tr", "td", "th",
        "h1", "h2", "h3", "h4", "h5", "h6", "dt", "dd",
    }

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._buf: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
        elif tag in self.BLOCK_TAGS:
            self._buf.append("\n")

    def handle_endtag(self, tag: str):
        if tag in self.SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag in self.BLOCK_TAGS:
            self._buf.append("\n")

    def handle_startendtag(self, tag: str, attrs):
        if tag == "br":
            self._buf.append("\n")

    def handle_data(self, data: str):
        if self._skip_depth == 0:
            self._buf.append(data)

    def get_text(self) -> str:
        raw = "".join(self._buf)
        lines = [re.sub(r"[ \t　]+", " ", ln).strip() for ln in raw.splitlines()]
        out_lines: list[str] = []
        prev_blank = False
        for ln in lines:
            if not ln:
                if not prev_blank and out_lines:
                    out_lines.append("")
                prev_blank = True
            else:
                out_lines.append(ln)
                prev_blank = False
        return "\n".join(out_lines).strip()


def _extract_title(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    if not m:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()


def extract_sections(html: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    pattern = re.compile(
        r"<h[2-4][^>]*>\s*(?:[IVX]+\.\s*)?(概要|対象|対策|軽減策|参考情報)\s*</h[2-4]>",
        re.I,
    )
    matches = list(pattern.finditer(html))
    for i, m in enumerate(matches):
        name = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html)
        body = html[start:end]
        ext = _TextExtractor()
        ext.feed(body)
        sections[name] = ext.get_text()
    return sections


def parse_detail_html(html: str) -> dict[str, Any]:
    title = _extract_title(html)
    sections = extract_sections(html)
    text_ext = _TextExtractor()
    text_ext.feed(html)
    body_text = text_ext.get_text()
    cves, jids = extract_ids(html)
    return {
        "title": title,
        "body_text": body_text,
        "sections": sections,
        "cves": cves,
        "jvn_ids": jids,
    }


# ---- Adapter ---------------------------------------------------------------


class JPCERTAdapter:
    def __init__(self, name: str) -> None:
        self.name = name
        self._feed_url = FEED_URLS[name]

    def list_items(self, q: ListQuery) -> list[dict[str, Any]]:
        body = http_get(self._feed_url, cache_dir=q.cache_dir)
        items = parse_feed(body, self.name)
        items = filter_items(
            items,
            start=q.start, end=q.end,
            keywords=q.keywords, category=q.category, cves=q.cves,
        )
        if q.limit is not None:
            items = items[: q.limit]
        return items

    def detail(
        self, url_or_id: str, cache_dir: Path | None
    ) -> dict[str, Any]:
        if not (url_or_id.startswith("http://") or url_or_id.startswith("https://")):
            raise ValueError(
                f"jpcert detail requires a URL, got '{url_or_id}'"
            )
        body = http_get(url_or_id, cache_dir=cache_dir)
        # JPCERT pages are UTF-8
        html = body.decode("utf-8", errors="replace")
        parsed = parse_detail_html(html)
        result: dict[str, Any] = {
            "source": "jpcert",
            "url": url_or_id,
            "id": None,
            "title": parsed["title"],
            "date_first_published": None,
            "date_last_updated": None,
            "date_public": None,
            "overview": parsed["sections"].get("概要") or None,
            "body_text": parsed["body_text"],
            "sections": parsed["sections"],
            "mitigation": parsed["sections"].get("対策") or None,
        }
        if parsed["cves"]:
            result["cves"] = parsed["cves"]
        if parsed["jvn_ids"]:
            result["jvn_ids"] = parsed["jvn_ids"]
        return result
