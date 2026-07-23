"""Integration tests against the live BOJ API.

Run with: pytest -m integration
These tests require network access and may be slow due to rate limiting.
"""

from __future__ import annotations

import pytest

from boj_statistics.boj_client import BojClient
from boj_statistics.exceptions import BojApiError, BojClientNotFoundError


pytestmark = pytest.mark.integration


class TestCodeApiIntegration:
    def test_fetch_tankan_data(self):
        client = BojClient(lang="jp")
        result = client.get_data_by_code(
            db="CO",
            codes=["TK99F1000601GCQ01000"],
            start_date="202401",
            end_date="202404",
        )
        assert result.status.status == 200
        assert len(result.series) >= 1
        assert result.series[0].series_code != ""

    def test_invalid_db_raises_api_error(self):
        client = BojClient()
        with pytest.raises(BojApiError) as exc_info:
            client.get_data_by_code("INVALID_DB_NAME", ["DUMMY"])
        assert exc_info.value.status_code == 400

    def test_fetch_flow_of_funds_no_date_range(self):
        """FF DB, series FOF_FFAS100A100 (cash & deposits / financial institutions / stock),
        no date range specified — should return full history."""
        client = BojClient(lang="jp", max_pages=1)
        result = client.get_data_by_code(db="FF", codes=["FOF_FFAS100A100"])
        assert result.status.status == 200
        assert len(result.series) == 1
        s = result.series[0]
        assert s.series_code == "FOF_FFAS100A100"
        assert s.name == "資産・現金・預金／金融機関／ストック"
        assert s.unit == "億円"
        assert len(s.data_points) > 0
        # Verify the same data is obtainable via Layer API (layer 1,1,1)
        layer_result = client.get_data_by_layer(
            db="FF", layer="1,1,1,1", frequency="Q",
        )
        layer_codes = [ls.series_code for ls in layer_result.series]
        assert "FOF_FFAS100A100" in layer_codes


