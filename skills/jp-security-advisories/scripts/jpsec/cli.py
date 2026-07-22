"""CLI orchestrator for jp-security-advisories."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from .adapters import ADAPTERS, ALL_SOURCES, DEFAULT_SOURCES, DETAIL_CAPABLE
from .adapters._base import ListQuery
from . import output

LOG = logging.getLogger(__name__)
DEFAULT_DAYS = 90


def _emit_error(code: str, message: str, **extras: Any) -> int:
    payload: dict[str, Any] = {"error": True, "code": code, "message": message}
    payload.update({k: v for k, v in extras.items() if v is not None})
    print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
    return 1


def _resolve_sources(arg_value: list[str] | None) -> list[str]:
    if not arg_value:
        return list(DEFAULT_SOURCES)
    if "all" in arg_value:
        return list(ALL_SOURCES)
    out: list[str] = []
    for s in arg_value:
        if s not in ADAPTERS:
            raise ValueError(f"Unknown source: {s}")
        if s not in out:
            out.append(s)
    return out


# ---- list-sources ----------------------------------------------------------


def cmd_list_sources(args: argparse.Namespace) -> int:
    src_specs = [
        {
            "name": "jpcert",
            "backend": "RSS + HTML",
            "endpoint": "https://www.jpcert.or.jp/rss/jpcert.rdf",
            "categories": ["alert", "weekly-report", "tsubame", "news", "blog", "other"],
        },
        {
            "name": "jpcert-all",
            "backend": "RSS + HTML",
            "endpoint": "https://www.jpcert.or.jp/rss/jpcert-all.rdf",
            "categories": ["alert", "weekly-report", "tsubame", "news", "blog", "other"],
        },
        {
            "name": "myjvn-alert",
            "backend": "MyJVN getAlertList API",
            "endpoint": "https://jvndb.jvn.jp/myjvn?method=getAlertList&feed=hnd",
            "categories": ["critical", "important", "low", "info"],
        },
        {
            "name": "myjvn-vuln",
            "backend": "MyJVN getVulnOverviewList + getVulnDetailInfo API",
            "endpoint": "https://jvndb.jvn.jp/myjvn?method=getVulnOverviewList&feed=hnd",
            "categories": ["critical", "high", "medium", "low", "none"],
        },
    ]
    payload = {"sources": src_specs}
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif args.format == "markdown":
        print("| Source | Backend | Endpoint |")
        print("|--------|---------|----------|")
        for s in src_specs:
            print(f"| `{s['name']}` | {s['backend']} | {s['endpoint']} |")
    elif args.format == "csv":
        import csv as csvlib
        w = csvlib.writer(sys.stdout)
        w.writerow(["name", "backend", "endpoint", "categories"])
        for s in src_specs:
            w.writerow([s["name"], s["backend"], s["endpoint"], ";".join(s["categories"])])
    return 0


# ---- list ------------------------------------------------------------------


def cmd_list(args: argparse.Namespace) -> int:
    try:
        sources = _resolve_sources(args.sources)
    except ValueError as e:
        return _emit_error("UNKNOWN_SOURCE", str(e))

    cache_dir = Path(args.cache_dir) if args.cache_dir else None

    today = dt.date.today()
    start: dt.date | None = None
    end: dt.date | None = None
    if not args.no_date_filter:
        start = (
            dt.date.fromisoformat(args.start_date)
            if args.start_date
            else today - dt.timedelta(days=DEFAULT_DAYS)
        )
        end = dt.date.fromisoformat(args.end_date) if args.end_date else today

    q = ListQuery(
        start=start,
        end=end,
        keywords=args.keywords,
        category=args.category,
        cves=args.cve,
        severity=args.severity,
        cpe=args.cpe,
        date_mode=args.date_mode,
        limit=args.limit,
        cache_dir=cache_dir,
    )

    all_items: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for s in sources:
        try:
            all_items.extend(ADAPTERS[s].list_items(q))
        except Exception as e:
            LOG.warning("source %s failed: %s", s, e)
            errors.append({"source": s, "code": "FETCH_ERROR", "message": str(e)})

    # Cap globally too (each adapter already caps per source)
    if args.limit is not None:
        all_items = all_items[: args.limit]

    payload = {
        "items": all_items,
        "metadata": {
            "total_fetched": len(all_items),
            "filtered_count": len(all_items),
            "sources_used": sources,
            "filters": {
                "start_date": start.isoformat() if start else None,
                "end_date": end.isoformat() if end else None,
                "date_mode": args.date_mode,
                "keywords": args.keywords or None,
                "category": args.category,
                "cve": args.cve or None,
                "severity": args.severity,
                "cpe": args.cpe,
                "limit": args.limit,
            },
            "errors": errors,
        },
    }

    if args.format == "json":
        print(output.list_json(payload))
    elif args.format == "csv":
        print(output.list_csv(all_items))
    elif args.format == "markdown":
        print(output.list_markdown(all_items))
    return 0


# ---- detail ----------------------------------------------------------------


def cmd_detail(args: argparse.Namespace) -> int:
    if args.source not in DETAIL_CAPABLE:
        return _emit_error(
            "UNKNOWN_SOURCE",
            f"detail not supported for source '{args.source}'. "
            f"Supported: {sorted(DETAIL_CAPABLE)}",
            source=args.source,
        )
    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    try:
        payload = ADAPTERS[args.source].detail(
            args.url_or_id, cache_dir=cache_dir
        )
    except ValueError as e:
        return _emit_error("UNRESOLVABLE_ID", str(e), source=args.source)
    except Exception as e:
        return _emit_error("FETCH_ERROR", str(e), source=args.source)

    if args.format == "json":
        print(output.detail_json(payload))
    elif args.format == "markdown":
        print(output.detail_markdown(payload))
    return 0


# ---- argparse --------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="fetch_advisories.py",
        description="Fetch and search Japanese security advisories",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    ls = sub.add_parser("list-sources", help="List available sources")
    ls.add_argument("--format", choices=["json", "csv", "markdown"], default="json")
    ls.set_defaults(func=cmd_list_sources)

    li = sub.add_parser("list", help="List / search advisories")
    li.add_argument("--sources", nargs="*",
                    help=f"One or more of {list(ADAPTERS) + ['all']}. "
                         f"Default: {' '.join(DEFAULT_SOURCES)}")
    li.add_argument("--start-date")
    li.add_argument("--end-date")
    li.add_argument("--no-date-filter", action="store_true")
    li.add_argument("--date-mode",
                    choices=["public", "published", "first-published"],
                    default="published",
                    help="myjvn-vuln only — which date axis to filter on")
    li.add_argument("--keywords", nargs="*")
    li.add_argument("--category")
    li.add_argument("--cve", nargs="*")
    li.add_argument("--severity",
                    choices=["none", "low", "medium", "high", "critical"])
    li.add_argument("--cpe")
    li.add_argument("--limit", type=int)
    li.add_argument("--format", choices=["json", "csv", "markdown"], default="json")
    li.add_argument(
        "--cache-dir",
        help="Optional directory for ETag / Last-Modified cache. "
             "If omitted, no files are written.",
    )
    li.set_defaults(func=cmd_list)

    de = sub.add_parser("detail", help="Get detail of a specific advisory")
    de.add_argument("--source", required=True, choices=sorted(DETAIL_CAPABLE))
    de.add_argument("url_or_id")
    de.add_argument("--format", choices=["json", "markdown"], default="json")
    de.add_argument(
        "--cache-dir",
        help="Optional directory for ETag / Last-Modified cache. "
             "If omitted, no files are written.",
    )
    de.set_defaults(func=cmd_detail)

    return p


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "WARN").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        LOG.exception("internal error")
        return _emit_error("INTERNAL_ERROR", str(e))
