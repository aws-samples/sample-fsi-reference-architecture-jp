# Sources

## News RSS feed

- **URL:** `https://www.fsa.go.jp/fsaNewsListAll_rss2.xml`
- **Format:** RSS 2.0
- **Item count:** 15 (FSA-controlled, not configurable)
- **Conditional GET:** `Last-Modified` only (no `ETag`)
- **Per-item fields:** `title`, `link`, `pubDate` (always; `description`/`category`/`guid` are absent)
- **Categories:** Some titles are prefixed with a category and a comma —
  `採用,職員を募集しています…`. Approximately a third of items have no
  category prefix. The skill normalises the prefix when present and
  defers to the `recent.html` page (which always carries an explicit
  category label) when both sources cover the same URL.
- **Time zone:** `pubDate` uses the non-standard `JST` zone abbreviation.
  RFC 822 expects a numeric offset; the skill substitutes `+0900` before
  parsing so that the timestamp does not become a naive datetime.

### Example item (from a real fetch)

```xml
<item>
  <title>記者会見,片山財務大臣兼内閣府特命担当大臣閣議後記者会見の概要（令和８年６月２日）について掲載しました。</title>
  <link>https://www.fsa.go.jp/common/conference/minister/2026a/20260602-1.html</link>
  <description />
  <pubDate>Thu, 04 Jun 2026 10:00:00 JST</pubDate>
</item>
```

## recent{YYYY}.html archive pages

- **URL pattern:** `https://www.fsa.go.jp/recent/recent{YYYY}.html`
  where `YYYY` is the **Western year**.
- **Coverage:** 2021 onwards (`recent2020.html` returns 404).
- **Format:** HTML 5, UTF-8, anchor structure:
  ```html
  <h2>令和X年Y月<a id="..."></a></h2>
  <ul class="listtype04 longType">
    <li>
      <p>令和X年Y月Z日 <span class="label_en label15">報道発表</span></p>
      <a href="/path/to/article.html">タイトル</a>
    </li>
    ...
  </ul>
  ```
- **Date format:** Wareki — `令和X年Y月Z日`. Half-width / full-width
  digits and the literal `元年` are all observed in the live HTML and
  normalised by the parser.
- **Category labels (canonical 9):** `報道発表`, `記者会見`, `審議会等`,
  `国際関係`, `イベント`, `刊行物`, `採用`, `調達`, `その他`. The
  parser reads category text from the `<span>` body so the trailing
  `labelNN` digit can change without breaking parsing.
- **Per-year volume (observed):**
  | Year | Entries |
  |---|---|
  | 2021 | 1,169 |
  | 2022 | 1,371 |
  | 2023 | 1,128 |
  | 2024 | 1,251 |
  | 2025 | 1,149 |
  | 2026 (through early June) | 468 |
- **Conditional GET:** `Last-Modified` only.

## URL normalisation

`recent{YYYY}.html` lists entry URLs as site-relative paths
(e.g. `/news/r7/sonota/20260608/20260608.html`). The skill prefixes
`https://www.fsa.go.jp` to produce absolute URLs.

## Robustness notes for parser maintenance

- If an FSA UI refresh renames the `<ul class="listtype04 longType">`
  anchor, the parser falls back to scanning every `<li>` in the
  document — only those that contain a wareki date, a `<span class="label_en">`
  category, AND an `<a href>` are surfaced as announcements, so
  navigation `<li>` items are filtered out automatically.
- If the same refresh renames the `label_en` class on the category
  `<span>`, the parser will still recognise entries (the date and
  href are sufficient) but will lose the category. The integration
  test `test_live_recent_current_year_parses_with_canonical_categories`
  fails immediately if this happens, signalling that the parser needs
  updating.
- `parse_recent_html` raises if the parsed entry count drops below
  `min_entries` (default 50) — silent zero-length failures are
  considered worse than a loud error.

## Out-of-scope

- **Public-comment portal (e-Gov)** — `https://public-comment.e-gov.go.jp/`
  hosts FSA public-comment cases but the available RSS does not
  support per-ministry filtering. Public-comment lookup is a separate
  problem.
- **Procurement / 入札 RSS** — `https://www.fsa.go.jp/fsaProcurementList_rss2.xml`
  is published but is operationally distinct from FSA news; treat
  procurement as a different concern.
- **Supervisory-guideline body text** — the `recent.html` entry links
  to the announcement page only; full body text and PDF attachments
  must be retrieved with a separate fetch.
