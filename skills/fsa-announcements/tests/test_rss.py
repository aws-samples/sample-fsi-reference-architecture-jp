"""Tests for the RSS feed parser."""

from __future__ import annotations

import datetime as dt

import pytest

from fetch_announcements import (
    _parse_pubdate_jst,
    _split_rss_title,
    parse_rss,
)


def test_parse_rss_returns_15_items(fixture_bytes):
    items = parse_rss(fixture_bytes("news_rss.xml"))
    assert len(items) == 15


def test_parse_rss_assigns_rss_source(fixture_bytes):
    items = parse_rss(fixture_bytes("news_rss.xml"))
    assert all(a.source == "rss" for a in items)


def test_parse_rss_dates_in_jst_calendar(fixture_bytes):
    items = parse_rss(fixture_bytes("news_rss.xml"))
    dates = sorted({a.published for a in items})
    # Fixture spans 2026-06-02 to 2026-06-08 in JST.
    assert dates[0] == dt.date(2026, 6, 2)
    assert dates[-1] == dt.date(2026, 6, 8)


def test_parse_rss_extracts_known_categories(fixture_bytes):
    items = parse_rss(fixture_bytes("news_rss.xml"))
    cats = {a.category for a in items if a.category is not None}
    # All observed prefixes in the fixture should be picked up.
    assert {"採用", "国際関係", "その他", "記者会見"}.issubset(cats)


def test_parse_rss_handles_missing_category_prefix(fixture_bytes):
    """Some RSS titles arrive without any 'カテゴリ,' prefix — still parsed."""
    items = parse_rss(fixture_bytes("news_rss.xml"))
    no_cat = [a for a in items if a.category is None]
    assert no_cat, "expected at least one entry without a category prefix"
    # The first item in the FSA feed has no prefix.
    assert no_cat[0].title.startswith("「中小・地域金融機関向け")


def test_parse_rss_links_are_absolute(fixture_bytes):
    items = parse_rss(fixture_bytes("news_rss.xml"))
    assert all(a.url.startswith("https://www.fsa.go.jp/") for a in items)


def test_parse_pubdate_jst_substitutes_rfc822_offset():
    d = _parse_pubdate_jst("Mon, 08 Jun 2026 15:00:00 JST")
    assert d == dt.date(2026, 6, 8)


def test_parse_pubdate_jst_handles_explicit_offset():
    d = _parse_pubdate_jst("Mon, 08 Jun 2026 23:30:00 +0900")
    assert d == dt.date(2026, 6, 8)


def test_parse_pubdate_jst_late_evening_keeps_jst_calendar_day():
    """A 23:00 JST timestamp stays on the same JST calendar date even though
    its UTC equivalent is the previous day."""
    d = _parse_pubdate_jst("Tue, 02 Jun 2026 23:00:00 +0900")
    assert d == dt.date(2026, 6, 2)


@pytest.mark.parametrize(
    "title,expected_cat,expected_body",
    [
        ("報道発表,X について", "報道発表", "X について"),
        ("記者会見, 大臣会見", "記者会見", "大臣会見"),
        ("「題名」", None, "「題名」"),
        ("採用,職員を募集", "採用", "職員を募集"),
        ("審議会等,会合", "審議会等", "会合"),
    ],
)
def test_split_rss_title(title, expected_cat, expected_body):
    cat, body = _split_rss_title(title)
    assert cat == expected_cat
    assert body == expected_body


def test_parse_rss_skips_unparseable_pubdate():
    """A malformed pubDate should drop the item, not crash."""
    bad = (
        b'<?xml version="1.0"?>\n<rss version="2.0"><channel>'
        b"<item><title>x</title><link>https://example/</link>"
        b"<pubDate>not-a-date</pubDate></item>"
        b"</channel></rss>"
    )
    assert parse_rss(bad) == []
