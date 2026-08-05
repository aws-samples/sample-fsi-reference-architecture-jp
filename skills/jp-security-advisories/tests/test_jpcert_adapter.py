"""JPCERT adapter — RSS parsing, classification, HTML detail extraction."""

from __future__ import annotations

import datetime as dt

import pytest

from jpsec.adapters.jpcert import (
    classify,
    extract_sections,
    parse_detail_html,
    parse_feed,
)
from jpsec.filters import filter_items
from jpsec.ids import extract_ids


class TestParseFeed:
    def test_jpcert_rss_yields_items(self, feed_bytes):
        items = parse_feed(feed_bytes("jpcert"), "jpcert")
        assert len(items) > 0
        for it in items:
            assert it["source"] == "jpcert"
            assert it["title"]
            assert it["link"].startswith("http")
            assert dt.datetime.fromisoformat(it["date"])

    def test_jpcert_all_classification_mix(self, feed_bytes):
        items = parse_feed(feed_bytes("jpcert-all"), "jpcert-all")
        cats = {it["category"] for it in items}
        assert len(cats) >= 2

    @pytest.mark.parametrize(
        "url,expected",
        [
            ("https://www.jpcert.or.jp/at/2026/at260015.html", "alert"),
            ("https://www.jpcert.or.jp/wr/2026/wr260520.html", "weekly-report"),
            ("https://www.jpcert.or.jp/tsubame/report/202601.html", "tsubame"),
            ("https://www.jpcert.or.jp/newsflash/2026010101.html", "news"),
            ("https://blogs.jpcert.or.jp/ja/2026/06/foo.html", "blog"),
            ("https://www.jpcert.or.jp/about/recruit.html", "other"),
        ],
    )
    def test_classify_url_pattern(self, url: str, expected: str):
        assert classify(url) == expected


class TestDetailHtml:
    def test_jpcert_at_sections_extracted(self, detail_bytes):
        html = detail_bytes("jpcert").decode("utf-8")
        parsed = parse_detail_html(html)
        assert "PAN-OS" in parsed["title"]
        assert {"概要", "対象", "対策", "参考情報"} <= set(parsed["sections"].keys())
        assert "CVE-2026-0265" in parsed["cves"]

    def test_extract_sections_handles_missing_headings(self):
        html = "<html><body><p>plain text without headings</p></body></html>"
        assert extract_sections(html) == {}


class TestExtractIDs:
    def test_extract_cve_uppercase_dedupe(self):
        cves, _ = extract_ids("cve-2026-0265 / CVE-2026-0265 / CVE-2025-20333")
        assert cves == ["CVE-2025-20333", "CVE-2026-0265"]

    def test_extract_jvn_id(self):
        _, jids = extract_ids("See JVN#35567473 and JVNDB-2026-018267")
        assert "JVN#35567473" in jids
        assert "JVNDB-2026-018267" in jids


class TestFilterItems:
    def test_date_keyword_category_cve(self):
        items = [
            {
                "source": "jpcert", "category": "alert", "title": "Cisco ASA",
                "link": "x", "date": "2026-04-15T10:00:00+09:00",
                "cves": ["CVE-2025-20333"],
            },
            {
                "source": "myjvn-alert", "category": "info", "title": "Joomla",
                "link": "y", "date": "2026-05-10T00:00:00+09:00", "cves": [],
            },
            {
                "source": "myjvn-vuln", "category": "high", "title": "TP-LINK",
                "link": "z", "date": "2026-06-05T12:00:00+09:00", "cves": [],
            },
        ]
        out = filter_items(
            items,
            start=dt.date(2026, 4, 1),
            end=dt.date(2026, 4, 30),
            keywords=["cisco"],
            category="alert",
            cves=["CVE-2025-20333"],
        )
        assert len(out) == 1 and out[0]["source"] == "jpcert"
