"""
RequirementMetadata - Links test cases to requirement management systems.

Supports:
- OpenProject (pm.embedlabs.de) - Work Packages
- Jira (planned) - Issues/Epics

Usage:
    class MyTest(BudTestCase):
        requirement_metadata = RequirementMetadata("BMS_Project", "WP-1234")
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
from enum import Enum


class RequirementSystem(Enum):
    """Supported requirement management systems."""
    OPENPROJECT = "openproject"
    JIRA = "jira"


@dataclass
class RequirementMetadata:
    """
    Metadata linking a test case to a requirement in a management system.
    
    For OpenProject:
        - project: Project identifier (e.g., "bms-project")
        - work_package_id: Work Package ID (e.g., "WP-1234" or "1234")
    
    For Jira (planned):
        - project: Project key (e.g., "BMS")
        - work_package_id: Issue key (e.g., "BMS-1234")
    
    Attributes:
        project: Project identifier in the requirement system.
        work_package_id: Work Package / Issue identifier.
        system: The requirement management system type.
        description: Optional description of the requirement link.
        url: Optional direct URL to the requirement.
    """
    
    project: str
    work_package_id: str
    system: RequirementSystem = RequirementSystem.OPENPROJECT
    description: Optional[str] = None
    url: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize the work package ID."""
        # Remove 'WP-' prefix if present for OpenProject
        if self.system == RequirementSystem.OPENPROJECT:
            if self.work_package_id.upper().startswith("WP-"):
                self.work_package_id = self.work_package_id[3:]

    def get_work_package_id(self) -> str:
        """Get the numeric/string Work Package ID."""
        return self.work_package_id

    def get_display_id(self) -> str:
        """Get a display-friendly ID with prefix."""
        if self.system == RequirementSystem.OPENPROJECT:
            return f"WP-{self.work_package_id}"
        elif self.system == RequirementSystem.JIRA:
            return f"{self.project}-{self.work_package_id}"
        return self.work_package_id

    def get_url(self, base_url: Optional[str] = None) -> str:
        """
        Get the URL to the requirement.
        
        Args:
            base_url: Base URL of the requirement system.
                      Defaults to pm.embedlabs.de for OpenProject.
        
        Returns:
            Full URL to the work package/issue.
        """
        if self.url:
            return self.url

        if self.system == RequirementSystem.OPENPROJECT:
            base = base_url or "https://pm.embedlabs.de"
            return f"{base}/projects/{self.project}/work_packages/{self.work_package_id}"
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
        system = RequirementSystem(data.get("system", "openproject"))
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
