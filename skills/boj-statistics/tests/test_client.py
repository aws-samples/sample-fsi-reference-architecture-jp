"""Tests for BojClient (mocked HTTP)."""

from __future__ import annotations

import io
import json
from unittest.mock import MagicMock, patch

import pytest

from boj_statistics.boj_client import BojClient
from boj_statistics.exceptions import (
    BojApiError,
    BojClientNotFoundError,
    BojClientValidationError,
)


def _mock_urlopen(data: dict) -> MagicMock:
    """Create a mock that behaves like the return value of urlopen()."""
    body = json.dumps(data).encode("utf-8")
    resp = MagicMock()
    resp.read.return_value = body
    resp.status = data.get("STATUS", 200)
    resp.headers = {}
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestClientValidation:
    def test_invalid_lang(self):
        with pytest.raises(BojClientValidationError, match="Invalid lang"):
            BojClient(lang="fr")

    def test_empty_db(self):
        client = BojClient()
        with pytest.raises(BojClientValidationError, match="DB name is required"):
            client.get_metadata("")

    def test_empty_codes(self):
        client = BojClient()
        with pytest.raises(BojClientValidationError, match="At least one series code"):
            client.get_data_by_code("FM08", [])

    def test_invalid_frequency(self):
        client = BojClient()
        with pytest.raises(BojClientValidationError, match="Invalid frequency"):
            client.get_data_by_layer("FM08", "*", "INVALID")


