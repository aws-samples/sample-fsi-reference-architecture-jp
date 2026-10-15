"""Tests for filter_by_date and dedupe_by_url."""

from __future__ import annotations

import datetime as dt

from fetch_announcements import (
    Announcement,
    dedupe_by_url,
    filter_by_date,
)


def _ann(source: str, day: int, url: str, title: str = "t", category: str | None = None) -> Announcement:
    return Announcement(
        source=source,
        published=dt.date(2026, 6, day),
        category=category,
        title=title,
        url=url,
    )


def test_filter_by_date_inclusive_bounds():
    items = [_ann("rss", 1, "u1"), _ann("rss", 5, "u5"), _ann("rss", 10, "u10")]
    out = filter_by_date(items, dt.date(2026, 6, 5), dt.date(2026, 6, 5))
    assert [a.url for a in out] == ["u5"]


def test_filter_by_date_excludes_outside_window():
    items = [_ann("rss", 1, "u1"), _ann("rss", 30, "u30")]
    out = filter_by_date(items, dt.date(2026, 6, 2), dt.date(2026, 6, 29))
    assert out == []


def test_filter_by_date_keeps_window_only():
    items = [_ann("rss", d, f"u{d}") for d in (1, 5, 10, 15, 20)]
    out = filter_by_date(items, dt.date(2026, 6, 5), dt.date(2026, 6, 15))
    assert sorted(a.url for a in out) == ["u10", "u15", "u5"]


def test_dedupe_prefers_recent_over_rss():
    rss = _ann("rss", 1, "u", title="rss-title", category=None)
    rec = _ann("recent", 1, "u", title="recent-title", category="報道発表")
    out = dedupe_by_url([rss, rec])
    assert len(out) == 1
    assert out[0].source == "recent"
    assert out[0].category == "報道発表"


def test_dedupe_keeps_first_when_both_same_source():
    a = _ann("rss", 1, "u", title="first")
    b = _ann("rss", 1, "u", title="second")
    out = dedupe_by_url([a, b])
    assert len(out) == 1
    assert out[0].title == "first"


def test_dedupe_does_not_collapse_distinct_urls():
    items = [_ann("rss", 1, "u1"), _ann("rss", 1, "u2"), _ann("recent", 1, "u3")]
    out = dedupe_by_url(items)
    assert {a.url for a in out} == {"u1", "u2", "u3"}
