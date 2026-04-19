"""
budtestlibrary - Test automation framework for embedded systems testing.

A comprehensive test framework providing:
- BudTestCase: Base class for test cases with lifecycle management, assertions, and logging
- RequirementMetadata: Bloom ALM/Jira integration for requirement traceability
- FlashEvent: Firmware flashing abstraction with success/failure handling
- BloomSync: Automatic test case synchronization to Bloom ALM

Backend: Bud ALM backend
ALM: Bloom ALM

Copyright (c) 2025 EmbedLabs
"""

from pathlib import Path

# Dynamic versioning logic
def _get_version():
    # 1. Prioritize local pyproject.toml (for source runs)
    try:
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            for line in pyproject_path.read_text().splitlines():
                if line.startswith("version = "):
                    return line.split("=")[1].strip().strip('"')
    except Exception:
        pass

    # 2. Fallback to installed package metadata
    try:
        from importlib.metadata import version
        return version("budtestlibrary")
    except Exception:
        return "0.0.0-unknown"

__version__ = _get_version()
__author__ = "EmbedLabs"
__email__ = "dev@embedlabs.de"

from budtestlibrary.budtestcase import BudTestCase
from budtestlibrary.requirement_metadata import RequirementMetadata
from budtestlibrary.flash_event import FlashEvent, FlashSuccess, FlashFailure
from budtestlibrary.config import BudConfig
from budtestlibrary.bloom_sync import BloomSync

__all__ = [
    "BudTestCase",
    "RequirementMetadata",
    "FlashEvent",
    "FlashSuccess",
    "FlashFailure",
    "BudConfig",
    "BloomSync",
]