class TestClientRequest:
    @patch("boj_statistics.boj_client.BojClient._wait")
    @patch("urllib.request.urlopen")
    def test_successful_code_api(self, mock_urlopen, mock_wait, sample_code_api_response):
        mock_urlopen.return_value = _mock_urlopen(sample_code_api_response)

        client = BojClient()
        result = client.get_data_by_code("FM08", ["FXERM01"], start_date="202501", end_date="202503")

        assert len(result.series) == 1
        assert result.series[0].series_code == "FXERM01"
        assert len(result.series[0].data_points) == 3
        assert result.series[0].data_points[0].value == "155.2"

    @patch("boj_statistics.boj_client.BojClient._wait")
    @patch("urllib.request.urlopen")
    def test_no_data_raises_not_found(self, mock_urlopen, mock_wait, sample_no_data_response):
        mock_urlopen.return_value = _mock_urlopen(sample_no_data_response)

        client = BojClient()
        with pytest.raises(BojClientNotFoundError) as exc_info:
            client.get_data_by_code("FM08", ["NONEXIST"])
        assert exc_info.value.message_id == "M181030I"

    @patch("boj_statistics.boj_client.BojClient._wait")
    @patch("urllib.request.urlopen")
    def test_api_400_error(self, mock_urlopen, mock_wait, sample_error_response):
        mock_urlopen.return_value = _mock_urlopen(sample_error_response)

        client = BojClient()
        with pytest.raises(BojApiError) as exc_info:
            client.get_metadata("INVALID_DB")
        assert exc_info.value.status_code == 400
        assert exc_info.value.message_id == "M181005E"

    @patch("boj_statistics.boj_client.BojClient._wait")
    @patch("urllib.request.urlopen")
    def test_pagination(self, mock_urlopen, mock_wait, sample_paginated_response_page1, sample_paginated_response_page2):
        mock_urlopen.side_effect = [
            _mock_urlopen(sample_paginated_response_page1),
            _mock_urlopen(sample_paginated_response_page2),
        ]

        client = BojClient()
        result = client.get_data_by_layer("MD10", "*", "Q")

        assert len(result.series) == 2
        assert result.series[0].series_code == "SERIES001"
        assert result.series[1].series_code == "SERIES002"

    @patch("boj_statistics.boj_client.BojClient._wait")
    @patch("urllib.request.urlopen")
    def test_layer_api_data_points_parsed(self, mock_urlopen, mock_wait):
        """Verify layer API response data points are correctly parsed."""
        response_data = {
            "STATUS": 200,
            "MESSAGEID": "M181000I",
            "MESSAGE": "正常に終了しました。",
            "DATE": "2026-03-19T10:00:00.000+09:00",
            "PARAMETER": {
                "FORMAT": "JSON", "LANG": "JP", "DB": "BP01",
                "LAYER1": "1", "LAYER2": "1", "LAYER3": "1",
                "LAYER4": "", "LAYER5": "", "FREQUENCY": "M",
                "STARTDATE": "202501", "ENDDATE": "202503", "STARTPOSITION": "",
            },
            "NEXTPOSITION": None,
            "RESULTSET": [
                {
                    "SERIES_CODE": "BPBP6JYNCB",
                    "NAME_OF_TIME_SERIES_J": "経常収支",
                    "UNIT_J": "億円",
                    "FREQUENCY": "MONTHLY",
                    "CATEGORY_J": "国際収支統計",
                    "LAST_UPDATE": 20260309,
                    "VALUES": {
                        "SURVEY_DATES": [202501, 202502, 202503],
                        "VALUES": [-3446.07, 40087.43, 25000.00],
                    },
                },
                {
                    "SERIES_CODE": "BPBP6JYNTR",
                    "NAME_OF_TIME_SERIES_J": "貿易収支",
                    "UNIT_J": "億円",
                    "FREQUENCY": "MONTHLY",
                    "CATEGORY_J": "国際収支統計",
                    "LAST_UPDATE": 20260309,
                    "VALUES": {
                        "SURVEY_DATES": [202501, 202502, 202503],
                        "VALUES": [-2000.0, 1500.0, None],
                    },
                },
            ],
        }
        mock_urlopen.return_value = _mock_urlopen(response_data)

        client = BojClient()
        result = client.get_data_by_layer("BP01", "1,1,1", "M", start_date="202501", end_date="202503")

        assert len(result.series) == 2
        assert result.series[0].series_code == "BPBP6JYNCB"
        assert result.series[0].name == "経常収支"
        assert len(result.series[0].data_points) == 3
        assert result.series[0].data_points[0].date == "202501"
        assert result.series[0].data_points[0].value == "-3446.07"
        # Null value handling
        assert result.series[1].data_points[2].value is None
        # Params parsed from PARAMETER block
        assert result.params.db == "BP01"
        assert result.params.layer1 == "1"
        assert result.params.frequency == "M"

    @patch("boj_statistics.boj_client.BojClient._wait")
    @patch("urllib.request.urlopen")
    def test_metadata_api(self, mock_urlopen, mock_wait, sample_metadata_response):
        mock_urlopen.return_value = _mock_urlopen(sample_metadata_response)

        client = BojClient()
        result = client.get_metadata("FM08")

        assert len(result.series) == 2
        assert result.series[0].name_jp == "東京市場 ドル・円 スポット 中心相場"
        assert result.series[1].name_en == "Tokyo Market EUR/JPY Spot Central Rate"

    @patch("boj_statistics.boj_client.BojClient._wait")
    @patch("urllib.request.urlopen")
    def test_search_series(self, mock_urlopen, mock_wait, sample_metadata_response):
        mock_urlopen.return_value = _mock_urlopen(sample_metadata_response)

        client = BojClient()
        results = client.search_series("FM08", ["ドル"])

        assert len(results) == 1
        assert "ドル" in results[0].name_jp

    @patch("boj_statistics.boj_client.BojClient._wait")
    @patch("urllib.request.urlopen")
    def test_search_series_no_match(self, mock_urlopen, mock_wait, sample_metadata_response):
        mock_urlopen.return_value = _mock_urlopen(sample_metadata_response)

        client = BojClient()
        results = client.search_series("FM08", ["存在しないキーワード"])
        assert len(results) == 0



