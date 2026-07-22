"""HTTP GET with optional on-disk conditional cache (ETag / Last-Modified).

Caching is OFF by default. Pass cache_dir=<Path> to enable HTTP caching;
when cache_dir is None, no files are written. This default suits restricted
environments such as financial institutions where third-party scripts cannot
write to local disk.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

LOG = logging.getLogger(__name__)

USER_AGENT = (
    "fsi-reference-arch-jp/jp-security-advisories "
    "(+https://gitlab.aws.dev/aws-jp-sa-fsi/fsi-reference-architecture-jp)"
)


def _cache_paths(cache_dir: Path, url: str) -> tuple[Path, Path]:
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return cache_dir / f"{key}.body", cache_dir / f"{key}.meta.json"


def http_get(
    url: str,
    cache_dir: Path | None = None,
    timeout: int = 30,
    max_attempts: int = 3,
    extra_headers: dict[str, str] | None = None,
) -> bytes:
    scheme = urllib.parse.urlparse(url).scheme
    if scheme not in ("http", "https"):
        raise ValueError(f"unsupported URL scheme '{scheme}': {url}")
    body_path: Path | None = None
    meta_path: Path | None = None
    headers: dict[str, str] = {"User-Agent": USER_AGENT}
    if extra_headers:
        headers.update(extra_headers)

    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        body_path, meta_path = _cache_paths(cache_dir, url)
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text("utf-8"))
                if etag := meta.get("etag"):
                    headers["If-None-Match"] = etag
                if last_mod := meta.get("last_modified"):
                    headers["If-Modified-Since"] = last_mod
            except Exception as e:
                LOG.debug("ignoring unreadable cache metadata %s: %s", meta_path, e)

    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            # scheme validated above (http/https only)
            req = urllib.request.Request(url, headers=headers)  # noqa: S310
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
                body = resp.read()
                if body_path is not None and meta_path is not None:
                    body_path.write_bytes(body)
                    meta_path.write_text(
                        json.dumps(
                            {
                                "url": url,
                                "etag": resp.headers.get("ETag"),
                                "last_modified": resp.headers.get("Last-Modified"),
                                "content_type": resp.headers.get("Content-Type"),
                                "fetched_at": dt.datetime.now(
                                    dt.timezone.utc
                                ).isoformat(),
                            },
                            ensure_ascii=False,
                        ),
                        "utf-8",
                    )
                return body
        except urllib.error.HTTPError as e:
            if e.code == 304 and body_path is not None and body_path.exists():
                LOG.debug("304 from %s, using cache", url)
                return body_path.read_bytes()
            last_err = e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = e
        if attempt < max_attempts:
            time.sleep(2 ** (attempt - 1))
    if last_err is None:
        raise RuntimeError(f"failed to fetch {url} but no error was recorded")
    raise last_err


def cached_content_type(cache_dir: Path | None, url: str) -> str | None:
    """Read the previously stored Content-Type from cache meta if present.

    Returns None when caching is disabled (cache_dir is None) or when the
    URL has not been fetched into the cache yet.
    """
    if cache_dir is None:
        return None
    _, meta_path = _cache_paths(cache_dir, url)
    if not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text("utf-8"))
        return meta.get("content_type")
    except Exception:
        return None
