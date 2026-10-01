"""Adapter abstract base."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Protocol


class ListQuery:
    """Bundle of list-time arguments passed to adapters."""

    def __init__(
        self,
        start: dt.date | None = None,
        end: dt.date | None = None,
        keywords: list[str] | None = None,
        category: str | None = None,
        cves: list[str] | None = None,
        severity: str | None = None,
        cpe: str | None = None,
        date_mode: str = "published",
        limit: int | None = None,
        cache_dir: Path | None = None,
    ) -> None:
        self.start = start
        self.end = end
        self.keywords = keywords
        self.category = category
        self.cves = cves
        self.severity = severity
        self.cpe = cpe
        self.date_mode = date_mode
        self.limit = limit
        self.cache_dir = cache_dir


class Adapter(Protocol):
    """Source adapter interface."""

    name: str

    def list_items(self, q: ListQuery) -> list[dict[str, Any]]: ...

    def detail(
        self, url_or_id: str, cache_dir: Path | None
    ) -> dict[str, Any]: ...
