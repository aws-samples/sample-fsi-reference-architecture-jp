---
name: boj-statistics
description: >-
  Fetch, search, and analyze time-series statistical data from the Bank of Japan
  (BOJ) public API. Covers all BOJ databases including interest rates, money
  markets, foreign exchange, monetary base, Tankan survey, price indices,
  balance of payments, flow of funds, and more. Use this skill whenever the user
  wants to retrieve Japanese macroeconomic or financial statistics, look up BOJ
  data series, check exchange rates, get Tankan DI values, or explore any
  time-series data published by the Bank of Japan. Also use when the user
  mentions 日銀, 日本銀行, 時系列統計, 短観, 為替, マネタリーベース, 国際収支,
  企業物価, 資金循環, or any BOJ database name (FM08, CO, BP01, etc.).
  Trigger keywords: BOJ, Bank of Japan, 日銀, 日本銀行, 時系列統計, Tankan, 短観,
  exchange rate, 為替, interest rate, 金利, monetary base, マネタリーベース,
  money stock, マネーストック, balance of payments, 国際収支, price index, 物価指数,
  flow of funds, 資金循環, BOJ statistics, 日銀統計, 統計データ.
license: MIT No Attribution
compatibility: Requires Python 3.11+ and uv. No external Python packages needed — uses only the standard library.
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# BOJ Statistics Skill

Retrieve and analyze time-series statistical data from the Bank of Japan API.

## Workflow overview

1. Determine the user's intent: **explore databases**, **search series**, **fetch data**, or **get latest values**.
2. Identify the target DB name — consult [references/db_list.md](references/db_list.md) to find the right DB without running a command. For example, exchange rates are in `FM08`, Tankan is `CO`, balance of payments is `BP01`.
3. Execute `scripts/boj_statistics_cli.py` via `uv run --project scripts` with the appropriate sub-command.
4. Present results as a table, summary, or raw data depending on context.

## Available sub-commands

| Command | Purpose |
|---------|---------|
| `list-db` | List all available BOJ databases |
| `get-metadata` | Get series metadata for a specific database |
| `search-series` | Search series by keyword within a database |
| `get-data` | Fetch time-series data by series code (Code API) |
| `get-layer` | Fetch time-series data by layer hierarchy (Layer API) |
| `latest` | Fetch the most recent data point for specified series |

## 1 — Explore available databases

```bash
uv run --project scripts scripts/boj_statistics_cli.py list-db [--format json|csv|tsv|table] [--lang jp|en]
```

Returns the full list of BOJ database names and descriptions.

## 2 — Get metadata for a database

```bash
uv run --project scripts scripts/boj_statistics_cli.py get-metadata --db <DB_NAME> [--format json|csv|tsv|table] [--lang jp|en]
```

Returns all series codes, names, frequencies, and coverage periods for the specified DB.

## 3 — Search series by keyword

```bash
uv run --project scripts scripts/boj_statistics_cli.py search-series --db <DB_NAME> --keywords <kw1> [<kw2> ...] [--format json|csv|tsv|table] [--lang jp|en]
```

Searches series names (OR match, case-insensitive) within the specified DB. Useful when the user describes what data they want but doesn't know the series code.

Use `--db all` to search across all 50 databases at once — useful when the user doesn't know which DB contains the data they need. This takes longer (~2 minutes) due to rate limiting but eliminates the need to check `list-db` first.

```bash
uv run --project scripts scripts/boj_statistics_cli.py search-series --db all --keywords マネタリーベース --format table --max-series-size 10
```

## 4 — Fetch time-series data by code

```bash
uv run --project scripts scripts/boj_statistics_cli.py get-data --db <DB_NAME> --code <CODE1>[,<CODE2>,...] [--start <YYYYMM>] [--end <YYYYMM>] [--format json|csv|tsv|table] [--lang jp|en]
```

Fetches actual data values. Pagination is handled automatically. Codes are comma-separated.
All codes in a single request must share the same frequency — if you need to mix frequencies, make separate calls.

