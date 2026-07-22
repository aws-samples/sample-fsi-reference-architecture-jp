"""Unit tests for fetch_announcements.http_get scheme validation."""

from __future__ import annotations

import pytest

import fetch_announcements as fa


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
        fa.http_get(url)