class TestLayerApiIntegration:
    def test_fetch_bop_specific_layer(self):
        """Specific layer path (1,1,1) with monthly frequency."""
        client = BojClient(lang="jp")
        result = client.get_data_by_layer(
            db="BP01",
            layer="1,1,1",
            frequency="M",
            start_date="202501",
            end_date="202503",
        )
        assert result.status.status == 200
        assert len(result.series) > 0
        series_with_data = [s for s in result.series if s.data_points]
        assert len(series_with_data) > 0
        assert series_with_data[0].series_code != ""
        assert series_with_data[0].data_points[0].date != ""

    def test_fetch_layer_wildcard(self):
        """Wildcard layer (*) — returns all series for the given frequency."""
        client = BojClient(lang="jp", max_pages=1)
        result = client.get_data_by_layer(
            db="IR01",
            layer="*",
            frequency="D",
            start_date="202503",
            end_date="202503",
        )
        assert result.status.status == 200
        assert len(result.series) > 0

    def test_fetch_layer_quarterly_tankan(self):
        """Layer API with quarterly frequency on Tankan (CO) — narrow 4-level hierarchy."""
        client = BojClient(lang="jp", max_pages=1)
        result = client.get_data_by_layer(
            db="CO",
            layer="1,1,1,1",
            frequency="Q",
            start_date="202401",
            end_date="202404",
        )
        assert result.status.status == 200
        assert len(result.series) > 0
        for s in result.series:
            if s.data_points:
                assert s.frequency != ""

    def test_fetch_layer_flow_of_funds(self):
        """Layer API on Flow of Funds (FF) — large DB, deep hierarchy."""
        client = BojClient(lang="jp", max_pages=1)
        result = client.get_data_by_layer(
            db="FF",
            layer="1,1,1",
            frequency="Q",
            start_date="202401",
            end_date="202404",
        )
        assert result.status.status == 200
        assert len(result.series) > 0

    def test_invalid_layer_raises_api_error(self):
        """Invalid layer info should return a 400 error from the API."""
        client = BojClient(lang="jp")
        with pytest.raises(BojApiError) as exc_info:
            client.get_data_by_layer(
                db="BP01",
                layer="999,999,999",
                frequency="M",
                start_date="202501",
                end_date="202503",
            )
        assert exc_info.value.status_code == 400

    # --- Frequency × date format combinations ---
    # API date format depends on frequency:
    #   CY/FY → YYYY, CH/FH → YYYYHH, Q → YYYYQQ, M/W/D → YYYYMM

    def test_frequency_CY_with_YYYY_dates(self):
        """CY (calendar year) with YYYY date format."""
        client = BojClient(lang="jp", max_pages=1)
        result = client.get_data_by_layer(
            db="BP01", layer="1,3,1", frequency="CY",
            start_date="2020", end_date="2024",
        )
        assert result.status.status == 200
        assert len(result.series) > 0
        # Verify returned dates are in YYYY format
        for s in result.series:
            for dp in s.data_points:
                assert len(dp.date) == 4, f"Expected YYYY, got '{dp.date}'"

    def test_frequency_FY_with_YYYY_dates(self):
        """FY (fiscal year) with YYYY date format."""
        client = BojClient(lang="jp", max_pages=1)
        result = client.get_data_by_layer(
            db="FF", layer="2,1,1,1", frequency="FY",
            start_date="2020", end_date="2024",
        )
        assert result.status.status == 200
        assert len(result.series) > 0
        for s in result.series:
            for dp in s.data_points:
                assert len(dp.date) == 4, f"Expected YYYY, got '{dp.date}'"

    def test_frequency_CH_with_YYYYHH_dates(self):
        """CH (calendar half-year) with YYYYHH date format — DER DB."""
        client = BojClient(lang="jp", max_pages=1)
        result = client.get_data_by_layer(
            db="DER", layer="1,1", frequency="CH",
            start_date="202301", end_date="202402",
        )
        assert result.status.status == 200
        assert len(result.series) > 0
        for s in result.series:
            for dp in s.data_points:
                assert len(dp.date) == 6, f"Expected YYYYHH, got '{dp.date}'"

    def test_frequency_FH_with_YYYYHH_dates(self):
        """FH (fiscal half-year) with YYYYHH date format — FF DB."""
        client = BojClient(lang="jp", max_pages=1)
        result = client.get_data_by_layer(
            db="FF", layer="6,1,1", frequency="FH",
            start_date="202001", end_date="202502",
        )
        assert result.status.status == 200
        assert len(result.series) > 0
        for s in result.series:
            for dp in s.data_points:
                assert len(dp.date) == 6, f"Expected YYYYHH, got '{dp.date}'"

    def test_frequency_Q_with_YYYYQQ_dates(self):
        """Q (quarterly) with YYYYQQ date format — CO (Tankan) DB."""
        client = BojClient(lang="jp", max_pages=1)
        result = client.get_data_by_layer(
            db="CO", layer="1,1,1,1", frequency="Q",
            start_date="202401", end_date="202404",
        )
        assert result.status.status == 200
        assert len(result.series) > 0
        for s in result.series:
            for dp in s.data_points:
                assert len(dp.date) == 6, f"Expected YYYYQQ, got '{dp.date}'"

    def test_frequency_M_with_YYYYMM_dates(self):
        """M (monthly) with YYYYMM date format — BP01 DB."""
        client = BojClient(lang="jp", max_pages=1)
        result = client.get_data_by_layer(
            db="BP01", layer="1,1,1", frequency="M",
            start_date="202501", end_date="202503",
        )
        assert result.status.status == 200
        assert len(result.series) > 0
        series_with_data = [s for s in result.series if s.data_points]
        assert len(series_with_data) > 0
        for dp in series_with_data[0].data_points:
            assert len(dp.date) == 6, f"Expected YYYYMM, got '{dp.date}'"

    def test_frequency_W_with_YYYYMM_dates(self):
        """W (weekly) with YYYYMM date params — IR02 DB.
        Note: date params use YYYYMM but returned dates are YYYYMMDD."""
        client = BojClient(lang="jp", max_pages=1)
        result = client.get_data_by_layer(
            db="IR02", layer="*", frequency="W",
            start_date="202501", end_date="202503",
        )
        assert result.status.status == 200
        assert len(result.series) > 0
        # Weekly data returns YYYYMMDD format dates
        series_with_data = [s for s in result.series if s.data_points]
        if series_with_data:
            for dp in series_with_data[0].data_points:
                assert len(dp.date) == 8, f"Expected YYYYMMDD, got '{dp.date}'"

    def test_frequency_D_with_YYYYMM_dates(self):
        """D (daily) with YYYYMM date params — IR01 DB.
        Note: date params use YYYYMM but returned dates are YYYYMMDD."""
        client = BojClient(lang="jp", max_pages=1)
        result = client.get_data_by_layer(
            db="IR01", layer="*", frequency="D",
            start_date="202503", end_date="202503",
        )
        assert result.status.status == 200
        assert len(result.series) > 0
        series_with_data = [s for s in result.series if s.data_points]
        if series_with_data:
            for dp in series_with_data[0].data_points:
                assert len(dp.date) == 8, f"Expected YYYYMMDD, got '{dp.date}'"

    # --- Language variation ---

    def test_lang_english(self):
        """English language output."""
        client = BojClient(lang="en", max_pages=1)
        result = client.get_data_by_layer(
            db="BP01", layer="1,1,1", frequency="M",
            start_date="202501", end_date="202503",
        )
        assert result.status.status == 200
        assert len(result.series) > 0
        # English response should have name populated from NAME_OF_TIME_SERIES
        series_with_data = [s for s in result.series if s.data_points]
        assert len(series_with_data) > 0

    # --- Date range variations ---

    def test_start_date_only(self):
        """Only start date specified — should return data from start to latest."""
        client = BojClient(lang="jp", max_pages=1)
        result = client.get_data_by_layer(
            db="IR01", layer="*", frequency="D",
            start_date="202503",
        )
        assert result.status.status == 200
        assert len(result.series) > 0

    def test_end_date_only(self):
        """Only end date specified — should return data from earliest to end."""
        client = BojClient(lang="jp", max_pages=1)
        result = client.get_data_by_layer(
            db="IR03", layer="1", frequency="M",
            end_date="202503",
        )
        assert result.status.status == 200
        assert len(result.series) > 0

    def test_no_date_range(self):
        """No date range — returns all available data (limited by max_pages)."""
        client = BojClient(lang="jp", max_pages=1)
        result = client.get_data_by_layer(
            db="IR01", layer="1,1", frequency="D",
        )
        assert result.status.status == 200
        assert len(result.series) > 0

    # --- Layer depth variations ---

    def test_layer_depth_1(self):
        """Single-level layer (hierarchy 1 only)."""
        client = BojClient(lang="jp", max_pages=1)
        result = client.get_data_by_layer(
            db="IR03", layer="1", frequency="M",
            start_date="202501", end_date="202503",
        )
        assert result.status.status == 200
        assert len(result.series) > 0

    def test_layer_depth_2(self):
        """Two-level layer."""
        client = BojClient(lang="jp", max_pages=1)
        result = client.get_data_by_layer(
            db="IR01", layer="1,1", frequency="D",
            start_date="202503", end_date="202503",
        )
        assert result.status.status == 200
        assert len(result.series) > 0

    def test_layer_depth_5(self):
        """Five-level layer (maximum depth)."""
        client = BojClient(lang="jp", max_pages=1)
        result = client.get_data_by_layer(
            db="FF", layer="1,1,1,1,0", frequency="Q",
            start_date="202401", end_date="202404",
        )
        assert result.status.status == 200