Date format depends on the series frequency (see [references/api_spec.md](references/api_spec.md) § Frequency Codes):
- Annual: `YYYY` (e.g. `2024`)
- Half-year / Quarterly: `YYYYHH` / `YYYYQQ` (e.g. `202401`)
- Monthly / Weekly / Daily: `YYYYMM` (e.g. `202503`)

## 5 — Fetch time-series data by layer

```bash
uv run --project scripts scripts/boj_statistics_cli.py get-layer --db <DB_NAME> --layer <LAYER_INFO> --frequency <FREQ> [--start <YYYYMM>] [--end <YYYYMM>] [--format json|csv|tsv|table] [--lang jp|en]
```

Layer info examples: `1,1,1` (specific path), `*` (all). Up to 5 levels can be specified.

The `--frequency` parameter is required and must be one of: `CY`, `FY`, `CH`, `FH`, `Q`, `M`, `W`, `D`.
See [references/api_spec.md](references/api_spec.md) § Frequency Codes for the full mapping.
Use `get-metadata` first to check which frequencies a DB actually contains — not every DB has every frequency.

## 6 — Get latest data point

```bash
uv run --project scripts scripts/boj_statistics_cli.py latest --db <DB_NAME> --code <CODE1>[,<CODE2>,...] [--format json|csv|tsv|table] [--lang jp|en]
```

Returns only the most recent observation for each series. Useful for quick lookups.

## Common options

| Option | Description | Default |
|--------|-------------|---------|
| `--format` | Output format: json, csv, tsv, table | json |
| `--lang` | Language: jp, en | jp |
| `--output` | Write to file instead of stdout | stdout |
| `--max-series-size` | Limit number of series in output | unlimited |
| `--max-item-length` | Limit data points per series | unlimited |
| `--max-pages` | Max pagination requests | 20 |

Pagination is automatic — the script follows `NEXTPOSITION` tokens across multiple requests.
See [references/api_spec.md](references/api_spec.md) § Pagination for API limits (250 series / 60,000 data points per request).

## Typical workflow

1. If the user wants to explore: run `list-db` → `get-metadata` → `search-series`
2. If the user doesn't know which DB to search: run `search-series --db all --keywords <terms>` to search across all databases
3. If the user knows the series: run `get-data` or `latest` directly
4. If the user wants hierarchical data: run `get-layer`
5. Use `--max-series-size` and `--max-item-length` to control output size for large datasets

## Use case examples

### Get exchange rate trends
```bash
uv run --project scripts scripts/boj_statistics_cli.py search-series --db FM08 --keywords ドル 円
uv run --project scripts scripts/boj_statistics_cli.py get-data --db FM08 --code FXERD01 --start 202401 --end 202412 --format table
```

### Get Tankan business conditions DI
```bash
uv run --project scripts scripts/boj_statistics_cli.py search-series --db CO --keywords 業況 大企業 製造業
uv run --project scripts scripts/boj_statistics_cli.py get-data --db CO --code TK99F1000601GCQ01000 --start 202401 --end 202504 --format table
```

### Explore series by keyword
```bash
uv run --project scripts scripts/boj_statistics_cli.py search-series --db BP01 --keywords 経常収支 --format table
```

## Gotchas

- Series codes do NOT include the DB name prefix. Use `FXERD01`, not `FM08'FXERD01`.
- All series in a single `get-data` request must share the same frequency.
- Weekly/daily date parameters use monthly format (YYYYMM).
- The API blocks high-frequency access. The script enforces rate limiting automatically.
- Metadata results include hierarchy header rows with empty series_code — these are structural, not data.

## Error handling

Errors are output to stderr as JSON with `error`, `message`, `status_code`, `message_id`, and `api_message` fields.
See [references/api_spec.md](references/api_spec.md) for the full error code table.

## Script reference

- **Script**: `scripts/boj_statistics_cli.py` (Python 3.11+, run via `uv run --project scripts`)
- **Package**: `scripts/boj_statistics/` (client library)
- **Dependencies**: None (Python standard library only)
- **Logging**: Set `LOG_LEVEL` env var (DEBUG, INFO, WARN, ERROR). Default: WARN.
- **Sample prompts**: See [references/sample-trigger.md](references/sample-trigger.md) for realistic trigger examples with outputs.
