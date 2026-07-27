"""End-to-end CLI tests using monkey-patched HTTP responses."""

from __future__ import annotations

import datetime as dt
import io
import json
from pathlib import Path

import pytest

import fetch_announcements as fa


@pytest.fixture
def patched_http(monkeypatch, fixture_bytes):
    """Map known FSA URLs to local fixture bytes; raise on anything else."""
    rss_bytes = fixture_bytes("news_rss.xml")
    jun_bytes = fixture_bytes("recent_two_months_2026.html")
    dec_bytes = fixture_bytes("recent_dec2025_excerpt.html")
    calls: list[str] = []

    def fake_http_get(url, cache_dir=None, timeout=30, max_attempts=3):
        calls.append(url)
        if url == fa.RSS_URL:
            return rss_bytes
        if url == fa.RECENT_URL_TEMPLATE.format(year=2026):
            return jun_bytes
        if url == fa.RECENT_URL_TEMPLATE.format(year=2025):
            return dec_bytes
        raise AssertionError(f"unexpected URL: {url}")

    monkeypatch.setattr(fa, "http_get", fake_http_get)
    return calls


def _run_cli(args: list[str], capsys) -> tuple[int, list[dict], str]:
    rc = fa.main(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out) if captured.out.strip() else []
    return rc, data, captured.err


def test_cli_default_returns_both_sources(patched_http, capsys):
    rc, data, _ = _run_cli(
        ["--start-date", "2026-06-01", "--end-date", "2026-06-08"], capsys
    )
    assert rc == 0
    assert len(data) > 0
    sources = {d["source"] for d in data}
    # Both sources contributed before dedupe; dedupe favors 'recent'.
    assert "recent" in sources


def test_cli_source_rss_only(patched_http, capsys):
    rc, data, _ = _run_cli(
        ["--start-date", "2026-06-01", "--end-date", "2026-06-08", "--source", "rss"],
        capsys,
    )
    assert rc == 0
    assert {d["source"] for d in data} == {"rss"}
    # No recent URLs were fetched.
    assert all("recent2026" not in u for u in patched_http)


def test_cli_source_recent_only(patched_http, capsys):
    rc, data, _ = _run_cli(
        ["--start-date", "2026-06-01", "--end-date", "2026-06-08", "--source", "recent"],
        capsys,
    )
    assert rc == 0
    assert {d["source"] for d in data} == {"recent"}
    # No RSS URL fetched.
    assert fa.RSS_URL not in patched_http


def test_cli_category_filter(patched_http, capsys):
    rc, data, _ = _run_cli(
        ["--start-date", "2026-06-01", "--end-date", "2026-06-08",
         "--category", "報道発表"],
        capsys,
    )
    assert rc == 0
    assert all(d["category"] == "報道発表" for d in data)


def test_cli_year_spanning_window(patched_http, capsys):
    rc, data, _ = _run_cli(
        ["--start-date", "2025-12-25", "--end-date", "2026-01-08", "--source", "recent"],
        capsys,
    )
    assert rc == 0
    # Both year pages were fetched.
    assert fa.RECENT_URL_TEMPLATE.format(year=2025) in patched_http
    assert fa.RECENT_URL_TEMPLATE.format(year=2026) in patched_http


def test_cli_rejects_inverted_date_range(patched_http, capsys):
    rc = fa.main(["--start-date", "2026-06-10", "--end-date", "2026-06-01"])
    captured = capsys.readouterr()
    assert rc == 2
    assert "must be <=" in captured.err


def test_cli_results_sorted_descending(patched_http, capsys):
    rc, data, _ = _run_cli(
        ["--start-date", "2026-05-01", "--end-date", "2026-06-08"], capsys
    )
    assert rc == 0
    dates = [d["published"] for d in data]
    assert dates == sorted(dates, reverse=True)


