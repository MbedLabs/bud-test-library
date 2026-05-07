"""
budtestlibrary - Bud Test Automation Framework.

A comprehensive test framework providing:
- BudTestCase: Base class for test cases with lifecycle management, assertions, and logging
- BloomMetaData: Bloom PLM integration for test case traceability (*-TC-*)
- FlashEvent: Firmware flashing abstraction with success/failure handling
- BloomSync: Automatic test case synchronization to Bloom PLM

Backend: Bud TMP
PLM/PLM: Bloom PLM

Copyright (c) 2026 EmbedLabs
"""

from pathlib import Path

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
    return "0.1.6"

__version__ = _get_version()
__author__ = "EmbedLabs"
__email__ = "dev@embedlabs.de"

from budtestlibrary.budtestcase import BudTestCase
from budtestlibrary.bloom_metadata import BloomMetaData
from budtestlibrary.flash_event import FlashEvent, FlashSuccess, FlashFailure
from budtestlibrary.config import BudConfig
from budtestlibrary.bloom_sync import BloomSync

__all__ = [
    "BudTestCase",
    "BloomMetaData",
    "FlashEvent",
    "FlashSuccess",
    "FlashFailure",
    "BudConfig",
    "BloomSync",
]
