"""MyJVN getVulnOverviewList + getVulnDetailInfo adapter.

Endpoints (both under https://jvndb.jvn.jp/myjvn):
  - method=getVulnOverviewList&feed=hnd  → JVNRSS 3.2 (RDF) list
  - method=getVulnDetailInfo&feed=hnd    → VULDEF 3.2 (XML) detail
"""

from __future__ import annotations

import datetime as dt
import re
import defusedxml.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from ..filters import filter_items
from ..http_cache import http_get
from ..ids import extract_ids
from ._base import ListQuery

ENDPOINT = "https://jvndb.jvn.jp/myjvn"

NS_RSS = {
    "rss": "http://purl.org/rss/1.0/",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "sec": "http://jvn.jp/rss/mod_sec/3.0/",
}
NS_VULDEF = {
    "vuldef": "http://jvn.jp/vuldef/",
    "sec": "http://jvn.jp/rss/mod_sec/3.0/",
    "status": "http://jvndb.jvn.jp/myjvn/Status",
}
DEFAULT_NS_VULDEF = "{http://jvn.jp/vuldef/}"

SEVERITY_MAP = {
    "n": "none", "none": "none",
    "l": "low", "low": "low",
    "m": "medium", "medium": "medium",
    "h": "high", "high": "high",
    "c": "critical", "critical": "critical",
}

DATE_MODE_PARAM = {
    "public": ("datePublicStart", "datePublicEnd"),
    "published": ("datePublishedStart", "datePublishedEnd"),
    "first-published": ("dateFirstPublishedStart", "dateFirstPublishedEnd"),
}


# ---- Tiny HTML-fragment to text helper (some VULDEF fields embed <ul><li>) ----


class _FragmentText(HTMLParser):
    BLOCK = {"p", "div", "br", "li", "tr", "td"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        if tag == "br":
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(data)

    def get_text(self) -> str:
        raw = "".join(self.parts)
        lines = [re.sub(r"[ \t　]+", " ", ln).strip() for ln in raw.splitlines()]
        out = "\n".join(ln for ln in lines if ln)
        return out


def _flatten(text: str | None) -> str | None:
    if text is None:
        return None
    if "<" in text:
        ext = _FragmentText()
        ext.feed(text)
        return ext.get_text()
    return text.strip() or None


# ---- List (getVulnOverviewList) -------------------------------------------


def _date_params(
    start: dt.date | None, end: dt.date | None, date_mode: str
) -> dict[str, str]:
    if date_mode not in DATE_MODE_PARAM:
        date_mode = "published"
    s_prefix, e_prefix = DATE_MODE_PARAM[date_mode]
    out: dict[str, str] = {}
    if start is not None:
        out[f"{s_prefix}Y"] = f"{start.year:04d}"
        out[f"{s_prefix}M"] = f"{start.month:02d}"
        out[f"{s_prefix}D"] = f"{start.day:02d}"
    if end is not None:
        out[f"{e_prefix}Y"] = f"{end.year:04d}"
        out[f"{e_prefix}M"] = f"{end.month:02d}"
        out[f"{e_prefix}D"] = f"{end.day:02d}"
    return out


def _build_overview_url(
    start_item: int = 1,
    max_count: int = 50,
    keyword: str | None = None,
    severity: str | None = None,
    cpe: str | None = None,
    date_params: dict[str, str] | None = None,
) -> str:
    params: dict[str, Any] = {
        "method": "getVulnOverviewList",
        "feed": "hnd",
        "startItem": start_item,
        "maxCountItem": max_count,
    }
    if keyword is not None:
        params["keyword"] = keyword
    if severity is not None:
        sev = severity.lower()
        rev = {v: k for k, v in SEVERITY_MAP.items() if len(k) == 1}
        params["severity"] = rev.get(sev, sev[:1])
    if cpe is not None:
        params["cpeName"] = cpe
    if date_params:
        params.update(date_params)
    return f"{ENDPOINT}?{urlencode(params)}"


def parse_overview(xml_bytes: bytes) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_bytes)
    items: list[dict[str, Any]] = []
    for it in root.findall("rss:item", NS_RSS):
        title = (it.findtext("rss:title", default="", namespaces=NS_RSS) or "").strip()
        link = (it.findtext("rss:link", default="", namespaces=NS_RSS) or "").strip()
        desc = (
            it.findtext("rss:description", default="", namespaces=NS_RSS) or ""
        ).strip()
        identifier = (
            it.findtext("sec:identifier", default="", namespaces=NS_RSS) or ""
        ).strip() or None
        date = (it.findtext("dc:date", default="", namespaces=NS_RSS) or "").strip()

        # CVSS — pick the highest base score across evaluators
        best_score: float | None = None
        best_severity: str | None = None
        for cv in it.findall("sec:cvss", NS_RSS):
            sev = (cv.get("severity") or "").lower() or None
            score_s = cv.get("score")
            try:
                score = float(score_s) if score_s else None
            except ValueError:
                score = None
            if score is not None and (best_score is None or score > best_score):
                best_score = score
                best_severity = sev

        # CVE references
        cve_refs: list[str] = []
        for ref in it.findall("sec:references", NS_RSS):
            src = (ref.get("source") or "").lower()
            rid = ref.get("id") or ""
            if "cve" in src and rid:
                cve_refs.append(rid.upper())

        cves_from_text, jvn_ids = extract_ids(f"{title}\n{desc}\n{identifier or ''}")
        cves = sorted(set(cves_from_text) | set(cve_refs))

        rec: dict[str, Any] = {
            "source": "myjvn-vuln",
            "category": best_severity or "vulnerability",
            "id": identifier,
            "title": title,
            "link": link,
            "date": date,
            "description": _flatten(desc)[:500] if desc else None,
            "severity": best_severity,
            "cvss_score": best_score,
        }
        if cves:
            rec["cves"] = cves
        if jvn_ids:
            rec["jvn_ids"] = jvn_ids
        items.append(rec)
    return items


