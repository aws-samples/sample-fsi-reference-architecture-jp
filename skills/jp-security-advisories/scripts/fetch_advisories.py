#!/usr/bin/env python3
"""Entry point for jp-security-advisories.

The implementation lives in the ``jpsec`` package alongside this script.
"""
from __future__ import annotations

import sys

from jpsec.cli import main


if __name__ == "__main__":
    sys.exit(main())
