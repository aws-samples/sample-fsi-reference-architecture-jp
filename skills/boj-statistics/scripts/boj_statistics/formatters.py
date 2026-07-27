"""Output formatters for BOJ Statistics CLI.

Supports JSON, CSV (UTF-8), TSV (UTF-8), and human-readable table formats.
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from typing import Any, Sequence

from .models import DataResponse, DbInfo, MetadataResponse, SeriesData, SeriesMeta


def _dsv_writer(fmt: str) -> tuple[io.StringIO, csv.writer]:
    """Create a delimiter-separated values writer for csv or tsv."""
    buf = io.StringIO()
    delimiter = "\t" if fmt == "tsv" else ","
    writer = csv.writer(buf, delimiter=delimiter)
    return buf, writer


def format_output(
    data: Any,
    fmt: str = "json",
    max_series_size: int | None = None,
    max_item_length: int | None = None,
) -> tuple[str, bool]:
    """Format data for output.

    Returns:
        Tuple of (formatted_string, was_truncated).
    """
    truncated = False

    if isinstance(data, DataResponse):
        series = data.series
        if max_series_size and len(series) > max_series_size:
            series = series[:max_series_size]
            truncated = True
        if max_item_length:
            for s in series:
                if len(s.data_points) > max_item_length:
                    s.data_points = s.data_points[:max_item_length]
                    truncated = True
        return _format_data_response(series, fmt), truncated

    if isinstance(data, MetadataResponse):
        series = data.series
        if max_series_size and len(series) > max_series_size:
            series = series[:max_series_size]
            truncated = True
        return _format_metadata_response(series, fmt), truncated

    if isinstance(data, list) and data and isinstance(data[0], DbInfo):
        return _format_db_list(data, fmt), truncated

    if isinstance(data, list) and data and isinstance(data[0], SeriesMeta):
        if max_series_size and len(data) > max_series_size:
            data = data[:max_series_size]
            truncated = True
        return _format_metadata_response(data, fmt), truncated

    # Fallback: serialize as JSON
    return json.dumps(data, ensure_ascii=False, indent=2, default=str), truncated


# ------------------------------------------------------------------
# Data response (Code API / Layer API)
# ------------------------------------------------------------------

def _format_data_response(series: Sequence[SeriesData], fmt: str) -> str:
    if fmt == "json":
        rows = []
        for s in series:
            rows.append({
                "series_code": s.series_code,
                "name": s.name,
                "unit": s.unit,
                "frequency": s.frequency,
                "category": s.category,
                "last_update": s.last_update,
                "data": [{"date": dp.date, "value": dp.value} for dp in s.data_points],
            })
        return json.dumps(rows, ensure_ascii=False, indent=2)

    if fmt in ("csv", "tsv"):
        buf, writer = _dsv_writer(fmt)
        writer.writerow(["series_code", "name", "unit", "frequency", "date", "value"])
        for s in series:
            for dp in s.data_points:
                writer.writerow([s.series_code, s.name, s.unit, s.frequency, dp.date, dp.value])
        return buf.getvalue()

    if fmt == "table":
        return _table_data_response(series)

    return json.dumps([asdict(s) for s in series], ensure_ascii=False, indent=2)


def _table_data_response(series: Sequence[SeriesData]) -> str:
    lines: list[str] = []
    for s in series:
        lines.append(f"--- {s.series_code}: {s.name} ({s.unit}) [{s.frequency}] ---")
        if not s.data_points:
            lines.append("  (no data)")
            continue
        max_date_len = max(len(dp.date) for dp in s.data_points)
        for dp in s.data_points:
            val = dp.value if dp.value is not None else "null"
            lines.append(f"  {dp.date:<{max_date_len}}  {val}")
        lines.append("")
    return "\n".join(lines)


# ------------------------------------------------------------------
# Metadata response
# ------------------------------------------------------------------

def _format_metadata_response(series: Sequence[SeriesMeta], fmt: str) -> str:
    if fmt == "json":
        rows = [asdict(s) for s in series]
        return json.dumps(rows, ensure_ascii=False, indent=2)

    if fmt in ("csv", "tsv"):
        buf, writer = _dsv_writer(fmt)
        writer.writerow([
            "series_code", "name_jp", "name_en", "unit_jp", "unit_en",
            "frequency", "category_jp", "category_en",
            "start_period", "end_period", "last_update",
        ])
        for s in series:
            writer.writerow([
                s.series_code, s.name_jp, s.name_en, s.unit_jp, s.unit_en,
                s.frequency, s.category_jp, s.category_en,
                s.start_period, s.end_period, s.last_update,
            ])
        return buf.getvalue()

    if fmt == "table":
        lines: list[str] = []
        code_w = max((len(s.series_code) for s in series), default=12)
        # Show DB name column when results come from cross-DB search
        show_db = any(s.notes_jp.startswith("DB:") or s.notes_en.startswith("DB:") for s in series)
        for s in series:
            name = s.name_jp or s.name_en
            db_tag = ""
            if show_db:
                db_name = (s.notes_jp or s.notes_en).removeprefix("DB:")
                db_tag = f"[{db_name}] "
            period = f"{s.start_period}~{s.end_period}"
            lines.append(
                f"  {db_tag}{s.series_code:<{code_w}}  {name}  "
                f"[{s.frequency}]  {period}"
            )
        return "\n".join(lines)

    return json.dumps([asdict(s) for s in series], ensure_ascii=False, indent=2)


# ------------------------------------------------------------------
# DB list
# ------------------------------------------------------------------

def _format_db_list(db_list: Sequence[DbInfo], fmt: str) -> str:
    if fmt == "json":
        rows = [asdict(d) for d in db_list]
        return json.dumps(rows, ensure_ascii=False, indent=2)

    if fmt in ("csv", "tsv"):
        buf, writer = _dsv_writer(fmt)
        writer.writerow(["db_name", "description_jp", "description_en", "source"])
        for d in db_list:
            writer.writerow([d.db_name, d.description_jp, d.description_en, d.source])
        return buf.getvalue()

    if fmt == "table":
        lines: list[str] = []
        name_w = max((len(d.db_name) for d in db_list), default=6)
        for d in db_list:
            desc = d.description_jp or d.description_en
            lines.append(f"  {d.db_name:<{name_w}}  {desc}")
        return "\n".join(lines)

    return json.dumps([asdict(d) for d in db_list], ensure_ascii=False, indent=2)
