# BOJ API Specification Reference

## Endpoints

| API | Endpoint | Purpose |
|-----|----------|---------|
| Code API | `GET /api/v1/getDataCode` | Fetch data by series code |
| Layer API | `GET /api/v1/getDataLayer` | Fetch data by hierarchy |
| Metadata API | `GET /api/v1/getMetadata` | Fetch series metadata |

Base URL: `https://www.stat-search.boj.or.jp`

## Error Codes

| STATUS | MESSAGEID | Description |
|--------|-----------|-------------|
| 200 | M181000I | Success |
| 200 | M181030I | Success but no matching data |
| 400 | M181001E | Invalid input parameters |
| 400 | M181002E | Invalid language setting |
| 400 | M181003E | Invalid output format |
| 400 | M181004E | DB not specified |
| 400 | M181005E | Invalid DB name |
| 400 | M181006E | Series code not specified |
| 400 | M181007E | Series code count exceeds 1250 |
| 400 | M181008E | Invalid start date |
| 400 | M181009E | Invalid end date |
| 400 | M181010E | Date must be between 1850 and 2050 |
| 400 | M181011E | Start date must be <= end date |
| 400 | M181012E | Invalid start position |
| 400 | M181013E | Series code does not exist |
| 400 | M181014E | Series code frequency mismatch |
| 400 | M181015E | Start date format does not match frequency |
| 400 | M181016E | End date format does not match frequency |
| 400 | M181017E | Frequency not specified |
| 400 | M181018E | Invalid frequency |
| 400 | M181019E | Layer info not specified |
| 400 | M181020E | Invalid layer info |
| 500 | M181090S | Unexpected error |
| 503 | M181091S | Database access error |

## Rate Limits

- Avoid high-frequency access; connections may be blocked.
- Data is typically updated around 08:50 JST.
- Supports gzip compression via `Accept-Encoding: gzip` header.

## Pagination

- Max 250 series per request.
- Max 60,000 data points (series × periods) per request.
- `NEXTPOSITION` in response indicates more data available.
- Use `startPosition` parameter to continue from where the previous request left off.

## Frequency Codes

| Code | Meaning |
|------|---------|
| CY | Calendar year |
| FY | Fiscal year |
| CH | Calendar half-year |
| FH | Fiscal half-year |
| Q | Quarterly |
| M | Monthly |
| W | Weekly |
| D | Daily |