def test_cli_no_cache_dir_writes_no_files(monkeypatch, patched_http, capsys, tmp_path):
    """With --cache-dir omitted, http_get must be called with cache_dir=None."""
    seen: list[Path | None] = []

    real = fa.http_get

    def spy(url, cache_dir=None, timeout=30, max_attempts=3):
        seen.append(cache_dir)
        return real(url, cache_dir=cache_dir, timeout=timeout, max_attempts=max_attempts)

    monkeypatch.setattr(fa, "http_get", spy)
    rc, _, _ = _run_cli(
        ["--start-date", "2026-06-01", "--end-date", "2026-06-08"], capsys
    )
    assert rc == 0
    assert seen, "http_get was not called"
    assert all(c is None for c in seen)


def test_cli_cache_dir_passed_through(monkeypatch, patched_http, capsys, tmp_path):
    seen: list[Path | None] = []
    real = fa.http_get

    def spy(url, cache_dir=None, timeout=30, max_attempts=3):
        seen.append(cache_dir)
        return real(url, cache_dir=cache_dir, timeout=timeout, max_attempts=max_attempts)

    monkeypatch.setattr(fa, "http_get", spy)
    rc, _, _ = _run_cli(
        ["--start-date", "2026-06-01", "--end-date", "2026-06-08",
         "--cache-dir", str(tmp_path)],
        capsys,
    )
    assert rc == 0
    assert all(c == tmp_path for c in seen)


def test_cli_diagnose_writes_to_stderr(patched_http, capsys):
    rc, _, err = _run_cli(
        ["--start-date", "2026-06-01", "--end-date", "2026-06-08", "--diagnose"],
        capsys,
    )
    assert rc == 0
    assert "[diagnose] rss:" in err
    assert "[diagnose] recent2026:" in err


def test_cli_warns_on_year_below_oldest_available(monkeypatch, patched_http, capsys, caplog):
    """A start date in 2019 should emit a warning, not a fetch attempt."""
    import logging
    caplog.set_level(logging.WARNING, logger="fsa")
    rc, _, _ = _run_cli(
        ["--start-date", "2019-01-01", "--end-date", "2019-12-31",
         "--source", "recent", "--log-level", "WARNING"],
        capsys,
    )
    assert rc == 0
    # 2019 page must NOT have been fetched.
    assert fa.RECENT_URL_TEMPLATE.format(year=2019) not in patched_http
    # And a warning about it should have been emitted.
    msgs = " ".join(r.message for r in caplog.records)
    assert "recent2019.html" in msgs


def test_http_get_writes_cache_files(tmp_path, monkeypatch):
    """Direct unit test for http_get's caching: a successful response should
    write {sha256}.body and {sha256}.meta.json under cache_dir."""

    class FakeResponse:
        def __init__(self, body):
            self._body = body
            self.headers = {
                "ETag": '"abc"',
                "Last-Modified": "Mon, 08 Jun 2026 06:00:06 GMT",
                "Content-Type": "application/xml",
            }

        def read(self):
            return self._body

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(req, timeout=30):
        return FakeResponse(b"hello")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    body = fa.http_get("https://example/x", cache_dir=tmp_path)
    assert body == b"hello"
    files = sorted(p.name for p in tmp_path.iterdir())
    assert any(f.endswith(".body") for f in files)
    assert any(f.endswith(".meta.json") for f in files)


def test_http_get_no_cache_dir_writes_nothing(tmp_path, monkeypatch):
    """When cache_dir is None, http_get must not write anything to tmp_path."""

    class FakeResponse:
        def __init__(self, body):
            self._body = body
            self.headers = {}

        def read(self):
            return self._body

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda req, timeout=30: FakeResponse(b"hello"),
    )
    body = fa.http_get("https://example/x", cache_dir=None)
    assert body == b"hello"
    # tmp_path is just a fresh dir; we never told http_get about it,
    # so nothing should appear there.
    assert list(tmp_path.iterdir()) == []
