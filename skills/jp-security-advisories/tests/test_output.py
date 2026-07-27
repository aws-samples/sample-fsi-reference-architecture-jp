"""Output formatter tests.

Markdown output must not embed any MyJVN API attribution footer; the
attribution requirement is documented in NOTICES.md and SKILL.md and is
expected to be honored by the displaying agent / human, not injected
mechanically into every generated table.
"""

from __future__ import annotations

from jpsec import output


SAMPLE_JPCERT_ITEM = {
    "source": "jpcert", "category": "alert",
    "title": "x", "link": "u", "date": "2026-01-01T00:00:00+09:00",
}
SAMPLE_MYJVN_ALERT_ITEM = {
    "source": "myjvn-alert", "category": "info",
    "title": "x", "link": "u", "date": "2026-01-01T00:00:00+09:00",
}
SAMPLE_MYJVN_VULN_ITEM = {
    "source": "myjvn-vuln", "category": "high",
    "title": "x", "link": "u", "date": "2026-01-01T00:00:00+09:00",
}


class TestListMarkdownNoEmbeddedAttribution:
    def test_jpcert_only_no_myjvn_text(self):
        md = output.list_markdown([SAMPLE_JPCERT_ITEM])
        assert "MyJVN" not in md

    def test_myjvn_alert_only_no_attribution_footer(self):
        md = output.list_markdown([SAMPLE_MYJVN_ALERT_ITEM])
        # Item link/source values are echoed in the table body but no
        # standalone attribution sentence should be appended.
        assert "提供" not in md
        assert "provided by" not in md.lower()

    def test_myjvn_vuln_only_no_attribution_footer(self):
        md = output.list_markdown([SAMPLE_MYJVN_VULN_ITEM])
        assert "提供" not in md
        assert "provided by" not in md.lower()


class TestDetailMarkdownNoEmbeddedAttribution:
    def test_jpcert_detail_no_attribution(self):
        payload = {
            "source": "jpcert", "url": "u", "title": "x", "body_text": "body",
        }
        md = output.detail_markdown(payload)
        assert "MyJVN" not in md
        assert "提供" not in md

    def test_myjvn_vuln_detail_no_attribution_footer(self):
        payload = {
            "source": "myjvn-vuln",
            "url": "https://jvndb.jvn.jp/ja/contents/2026/JVNDB-2026-018267.html",
            "id": "JVNDB-2026-018267",
            "title": "Securly",
            "overview": "Overview text",
            "affected": [{"vendor": "X", "product": "Y", "versions": []}],
            "cvss": [],
            "references": [],
        }
        md = output.detail_markdown(payload)
        assert "MyJVN" not in md
        assert "provided by" not in md.lower()
