"""Tests for the recent{YYYY}.html parser."""

from __future__ import annotations

import datetime as dt

import pytest

from fetch_announcements import (
    parse_recent_html,
    parse_wareki_date,
)


def test_parse_wareki_date_reiwa_halfwidth():
    assert parse_wareki_date("令和8年6月5日") == dt.date(2026, 6, 5)


def test_parse_wareki_date_reiwa_fullwidth():
    assert parse_wareki_date("令和８年６月５日") == dt.date(2026, 6, 5)


def test_parse_wareki_date_kansuji():
    assert parse_wareki_date("令和七年12月26日") == dt.date(2025, 12, 26)


def test_parse_wareki_date_gannen():
    # 元年 = first year of the era.
    assert parse_wareki_date("令和元年5月1日") == dt.date(2019, 5, 1)


def test_parse_wareki_date_heisei():
    assert parse_wareki_date("平成31年4月30日") == dt.date(2019, 4, 30)


@pytest.mark.parametrize("text", ["令和", "令和X年Y月Z日", "abc", ""])
def test_parse_wareki_date_invalid(text):
    assert parse_wareki_date(text) is None


def test_parse_recent_excerpt_yields_entries(fixture_bytes):
    items = parse_recent_html(
        fixture_bytes("recent_jun2026_excerpt.html"), year=2026, min_entries=1
    )
    assert items, "expected at least one entry"
    # Every entry must carry an authoritative category (recent.html is the
    # source of truth for category text).
    assert all(a.category for a in items)
    assert all(a.source == "recent" for a in items)


def test_parse_recent_excerpt_dates_within_target_month(fixture_bytes):
    items = parse_recent_html(
        fixture_bytes("recent_jun2026_excerpt.html"), year=2026, min_entries=1
    )
    months = {a.published.month for a in items}
    assert months == {6}
    years = {a.published.year for a in items}
    assert years == {2026}


def test_parse_recent_excerpt_categories_observed(fixture_bytes):
    items = parse_recent_html(
        fixture_bytes("recent_jun2026_excerpt.html"), year=2026, min_entries=1
    )
    cats = {a.category for a in items}
    # All categories observed in the fixture should be the canonical set.
    canonical = {
        "報道発表", "記者会見", "審議会等", "国際関係",
        "イベント", "刊行物", "採用", "調達", "その他",
    }
    assert cats.issubset(canonical)


def test_parse_recent_excerpt_urls_absolute(fixture_bytes):
    items = parse_recent_html(
        fixture_bytes("recent_jun2026_excerpt.html"), year=2026, min_entries=1
    )
    assert all(a.url.startswith("https://www.fsa.go.jp/") for a in items)


def test_parse_recent_two_months_covers_both(fixture_bytes):
    items = parse_recent_html(
        fixture_bytes("recent_two_months_2026.html"), year=2026, min_entries=1
    )
    months = {a.published.month for a in items}
    assert {5, 6}.issubset(months)


def test_parse_recent_dec2025_handles_year_boundary(fixture_bytes):
    items = parse_recent_html(
        fixture_bytes("recent_dec2025_excerpt.html"), year=2025, min_entries=1
    )
    assert items
    assert {a.published.year for a in items} == {2025}
    assert {a.published.month for a in items} == {12}


def test_parse_recent_raises_when_below_threshold(fixture_bytes):
    """If FSA changes the page structure and we end up parsing 0 entries,
    the call must raise rather than silently return []. The June fixture has
    well over 5 entries, so a threshold of 9999 forces the failure path."""
    with pytest.raises(RuntimeError, match="parsed only"):
        parse_recent_html(
            fixture_bytes("recent_jun2026_excerpt.html"),
            year=2026,
            min_entries=9999,
        )


def test_parse_recent_ignores_unrelated_li(fixture_bytes):
    """The fixture appends a <ul class='nav'> with non-announcement <li>
    items. They must not appear in the parsed output."""
    items = parse_recent_html(
        fixture_bytes("recent_jun2026_excerpt.html"), year=2026, min_entries=1
    )
    titles = {a.title for a in items}
    assert "戻る" not in titles
    assert "トップ" not in titles
