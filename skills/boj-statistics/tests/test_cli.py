"""Tests for CLI argument parsing and command dispatch."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from boj_statistics_cli import build_parser, cmd_list_db, cmd_search


class TestArgParsing:
    def test_list_db(self):
        parser = build_parser()
        args = parser.parse_args(["list-db"])
        assert args.command == "list-db"
        assert args.format == "json"

    def test_metadata(self):
        parser = build_parser()
        args = parser.parse_args(["get-metadata", "--db", "FM08"])
        assert args.command == "get-metadata"
        assert args.db == "FM08"

    def test_search(self):
        parser = build_parser()
        args = parser.parse_args(["search-series", "--db", "FM08", "--keywords", "ドル", "円"])
        assert args.command == "search-series"
        assert args.keywords == ["ドル", "円"]

    def test_get_data(self):
        parser = build_parser()
        args = parser.parse_args([
            "get-data", "--db", "CO", "--code", "TK99F1000601GCQ01000",
            "--start", "202401", "--end", "202504",
        ])
        assert args.command == "get-data"
        assert args.code == "TK99F1000601GCQ01000"

    def test_get_layer(self):
        parser = build_parser()
        args = parser.parse_args([
            "get-layer", "--db", "BP01", "--layer", "1,1,1",
            "--frequency", "M", "--start", "202504",
        ])
        assert args.command == "get-layer"
        assert args.layer == "1,1,1"
        assert args.frequency == "M"

    def test_latest(self):
        parser = build_parser()
        args = parser.parse_args(["latest", "--db", "FM01", "--code", "STRDCLUCON"])
        assert args.command == "latest"

    def test_format_choices(self):
        parser = build_parser()
        for fmt in ["json", "csv", "tsv", "table"]:
            args = parser.parse_args(["list-db", "--format", fmt])
            assert args.format == fmt

    def test_output_option(self):
        parser = build_parser()
        args = parser.parse_args(["list-db", "--output", "/tmp/test.json"])
        assert args.output == "/tmp/test.json"

    def test_max_options(self):
        parser = build_parser()
        args = parser.parse_args([
            "get-metadata", "--db", "FM08",
            "--max-series-size", "50",
            "--max-item-length", "10",
            "--max-pages", "5",
        ])
        assert args.max_series_size == 50
        assert args.max_item_length == 10
        assert args.max_pages == 5


class TestListDbCommand:
    def test_outputs_json(self, capsys):
        parser = build_parser()
        args = parser.parse_args(["list-db"])
        cmd_list_db(args)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) > 0
        assert any(d["db_name"] == "FM08" for d in data)
