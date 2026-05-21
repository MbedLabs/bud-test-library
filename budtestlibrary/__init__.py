"""
budtestlibrary - Bud Test Automation Framework.

A comprehensive test framework providing:
- BudTestCase: Base class for test cases with lifecycle management, assertions, and logging
- BloomMetaData: Bloom PLM integration for test case traceability (*-TC-*)
- FlashEvent: Firmware flashing abstraction with success/failure handling

Backend: Bud TMP
PLM/PLM: Bloom PLM

Copyright (c) 2026 EmbedLabs
"""

from pathlib import Path

from budtestlibrary.bloom_metadata import BloomMetaData
from budtestlibrary.budtestcase import BudTestCase
from budtestlibrary.config import BudConfig, get_default_config
from budtestlibrary.flash_event import FlashEvent, FlashFailure, FlashSuccess


def _get_version():
    """Reads version from pyproject.toml."""
    try:
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            for line in pyproject_path.read_text().splitlines():
                if line.startswith("version = "):
                    return line.split("=")[1].strip().strip('"')
    except Exception:
        pass
    return "0.2.1"


__version__ = _get_version()
__author__ = "EmbedLabs"
__email__ = "dev@embedlabs.net"

__all__ = [
    "BudTestCase",
    "BloomMetaData",
    "FlashEvent",
    "FlashSuccess",
    "FlashFailure",
    "BudConfig",
    "get_default_config",
]
