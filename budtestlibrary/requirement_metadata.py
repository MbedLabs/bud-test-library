"""
RequirementMetadata - Links test cases to requirement management systems.

Supports:
- Bloom ALM (bloom.embedlabs.de) - Requirements
- Jira (planned) - Issues/Epics

Usage:
    class MyTest(BudTestCase):
        requirement_metadata = RequirementMetadata("BMS_Project", "REQ-1234")
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
from enum import Enum


class RequirementSystem(Enum):
    """Supported requirement management systems."""
    BLOOM = "bloom"
    JIRA = "jira"


@dataclass
class RequirementMetadata:
    """
    Metadata linking a test case to a requirement in a management system.
    
    For Bloom ALM:
        - project: Project prefix or identifier (e.g., "bms-project")
        - work_package_id: Requirement ID (e.g., "REQ-1234" or "1234")
    
    For Jira (planned):
        - project: Project key (e.g., "BMS")
        - work_package_id: Issue key (e.g., "BMS-1234")
    
    Attributes:
        project: Project identifier in the requirement system.
        work_package_id: Requirement / Issue identifier.
        system: The requirement management system type.
        description: Optional description of the requirement link.
        url: Optional direct URL to the requirement.
    """
    
    project: str
    work_package_id: str
    system: RequirementSystem = RequirementSystem.BLOOM
    description: Optional[str] = None
    url: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize the requirement ID."""
        if self.system == RequirementSystem.BLOOM:
            if self.work_package_id.upper().startswith("REQ-"):
                self.work_package_id = self.work_package_id[4:]

    def get_work_package_id(self) -> str:
        """Get the numeric/string requirement ID."""
        return self.work_package_id

    def get_display_id(self) -> str:
        """Get a display-friendly ID with prefix."""
        if self.system == RequirementSystem.BLOOM:
            return f"REQ-{self.work_package_id}"
        elif self.system == RequirementSystem.JIRA:
            return f"{self.project}-{self.work_package_id}"
        return self.work_package_id

    def get_url(self, base_url: Optional[str] = None) -> str:
        """
        Get the URL to the requirement.
        
        Args:
            base_url: Base URL of the requirement system.
                      Defaults to bloom.embedlabs.de for Bloom.
        
        Returns:
            Full URL to the requirement/issue.
        """
        if self.url:
            return self.url

        if self.system == RequirementSystem.BLOOM:
            base = base_url or ""
            if not base:
                return f"projects/{self.project}/requirements/{self.work_package_id}"
            return f"{base.rstrip('/')}/projects/{self.project}/requirements/{self.work_package_id}"
        elif self.system == RequirementSystem.JIRA:
            base = base_url or "https://jira.atlassian.com"
            return f"{base}/browse/{self.project}-{self.work_package_id}"
        
        return ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "project": self.project,
            "work_package_id": self.work_package_id,
            "system": self.system.value,
            "display_id": self.get_display_id(),
            "description": self.description,
            "url": self.get_url(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RequirementMetadata":
        """Create from dictionary."""
        system = RequirementSystem(data.get("system", "bloom"))
        return cls(
            project=data["project"],
            work_package_id=data["work_package_id"],
            system=system,
            description=data.get("description"),
            url=data.get("url"),
        )

    def __repr__(self) -> str:
        return f"RequirementMetadata({self.project}, {self.get_display_id()})"


# Alias for backwards compatibility with Polarion-style usage
PolarionMetadata = RequirementMetadata
