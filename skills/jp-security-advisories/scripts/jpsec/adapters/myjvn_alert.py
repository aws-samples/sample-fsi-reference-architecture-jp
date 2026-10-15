"""MyJVN getAlertList adapter.

Endpoint: https://jvndb.jvn.jp/myjvn?method=getAlertList&feed=hnd
Returns Atom 1.0 + mod_sec 3.0 (XML) or JSON when ft=json.
"""

from __future__ import annotations

import datetime as dt
import json as jsonlib
import defusedxml.ElementTree as ET
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from ..filters import filter_items
from ..http_cache import http_get
from ..ids import extract_ids
from ._base import ListQuery

ENDPOINT = "https://jvndb.jvn.jp/myjvn"
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "sec": "http://jvn.jp/rss/mod_sec/3.0/",
    "status": "http://jvndb.jvn.jp/myjvn/Status",
}

# IPA term → normalized severity / category
TERM_MAP = {
    "Critical": "critical",
    "緊急": "critical",
    "Important": "important",
    "重要": "important",
    "Low": "low",
    "注意": "low",
    "Information": "info",
    "参考": "info",
}


def _build_url(
    start_item: int = 1,
    max_count: int = 50,
    date_published_year: int | None = None,
) -> str:
    params: dict[str, Any] = {
        "method": "getAlertList",
        "feed": "hnd",
        "startItem": start_item,
        "maxCountItem": max_count,
    }
    if date_published_year is not None:
        params["datePublished"] = date_published_year
    return f"{ENDPOINT}?{urlencode(params)}"


def parse_atom(xml_bytes: bytes) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_bytes)
    items: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", NS):
        title = (entry.findtext("atom:title", default="", namespaces=NS) or "").strip()
        eid = (entry.findtext("atom:id", default="", namespaces=NS) or "").strip()
        published = (
            entry.findtext("atom:published", default="", namespaces=NS) or ""
        ).strip()
        updated = (
            entry.findtext("atom:updated", default="", namespaces=NS) or ""
        ).strip()
        link_el = entry.find("atom:link", NS)
        link = (link_el.get("href") if link_el is not None else "") or ""
        summary = (
            entry.findtext("atom:summary", default="", namespaces=NS) or ""
        ).strip()
        cat_el = entry.find("atom:category", NS)
        term = cat_el.get("term") if cat_el is not None else None
        # term often comes like "/Critical" — normalize
        term_norm = (term or "").lstrip("/").strip()
        severity = TERM_MAP.get(term_norm, term_norm.lower() if term_norm else None)

        related: list[dict[str, Any]] = []
        # mod_sec items: each <sec:items><sec:item>...</sec:item></sec:items>
        for items_el in entry.findall("sec:items", NS):
            for item_el in items_el.findall("sec:item", NS):
                r_title = (
                    item_el.findtext("sec:title", default="", namespaces=NS) or ""
                ).strip()
                r_id = (
                    item_el.findtext("sec:identifier", default="", namespaces=NS)
                    or ""
                ).strip() or None
                r_link_el = item_el.find("sec:link", NS)
                r_url = r_link_el.get("href") if r_link_el is not None else None
                r_published = (
                    item_el.findtext("sec:published", default="", namespaces=NS)
                    or ""
                ).strip() or None
                if r_url:
                    related.append(
                        {
                            "title": r_title,
                            "identifier": r_id,
                            "url": r_url,
                            "published": r_published,
                        }
                    )

        # Choose the most useful link: entry-level link, or the first related URL
        primary_link = link or (related[0]["url"] if related else "")

        text_for_ids = "\n".join(
            [title, summary] + [r["title"] for r in related]
        )
        cves, jvn_ids = extract_ids(text_for_ids)

        rec: dict[str, Any] = {
            "source": "myjvn-alert",
            "category": severity or "info",
            "id": eid or None,
            "title": title,
            "link": primary_link,
            "date": published or updated,
            "description": summary[:500] if summary else None,
            "severity": severity,
        }
        if cves:
            rec["cves"] = cves
        if jvn_ids:
            rec["jvn_ids"] = jvn_ids
        if related:
            rec["related"] = related
        items.append(rec)
    return items


class MyJvnAlertAdapter:
    name = "myjvn-alert"

    def list_items(self, q: ListQuery) -> list[dict[str, Any]]:
        # API supports per-year filter only for getAlertList. Pull all years
        # touched by the requested range, then filter client-side to day precision.
        years: list[int | None]
        if q.start is None and q.end is None:
            years = [None]
        else:
            s = q.start or dt.date(2000, 1, 1)
            e = q.end or dt.date.today()
            years = list(range(s.year, e.year + 1))

        all_items: list[dict[str, Any]] = []
        for year in years:
            start_item = 1
            while True:
                url = _build_url(
                    start_item=start_item,
                    max_count=50,
                    date_published_year=year,
                )
                body = http_get(url, cache_dir=q.cache_dir)
                page_items = parse_atom(body)
                if not page_items:
                    break
                all_items.extend(page_items)
                if len(page_items) < 50:
                    break
                start_item += 50
                # safety cap
                if start_item > 1000:
                    break

        items = filter_items(
            all_items,
            start=q.start, end=q.end,
            keywords=q.keywords, category=q.category, cves=q.cves,
        )
        if q.limit is not None:
            items = items[: q.limit]
        return items

    def detail(
        self, url_or_id: str, cache_dir: Path | None
    ) -> dict[str, Any]:
        # myjvn-alert does not currently have a separate detail call —
        # the list response already contains structured related-references.
        raise NotImplementedError(
            "myjvn-alert has no separate detail call; use the related-references "
            "from the list output."
        )
