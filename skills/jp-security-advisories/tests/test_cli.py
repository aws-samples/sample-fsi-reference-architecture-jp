"""CLI tests via subprocess."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "fetch_advisories.py"


def _run(*args: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(SCRIPT), *args]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


class TestCLIOffline:
    def test_help(self):
        r = _run("--help")
        assert r.returncode == 0
        assert "list-sources" in r.stdout
        assert "detail" in r.stdout

    def test_list_sources_json(self):
        r = _run("list-sources", "--format", "json")
        assert r.returncode == 0, r.stderr
        payload = json.loads(r.stdout)
        names = [s["name"] for s in payload["sources"]]
        assert {"jpcert", "jpcert-all", "myjvn-alert", "myjvn-vuln"} <= set(names)

    def test_list_sources_markdown(self):
        r = _run("list-sources", "--format", "markdown")
        assert r.returncode == 0
        assert "| Source | Backend |" in r.stdout

    def test_unknown_source_error(self):
        r = _run("list", "--sources", "not-a-source")
        assert r.returncode == 1
        err = json.loads(r.stderr.splitlines()[-1])
        assert err["error"] is True and err["code"] == "UNKNOWN_SOURCE"

    def test_detail_unsupported_source(self):
        r = _run("detail", "--source", "myjvn-alert", "JVNDB-2026-018267")
        # myjvn-alert is not in DETAIL_CAPABLE — argparse rejects it as not-a-choice
        assert r.returncode != 0


@pytest.mark.integration
class TestCLILive:
    def test_list_jpcert_only(self, tmp_path: Path):
        r = _run(
            "list", "--sources", "jpcert",
            "--no-date-filter", "--limit", "3",
            "--cache-dir", str(tmp_path),
        )
        assert r.returncode == 0, r.stderr
        payload = json.loads(r.stdout)
        assert payload["metadata"]["sources_used"] == ["jpcert"]
        assert 0 < len(payload["items"]) <= 3
        for it in payload["items"]:
            assert it["source"] == "jpcert"

    def test_list_myjvn_vuln_severity_high(self, tmp_path: Path):
        r = _run(
            "list", "--sources", "myjvn-vuln",
            "--severity", "high", "--no-date-filter", "--limit", "3",
            "--cache-dir", str(tmp_path),
        )
        assert r.returncode == 0, r.stderr
        payload = json.loads(r.stdout)
        assert payload["metadata"]["sources_used"] == ["myjvn-vuln"]
        for it in payload["items"]:
            assert it["source"] == "myjvn-vuln"
            assert it["severity"] in {"high", "critical"}

    def test_list_myjvn_alert_smoke(self, tmp_path: Path):
        r = _run(
            "list", "--sources", "myjvn-alert",
            "--no-date-filter", "--limit", "3",
            "--cache-dir", str(tmp_path),
        )
        assert r.returncode == 0, r.stderr
        payload = json.loads(r.stdout)
        assert payload["metadata"]["sources_used"] == ["myjvn-alert"]
        # Each item should carry severity normalised to one of the known terms
        valid = {"critical", "important", "low", "info", None}
        for it in payload["items"]:
            assert it.get("severity") in valid

    def test_detail_myjvn_vuln(self, tmp_path: Path):
        r = _run(
            "detail", "--source", "myjvn-vuln", "JVNDB-2026-018267",
            "--cache-dir", str(tmp_path),
        )
        assert r.returncode == 0, r.stderr
        payload = json.loads(r.stdout)
        assert payload["source"] == "myjvn-vuln"
        assert payload["id"] == "JVNDB-2026-018267"
        assert payload["title"]
        assert isinstance(payload.get("affected"), list)
        assert isinstance(payload.get("cvss"), list)
        assert isinstance(payload.get("references"), list)

    def test_detail_jpcert(self, tmp_path: Path):
        # Discover a JPCERT alert URL
        r1 = _run(
            "list", "--sources", "jpcert",
            "--no-date-filter", "--category", "alert", "--limit", "1",
            "--cache-dir", str(tmp_path),
        )
        items = json.loads(r1.stdout)["items"]
        if not items:
            pytest.skip("no JPCERT alert items available")
        url = items[0]["link"]
        r2 = _run(
            "detail", "--source", "jpcert", url,
            "--cache-dir", str(tmp_path),
        )
        assert r2.returncode == 0, r2.stderr
        d = json.loads(r2.stdout)
        assert d["source"] == "jpcert"
        assert d["url"] == url
        assert d["title"]

    def test_csv_format(self, tmp_path: Path):
        r = _run(
            "list", "--sources", "jpcert",
            "--no-date-filter", "--limit", "2", "--format", "csv",
            "--cache-dir", str(tmp_path),
        )
        assert r.returncode == 0, r.stderr
        first = r.stdout.splitlines()[0]
        assert first.startswith("source,category,date,id,title")

    def test_default_writes_no_cache_files(self, tmp_path: Path, monkeypatch):
        """Without --cache-dir, the CLI must not write anywhere on disk.

        We point HOME and XDG_CACHE_HOME at an empty tmp dir and run the CLI;
        afterwards the dir tree must still be empty (no fallback to a default
        cache location)."""
        env_home = tmp_path / "home"
        env_home.mkdir()
        monkeypatch.setenv("HOME", str(env_home))
        monkeypatch.setenv("XDG_CACHE_HOME", str(env_home / ".cache"))
        cmd = [
            sys.executable, str(SCRIPT),
            "list", "--sources", "jpcert",
            "--no-date-filter", "--limit", "1",
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, r.stderr
        # tmp_path/home should be unchanged: no .cache or any other artefacts.
        leftover = list(env_home.rglob("*"))
        assert leftover == [], f"unexpected files: {leftover}"
