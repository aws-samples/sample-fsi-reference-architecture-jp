"""Common client-side filters for advisory items."""

from __future__ import annotations

import datetime as dt
from typing import Any


def _parse_date(s: str | None) -> dt.date | None:
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s).date()
    except Exception:
        return None


def filter_items(
    items: list[dict[str, Any]],
    start: dt.date | None = None,
    end: dt.date | None = None,
    keywords: list[str] | None = None,
    category: str | None = None,
    cves: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Apply common client-side filters to a normalized item list."""
    kw_lower = [k.lower() for k in (keywords or [])]
    cve_upper = [c.upper() for c in (cves or [])]
    out: list[dict[str, Any]] = []
    for it in items:
        if start is not None or end is not None:
            d = _parse_date(it.get("date"))
            if d is None:
                continue
            if start is not None and d < start:
                continue
            if end is not None and d > end:
                continue
        if kw_lower:
            hay = (it.get("title") or "") + " " + (it.get("description") or "")
            hay_l = hay.lower()
            if not any(k in hay_l for k in kw_lower):
                continue
        if category and it.get("category") != category:
            continue
        if cve_upper:
            item_cves = set(it.get("cves") or [])
            if not (item_cves & set(cve_upper)):
                continue
        out.append(it)
    return out
