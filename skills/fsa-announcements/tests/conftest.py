"""Shared fixtures for fsa-announcements tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def fixture_bytes():
    """Load a fixture file as raw bytes by relative filename."""

    def _load(name: str) -> bytes:
        return (FIXTURES / name).read_bytes()

    return _load