class TestNoDataPatterns:
    """Test the two M181030I patterns: RESULTSET empty vs non-empty."""

    @patch("boj_statistics.boj_client.BojClient._wait")
    @patch("urllib.request.urlopen")
    def test_no_data_empty_resultset_raises_not_found(self, mock_urlopen, mock_wait):
        """M181030I with empty RESULTSET → BojClientNotFoundError."""
        mock_urlopen.return_value = _mock_urlopen({
            "STATUS": 200,
            "MESSAGEID": "M181030I",
            "MESSAGE": "正常に終了しましたが、該当データはありませんでした。",
            "DATE": "2026-03-19T10:00:00.000+09:00",
            "RESULTSET": [],
        })

        client = BojClient()
        with pytest.raises(BojClientNotFoundError) as exc_info:
            client.get_data_by_code("FM08", ["NONEXIST"])
        assert exc_info.value.message_id == "M181030I"

    @patch("boj_statistics.boj_client.BojClient._wait")
    @patch("urllib.request.urlopen")
    def test_no_data_with_resultset_returns_series(self, mock_urlopen, mock_wait):
        """M181030I with non-empty RESULTSET → returns data (series exist but no values in period)."""
        mock_urlopen.return_value = _mock_urlopen({
            "STATUS": 200,
            "MESSAGEID": "M181030I",
            "MESSAGE": "正常に終了しましたが、該当データはありませんでした。",
            "DATE": "2026-03-19T10:00:00.000+09:00",
            "PARAMETER": {
                "FORMAT": "JSON", "LANG": "JP", "DB": "IR02",
                "LAYER1": "*", "LAYER2": "", "LAYER3": "", "LAYER4": "", "LAYER5": "",
                "FREQUENCY": "W", "STARTDATE": "202501", "ENDDATE": "202503",
                "STARTPOSITION": "",
            },
            "NEXTPOSITION": None,
            "RESULTSET": [
                {
                    "SERIES_CODE": "DLDR43TL11MN",
                    "NAME_OF_TIME_SERIES_J": "定期預金",
                    "UNIT_J": "%",
                    "FREQUENCY": "WEEKLY(MONDAY)",
                    "CATEGORY_J": "テスト",
                    "LAST_UPDATE": 20260315,
                    "VALUES": {"SURVEY_DATES": [], "VALUES": []},
                }
            ],
        })

        client = BojClient()
        result = client.get_data_by_layer("IR02", "*", "W", start_date="202501", end_date="202503")
        # Should NOT raise NotFoundError — series exist even though no data points
        assert len(result.series) == 1
        assert result.series[0].series_code == "DLDR43TL11MN"
        assert result.series[0].data_points == []

    @patch("boj_statistics.boj_client.BojClient._wait")
    @patch("urllib.request.urlopen")
    def test_no_data_without_resultset_key_raises_not_found(self, mock_urlopen, mock_wait):
        """M181030I without RESULTSET key at all → BojClientNotFoundError."""
        mock_urlopen.return_value = _mock_urlopen({
            "STATUS": 200,
            "MESSAGEID": "M181030I",
            "MESSAGE": "正常に終了しましたが、該当データはありませんでした。",
            "DATE": "2026-03-19T10:00:00.000+09:00",
        })

        client = BojClient()
        with pytest.raises(BojClientNotFoundError):
            client.get_data_by_code("FM08", ["NONEXIST"])

class TestGzipHeader:
    @patch("urllib.request.urlopen")
    def test_gzip_header_sent_in_request(self, mock_urlopen, sample_code_api_response):
        """Verify Accept-Encoding: gzip header is set on the request."""
        mock_urlopen.return_value = _mock_urlopen(sample_code_api_response)

        client = BojClient()
        client._wait = MagicMock()
        client.get_data_by_code("FM08", ["FXERM01"])

        assert mock_urlopen.called
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Accept-encoding") == "gzip"


class TestBackoff:
    def test_backoff_increases(self):
        delays = [BojClient._backoff_delay(i) for i in range(1, 4)]
        # Each delay should roughly double (with jitter, check the trend)
        assert delays[1] > delays[0] * 0.5  # allow for jitter
        assert delays[2] > delays[1] * 0.5

    def test_backoff_minimum(self):
        # Base is 2 ± 1, so minimum possible is 1.0 * 2^0 = 1.0
        for _ in range(100):
            delay = BojClient._backoff_delay(1)
            assert delay >= 1.0


class TestCodeSplitting:
    @patch("boj_statistics.boj_client.BojClient._wait")
    @patch("urllib.request.urlopen")
    def test_splits_over_250_codes(self, mock_urlopen, mock_wait, sample_code_api_response):
        mock_urlopen.return_value = _mock_urlopen(sample_code_api_response)

        client = BojClient()
        codes = [f"CODE{i:04d}" for i in range(300)]
        client.get_data_by_code("FM08", codes)

        # Should make 2 chunks: 250 + 50
        assert mock_urlopen.call_count == 2
