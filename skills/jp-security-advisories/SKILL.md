---
name: jp-security-advisories
description: >
  Fetch, search, and retrieve Japanese security advisories and vulnerability
  information from JPCERT/CC and the MyJVN API (IPA's structured advisory
  service that exposes IPA security alerts and JVN iPedia vulnerability data).
  Use this skill when the user wants to check, list, search, or get details of
  Japanese security advisories, CVE-related disclosures published in Japan, or
  coordinated vulnerability notices that may impact financial systems.
  Triggers on: "JPCERT", "JPCERT/CC", "IPA security", "MyJVN", "JVN", "JVN iPedia",
  "注意喚起", "重要なセキュリティ情報", "セキュリティアドバイザリ", "脆弱性情報",
  "国内セキュリティ動向", "CVE 日本語".
license: MIT No Attribution
compatibility: Requires Python 3.11+, uv, and internet access to jpcert.or.jp and jvndb.jvn.jp.
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# Japan Security Advisories

Aggregate and search Japanese security advisories — JPCERT/CC alerts and
the MyJVN API endpoints — and retrieve the body of individual advisories.

## When to use this skill

Use this skill when the user wants to:

- List or search **JPCERT/CC** 注意喚起 (alerts), Weekly Reports, TSUBAME
  reports, or JPCERT/CC Eyes blog posts
- List or search **IPA 注意警戒情報** (IPA security alerts) via the MyJVN
  API (`getAlertList`)
- List or search **JVN iPedia** vulnerability database via the MyJVN API
  (`getVulnOverviewList`) — supports CPE, keyword, CVSS severity, and
  multi-axis date filtering
- Get the structured detail of a JVN iPedia entry (`getVulnDetailInfo`) —
  affected products, CVSS scores, related CVEs, mitigation
- Get the body of a JPCERT/CC alert (HTML parsing — JPCERT does not expose
  a structured API)

This skill is complementary to `aws-security-bulletins`, which covers AWS
disclosures only.

## Sources

| `--sources` value | Backend | Coverage |
|---|---|---|
| `jpcert` | RSS (`https://www.jpcert.or.jp/rss/jpcert.rdf`) + HTML | JPCERT/CC alerts, urgent reports, latest Weekly Report vulnerabilities |
| `jpcert-all` | RSS (`https://www.jpcert.or.jp/rss/jpcert-all.rdf`) + HTML | `jpcert` + announcements + new JVN posts |
| `myjvn-alert` | **MyJVN API** `getAlertList` (Atom XML / JSON) | IPA 注意警戒情報, with structured related-references |
| `myjvn-vuln` | **MyJVN API** `getVulnOverviewList` + `getVulnDetailInfo` | JVN iPedia vulnerability database |

`jpcert` requires HTML scraping for advisory detail because JPCERT/CC does
not provide a structured API. `myjvn-alert` and `myjvn-vuln` rely entirely
on the MyJVN API and return XSD-validated XML.

Default `--sources`: `jpcert myjvn-alert myjvn-vuln`.

See [references/sources.md](references/sources.md) for endpoint details,
parameter mappings, and known limits.

## Workflow

First decide whether the user wants **(1) list/search** or **(2) detail**.
Then run the appropriate sub-command.

### 1. List / Search advisories

#### 1-a. Determine arguments

| Argument | Description | Default |
|---|---|---|
| `--sources` | One or more of `jpcert`, `jpcert-all`, `myjvn-alert`, `myjvn-vuln`, `all` | `jpcert myjvn-alert myjvn-vuln` |
| `--start-date` | ISO date `YYYY-MM-DD` (inclusive) | 90 days ago |
| `--end-date` | ISO date `YYYY-MM-DD` (inclusive) | today |
| `--no-date-filter` | Disable the date filter entirely | off |
| `--date-mode` | For `myjvn-vuln`: `public` / `published` / `first-published` (which date axis to filter) | `published` |
| `--keywords` | Space-separated keywords (OR, case-insensitive). Server-side for `myjvn-vuln`, client-side for others | (none) |
| `--category` | Filter by category — see [references/sources.md](references/sources.md) | (none) |
| `--cve` | One or more CVE identifiers. OR-matched against extracted CVEs | (none) |
| `--severity` | For `myjvn-vuln`: `none`, `low`, `medium`, `high`, `critical` | (none) |
| `--cpe` | For `myjvn-vuln`: CPE identifier (e.g. `cpe:/a:apache:tomcat`) | (none) |
| `--limit` | Cap the number of items returned | unlimited |
| `--format` | `json`, `csv`, or `markdown` | `json` |
| `--cache-dir` | If supplied, cache HTTP responses under this directory using ETag / Last-Modified conditional GETs. **Omitted by default — no files are written when the flag is absent.** | (off) |

If the user's intent is ambiguous (no source, no date, no keyword), ask
whether to proceed with the defaults.

#### 1-b. Sub-commands

```bash
uv run --project scripts scripts/fetch_advisories.py list-sources
uv run --project scripts scripts/fetch_advisories.py list [...]
uv run --project scripts scripts/fetch_advisories.py detail [...]
```

`list-sources` prints available sources, their backend endpoints, and
the categories supported per source.

#### 1-c. Run

