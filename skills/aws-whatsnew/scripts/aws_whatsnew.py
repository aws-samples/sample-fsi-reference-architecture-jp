#!/usr/bin/env python3
"""Fetch AWS What's New announcements with date filtering."""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

API_URL = "https://aws.amazon.com/api/dirs/items/search?item.directoryId=whats-new-v2&sort_by=item.additionalFields.postDateTime&sort_order=desc&size={size}&item.locale=en_US&page={page}"


def parse_date(date_str: str) -> datetime:
    """Parse API date format to datetime."""
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")


def get_today_range() -> tuple[str, str]:
    """Get today's date range in UTC."""
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=0)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def to_utc_range(start_date: str, end_date: str) -> tuple[datetime, datetime]:
    """Convert date strings to UTC datetime range."""
    start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end = datetime.strptime(end_date, "%Y-%m-%d").replace(
        hour=23, minute=59, second=59, tzinfo=timezone.utc
    )
    return start, end


def fetch_with_retry(url: str, max_retries: int = 3) -> dict:
    """Fetch URL with exponential backoff retry."""
    scheme = urlparse(url).scheme
    if scheme not in ("http", "https"):
        raise ValueError(f"unsupported URL scheme '{scheme}': {url}")
    for attempt in range(max_retries):
        try:
            req = Request(url, headers={"User-Agent": "aws-whatsnew-skill/1.0"})  # noqa: S310 - scheme validated above
            with urlopen(req, timeout=30) as resp:  # noqa: S310 - scheme validated above  # nosec B310
                return json.loads(resp.read().decode("utf-8"))
        except (URLError, HTTPError) as e:
            if attempt == max_retries - 1:
                raise
            wait = 2**attempt
            print(f"Retry {attempt + 1}/{max_retries} after {wait}s: {e}", file=sys.stderr)
            time.sleep(wait)


def extract_service_name(tags: list) -> str | None:
    """Extract AWS service name from tags."""
    for tag in tags:
        tag_id = tag.get("id", "")
        if "#general-products#" in tag_id:
            service = tag_id.split("#")[-1]
            if service != "aws-govcloud-us":
                return service
    return None


def extract_category(tags: list) -> str | None:
    """Extract category name from tags."""
    for tag in tags:
        if tag.get("tagNamespaceId") == "whats-new-v2#marketing-marchitecture":
            return tag.get("name")
    return None


def fetch_whatsnew(start_date: str, end_date: str, size: int) -> list[dict]:
    """Fetch all What's New items within date range."""
    start_dt, end_dt = to_utc_range(start_date, end_date)
    results = []
    page = 0

    while True:
        url = API_URL.format(size=size, page=page)
        data = fetch_with_retry(url)
        items = data.get("items", [])

        if not items:
            break

        for item in items:
            fields = item.get("item", {}).get("additionalFields", {})
            date_str = fields.get("postDateTime", "")

            if not date_str:
                continue

            item_date = parse_date(date_str)

            if item_date < start_dt:
                return results

            if item_date > end_dt:
                continue

            tags = item.get("tags", [])
            results.append(
                {
                    "postDateTime": date_str,
                    "headline": fields.get("headline", ""),
                    "headlineUrl": fields.get("headlineUrl", ""),
                    "service": extract_service_name(tags),
                    "category": extract_category(tags),
                }
            )

        page += 1

    return results


def main():
    default_start, default_end = get_today_range()

    parser = argparse.ArgumentParser(description="Fetch AWS What's New announcements")
    parser.add_argument(
        "--start-date",
        default=default_start,
        help=f"Start date YYYY-MM-DD (default: {default_start})",
    )
    parser.add_argument(
        "--end-date", default=default_end, help=f"End date YYYY-MM-DD (default: {default_end})"
    )
    parser.add_argument(
        "--size",
        type=int,
        default=100,
        choices=range(1, 101),
        metavar="1-100",
        help="Items per page (default: 100)",
    )

    args = parser.parse_args()
    results = fetch_whatsnew(args.start_date, args.end_date, args.size)
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
