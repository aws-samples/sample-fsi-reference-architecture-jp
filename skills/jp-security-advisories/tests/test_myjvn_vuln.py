"""MyJVN getVulnOverviewList / getVulnDetailInfo parser tests."""

from __future__ import annotations

from jpsec.adapters.myjvn_vuln import (
    _build_detail_url,
    _build_overview_url,
    _date_params,
    parse_detail,
    parse_overview,
)


class TestParseOverview:
    def test_overview_yields_items(self, myjvn_bytes):
        items = parse_overview(myjvn_bytes("getVulnOverviewList.rdf"))
        assert len(items) > 0
        for it in items:
            assert it["source"] == "myjvn-vuln"
            assert it["title"]
            assert it["link"].startswith("https://jvndb.jvn.jp/")
            assert it.get("id", "").startswith("JVNDB-")
            # cvss_score must be numeric or None
            assert it.get("cvss_score") is None or isinstance(it["cvss_score"], (int, float))

    def test_severity_picked_from_highest_cvss(self, myjvn_bytes):
        items = parse_overview(myjvn_bytes("getVulnOverviewList.rdf"))
        sev_values = {it.get("severity") for it in items}
        assert sev_values <= {None, "none", "low", "medium", "high", "critical"}

    def test_cves_extracted_from_references(self, myjvn_bytes):
        items = parse_overview(myjvn_bytes("getVulnOverviewList.rdf"))
        all_cves: set[str] = set()
        for it in items:
            all_cves.update(it.get("cves") or [])
        # Most JVN iPedia entries reference at least one CVE
        assert any(c.startswith("CVE-") for c in all_cves)


class TestParseDetail:
    def test_detail_minimum_shape(self, myjvn_bytes):
        d = parse_detail(myjvn_bytes("getVulnDetailInfo.xml"))
        assert d["source"] == "myjvn-vuln"
        assert d["id"] == "JVNDB-2026-018267"
        assert d["title"]
        assert d["url"].endswith(f"{d['id']}.html")
        assert isinstance(d["affected"], list)
        assert isinstance(d["cvss"], list)
        assert isinstance(d["references"], list)

    def test_rich_detail_has_many_cves_and_affected(self, myjvn_bytes):
        d = parse_detail(myjvn_bytes("getVulnDetailInfo-rich.xml"))
        assert d["id"] == "JVNDB-2026-018098"
        # The Hitachi disk array bundle references many Microsoft CVEs
        assert len(d["cves"]) > 50
        assert all(c.startswith("CVE-") for c in d["cves"])
        # Affected products are populated
        assert len(d["affected"]) >= 1
        for a in d["affected"]:
            assert "vendor" in a and "product" in a

    def test_dates_parsed(self, myjvn_bytes):
        d = parse_detail(myjvn_bytes("getVulnDetailInfo-rich.xml"))
        assert d["date_first_published"]
        assert d["date_last_updated"]


class TestUrlBuilders:
    def test_overview_url_includes_required_params(self):
        url = _build_overview_url(start_item=1, max_count=10)
        assert "method=getVulnOverviewList" in url
        assert "feed=hnd" in url
        assert "startItem=1" in url
        assert "maxCountItem=10" in url

    def test_overview_url_severity_translated_to_single_letter(self):
        url = _build_overview_url(severity="high")
        assert "severity=h" in url

    def test_overview_url_with_cpe_and_keyword(self):
        url = _build_overview_url(keyword="microsoft", cpe="cpe:/a:microsoft:office")
        assert "keyword=microsoft" in url
        assert "cpeName=cpe" in url

    def test_detail_url_with_single_id(self):
        url = _build_detail_url(["JVNDB-2026-018267"])
        assert "method=getVulnDetailInfo" in url
        assert "vulnId=JVNDB-2026-018267" in url

    def test_detail_url_with_multiple_ids_uses_plus_separator(self):
        url = _build_detail_url(["JVNDB-2026-018267", "JVNDB-2026-018098"])
        assert "vulnId=JVNDB-2026-018267+JVNDB-2026-018098" in url


class TestDateParams:
    def test_date_mode_published(self):
        import datetime as dt
        p = _date_params(dt.date(2026, 1, 15), dt.date(2026, 6, 5), "published")
        assert p == {
            "datePublishedStartY": "2026",
            "datePublishedStartM": "01",
            "datePublishedStartD": "15",
            "datePublishedEndY": "2026",
            "datePublishedEndM": "06",
            "datePublishedEndD": "05",
        }

    def test_date_mode_public(self):
        import datetime as dt
        p = _date_params(dt.date(2026, 4, 1), None, "public")
        assert p == {
            "datePublicStartY": "2026",
            "datePublicStartM": "04",
            "datePublicStartD": "01",
        }

    def test_date_mode_first_published(self):
        import datetime as dt
        p = _date_params(None, dt.date(2026, 6, 1), "first-published")
        assert "dateFirstPublishedEndY" in p

    def test_invalid_mode_falls_back_to_published(self):
        import datetime as dt
        p = _date_params(dt.date(2026, 1, 1), None, "bogus-mode")
        assert "datePublishedStartY" in p
