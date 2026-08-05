"""CVE / JVN identifier extraction."""

from __future__ import annotations

import re

CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}", re.I)
JVN_ID_RE = re.compile(r"JVNDB-\d{4}-\d+|JVN#\d+", re.I)


def extract_ids(text: str) -> tuple[list[str], list[str]]:
    """Return (cves, jvn_ids) — sorted, deduped."""
    cves = sorted({m.group(0).upper() for m in CVE_RE.finditer(text or "")})
    jids = sorted({m.group(0) for m in JVN_ID_RE.finditer(text or "")})
    return cves, jids
