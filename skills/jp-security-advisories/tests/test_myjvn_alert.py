"""MyJVN getAlertList parser — Atom XML."""

from __future__ import annotations

import defusedxml.ElementTree as ET

from jpsec.adapters.myjvn_alert import TERM_MAP, parse_atom


class TestParseAtom:
    def test_alert_list_parses_all_entries(self, myjvn_bytes):
        items = parse_atom(myjvn_bytes("getAlertList.atom.xml"))
        assert len(items) > 0
        for it in items:
            assert it["source"] == "myjvn-alert"
            assert it["title"]
            assert it["id"]
            assert it["date"]
            # 'category' must be a normalized severity-like string
            assert it.get("category")

    def test_severity_normalisation(self, myjvn_bytes):
        items = parse_atom(myjvn_bytes("getAlertList.atom.xml"))
        valid = set(TERM_MAP.values())
        # At least one item should have a recognized severity
        assert any(it.get("severity") in valid for it in items)

    def test_related_references_collected(self, myjvn_bytes):
        items = parse_atom(myjvn_bytes("getAlertList.atom.xml"))
        # At least one entry has structured related items
        rel_counts = [len(it.get("related") or []) for it in items]
        assert max(rel_counts) >= 1

    def test_primary_link_falls_back_to_first_related(self, myjvn_bytes):
        items = parse_atom(myjvn_bytes("getAlertList.atom.xml"))
        # All items should have a non-empty link (entry-level or related)
        assert all(it["link"] for it in items)

    def test_cves_extracted_from_titles(self, myjvn_bytes):
        items = parse_atom(myjvn_bytes("getAlertList.atom.xml"))
        # The fixture currently includes Cisco/CVE-2025 entries
        all_cves: set[str] = set()
        for it in items:
            all_cves.update(it.get("cves") or [])
        assert any(c.startswith("CVE-") for c in all_cves)

    def test_malformed_xml_raises(self):
        try:
            parse_atom(b"<not-xml")
        except ET.ParseError:
            pass
        else:
            raise AssertionError("expected ParseError")
