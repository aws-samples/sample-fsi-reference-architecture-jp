"""Output formatters: JSON / CSV / Markdown."""

from __future__ import annotations

import csv
import io
import json
from typing import Any


def list_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def list_csv(items: list[dict[str, Any]]) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow([
        "source", "category", "date", "id", "title",
        "severity", "cvss_score", "cves", "jvn_ids", "link",
    ])
    for it in items:
        writer.writerow([
            it.get("source", ""),
            it.get("category", ""),
            it.get("date", ""),
            it.get("id") or "",
            it.get("title", ""),
            it.get("severity") or "",
            it.get("cvss_score") if it.get("cvss_score") is not None else "",
            ";".join(it.get("cves") or []),
            ";".join(it.get("jvn_ids") or []),
            it.get("link", ""),
        ])
    return out.getvalue()


def list_markdown(items: list[dict[str, Any]]) -> str:
    out = ["| # | Source | Category | Date | Title | CVEs | Severity | URL |",
           "|---|--------|----------|------|-------|------|----------|-----|"]
    for i, it in enumerate(items, 1):
        title = (it.get("title") or "").replace("|", "\\|")
        cves = ", ".join(it.get("cves") or [])
        sev = it.get("severity") or ""
        out.append(
            f"| {i} | {it.get('source','')} | {it.get('category','')} | "
            f"{(it.get('date') or '')[:10]} | {title} | {cves} | {sev} | "
            f"{it.get('link','')} |"
        )
    return "\n".join(out)


def detail_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def detail_markdown(payload: dict[str, Any]) -> str:
    out: list[str] = [f"# {payload.get('title','')}", ""]
    if payload.get("id"):
        out.append(f"- ID: {payload['id']}")
    if payload.get("date_first_published"):
        out.append(f"- 初出: {payload['date_first_published']}")
    if payload.get("date_last_updated"):
        out.append(f"- 更新: {payload['date_last_updated']}")
    if payload.get("date_public"):
        out.append(f"- 公開: {payload['date_public']}")
    if payload.get("url"):
        out.append(f"- URL: {payload['url']}")
    if payload.get("cves"):
        out.append(f"- CVE: {', '.join(payload['cves'])}")
    if payload.get("jvn_ids"):
        out.append(f"- JVN: {', '.join(payload['jvn_ids'])}")
    out.append("")

    if payload.get("overview"):
        out.append("## 概要")
        out.append(payload["overview"])
        out.append("")
    if payload.get("affected"):
        out.append("## 影響を受ける製品")
        for a in payload["affected"]:
            line = f"- **{a.get('vendor','')}** {a.get('product','')}"
            if a.get("versions"):
                line += " — " + ", ".join(a["versions"])
            if a.get("cpe"):
                line += f"  ({a['cpe']})"
            out.append(line)
        out.append("")
    if payload.get("cvss"):
        out.append("## CVSS")
        for c in payload["cvss"]:
            score = c.get("score")
            sev = c.get("severity") or ""
            out.append(
                f"- CVSS{c.get('version','')}: "
                f"{('%.1f' % score) if isinstance(score, (int, float)) else 'N/A'} "
                f"({sev})  {c.get('vector','')}"
            )
        out.append("")
    if payload.get("impact"):
        out.append("## 想定される影響")
        out.append(payload["impact"])
        out.append("")
    if payload.get("mitigation"):
        out.append("## 対策")
        out.append(payload["mitigation"])
        out.append("")
    if payload.get("references"):
        out.append("## 参考情報")
        for r in payload["references"]:
            label = r.get("title") or r.get("name") or r.get("id") or r.get("url")
            out.append(f"- {label} <{r['url']}>")
        out.append("")
    if payload.get("sections"):
        for name, body in payload["sections"].items():
            out.append(f"## {name}")
            out.append(body)
            out.append("")
    elif payload.get("body_text"):
        out.append("## 本文")
        out.append(payload["body_text"])

    return "\n".join(out).rstrip() + "\n"
