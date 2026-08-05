#!/usr/bin/env python3
"""Fetch and filter AWS customer reference case studies."""

import argparse
import json
import logging
import os
import sys
import urllib.request
import urllib.parse

LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARN").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.WARN),
                    format="%(asctime)s %(levelname)s %(message)s",
                    stream=sys.stderr)
log = logging.getLogger(__name__)

API_BASE = ("https://aws.amazon.com/api/dirs/items/search"
            "?item.directoryId=solution-case-studies-cards-interactive-customer-references"
            "&sort_by=item.additionalFields.date&sort_order=desc")

INDUSTRY_MAP = {
    "financial-services": [
        "financial", "finance", "banking", "insurance", "fintech",
        "金融", "銀行", "保険", "フィンテック",
    ],
    "healthcare": ["healthcare", "health", "medical", "ヘルスケア", "医療"],
    "manufacturing": ["manufacturing", "manufacture", "製造"],
    "retail": ["retail", "ecommerce", "e-commerce", "小売", "EC"],
    "media-entertainment": ["media", "entertainment", "メディア", "エンターテインメント"],
    "automotive": ["automotive", "auto", "car", "自動車"],
    "education": ["education", "学校", "教育"],
    "gaming": ["gaming", "game", "ゲーム"],
    "energy": ["energy", "エネルギー"],
    "telecommunications": ["telecom", "telecommunications", "通信"],
    "software-internet": ["software", "internet", "saas", "ソフトウェア", "インターネット"],
    "travel": ["travel", "旅行"],
    "hospitality": ["hospitality", "ホスピタリティ"],
    "life-sciences": ["life-sciences", "pharma", "ライフサイエンス", "製薬"],
    "power-utilities": ["power", "utilities", "電力"],
    "construction-real-estate": ["construction", "real-estate", "建設", "不動産"],
    "transport-logistics": ["transport", "logistics", "物流", "運輸"],
    "non-profit": ["non-profit", "nonprofit", "非営利"],
    "general-public-services": ["public-services", "government", "公共", "行政"],
    "digital-marketing": ["digital-marketing", "デジタルマーケティング"],
    "electronics": ["electronics", "電子"],
    "prof-services": ["professional-services", "consulting", "コンサルティング"],
}

LANGUAGE_MAP = {
    "en_US": ["english", "en", "英語"],
    "ja_JP": ["japanese", "ja", "日本語"],
    "zh_CN": ["chinese-simplified", "zh-cn", "中国語簡体"],
    "zh_TW": ["chinese-traditional", "zh-tw", "中国語繁体"],
    "ko_KR": ["korean", "ko", "韓国語"],
    "fr_FR": ["french", "fr", "フランス語"],
    "de_DE": ["german", "de", "ドイツ語"],
    "es_ES": ["spanish", "es", "スペイン語"],
    "pt_BR": ["portuguese", "pt", "ポルトガル語"],
}

PAGE_SIZE = 100


def resolve_industry(value: str) -> str:
    """Resolve a natural-language industry keyword to an API tag name."""
    v = value.lower().strip()
    if v in INDUSTRY_MAP:
        return v
    for tag, keywords in INDUSTRY_MAP.items():
        if v in [k.lower() for k in keywords]:
            return tag
    log.warning("Unknown industry '%s', using as-is", value)
    return v


def resolve_locales(values: list[str]) -> list[str]:
    """Resolve natural-language locale keywords to locale codes."""
    result = []
    for v in values:
        v_stripped = v.strip()
        # Check exact match against LANGUAGE_MAP keys (e.g. "en_US")
        if v_stripped in LANGUAGE_MAP:
            result.append(v_stripped)
            continue
        # Check keyword match (case-insensitive)
        v_lower = v_stripped.lower()
        found = False
        for code, keywords in LANGUAGE_MAP.items():
            if v_lower in [k.lower() for k in keywords]:
                result.append(code)
                found = True
                break
        if not found:
            log.warning("Unknown locale '%s', using as-is", v)
            result.append(v_stripped)
    return result


