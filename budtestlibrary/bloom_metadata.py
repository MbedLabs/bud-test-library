"""
BloomMetadata - Direct linkage to Bloom PLM Test Cases (*-TC-*).
"""

import re
from dataclasses import dataclass
from typing import Any, Optional

_TC_ID_SUFFIX_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


@dataclass
class BloomMetaData:
    """
    Metadata linking a test class to a Test Case in Bloom PLM.
    Standard Format: {Project}-TC-{ID}
    """

    project: str
    tc_id_suffix: str
    description: Optional[str] = None

    def __post_init__(self):
        if not self.project or not self.project.strip():
            raise ValueError("BloomMetaData.project must be a non-empty string")
        if not self.tc_id_suffix or not self.tc_id_suffix.strip():
            raise ValueError("BloomMetaData.tc_id_suffix must be a non-empty string")
        if not _TC_ID_SUFFIX_PATTERN.match(self.tc_id_suffix):
            raise ValueError(
                f"BloomMetaData.tc_id_suffix must match '{_TC_ID_SUFFIX_PATTERN.pattern}', "
                f"got '{self.tc_id_suffix}'"
            )

    def get_full_tc_id(self) -> str:
        """Returns the full standard ID: *-TC-*"""
        return f"{self.project}-TC-{self.tc_id_suffix}"

    def get_url(self, base_url: str = "") -> str:
        """Get the direct URL to the test case."""
        return f"{base_url.rstrip('/')}/projects/{self.project}/test-cases/{self.tc_id_suffix}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "tc_id": self.get_full_tc_id(),
            "display_id": self.get_full_tc_id(),
            "description": self.description,
            "url": self.get_url(),
        }
