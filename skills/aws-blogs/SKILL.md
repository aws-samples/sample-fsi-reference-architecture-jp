---
name: aws-blogs
description: >-
  Search and retrieve AWS blog posts (service guides, customer stories, event
  recaps, new feature announcements, etc.) from the public AWS Blog directory
  API. Supports both English (en_US) and Japanese (ja_JP) blogs — these are
  independent content sets, not translations of each other. Use this skill
  whenever the user wants to browse, search, or read AWS blog articles.
  Trigger keywords: AWS blog, AWS ブログ, blog search, blog article, blog post,
  customer story, 事例, new launch, what's new, ブログ検索, ブログ記事.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# AWS Blogs Skill

Retrieve and present AWS blog posts via the public directory API.

## Workflow overview

1. Determine the user's intent: **list/search** or **detail** (or both sequentially).
2. Confirm the target language (`en_US` or `ja_JP`) — content differs by locale.
3. Execute `scripts/fetch_blogs.py` with the appropriate sub-command.
4. Present results as a Markdown table (list) or summarised content (detail).

## 1 — List / Search blog posts

### 1-a Confirm parameters

| Parameter | How to determine |
|---|---|
| `--locale` | Ask the user if unclear. `en_US` and `ja_JP` are separate article sets. |
| `--start-date` | Convert natural language ("this week", "last month") to `YYYY-MM-DD`. Default: 30 days ago. |
| `--end-date` | Same conversion. Default: today. |
| `--no-date-filter` | When specified, skip date filtering and retrieve all available posts. `--start-date` and `--end-date` are ignored. |
| `--keywords` | Optional. Multiple keywords are OR-matched (case-insensitive) against title and excerpt. |

### 1-b Execute

```bash
uv run --project scripts scripts/fetch_blogs.py list \
  --locale <en_US|ja_JP> \
  --start-date <YYYY-MM-DD> \
  --end-date <YYYY-MM-DD> \
  [--no-date-filter] \
  [--keywords <kw1> <kw2> ...]
```

The script pages through the API automatically and outputs a JSON array to stdout.
When `--no-date-filter` is specified, `--start-date` and `--end-date` are ignored and all available posts are retrieved.
See [list_response_schema.json](references/list_response_schema.json) for the output schema.

### 1-c Present results

Convert the JSON array into a Markdown table:

```
| # | Title | Date | URL |
|---|-------|------|-----|
| 1 | ...   | ...  | ... |
```

Include the excerpt when the result set is small (≤10). Omit it for larger sets to save context.

### 1-d Follow-up

Ask the user whether they want to read the full content of any listed article (→ step 2).

## 2 — Retrieve blog post detail

### 2-a Confirm input

One or more identifiers are required:
- A full URL (`https://aws.amazon.com/blogs/...` or `https://aws.amazon.com/jp/blogs/...`)
- An API ID (`blog-posts-v2#<uuid>`)

Both forms require `--locale`.

### 2-b Execute (prefer subagent)

Run in a subagent when possible to avoid filling the caller's context with large HTML content.

```bash
uv run --project scripts scripts/fetch_blogs.py detail \
  --locale <en_US|ja_JP> \
  <url_or_id_1> [<url_or_id_2> ...]
```

Output is a JSON array to stdout.
See [detail_response_schema.json](references/detail_response_schema.json) for the output schema.

### 2-c Present results

- If the user asked a specific question, answer it based on the content.
- Otherwise, summarise the article and return the summary to the caller.

## Error handling

Fatal errors are written to stderr as JSON.
See [error_response_schema.json](references/error_response_schema.json) for the schema.

## Script reference

- **Script**: `scripts/fetch_blogs.py` (Python 3.11+, run via `uv run --project scripts`)
- **Dependencies**: None (Python standard library only)
- **Logging**: Set `LOG_LEVEL` env var (`DEBUG`, `INFO`, `WARN`, `ERROR`). Default: `WARN`.
- **Retries**: Exponential backoff, max 3 attempts on network errors.

## Disclaimer

This skill depends on an unofficial AWS endpoint (`https://aws.amazon.com/api/dirs/items/search`). This API is not publicly documented and may change without notice, which could cause this skill to stop working.