def _urlopen_with_retry(url: str, max_retries: int = 3, timeout: int = 30):
    """Open URL with exponential backoff retry."""
    import time
    scheme = urllib.parse.urlparse(url).scheme
    if scheme not in ("http", "https"):
        raise ValueError(f"unsupported URL scheme '{scheme}': {url}")
    for attempt in range(max_retries):
        try:
            return urllib.request.urlopen(url, timeout=timeout)  # noqa: S310 - scheme validated above  # nosec B310
        except (urllib.error.URLError, OSError) as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt
            log.warning("Request failed (attempt %d/%d): %s. Retrying in %ds...",
                        attempt + 1, max_retries, e, wait)
            time.sleep(wait)


def fetch_all(industry: str) -> tuple[list[dict], int]:
    """Fetch all items for a given industry from the API with pagination."""
    tag_id = f"GLOBAL#aws-industry#{industry}"
    all_items = []
    page = 0
    total_hits = 0
    while True:
        tag_encoded = urllib.parse.quote(tag_id, safe='')
        url = (
            f"{API_BASE}&size={PAGE_SIZE}&page={page}"
            f"&tags.id={tag_encoded}"
        )
        log.info("Fetching page %d: %s", page, url)
        with _urlopen_with_retry(url) as resp:
            data = json.loads(resp.read())
        total_hits = data["metadata"]["totalHits"]
        items = data.get("items", [])
        if not items:
            break
        all_items.extend(items)
        log.info(
            "Page %d: got %d items (total so far: %d / %d)",
            page, len(items), len(all_items), total_hits,
        )
        if len(all_items) >= total_hits:
            break
        page += 1
    return all_items, total_hits


def filter_items(items: list[dict], locales: list[str], start_date: str | None,
                 end_date: str | None, keywords: list[str]) -> list[dict]:
    """Filter items by locale, date range, and keywords."""
    results = []
    for entry in items:
        item = entry["item"]
        af = item.get("additionalFields", {})

        # locale filter
        if locales and item.get("locale") not in locales:
            continue

        # date filter
        pub_date = af.get("date", "")
        if start_date and pub_date < start_date:
            continue
        if end_date and pub_date > end_date:
            continue

        # keyword filter (OR across keywords, searched in title/body/name)
        if keywords:
            searchable = " ".join([
                af.get("title", ""),
                af.get("body", ""),
                item.get("name", ""),
            ]).lower()
            if not any(kw.lower() in searchable for kw in keywords):
                continue

        results.append({
            "locale": item.get("locale", ""),
            "location": af.get("location", ""),
            "name": item.get("name", ""),
            "publishedDate": af.get("publishedDate", af.get("date", "")),
            "title": af.get("title", ""),
            "body": af.get("body", ""),
            "url": af.get("ctaLink", ""),
        })
    return results


def main():
    parser = argparse.ArgumentParser(description="Fetch AWS customer reference case studies")
    parser.add_argument("--industry", default="financial-services",
                        help="Industry filter keyword (default: financial-services)")
    parser.add_argument("--locales", nargs="+", default=["en_US", "ja_JP"],
                        help="Locale codes or keywords (default: en_US ja_JP)")
    parser.add_argument("--start-date", default=None,
                        help="Start date filter YYYY-MM-DD (inclusive)")
    parser.add_argument("--end-date", default=None,
                        help="End date filter YYYY-MM-DD (inclusive)")
    parser.add_argument("--keywords", nargs="+", default=[],
                        help="Keywords to filter (OR condition, case-insensitive)")
    args = parser.parse_args()

    industry = resolve_industry(args.industry)
    locales = resolve_locales(args.locales)
    log.info("Industry: %s, Locales: %s, Date: %s~%s, Keywords: %s",
             industry, locales, args.start_date, args.end_date, args.keywords)

    items, total_hits = fetch_all(industry)
    references = filter_items(items, locales, args.start_date, args.end_date, args.keywords)

    # sort by publishedDate descending
    references.sort(key=lambda r: r.get("publishedDate", ""), reverse=True)

    output = {
        "metadata": {
            "total_hits": total_hits,
            "filtered_count": len(references),
            "filters_applied": {
                "industry": industry,
                "locales": locales,
                "start_date": args.start_date,
                "end_date": args.end_date,
                "keywords": args.keywords,
            },
        },
        "references": references,
    }
    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