class TestGzipIntegration:
    def test_gzip_vs_no_gzip_same_result(self):
        """Verify gzip-enabled and gzip-disabled requests return identical data."""
        # With gzip (default)
        client_gzip = BojClient(lang="jp")
        result_gzip = client_gzip.get_metadata("IR01")

        # Without gzip
        client_plain = BojClient(lang="jp", accept_gzip=False)
        result_plain = client_plain.get_metadata("IR01")

        assert result_gzip.status.status == result_plain.status.status
        assert len(result_gzip.series) == len(result_plain.series)
        # Spot-check first series with code
        gzip_codes = [s.series_code for s in result_gzip.series if s.series_code]
        plain_codes = [s.series_code for s in result_plain.series if s.series_code]
        assert gzip_codes == plain_codes



class TestNoDataIntegration:
    def test_code_api_future_date_all_null_values(self):
        """Code API with future dates → series returned but all values are null."""
        client = BojClient(lang="jp")
        result = client.get_data_by_code(
            db="CO", codes=["TK99F1000601GCQ01000"],
            start_date="204901", end_date="205004",
        )
        # API returns series with null values, not NotFoundError
        assert len(result.series) == 1
        assert all(dp.value is None for dp in result.series[0].data_points)

    def test_layer_api_no_data_but_series_exist(self):
        """Layer API where series exist but have no data in the requested period.

        IR02 weekly with a narrow future date range returns RESULTSET with
        series but empty VALUES — should NOT raise NotFoundError.
        """
        client = BojClient(lang="jp", max_pages=1)
        result = client.get_data_by_layer(
            db="IR02", layer="*", frequency="W",
            start_date="204901", end_date="205012",
        )
        # Series are returned even though no data points exist
        assert len(result.series) > 0

    def test_search_no_match_returns_empty(self):
        """Search with a keyword that matches nothing."""
        client = BojClient(lang="jp")
        results = client.search_series("FM08", ["ZZZZNONEXISTENT999"])
        assert results == []

