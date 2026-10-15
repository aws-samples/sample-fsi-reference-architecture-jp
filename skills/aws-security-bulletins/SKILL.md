---
name: aws-security-bulletins
description: >
  Fetch, search, and retrieve AWS Security Bulletins (vulnerability advisories and security announcements
  published by AWS). Use this skill when the user wants to check, search, list, or get details of
  AWS security bulletins, CVEs affecting AWS services, or AWS vulnerability disclosures.
  Trigger keywords: "security bulletin", "AWS CVE", "AWS vulnerability", "セキュリティ速報",
  "脆弱性情報", "AWS脆弱性", "security advisory".
license: MIT No Attribution
compatibility: Requires Python 3.11+, uv, and internet access to aws.amazon.com
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# AWS Security Bulletins

## When to use this skill

Use this skill when the user wants to:
- List or search AWS Security Bulletins
- Check recent AWS vulnerability disclosures or CVEs
- Get details of a specific AWS Security Bulletin by its ID or URL
- Monitor AWS security announcements

## Workflow

First, determine whether the user wants to **(1) list/search** bulletins or **(2) get details** of a specific one. Then execute the appropriate script command.

### 1. List / Search Bulletins

**1-a. Determine script arguments:**
- `--start-date` / `--end-date`: ISO 8601 dates. Default is the last 1 year. Convert natural language like "today", "this week", "last month" to appropriate dates.
- `--keyword`: Optional keyword(s) for title filtering (OR logic, case-insensitive). Multiple keywords can be specified.
- `--no-date-filter`: Disables date filtering entirely.

If the user's intent is ambiguous, ask for clarification before running the script.

**1-b. Run the script:**

```bash
uv run --project scripts scripts/fetch_bulletins.py list [--start-date YYYY-MM-DDTHH:MM:SSZ] [--end-date YYYY-MM-DDTHH:MM:SSZ] [--keyword kw1 kw2 ...] [--no-date-filter]
```

**1-c. Format the output as a Markdown table:**

The script outputs JSON conforming to [list-response-schema.json](references/list-response-schema.json). Present it as:

| # | Bulletin ID | Title | Published | Severity | URL |
|---|-------------|-------|-----------|----------|-----|
| 1 | AWS-2025-032 | Key Commitment Issues… | 2025-12-17 | important | https://… |

**1-d. Ask the user** if they want to retrieve details for any specific bulletin.

### 2. Get Bulletin Detail

**2-a. Confirm input:** Ensure a bulletin ID (e.g. `AWS-2025-032`, `2026-003-AWS`) or a full URL is provided. These are available from the `url` field in the list output.

**2-b. Prefer running this as a sub-agent** to avoid consuming the caller's context window with the full HTML body.

**2-c. Run the script:**

```bash
uv run --project scripts scripts/fetch_bulletins.py detail <BULLETIN_ID_OR_URL>
```

The script outputs JSON conforming to [detail-response-schema.json](references/detail-response-schema.json). The `body` field contains the full HTML of the bulletin.

**2-d. Summarize or answer:** If the user has a specific question, answer it based on the body content. Otherwise, provide a concise summary of the bulletin including: affected versions, description, resolution, and any CVE identifiers.

## Output schemas

- List response: [references/list-response-schema.json](references/list-response-schema.json)
- Detail response: [references/detail-response-schema.json](references/detail-response-schema.json)
- Error response: [references/error-response-schema.json](references/error-response-schema.json)

## Script details

- **Runtime:** Python 3.11+, standard library only, run via `uv run --project scripts`
- **Logging:** Uses `logging` module to stderr. Control via `LOG_LEVEL` env var (default: `WARN`)
- **Retries:** Exponential backoff, max 3 attempts for HTTP requests
- **Output:** JSON to stdout. Errors as JSON to stderr with non-zero exit code.

## Examples

List bulletins from the last year:
```bash
uv run --project scripts scripts/fetch_bulletins.py list
```

Search for S3-related bulletins:
```bash
uv run --project scripts scripts/fetch_bulletins.py list --keyword S3 encryption
```

Get bulletins from a specific date range:
```bash
uv run --project scripts scripts/fetch_bulletins.py list --start-date 2025-01-01T00:00:00Z --end-date 2025-12-31T23:59:59Z
```

Get all bulletins without date filtering:
```bash
uv run --project scripts scripts/fetch_bulletins.py list --no-date-filter
```

Get detail of a specific bulletin:
```bash
uv run --project scripts scripts/fetch_bulletins.py detail AWS-2025-032
uv run --project scripts scripts/fetch_bulletins.py detail https://aws.amazon.com/security/security-bulletins/AWS-2025-032/
```

## Disclaimer

This skill depends on an unofficial AWS endpoint (`https://aws.amazon.com/api/dirs/items/search`). This API is not publicly documented and may change without notice, which could cause this skill to stop working.