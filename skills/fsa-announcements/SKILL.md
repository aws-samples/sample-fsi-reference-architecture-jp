---
name: fsa-announcements
description: >
  Fetch announcements from the Financial Services Agency of Japan (FSA),
  combining the official news RSS feed (~15 latest items) with archive pages
  recent{YYYY}.html for date-range queries reaching back to 2021. Categories
  cover 報道発表 (press release), 記者会見 (press conference), 審議会等
  (council), 国際関係 (international), イベント (event), 刊行物 (publication),
  採用 (recruitment), 調達 (procurement), and その他 (other). Use this skill
  when the user wants to monitor regulatory announcements, council outcomes,
  supervisory guideline drafts, or other FSA disclosures relevant to financial
  institutions in Japan.
  Triggers on: "金融庁", "FSA", "報道発表", "監督指針", "パブコメ" (use only
  the FSA-side notice — public comment portal lookup is out of scope), "審議会",
  "金融庁 新着", "金融庁 ニュース", "金融行政方針".
license: MIT No Attribution
compatibility: >
  Requires Python 3.11+, uv, and internet access to www.fsa.go.jp.
  No third-party Python packages are used.
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# FSA Announcements

Aggregate and filter announcements published by the Financial Services
Agency of Japan (FSA) — combining the official news RSS feed with the
yearly `recent{YYYY}.html` archive pages.

## When to use this skill

Use this skill when the user wants to:

- Monitor recent FSA **press releases** (報道発表), **council outcomes**
  (審議会等), or **international relations** announcements (国際関係)
- Build a date-bounded list of FSA announcements within an arbitrary
  window (today back to 2021) — for instance, "all 報道発表 from
  2026-04-01 to today"
- Filter by one or more categories (e.g. only 報道発表 and 審議会等)
- Cross-reference an item observed elsewhere against the FSA's own list
  to confirm publication date and category

This skill is complementary to `boj-statistics` (BOJ time-series data)
and `jp-security-advisories` (JPCERT/MyJVN security disclosures).

## Sources

| Source | Backend | Coverage |
|---|---|---|
| News RSS | `https://www.fsa.go.jp/fsaNewsListAll_rss2.xml` | The newest ~15 items across all categories. RFC 822 RSS 2.0; `pubDate` uses the non-standard `JST` zone abbreviation, normalised by this skill. |
| `recent{YYYY}.html` | `https://www.fsa.go.jp/recent/recent{YYYY}.html` | One HTML page per Western year, with month-by-month `<ul>` blocks. Pages exist from 2021 onward. |

The RSS feed is small but always current; the recent pages are large
(typically 1,100+ entries per full year) and provide authoritative
category labels. When both sources contribute to a date range, the
skill de-duplicates by URL and prefers the recent-page entry because it
carries an authoritative category derived from the FSA's own label
markup.

See [references/sources.md](references/sources.md) for endpoint details
and known limits.

## Workflow

### 1. Determine arguments

| Argument | Description | Default |
|---|---|---|
| `--start-date` | Inclusive start date in `YYYY-MM-DD` (JST calendar). **Required.** | — |
| `--end-date` | Inclusive end date. | today (JST) |
| `--source` | One of `rss`, `recent`, `both` | `both` |
| `--category` | Filter by category (repeatable). One of: `報道発表`, `記者会見`, `審議会等`, `国際関係`, `イベント`, `刊行物`, `採用`, `調達`, `その他` | (none → all categories) |
| `--cache-dir` | If supplied, cache HTTP responses under this directory using ETag / Last-Modified conditional GETs. **Omitted by default — no files are written when the flag is absent.** | (off) |
| `--diagnose` | Print per-source counts to stderr (helpful when investigating coverage anomalies or FSA HTML changes) | off |
| `--log-level` | `DEBUG`/`INFO`/`WARNING`/`ERROR` (or via `FSA_LOG_LEVEL`) | `WARNING` |

If the user's intent is ambiguous (no date hint, no keyword), confirm
the date range before proceeding.

### 2. Run

```bash
uv run --project scripts scripts/fetch_announcements.py \
  --start-date <YYYY-MM-DD> [--end-date <YYYY-MM-DD>] \
  [--source rss|recent|both] \
  [--category 報道発表 ...] \
  [--cache-dir <PATH>] [--diagnose]
```

The script writes a JSON array to stdout, one object per announcement,
sorted by `published` descending. See [references/fields.md](references/fields.md)
for the field schema.

### 3. Summarise

Either:

- Pass the JSON straight to the user when they asked for a list,
- Or summarise — typically grouping by category and date range,
  highlighting items the user is likely to care about (e.g. supervisory
  guideline drafts inside 報道発表), and citing the FSA URL alongside.

### 4. Handle large windows in a sub-agent

A multi-year `recent{YYYY}.html` pull can return thousands of items.
Run such pulls inside a sub-agent so that the parent context is not
flooded with raw entries.

## Cache behaviour (important for restricted environments)

By default the script writes **no files** to the local filesystem.
Pass `--cache-dir <path>` to opt into HTTP caching:

- Each response is stored as `{sha256(url)}.body` and `{sha256(url)}.meta.json`
- Subsequent runs send `If-None-Match` / `If-Modified-Since` and reuse
  the cached body on `304 Not Modified`
- Errors during caching are non-fatal; the network response always
  takes precedence

This default suits financial institutions where third-party scripts
writing to local disk is typically not permitted.

## Script details

- **Runtime:** Python 3.11+, standard library only, run via `uv run --project scripts`
- **Logging:** `logging` module to stderr (`--log-level` or `FSA_LOG_LEVEL`)
- **Retries:** Exponential backoff, max 3 attempts per HTTP request
- **Output:** JSON to stdout; errors to stderr with non-zero exit code
- **Network access:** `www.fsa.go.jp`

## Examples

Last 7 days, all categories:
```bash
uv run --project scripts scripts/fetch_announcements.py --start-date 2026-06-01
```

Press releases only, full quarter:
```bash
uv run --project scripts scripts/fetch_announcements.py \
  --start-date 2026-04-01 --end-date 2026-06-30 \
  --category 報道発表
```

Multi-category audit (press releases + council outcomes) for a fiscal year:
```bash
uv run --project scripts scripts/fetch_announcements.py \
  --start-date 2025-04-01 --end-date 2026-03-31 \
  --category 報道発表 --category 審議会等
```

Opt into local caching:
```bash
uv run --project scripts scripts/fetch_announcements.py \
  --start-date 2026-06-01 \
  --cache-dir ~/.cache/aws-jp-fsi/fsa-announcements
```

## Disclaimer

The FSA is the publisher of every item this skill returns. The published
HTML page is the **canonical, authoritative source** — consult the
original page before taking any regulatory or operational action. This
skill retrieves and re-shapes content for convenience; it does not
verify, interpret, or warrant the accuracy of FSA notices, and titles
may be paraphrased by the upstream feed when the underlying article is
revised.

**Attribution requirement (PDL 1.0):** FSA content is licensed under the
[Public Domain Licence (PDL) 1.0](https://www.digital.go.jp/resources/open_data/public_data_license_v1.0)
(CC BY 4.0–compatible) and **requires attribution**. When you display
items produced by this skill, include the URL alongside, and credit
"出典：金融庁ウェブサイト". When editing or summarising, also disclose
the editing — see [NOTICES.md](NOTICES.md) for the required forms.
