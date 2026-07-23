"""Integration tests: verify metadata retrieval for ALL BOJ databases.

Run with: pytest tests/test_all_db.py -m integration -v
These tests hit the live API with rate limiting (2s+ between requests).
"""

from __future__ import annotations

import time

import pytest

from boj_statistics.boj_client import BojClient
from boj_statistics.constants import DB_CATALOG

pytestmark = pytest.mark.integration

# All 50 DB names from the BOJ API manual
ALL_DB_NAMES = list(DB_CATALOG.keys())


class TestAllDbMetadata:
    """Verify that the Metadata API returns a successful response for every DB."""

    @pytest.fixture(autouse=True)
    def _rate_limit(self):
        """Enforce minimum 2s gap between API calls."""
        yield
        time.sleep(2.0)

    @pytest.mark.parametrize("db_name", ALL_DB_NAMES)
    def test_metadata_returns_200(self, db_name: str):
        client = BojClient(lang="jp", max_pages=1)
        result = client.get_metadata(db_name)
        assert result.status.status == 200, (
            f"DB '{db_name}' returned status {result.status.status}: "
            f"[{result.status.message_id}] {result.status.message}"
        )
        assert len(result.series) > 0, f"DB '{db_name}' returned no series"
