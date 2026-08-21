"""Source adapters."""

from __future__ import annotations

from . import jpcert, myjvn_alert, myjvn_vuln
from ._base import Adapter

ADAPTERS: dict[str, Adapter] = {
    "jpcert": jpcert.JPCERTAdapter("jpcert"),
    "jpcert-all": jpcert.JPCERTAdapter("jpcert-all"),
    "myjvn-alert": myjvn_alert.MyJvnAlertAdapter(),
    "myjvn-vuln": myjvn_vuln.MyJvnVulnAdapter(),
}

DEFAULT_SOURCES = ("jpcert", "myjvn-alert", "myjvn-vuln")
ALL_SOURCES = ("jpcert", "myjvn-alert", "myjvn-vuln")
DETAIL_CAPABLE = {"jpcert", "myjvn-vuln"}

__all__ = ["ADAPTERS", "DEFAULT_SOURCES", "ALL_SOURCES", "DETAIL_CAPABLE", "Adapter"]
