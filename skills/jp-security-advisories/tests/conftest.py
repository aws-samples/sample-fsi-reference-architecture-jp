"""Shared fixtures for jp-security-advisories tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

FIXTURES = Path(__file__).resolve().parent / "fixtures"
FEED_DIR = FIXTURES / "feeds"
DETAIL_DIR = FIXTURES / "details"
MYJVN_DIR = FIXTURES / "myjvn"


@pytest.fixture
def scripts_dir() -> Path:
    return _SCRIPTS_DIR


@pytest.fixture
def feed_bytes():
    """Load a JPCERT RSS fixture by source name."""

    def _load(source: str) -> bytes:
        return (FEED_DIR / f"{source}.rdf").read_bytes()

    return _load


@pytest.fixture
def detail_bytes():
    """Load a JPCERT detail HTML fixture by source name."""

    def _load(source: str) -> bytes:
        name = {"jpcert": "jpcert-at"}.get(source, source)
        return (DETAIL_DIR / f"{name}.html").read_bytes()

    return _load


@pytest.fixture
def myjvn_bytes():
    """Load a MyJVN API response fixture by name."""

    def _load(name: str) -> bytes:
        return (MYJVN_DIR / name).read_bytes()

    return _load
