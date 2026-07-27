#!/usr/bin/env python3
"""CLI entry point for BOJ Statistics API.

Usage:
    python3 boj_statistics_cli.py <command> [options]

Commands:
    list-db        List available database names
    get-metadata   Get series metadata for a database
    search-series  Search series by keyword
    get-data       Fetch time-series data by series code (Code API)
    get-layer      Fetch time-series data by layer hierarchy (Layer API)
    latest         Fetch the most recent data point for series

Examples:
    python3 boj_statistics_cli.py list-db
    python3 boj_statistics_cli.py get-metadata --db FM08
    python3 boj_statistics_cli.py search-series --db FM08 --keywords ドル 円
    python3 boj_statistics_cli.py search-series --db all --keywords マネタリーベース
    python3 boj_statistics_cli.py get-data --db CO --code TK99F1000601GCQ01000 \
        --start 202401 --end 202504
    python3 boj_statistics_cli.py get-layer --db BP01 --layer 1,1,1 \
        --frequency M --start 202504 --end 202509
    python3 boj_statistics_cli.py latest --db FM01 --code STRDCLUCON
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys

from boj_statistics.boj_client import BojClient
from boj_statistics.constants import DB_CATALOG
from boj_statistics.exceptions import BojClientError
from boj_statistics.formatters import format_output
from boj_statistics.models import DbInfo

logger = logging.getLogger("boj_statistics")


def _setup_logging() -> None:
    level_name = os.environ.get("LOG_LEVEL", "WARN").upper()
    level = getattr(logging, level_name, logging.WARN)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--format",
        choices=["json", "csv", "tsv", "table"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument("--lang", choices=["jp", "en"], default="jp", help="Language (default: jp)")
    parser.add_argument(
        "--output", type=str, default=None, help="Output file path (default: stdout)"
    )
    parser.add_argument(
        "--max-series-size", type=int, default=None, help="Max number of series to output"
    )
    parser.add_argument(
        "--max-item-length", type=int, default=None, help="Max data points per series"
    )
    parser.add_argument(
        "--max-pages", type=int, default=20, help="Max pagination requests (default: 20)"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="boj_statistics",
        description="CLI for the Bank of Japan Time-Series Statistics API",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # list-db
    p_list = sub.add_parser("list-db", help="List available databases")
    _add_common_args(p_list)

    # metadata → get-metadata
    p_meta = sub.add_parser("get-metadata", help="Get series metadata for a database")
    p_meta.add_argument("--db", required=True, help="Database name (e.g. FM08)")
    _add_common_args(p_meta)

    # search → search-series
    p_search = sub.add_parser("search-series", help="Search series by keyword")
    p_search.add_argument(
        "--db", required=True, help="Database name (or 'all' for cross-DB search)"
    )
    p_search.add_argument("--keywords", nargs="+", required=True, help="Search keywords (OR match)")
    _add_common_args(p_search)

    # get-data
    p_data = sub.add_parser("get-data", help="Fetch data by series code (Code API)")
    p_data.add_argument("--db", required=True, help="Database name")
    p_data.add_argument("--code", required=True, help="Series codes (comma-separated)")
    p_data.add_argument("--start", default="", help="Start date (e.g. 202401)")
    p_data.add_argument("--end", default="", help="End date (e.g. 202504)")
    _add_common_args(p_data)

    # get-layer
    p_layer = sub.add_parser("get-layer", help="Fetch data by layer hierarchy (Layer API)")
    p_layer.add_argument("--db", required=True, help="Database name")
    p_layer.add_argument("--layer", required=True, help="Layer info (e.g. 1,1,1 or *)")
    p_layer.add_argument("--frequency", required=True, help="Frequency: CY,FY,CH,FH,Q,M,W,D")
    p_layer.add_argument("--start", default="", help="Start date")
    p_layer.add_argument("--end", default="", help="End date")
    _add_common_args(p_layer)

    # latest
    p_latest = sub.add_parser("latest", help="Fetch the most recent data point")
    p_latest.add_argument("--db", required=True, help="Database name")
    p_latest.add_argument("--code", required=True, help="Series codes (comma-separated)")
    _add_common_args(p_latest)

    return parser


def _write_output(text: str, output_path: str | None, truncated: bool) -> None:
    if truncated:
        print(
            "WARNING: Output was truncated due to --max-series-size or --max-item-length limits.",
            file=sys.stderr,
        )

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Output written to: {output_path}", file=sys.stderr)
    else:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")


def cmd_list_db(args: argparse.Namespace) -> None:
    db_list = [
        DbInfo(
            db_name=name,
            description_jp=info["jp"],
            description_en=info["en"],
            source="local",
        )
        for name, info in DB_CATALOG.items()
    ]
    text, truncated = format_output(db_list, args.format, max_series_size=args.max_series_size)
    _write_output(text, args.output, truncated)


def cmd_metadata(args: argparse.Namespace) -> None:
    client = BojClient(lang=args.lang, max_pages=args.max_pages)
    result = client.get_metadata(args.db)
    text, truncated = format_output(
        result,
        args.format,
        max_series_size=args.max_series_size,
        max_item_length=args.max_item_length,
    )
    _write_output(text, args.output, truncated)


def cmd_search(args: argparse.Namespace) -> None:
    client = BojClient(lang=args.lang, max_pages=args.max_pages)
    results = client.search_series(args.db, args.keywords)
    if not results:
        print(
            json.dumps({"message": "No series matched the given keywords."}, ensure_ascii=False),
            file=sys.stderr,
        )
        return
    text, truncated = format_output(
        results,
        args.format,
        max_series_size=args.max_series_size,
    )
    _write_output(text, args.output, truncated)


def cmd_get_data(args: argparse.Namespace) -> None:
    codes = [c.strip() for c in args.code.split(",")]
    client = BojClient(lang=args.lang, max_pages=args.max_pages)
    result = client.get_data_by_code(args.db, codes, start_date=args.start, end_date=args.end)
    text, truncated = format_output(
        result,
        args.format,
        max_series_size=args.max_series_size,
        max_item_length=args.max_item_length,
    )
    _write_output(text, args.output, truncated)


def cmd_get_layer(args: argparse.Namespace) -> None:
    client = BojClient(lang=args.lang, max_pages=args.max_pages)
    result = client.get_data_by_layer(
        args.db,
        args.layer,
        args.frequency,
        start_date=args.start,
        end_date=args.end,
    )
    text, truncated = format_output(
        result,
        args.format,
        max_series_size=args.max_series_size,
        max_item_length=args.max_item_length,
    )
    _write_output(text, args.output, truncated)


def cmd_latest(args: argparse.Namespace) -> None:
    codes = [c.strip() for c in args.code.split(",")]
    client = BojClient(lang=args.lang, max_pages=args.max_pages)
    result = client.get_latest(args.db, codes)
    text, truncated = format_output(
        result,
        args.format,
        max_series_size=args.max_series_size,
        max_item_length=args.max_item_length,
    )
    _write_output(text, args.output, truncated)


_COMMANDS = {
    "list-db": cmd_list_db,
    "get-metadata": cmd_metadata,
    "search-series": cmd_search,
    "get-data": cmd_get_data,
    "get-layer": cmd_get_layer,
    "latest": cmd_latest,
}


def main() -> None:
    _setup_logging()
    parser = build_parser()
    args = parser.parse_args()

    try:
        _COMMANDS[args.command](args)
    except BojClientError as exc:
        error_data: dict[str, str | int] = {"error": type(exc).__name__, "message": str(exc)}
        if hasattr(exc, "status_code"):
            error_data["status_code"] = exc.status_code  # type: ignore[attr-defined]
        if hasattr(exc, "message_id") and exc.message_id:  # type: ignore[attr-defined]
            error_data["message_id"] = exc.message_id  # type: ignore[attr-defined]
        if hasattr(exc, "api_message") and exc.api_message:  # type: ignore[attr-defined]
            error_data["api_message"] = exc.api_message  # type: ignore[attr-defined]
        print(json.dumps(error_data, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