# ---- Detail (getVulnDetailInfo) -------------------------------------------


def _build_detail_url(vuln_ids: list[str]) -> str:
    params = {
        "method": "getVulnDetailInfo",
        "feed": "hnd",
        "vulnId": "+".join(vuln_ids),
    }
    return f"{ENDPOINT}?{urlencode(params, safe='+')}"


def parse_detail(xml_bytes: bytes) -> dict[str, Any]:
    root = ET.fromstring(xml_bytes)
    vulinfo = root.find("vuldef:Vulinfo", NS_VULDEF)
    if vulinfo is None:
        raise ValueError("no Vulinfo in response")

    vid = (
        vulinfo.findtext("vuldef:VulinfoID", default="", namespaces=NS_VULDEF) or ""
    ).strip() or None
    data = vulinfo.find("vuldef:VulinfoData", NS_VULDEF)
    if data is None:
        raise ValueError("no VulinfoData in response")

    title = (
        data.findtext("vuldef:Title", default="", namespaces=NS_VULDEF) or ""
    ).strip()
    desc = data.find("vuldef:VulinfoDescription", NS_VULDEF)
    overview = ""
    if desc is not None:
        overview = (
            desc.findtext("vuldef:Overview", default="", namespaces=NS_VULDEF) or ""
        )
    overview = _flatten(overview) or ""

    # Affected
    affected: list[dict[str, Any]] = []
    for ai in data.findall("vuldef:Affected/vuldef:AffectedItem", NS_VULDEF):
        vendor = (
            ai.findtext("vuldef:Name", default="", namespaces=NS_VULDEF) or ""
        ).strip()
        product = (
            ai.findtext("vuldef:ProductName", default="", namespaces=NS_VULDEF) or ""
        ).strip()
        cpe = (
            ai.findtext("vuldef:Cpe", default="", namespaces=NS_VULDEF) or ""
        ).strip() or None
        versions = []
        for v in ai.findall("vuldef:VersionNumber", NS_VULDEF):
            t = (v.text or "").strip()
            if t:
                versions.append(t)
        affected.append(
            {"vendor": vendor, "product": product, "cpe": cpe, "versions": versions}
        )

    # CVSS
    cvss: list[dict[str, Any]] = []
    for impact in data.findall("vuldef:Impact", NS_VULDEF):
        for c in impact.findall("vuldef:Cvss", NS_VULDEF):
            severity_jp_to_en = {"なし": "none", "緊急": "critical", "重要": "high",
                                 "警告": "medium", "注意": "low", "情報": "none"}
            severity_attr = (
                c.findtext("vuldef:Severity", default="", namespaces=NS_VULDEF) or ""
            ).strip()
            severity_type = (c.find("vuldef:Severity", NS_VULDEF).get("type")
                             if c.find("vuldef:Severity", NS_VULDEF) is not None else None)
            sev = severity_jp_to_en.get(severity_attr, severity_attr.lower() or None)
            vector = (
                c.findtext("vuldef:Vector", default="", namespaces=NS_VULDEF) or ""
            ).strip() or None
            base_s = (c.findtext("vuldef:Base", default="", namespaces=NS_VULDEF) or "").strip()
            try:
                base = float(base_s) if base_s else None
            except ValueError:
                base = None
            cvss.append(
                {
                    "version": c.get("version") or "",
                    "type": severity_type,
                    "severity": sev,
                    "score": base,
                    "vector": vector,
                }
            )

    # Impact description (first ImpactItem/Description)
    impact_text: str | None = None
    impact_node = data.find("vuldef:Impact/vuldef:ImpactItem/vuldef:Description", NS_VULDEF)
    if impact_node is not None and impact_node.text:
        impact_text = _flatten(impact_node.text)

    # Mitigation (Solution/SolutionItem/Description)
    mitigation_parts: list[str] = []
    for s in data.findall("vuldef:Solution/vuldef:SolutionItem/vuldef:Description", NS_VULDEF):
        if s.text:
            t = _flatten(s.text)
            if t:
                mitigation_parts.append(t)
    mitigation = "\n\n".join(mitigation_parts) or None

    # References
    refs: list[dict[str, Any]] = []
    for ri in data.findall("vuldef:Related/vuldef:RelatedItem", NS_VULDEF):
        refs.append(
            {
                "type": ri.get("type"),
                "name": (
                    ri.findtext("vuldef:Name", default="", namespaces=NS_VULDEF) or ""
                ).strip() or None,
                "id": (
                    ri.findtext("vuldef:VulinfoID", default="", namespaces=NS_VULDEF) or ""
                ).strip() or None,
                "title": (
                    ri.findtext("vuldef:Title", default="", namespaces=NS_VULDEF) or ""
                ).strip() or None,
                "url": (
                    ri.findtext("vuldef:URL", default="", namespaces=NS_VULDEF) or ""
                ).strip(),
            }
        )
    refs = [r for r in refs if r.get("url")]

    # History
    history: list[dict[str, Any]] = []
    for h in data.findall("vuldef:History/vuldef:HistoryItem", NS_VULDEF):
        history.append(
            {
                "date": (
                    h.findtext("vuldef:DateTime", default="", namespaces=NS_VULDEF) or ""
                ).strip() or None,
                "description": (
                    h.findtext("vuldef:Description", default="", namespaces=NS_VULDEF) or ""
                ).strip(),
            }
        )

    date_first = (
        data.findtext("vuldef:DateFirstPublished", default="", namespaces=NS_VULDEF)
        or ""
    ).strip() or None
    date_last = (
        data.findtext("vuldef:DateLastUpdated", default="", namespaces=NS_VULDEF)
        or ""
    ).strip() or None
    date_public = (
        data.findtext("vuldef:DatePublic", default="", namespaces=NS_VULDEF) or ""
    ).strip() or None

    # IDs
    ref_text = "\n".join(
        [(r.get("name") or "") + " " + (r.get("id") or "") + " " + (r.get("title") or "")
         for r in refs]
    )
    cves_from_text, jvn_ids = extract_ids(f"{title}\n{overview}\n{ref_text}")
    cve_from_refs = sorted({
        (r["id"] or "").upper()
        for r in refs
        if r.get("id") and r["id"].upper().startswith("CVE-")
    })
    cves = sorted(set(cves_from_text) | set(cve_from_refs))

    url = f"https://jvndb.jvn.jp/ja/contents/{vid[6:10]}/{vid}.html" if vid else ""

    return {
        "source": "myjvn-vuln",
        "url": url,
        "id": vid,
        "title": title,
        "date_first_published": date_first,
        "date_last_updated": date_last,
        "date_public": date_public,
        "overview": overview or None,
        "affected": affected,
        "cvss": cvss,
        "impact": impact_text,
        "mitigation": mitigation,
        "references": refs,
        "history": history,
        "cves": cves,
        "jvn_ids": jvn_ids,
    }