```bash
uv run --project scripts scripts/fetch_advisories.py list \
  [--sources <s1> <s2> ...] \
  [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD] [--no-date-filter] \
  [--date-mode public|published|first-published] \
  [--keywords <kw1> <kw2> ...] \
  [--category <cat>] \
  [--cve <CVE-YYYY-NNNN> ...] \
  [--severity none|low|medium|high|critical] \
  [--cpe <cpe-string>] \
  [--limit N] \
  [--format json|csv|markdown]
```

Output JSON conforms to
[references/list-response-schema.json](references/list-response-schema.json).

#### 1-d. Format the output

For JSON output, render a Markdown table for the user:

| # | Source | Category | Date | Title | CVEs | Severity | URL |

`--format markdown` emits the Markdown table directly.

#### 1-e. Follow up

Ask the user whether they want detail for a specific advisory.

### 2. Get advisory detail

#### 2-a. Confirm input

A URL, or where applicable an ID:

- JPCERT URL (`https://www.jpcert.or.jp/at/.../...`)
- JVN iPedia URL or ID (`JVNDB-YYYY-NNNNNN`) — uses `getVulnDetailInfo`
- IPA security alert URL — handled via the related-references in the
  `myjvn-alert` list output (no separate detail call is necessary; the
  `getAlertList` response already contains structured items)

#### 2-b. Prefer running detail in a sub-agent

Detail responses can be substantial (especially for `myjvn-vuln` entries
with many affected products). Run `detail` in a sub-agent.

#### 2-c. Run

```bash
uv run --project scripts scripts/fetch_advisories.py detail \
  --source <jpcert|myjvn-vuln> \
  <URL_OR_ID> \
  [--format json|markdown]
```

Output JSON conforms to
[references/detail-response-schema.json](references/detail-response-schema.json).

For `myjvn-vuln`, the response is fully structured (no HTML parsing
involved): title, overview, affected products with vendor/product/CPE,
CVSS scores per evaluator, related advisories, and mitigation are all
parsed from VULDEF 3.2 XML.

For `jpcert`, the page is fetched and parsed best-effort into known
sections (概要 / 対象 / 対策 / 軽減策 / 参考情報). When the heading
pattern does not match, `sections` is empty — use `body_text`.

#### 2-d. Summarise or answer

If the user has a specific question, answer from the structured fields
(`affected`, `cvss`, `references`, `mitigation`) or `body_text`.
Otherwise, summarise: affected products / versions, description, CVSS,
mitigation, CVE references.

## Output schemas

- List response: [references/list-response-schema.json](references/list-response-schema.json)
- Detail response: [references/detail-response-schema.json](references/detail-response-schema.json)
- Error response: [references/error-response-schema.json](references/error-response-schema.json)

## Sources reference

[references/sources.md](references/sources.md) documents:

- Each source's endpoint and backend choice (RSS+HTML vs MyJVN API)
- MyJVN API parameter mapping
- Per-source category values
- Terms of use for each publisher

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
- **Logging:** Uses the `logging` module to stderr. Control via the `LOG_LEVEL` env var (default: `WARN`).
- **Retries:** Exponential backoff, max 3 attempts per HTTP request.
- **Output:** JSON to stdout. Errors as JSON to stderr with non-zero exit code.
- **Network access:** `jpcert.or.jp`, `blogs.jpcert.or.jp`, `jvndb.jvn.jp`.

## Examples

List the last 90 days from the default sources:
```bash
uv run --project scripts scripts/fetch_advisories.py list
```

JVN iPedia entries with CVSS severity ≥ high in the last 30 days:
```bash
uv run --project scripts scripts/fetch_advisories.py list \
  --sources myjvn-vuln --severity high \
  --start-date $(date -v-30d +%Y-%m-%d)
```

Find advisories that mention specific CVEs:
```bash
uv run --project scripts scripts/fetch_advisories.py list \
  --sources all --cve CVE-2026-0265 CVE-2025-20333
```

Get structured detail for a JVN iPedia entry:
```bash
uv run --project scripts scripts/fetch_advisories.py detail \
  --source myjvn-vuln JVNDB-2026-018267
```

Get the body of a JPCERT/CC alert:
```bash
uv run --project scripts scripts/fetch_advisories.py detail \
  --source jpcert https://www.jpcert.or.jp/at/2026/at260015.html
```

## Disclaimer

Each source is the property of its publishing organisation:

- **JPCERT/CC** — Japan Computer Emergency Response Team Coordination Center
- **IPA** — Information-technology Promotion Agency, Japan (via the MyJVN API)
- **JVN iPedia** — Operated by IPA / JPCERT/CC (via the MyJVN API)

The published HTML and API responses are the **canonical, authoritative
source** for any given advisory. This skill retrieves and summarises
content for convenience; consult the original page or API response before
taking action, especially for impact assessment and remediation. Each
publisher's terms of use govern downstream redistribution — see
[references/sources.md](references/sources.md) and [NOTICES.md](NOTICES.md).

**MyJVN API attribution**: IPA requests that applications displaying
information obtained from the MyJVN API show that the content is
"provided by the MyJVN API". When you display advisory information that
this skill produces from `myjvn-alert` or `myjvn-vuln` sources, please
include this attribution. The `source` field of each item indicates
whether the data originates from the MyJVN API.
