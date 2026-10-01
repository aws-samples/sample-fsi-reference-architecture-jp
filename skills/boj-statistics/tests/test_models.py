"""Tests for data models."""

from boj_statistics.models import (
    ApiParams,
    ApiStatus,
    DataPoint,
    DataResponse,
    DbInfo,
    MetadataResponse,
    SeriesData,
    SeriesMeta,
)


class TestDataPoint:
    def test_creation(self):
        dp = DataPoint(date="202501", value="100.5")
        assert dp.date == "202501"
        assert dp.value == "100.5"

    def test_null_value(self):
        dp = DataPoint(date="202501", value=None)
        assert dp.value is None


class TestSeriesData:
    def test_defaults(self):
        s = SeriesData(series_code="TEST001")
        assert s.series_code == "TEST001"
        assert s.data_points == []
        assert s.name == ""

    def test_with_data(self):
        s = SeriesData(
            series_code="TEST001",
            name="テスト",
            data_points=[DataPoint("202501", "100")],
        )
        assert len(s.data_points) == 1


class TestDataResponse:
    def test_defaults(self):
        r = DataResponse(
            status=ApiStatus(status=200, message_id="M181000I", message="OK"),
            params=ApiParams(),
        )
        assert r.next_position is None
        assert r.series == []


class TestSeriesMeta:
    def test_defaults(self):
        m = SeriesMeta(series_code="TEST001")
        assert m.name_jp == ""
        assert m.frequency == ""


class TestDbInfo:
    def test_creation(self):
        d = DbInfo(db_name="FM08", description_jp="外国為替市況", description_en="FX Rates")
        assert d.source == "local"
