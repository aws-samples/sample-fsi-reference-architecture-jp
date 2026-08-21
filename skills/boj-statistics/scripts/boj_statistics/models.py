"""Data models for BOJ Statistics API responses.

All models use dataclasses for type safety. Fields mirror the BOJ API
output tags so that API message IDs and messages are never hidden.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Common response envelope
# ---------------------------------------------------------------------------

@dataclass
class ApiStatus:
    """API processing result information (common to all APIs)."""

    status: int
    message_id: str
    message: str
    date: str = ""


@dataclass
class ApiParams:
    """Parameters echoed back in the API response (Code/Layer APIs)."""

    format: str = ""
    lang: str = ""
    db: str = ""
    start_date: str = ""
    end_date: str = ""
    start_position: str = ""
    # Layer API specific
    layer1: str = ""
    layer2: str = ""
    layer3: str = ""
    layer4: str = ""
    layer5: str = ""
    frequency: str = ""


# ---------------------------------------------------------------------------
# Code API / Layer API data models
# ---------------------------------------------------------------------------

@dataclass
class DataPoint:
    """A single observation (date + value)."""

    date: str
    value: str | None  # null when data is missing


@dataclass
class SeriesData:
    """One time-series returned by Code API or Layer API."""

    series_code: str
    name: str = ""
    unit: str = ""
    frequency: str = ""
    category: str = ""
    last_update: str = ""
    data_points: list[DataPoint] = field(default_factory=list)


@dataclass
class DataResponse:
    """Full response from Code API or Layer API."""

    status: ApiStatus
    params: ApiParams
    next_position: int | None = None
    series: list[SeriesData] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Metadata API data models
# ---------------------------------------------------------------------------

@dataclass
class SeriesMeta:
    """Metadata for a single series (from Metadata API)."""

    series_code: str
    name_jp: str = ""
    name_en: str = ""
    unit_jp: str = ""
    unit_en: str = ""
    frequency: str = ""
    category_jp: str = ""
    category_en: str = ""
    layer1: str = ""
    layer2: str = ""
    layer3: str = ""
    layer4: str = ""
    layer5: str = ""
    start_period: str = ""
    end_period: str = ""
    last_update: str = ""
    notes_jp: str = ""
    notes_en: str = ""


@dataclass
class MetadataResponse:
    """Full response from Metadata API."""

    status: ApiStatus
    db: str = ""
    series: list[SeriesMeta] = field(default_factory=list)


# ---------------------------------------------------------------------------
# DB catalog model
# ---------------------------------------------------------------------------

@dataclass
class DbInfo:
    """Database entry for list-db output."""

    db_name: str
    description_jp: str = ""
    description_en: str = ""
    source: str = "local"  # "local" or "api"
