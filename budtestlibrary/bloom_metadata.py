"""
BloomMetadata - Direct linkage to Bloom ALM Test Cases (*-TC-*).
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class BloomMetaData:
    """
    Metadata linking a test class to a Test Case in Bloom ALM.
    Standard Format: {Project}-TC-{ID}
    """
    project: str
    tc_id_suffix: str
    description: Optional[str] = None

    def get_full_tc_id(self) -> str:
        """Returns the full standard ID: *-TC-*"""
        return f"{self.project}-TC-{self.tc_id_suffix}"

    def get_url(self, base_url: str = "https://bloom.embedlabs.de") -> str:
        """Get the direct URL to the test case."""
        return f"{base_url.rstrip('/')}/projects/{self.project}/test-cases/{self.tc_id_suffix}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project": self.project,
            "tc_id": self.get_full_tc_id(),
            "display_id": self.get_full_tc_id(),
            "description": self.description,
            "url": self.get_url()
        }