# ---- Adapter ---------------------------------------------------------------


class MyJvnVulnAdapter:
    name = "myjvn-vuln"

    def list_items(self, q: ListQuery) -> list[dict[str, Any]]:
        date_params = _date_params(q.start, q.end, q.date_mode)
        keywords = q.keywords or [None]  # type: ignore[list-item]

        all_items: list[dict[str, Any]] = []
        for kw in keywords:
            start_item = 1
            while True:
                url = _build_overview_url(
                    start_item=start_item,
                    max_count=50,
                    keyword=kw,
                    severity=q.severity,
                    cpe=q.cpe,
                    date_params=date_params,
                )
                body = http_get(url, cache_dir=q.cache_dir)
                page = parse_overview(body)
                if not page:
                    break
                all_items.extend(page)
                if len(page) < 50:
                    break
                start_item += 50
                if start_item > 1000:
                    break

        # Dedup by id then by link
        seen: set[str] = set()
        uniq: list[dict[str, Any]] = []
        for it in all_items:
            key = it.get("id") or it.get("link") or ""
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            uniq.append(it)

        items = filter_items(
            uniq,
            start=q.start, end=q.end,
            keywords=None,  # already applied server-side; client-side keyword skip
            category=q.category, cves=q.cves,
        )
        if q.limit is not None:
            items = items[: q.limit]
        return items

    def detail(
        self, url_or_id: str, cache_dir: Path | None
    ) -> dict[str, Any]:
        # Accept URL or JVNDB ID; extract ID
        m = re.search(r"JVNDB-\d{4}-\d+", url_or_id, re.I)
        if not m:
            raise ValueError(f"cannot extract JVNDB ID from '{url_or_id}'")
        vid = m.group(0).upper()
        url = _build_detail_url([vid])
        body = http_get(url, cache_dir=cache_dir)
        return parse_detail(body)
