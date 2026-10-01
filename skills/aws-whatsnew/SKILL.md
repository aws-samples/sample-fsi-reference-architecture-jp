---
name: aws-whatsnew
description: Fetch AWS What's New announcements from the official AWS API. Use when users ask about recent AWS announcements, new features, service updates, or want to know what's new in AWS. Supports date range filtering and returns structured JSON with headline, URL, service name, and category.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# AWS What's New

Fetch AWS What's New announcements with date filtering.

## Usage

Run the script:

```bash
uv run --project scripts scripts/aws_whatsnew.py [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD] [--size 1-100]
```

## Parameters

- `--start-date`: Start date (default: today in UTC)
- `--end-date`: End date (default: today in UTC)
- `--size`: Items per API request, 1-100 (default: 100)

## Output

JSON array with each item containing:

- `postDateTime`: Announcement date
- `headline`: Announcement title
- `headlineUrl`: URL path (prefix with `https://aws.amazon.com`)
- `service`: AWS service name (e.g., `amazon-connect`)
- `category`: Category name (e.g., `security-identity-and-compliance`)

## Response Schema

See [references/response-schema.json](references/response-schema.json) for the JSON Schema definition of the output
format.

## Example

```bash
# Get today's announcements
uv run --project scripts scripts/aws_whatsnew.py

# Get announcements for a specific date range
uv run --project scripts scripts/aws_whatsnew.py --start-date 2026-02-01 --end-date 2026-02-11
```

## Disclaimer

This skill depends on an unofficial AWS endpoint (`https://aws.amazon.com/api/dirs/items/search`). This API is not publicly documented and may change without notice, which could cause this skill to stop working.