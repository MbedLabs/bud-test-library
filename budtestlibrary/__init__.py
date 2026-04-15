"""
budtestlibrary - Test automation framework for embedded systems testing.

A comprehensive test framework providing:
- BudTestCase: Base class for test cases with lifecycle management, assertions, and logging
- RequirementMetadata: Bloom ALM/Jira integration for requirement traceability
- FlashEvent: Firmware flashing abstraction with success/failure handling
- BloomSync: Automatic test case synchronization to Bloom ALM

Backend: https://bud.embedlabs.de/
ALM: https://bloom.embedlabs.de/ (Bloom)

Copyright (c) 2025 EmbedLabs
"""

from budtestlibrary.budtestcase import BudTestCase
from budtestlibrary.requirement_metadata import RequirementMetadata
from budtestlibrary.flash_event import FlashEvent, FlashSuccess, FlashFailure
from budtestlibrary.config import BudConfig
from budtestlibrary.bloom_sync import BloomSync

__version__ = "0.1.0"
__author__ = "EmbedLabs"
__email__ = "dev@embedlabs.de"

__all__ = [
    "BudTestCase",
    "RequirementMetadata",
    "FlashEvent",
    "FlashSuccess",
    "FlashFailure",
    "BudConfig",
    "BloomSync",
]
