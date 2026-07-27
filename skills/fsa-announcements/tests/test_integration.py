"""Integration tests that hit the live FSA endpoints.

Run only when explicitly selected:

    uv run --project scripts --extra dev pytest -m integration

These tests intentionally exercise the live HTML/RSS so that any FSA
structure change is caught the next time the suite runs."""

from __future__ import annotations

import datetime as dt

import pytest

from fetch_announcements import (
    RECENT_URL_TEMPLATE,
    RSS_URL,
    http_get,
    parse_recent_html,
    parse_rss,
)

pytestmark = pytest.mark.integration


def test_live_rss_returns_at_least_one_item():
    items = parse_rss(http_get(RSS_URL))
    assert len(items) > 0
    assert all(a.url.startswith("https://www.fsa.go.jp/") for a in items)


def test_live_rss_pubdates_are_recent():
    items = parse_rss(http_get(RSS_URL))
    today = dt.datetime.now(dt.timezone.utc).date()
    # The newest entry should be within the last 90 days.
    newest = max(a.published for a in items)
    assert (today - newest).days <= 90, f"newest pubDate suspicious: {newest}"


def test_live_recent_current_year_parses_with_canonical_categories():
    year = dt.datetime.now(dt.timezone.utc).year
    items = parse_recent_html(
        http_get(RECENT_URL_TEMPLATE.format(year=year)),
        year=year,
        min_entries=10,
    )
    cats = {a.category for a in items if a.category}
    canonical = {
        "報道発表", "記者会見", "審議会等", "国際関係",
        "イベント", "刊行物", "採用", "調達", "その他",
    }
    # Every category we observe must come from the canonical set,
    # otherwise FSA introduced a new label and we want to know.
    assert cats.issubset(canonical), f"unexpected category(s): {cats - canonical}"


def test_live_recent_2025_archive_exceeds_yearly_baseline():
    items = parse_recent_html(
        http_get(RECENT_URL_TEMPLATE.format(year=2025)),
        year=2025,
        min_entries=100,
    )
    # 2025 was a complete year by the time this test runs; we expect a
    # comfortably four-digit count. A sudden drop is itself a red flag.
    assert len(items) >= 800
