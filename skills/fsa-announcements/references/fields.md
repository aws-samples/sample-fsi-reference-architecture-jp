# Output fields

`fetch_announcements.py` writes a JSON array to stdout, sorted by
`published` descending. Each element is shaped as below.

```json
{
  "source": "rss",
  "published": "2026-06-08",
  "category": "報道発表",
  "title": "「金融サービス利用者相談室」における相談等の受付状況等…",
  "url": "https://www.fsa.go.jp/soudan/2026soudan01-03/2026_01-03.html"
}
```

| Field | Type | Description |
|---|---|---|
| `source` | string (`"rss"` \| `"recent"`) | Which upstream produced the entry. After de-duplication, an entry that appears in both is reported as `recent` (the more authoritative side). |
| `published` | string `YYYY-MM-DD` | JST-calendar publication date. RSS pubDates with the non-standard `JST` zone are normalised to `+0900` before parsing; recent.html wareki dates are converted to Western dates. |
| `category` | string \| null | One of `報道発表`, `記者会見`, `審議会等`, `国際関係`, `イベント`, `刊行物`, `採用`, `調達`, `その他`. From `recent.html` the value is always present; from RSS it can be `null` because some FSA RSS titles omit the prefix. |
| `title` | string | Announcement title. The category prefix (e.g. `報道発表,…`) is stripped from RSS titles. |
| `url` | string | Absolute URL pointing to the FSA announcement page. Site-relative recent.html hrefs are prefixed with `https://www.fsa.go.jp`. |

## De-duplication

When the same URL appears in both the RSS feed and a recent.html page,
the recent.html entry wins — it carries an authoritative `category`
label, which the RSS feed sometimes omits. The earlier-encountered
duplicate within the same source is kept. After de-duplication, items
are sorted by `(published, title)` descending.

## Category values are stable but extensible

The nine canonical categories listed above are stable as of the live
fetch on 2026-06-08. The integration test
`test_live_recent_current_year_parses_with_canonical_categories`
will fail if a new category appears, prompting an update.
