"""Shared fixtures for BOJ Statistics tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure scripts/ is on sys.path so boj_statistics is importable
_scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)


@pytest.fixture
def sample_code_api_response() -> dict:
    """Minimal Code API JSON response (matches real API structure)."""
    return {
        "STATUS": 200,
        "MESSAGEID": "M181000I",
        "MESSAGE": "正常に終了しました。",
        "DATE": "2026-03-19T10:00:00.000+09:00",
        "PARAMETER": {
            "FORMAT": "JSON",
            "LANG": "JP",
            "DB": "FM08",
            "STARTDATE": "202501",
            "ENDDATE": "202503",
            "STARTPOSITION": "",
        },
        "NEXTPOSITION": None,
        "RESULTSET": [
            {
                "SERIES_CODE": "FXERM01",
                "NAME_OF_TIME_SERIES_J": "東京市場 ドル・円 スポット 中心相場",
                "UNIT_J": "円",
                "FREQUENCY": "MONTHLY",
                "CATEGORY_J": "外国為替市況",
                "LAST_UPDATE": 20260315,
                "VALUES": {
                    "SURVEY_DATES": [202501, 202502, 202503],
                    "VALUES": [155.20, 153.80, 150.10],
                },
            }
        ],
    }


@pytest.fixture
def sample_metadata_response() -> dict:
    """Minimal Metadata API JSON response (matches real API structure)."""
    return {
        "STATUS": 200,
        "MESSAGEID": "M181000I",
        "MESSAGE": "正常に終了しました。",
        "DATE": "2026-03-19T9:00:11.234+09:00",
        "DB": "FM08",
        "RESULTSET": [
            {
                "SERIES_CODE": "FXERM01",
                "NAME_OF_TIME_SERIES_J": "東京市場 ドル・円 スポット 中心相場",
                "NAME_OF_TIME_SERIES": "Tokyo Market USD/JPY Spot Central Rate",
                "UNIT_J": "円",
                "UNIT": "Yen",
                "FREQUENCY": "MONTHLY",
                "CATEGORY_J": "外国為替市況",
                "CATEGORY": "Foreign Exchange Rates",
                "LAYER1": 1,
                "LAYER2": 1,
                "LAYER3": 0,
                "LAYER4": 0,
                "LAYER5": 0,
                "START_OF_THE_TIME_SERIES": "197901",
                "END_OF_THE_TIME_SERIES": "202503",
                "LAST_UPDATE": 20260315,
                "NOTES_J": "",
                "NOTES": "",
            },
            {
                "SERIES_CODE": "FXERM02",
                "NAME_OF_TIME_SERIES_J": "東京市場 ユーロ・円 スポット 中心相場",
                "NAME_OF_TIME_SERIES": "Tokyo Market EUR/JPY Spot Central Rate",
                "UNIT_J": "円",
                "UNIT": "Yen",
                "FREQUENCY": "MONTHLY",
                "CATEGORY_J": "外国為替市況",
                "CATEGORY": "Foreign Exchange Rates",
                "LAYER1": 1,
                "LAYER2": 2,
                "LAYER3": 0,
                "LAYER4": 0,
                "LAYER5": 0,
                "START_OF_THE_TIME_SERIES": "199901",
                "END_OF_THE_TIME_SERIES": "202503",
                "LAST_UPDATE": 20260315,
                "NOTES_J": "",
                "NOTES": "",
            },
        ],
    }


@pytest.fixture
def sample_no_data_response() -> dict:
    """API response when no data matches."""
    return {
        "STATUS": 200,
        "MESSAGEID": "M181030I",
        "MESSAGE": "正常に終了しましたが、該当データはありませんでした。",
        "DATE": "2026-03-19T10:00:00.000+09:00",
    }


@pytest.fixture
def sample_error_response() -> dict:
    """API 400 error response."""
    return {
        "STATUS": 400,
        "MESSAGEID": "M181005E",
        "MESSAGE": "DB名が正しくありません。",
    }


@pytest.fixture
def sample_paginated_response_page1() -> dict:
    """First page of a paginated response."""
    return {
        "STATUS": 200,
        "MESSAGEID": "M181000I",
        "MESSAGE": "正常に終了しました。",
        "DATE": "2026-03-19T10:00:00.000+09:00",
        "PARAMETER": {
            "FORMAT": "JSON",
            "LANG": "JP",
            "DB": "MD10",
            "STARTDATE": "",
            "ENDDATE": "",
            "STARTPOSITION": "",
            "LAYER1": "*",
            "LAYER2": "",
            "LAYER3": "",
            "LAYER4": "",
            "LAYER5": "",
            "FREQUENCY": "Q",
        },
        "NEXTPOSITION": 255,
        "RESULTSET": [
            {
                "SERIES_CODE": "SERIES001",
                "NAME_OF_TIME_SERIES_J": "テスト系列1",
                "UNIT_J": "億円",
                "FREQUENCY": "QUARTERLY",
                "CATEGORY_J": "テスト",
                "LAST_UPDATE": 20260315,
                "VALUES": {
                    "SURVEY_DATES": [202501],
                    "VALUES": [100],
                },
            }
        ],
    }


@pytest.fixture
def sample_paginated_response_page2() -> dict:
    """Second (final) page of a paginated response."""
    return {
        "STATUS": 200,
        "MESSAGEID": "M181000I",
        "MESSAGE": "正常に終了しました。",
        "DATE": "2026-03-19T10:00:00.000+09:00",
        "PARAMETER": {
            "FORMAT": "JSON",
            "LANG": "JP",
            "DB": "MD10",
            "STARTDATE": "",
            "ENDDATE": "",
            "STARTPOSITION": "255",
            "LAYER1": "*",
            "LAYER2": "",
            "LAYER3": "",
            "LAYER4": "",
            "LAYER5": "",
            "FREQUENCY": "Q",
        },
        "NEXTPOSITION": None,
        "RESULTSET": [
            {
                "SERIES_CODE": "SERIES002",
                "NAME_OF_TIME_SERIES_J": "テスト系列2",
                "UNIT_J": "億円",
                "FREQUENCY": "QUARTERLY",
                "CATEGORY_J": "テスト",
                "LAST_UPDATE": 20260315,
                "VALUES": {
                    "SURVEY_DATES": [202501],
                    "VALUES": [200],
                },
            }
        ],
    }