class TestMetadataApiIntegration:
    def test_fetch_fx_metadata_jp(self):
        """Metadata API with Japanese language."""
        client = BojClient(lang="jp")
        result = client.get_metadata("FM08")
        assert result.status.status == 200
        assert len(result.series) > 0
        series_with_code = [s for s in result.series if s.series_code]
        assert len(series_with_code) > 0
        # Japanese fields should be populated
        assert series_with_code[0].name_jp != ""
        assert series_with_code[0].unit_jp != ""
        assert series_with_code[0].category_jp != ""

    def test_fetch_fx_metadata_en(self):
        """Metadata API with English language."""
        client = BojClient(lang="en")
        result = client.get_metadata("FM08")
        assert result.status.status == 200
        assert len(result.series) > 0
        series_with_code = [s for s in result.series if s.series_code]
        assert len(series_with_code) > 0
        # English fields should be populated
        assert series_with_code[0].name_en != ""
        assert series_with_code[0].unit_en != ""
        assert series_with_code[0].category_en != ""

    def test_metadata_fields_complete(self):
        """Verify all expected metadata fields are returned."""
        client = BojClient(lang="jp")
        result = client.get_metadata("IR01")
        series_with_code = [s for s in result.series if s.series_code]
        assert len(series_with_code) > 0
        s = series_with_code[0]
        assert s.frequency != ""
        assert s.start_period != ""
        assert s.end_period != ""
        assert s.last_update != ""
        # Layer info should be present
        assert s.layer1 != ""

    def test_search_series_jp(self):
        """Search with Japanese keywords."""
        client = BojClient(lang="jp")
        results = client.search_series("FM08", ["ドル"])
        assert len(results) > 0
        assert any("ドル" in s.name_jp for s in results)

    def test_search_series_en(self):
        """Search with English keywords."""
        client = BojClient(lang="en")
        results = client.search_series("FM08", ["Dollar"])
        assert len(results) > 0
        assert any("Dollar" in s.name_en for s in results)
