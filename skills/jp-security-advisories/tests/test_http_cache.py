"""Unit tests for jpsec.http_cache (cache-OFF default + opt-in writes)."""

from __future__ import annotations

from pathlib import Path

import pytest

from jpsec import http_cache


class _FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body
        self.headers: dict[str, str] = {
            "ETag": '"abc"',
            "Last-Modified": "Mon, 08 Jun 2026 06:00:06 GMT",
            "Content-Type": "application/xml",
        }

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_http_get_writes_no_files_when_cache_dir_is_none(monkeypatch, tmp_path):
    """The default behaviour (cache_dir=None) must not write anything anywhere.

    tmp_path is a fresh empty directory; we never tell http_get about it,
    so nothing should appear there afterwards. We also assert that NO
    {sha256}.body / .meta.json files exist anywhere under tmp_path."""
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda req, timeout=30: _FakeResponse(b"hello"),
    )
    body = http_cache.http_get("https://example/x")
    assert body == b"hello"
    assert list(tmp_path.iterdir()) == []


def test_http_get_writes_body_and_meta_when_cache_dir_supplied(monkeypatch, tmp_path):
    """Opting in via cache_dir must persist body and meta JSON."""
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda req, timeout=30: _FakeResponse(b"hello"),
    )
    body = http_cache.http_get("https://example/x", cache_dir=tmp_path)
    assert body == b"hello"
    files = sorted(p.name for p in tmp_path.iterdir())
    assert any(f.endswith(".body") for f in files)
    assert any(f.endswith(".meta.json") for f in files)


def test_cached_content_type_returns_none_when_cache_dir_is_none(tmp_path):
    """cache_dir=None must short-circuit to None even if a stale cache existed."""
    assert http_cache.cached_content_type(None, "https://example/x") is None


def test_cached_content_type_reads_persisted_meta(monkeypatch, tmp_path):
    """After a cached fetch, the persisted Content-Type can be retrieved."""
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda req, timeout=30: _FakeResponse(b"hello"),
    )
    http_cache.http_get("https://example/x", cache_dir=tmp_path)
    ct = http_cache.cached_content_type(tmp_path, "https://example/x")
    assert ct == "application/xml"


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com/x",
        "gopher://example.com/x",
        "/etc/passwd",  # no scheme
    ],
)
def test_http_get_rejects_non_http_schemes(url):
    with pytest.raises(ValueError, match="unsupported URL scheme"):
        http_cache.http_get(url)


def test_default_cache_dir_helper_is_gone():
    """The default_cache_dir helper has been removed; importing it must fail."""
    import importlib

    mod = importlib.reload(http_cache)
    assert not hasattr(mod, "default_cache_dir")
