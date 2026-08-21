"""Tests for output formatters."""

import csv
import io
import json

from boj_statistics.formatters import format_output
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


def _make_data_response(n_series: int = 2, n_points: int = 3) -> DataResponse:
    series = []
    for i in range(n_series):
        dps = [DataPoint(date=f"20250{j+1}", value=str(100 + j)) for j in range(n_points)]
        series.append(SeriesData(
            series_code=f"CODE{i:03d}",
            name=f"テスト系列{i}",
            unit="億円",
            frequency="MONTHLY",
            data_points=dps,
        ))
    return DataResponse(
        status=ApiStatus(status=200, message_id="M181000I", message="OK"),
        params=ApiParams(),
        series=series,
    )


class TestDataResponseFormat:
    def test_json_output(self):
        resp = _make_data_response()
        text, truncated = format_output(resp, "json")
        assert not truncated
        data = json.loads(text)
        assert len(data) == 2
        assert data[0]["series_code"] == "CODE000"

    def test_csv_output(self):
        resp = _make_data_response(n_series=1, n_points=2)
        text, truncated = format_output(resp, "csv")
        assert not truncated
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        assert rows[0] == ["series_code", "name", "unit", "frequency", "date", "value"]
        assert len(rows) == 3  # header + 2 data rows

    def test_table_output(self):
        resp = _make_data_response(n_series=1, n_points=1)
        text, truncated = format_output(resp, "table")
        assert "CODE000" in text
        assert "テスト系列0" in text

    def test_tsv_output(self):
        resp = _make_data_response(n_series=1, n_points=2)
        text, truncated = format_output(resp, "tsv")
        assert not truncated
        lines = text.strip().splitlines()
        assert len(lines) == 3  # header + 2 data rows
        # Tab-separated, not comma-separated
        assert "\t" in lines[0]
        header = lines[0].split("\t")
        assert header == ["series_code", "name", "unit", "frequency", "date", "value"]
        # Verify data row is also tab-separated
        row1 = lines[1].split("\t")
        assert row1[0] == "CODE000"


class TestTruncation:
    def test_max_series_size(self):
        resp = _make_data_response(n_series=5)
        text, truncated = format_output(resp, "json", max_series_size=2)
        assert truncated
        data = json.loads(text)
        assert len(data) == 2

    def test_max_item_length(self):
        resp = _make_data_response(n_series=1, n_points=10)
        text, truncated = format_output(resp, "json", max_item_length=3)
        assert truncated
        data = json.loads(text)
        assert len(data[0]["data"]) == 3

    def test_no_truncation_when_within_limits(self):
        resp = _make_data_response(n_series=2, n_points=3)
        text, truncated = format_output(resp, "json", max_series_size=10, max_item_length=10)
        assert not truncated


class TestDbListFormat:
    def test_json(self):
        db_list = [DbInfo("FM08", "外国為替市況", "FX Rates")]
        text, _ = format_output(db_list, "json")
        data = json.loads(text)
        assert data[0]["db_name"] == "FM08"

    def test_csv(self):
        db_list = [DbInfo("FM08", "外国為替市況", "FX Rates")]
        text, _ = format_output(db_list, "csv")
        assert "FM08" in text

    def test_table(self):
        db_list = [DbInfo("FM08", "外国為替市況", "FX Rates")]
        text, _ = format_output(db_list, "table")
        assert "FM08" in text
        assert "外国為替市況" in text

    def test_tsv(self):
        db_list = [DbInfo("FM08", "外国為替市況", "FX Rates")]
        text, _ = format_output(db_list, "tsv")
        lines = text.strip().split("\n")
        assert "\t" in lines[0]
        assert "FM08" in lines[1]
        assert "," not in lines[1] or "外国為替市況" in lines[1]  # no spurious commas as delimiters


class TestMetadataFormat:
    def test_series_meta_list(self):
        meta_list = [
            SeriesMeta(series_code="TEST001", name_jp="テスト", frequency="MONTHLY"),
        ]
        text, _ = format_output(meta_list, "json")
        data = json.loads(text)
        assert data[0]["series_code"] == "TEST001"

    def test_series_meta_tsv(self):
        meta_list = [
            SeriesMeta(series_code="TEST001", name_jp="テスト", frequency="MONTHLY"),
        ]
        text, _ = format_output(meta_list, "tsv")
        lines = text.strip().split("\n")
        assert "\t" in lines[0]
        assert "TEST001" in lines[1]
