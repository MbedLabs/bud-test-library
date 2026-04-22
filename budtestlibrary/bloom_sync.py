"""
BloomSync - Synchronize test cases to Bloom PLM.

Creates and updates test cases and campaigns in Bloom (bloom.embedlabs.de)
to track test case definitions and execution results.

Structure:
    Project
    └── Test Campaign (groups test cases, replaces "Test Suite")
        ├── Test Case 1
        ├── Test Case 2
        └── ...

Usage:
    sync = BloomSync()

    # Sync a test class
    sync.sync_test_case(
        project_identifier="bms-project",
        campaign_name="XYZ Tests",
        test_class=MyTestClass,
    )

    # Update with results
    sync.update_test_result(
        campaign_id=1,
        test_case_id=42,
        passed=True,
    )
"""

import requests
from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass, field
from enum import Enum

from budtestlibrary.config import BudConfig


class TestStatus(Enum):
    """Test execution status values."""
    NOT_RUN = "NotRun"
    PASS = "Pass"
    FAIL = "Fail"
    SKIPPED = "Skipped"


@dataclass
class BloomTestCaseInfo:
    """Information about a Bloom test case."""
    id: int
    tc_id: str
    title: str
    project_id: int
    description: Optional[str] = None
    status: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None
    campaign_id: Optional[int] = None
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tc_id": self.tc_id,
            "title": self.title,
            "project_id": self.project_id,
            "description": self.description,
            "status": self.status,
            "steps": self.steps,
            "campaign_id": self.campaign_id,
            "url": self.url,
        }


@dataclass
class BloomCampaignInfo:
    """Information about a Bloom test campaign."""
    id: int
    name: str
    project_id: int
    status: Optional[str] = None
    description: Optional[str] = None


class BloomSync:
    """
    Synchronizes test cases with Bloom PLM.

    Manages the creation and updating of test cases and campaigns,
    including execution result tracking via campaign items.

    Supports two authentication modes:
    - Token mode: provide a pre-obtained JWT via BudConfig.bloom_token
    - Login mode: provide email/password via BudConfig.bloom_email / bloom_password
    """

    def __init__(self, config: Optional[BudConfig] = None):
        """
        Initialize the Bloom sync client.

        Args:
            config: BudConfig instance. Uses default if not provided.
        """
        self._config = config or BudConfig()
        self._base_url = self._config.bloom_url.rstrip("/")
        self._api_url = f"{self._base_url}/api"
        self._session = requests.Session()
        self._session.headers["Content-Type"] = "application/json"

        if self._config.bloom_token:
            self._session.headers["Authorization"] = f"Bearer {self._config.bloom_token}"
        elif self._config.bloom_email and self._config.bloom_password:
            self._login(self._config.bloom_email, self._config.bloom_password)

    def _login(self, email: str, password: str) -> None:
        """Authenticate with Bloom and store the JWT."""
        response = self._session.post(
            f"{self._api_url}/auth/login",
            json={"email": email, "password": password},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        self._session.headers["Authorization"] = f"Bearer {data['access_token']}"

    # ==================== Project Methods ====================

    def find_project(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Find a project by prefix or numeric ID.

        Args:
            identifier: Project prefix string or numeric ID.

        Returns:
            Project dict if found, None otherwise.
        """
        try:
            project_id = int(identifier)
            response = self._session.get(
                f"{self._api_url}/projects/{project_id}",
                timeout=30,
            )
            if response.status_code == 200:
                return response.json()
            return None
        except ValueError:
            pass

        try:
            response = self._session.get(
                f"{self._api_url}/projects",
                timeout=30,
            )
            if response.status_code == 200:
                for project in response.json():
                    if project.get("prefix") == identifier:
                        return project
        except requests.exceptions.RequestException as e:
            print(f"Error fetching projects: {e}")

        return None

    def _resolve_project_id(self, identifier: str) -> int:
        """Resolve a project prefix/ID string to a numeric project ID."""
        try:
            return int(identifier)
        except ValueError:
            project = self.find_project(identifier)
            if project is None:
                raise ValueError(f"Project not found: {identifier}")
            return project["id"]

    # ==================== Test Case Methods ====================

    def find_test_case(
        self,
        project_id: int,
        title: str,
    ) -> Optional[Dict[str, Any]]:
        """Find a test case by project and title."""
        try:
            response = self._session.get(
                f"{self._api_url}/test-cases",
                params={"project_id": project_id},
                timeout=30,
            )
            if response.status_code == 200:
                for tc in response.json():
                    if tc.get("title") == title:
                        return tc
        except requests.exceptions.RequestException as e:
            print(f"Error finding test case: {e}")
        return None

    def create_test_case(
        self,
        project_id: int,
        title: str,
        description: str = "",
        steps: Optional[List[Dict[str, Any]]] = None,
        status: str = "Draft",
    ) -> Optional[Dict[str, Any]]:
        """Create a new test case in Bloom."""
        try:
            payload: Dict[str, Any] = {
                "project_id": project_id,
                "title": title,
                "description": description,
                "status": status,
            }
            if steps:
                payload["steps"] = steps

            response = self._session.post(
                f"{self._api_url}/test-cases",
                json=payload,
                timeout=30,
            )
            if response.status_code in (200, 201):
                return response.json()
            else:
                print(f"Error creating test case: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error creating test case: {e}")
        return None

    def update_test_case(
        self,
        test_case_id: int,
        updates: Dict[str, Any],
    ) -> bool:
        """Update an existing test case."""
        try:
            response = self._session.patch(
                f"{self._api_url}/test-cases/{test_case_id}",
                json=updates,
                timeout=30,
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"Error updating test case: {e}")
            return False

    # ==================== Campaign Methods ====================

    def find_campaign(
        self,
        project_id: int,
        name: str,
    ) -> Optional[Dict[str, Any]]:
        """Find a test campaign by project and name."""
        try:
            response = self._session.get(
                f"{self._api_url}/campaigns",
                params={"project_id": project_id},
                timeout=30,
            )
            if response.status_code == 200:
                for campaign in response.json():
                    if campaign.get("name") == name:
                        return campaign
        except requests.exceptions.RequestException as e:
            print(f"Error finding campaign: {e}")
        return None

    def create_campaign(
        self,
        project_id: int,
        name: str,
        description: str = "",
        test_case_ids: Optional[List[int]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a new test campaign."""
        try:
            payload: Dict[str, Any] = {
                "project_id": project_id,
                "name": name,
                "description": description,
                "test_case_ids": test_case_ids or [],
            }
            response = self._session.post(
                f"{self._api_url}/campaigns",
                json=payload,
                timeout=30,
            )
            if response.status_code in (200, 201):
                return response.json()
            else:
                print(f"Error creating campaign: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error creating campaign: {e}")
        return None

    def get_campaign_detail(self, campaign_id: int) -> Optional[Dict[str, Any]]:
        """Get full campaign details including items."""
        try:
            response = self._session.get(
                f"{self._api_url}/campaigns/{campaign_id}",
                timeout=30,
            )
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching campaign detail: {e}")
        return None

    def add_to_campaign(
        self,
        campaign_id: int,
        test_case_id: int,
    ) -> Optional[Dict[str, Any]]:
        """Add a test case to a campaign."""
        try:
            response = self._session.post(
                f"{self._api_url}/campaigns/{campaign_id}/items",
                params={"test_case_id": test_case_id},
                timeout=30,
            )
            if response.status_code in (200, 201):
                return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error adding to campaign: {e}")
        return None

    def update_campaign_item(
        self,
        campaign_id: int,
        item_id: int,
        status: Optional[str] = None,
        result: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> bool:
        """Update a campaign item (test execution result)."""
        try:
            payload: Dict[str, Any] = {}
            if status is not None:
                payload["status"] = status
            if result is not None:
                payload["result"] = result
            if comment is not None:
                payload["comment"] = comment

            response = self._session.patch(
                f"{self._api_url}/campaigns/{campaign_id}/items/{item_id}",
                json=payload,
                timeout=30,
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"Error updating campaign item: {e}")
            return False

    # ==================== Test Run Links ====================

    def link_test_run(
        self,
        requirement_id: int,
        test_run_id: int,
        test_run_name: Optional[str] = None,
        teststation_url: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Link a Bud test run to a Bloom requirement."""
        try:
            payload: Dict[str, Any] = {"test_run_id": test_run_id}
            if test_run_name is not None:
                payload["test_run_name"] = test_run_name
            if teststation_url is not None:
                payload["teststation_url"] = teststation_url
            if status is not None:
                payload["status"] = status

            response = self._session.post(
                f"{self._api_url}/requirements/{requirement_id}/link-testrun",
                json=payload,
                timeout=30,
            )
            if response.status_code in (200, 201):
                return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error linking test run: {e}")
        return None

    # ==================== Test Sync Methods ====================

    def sync_test_case(
        self,
        project_identifier: str,
        campaign_name: str,
        test_class: Type,
        description: str = "",
    ) -> Optional[BloomTestCaseInfo]:
        """
        Sync a test class to Bloom as a TestCase inside a campaign.

        Creates or finds a campaign (equivalent to the old "Test Suite"),
        then creates or finds the test case and adds it to the campaign.

        Args:
            project_identifier: Bloom project prefix or numeric ID.
            campaign_name: Campaign name (groups test cases).
            test_class: The test class to sync.
            description: Optional description for the test case.

        Returns:
            BloomTestCaseInfo for the synced test case.
        """
        project_id = self._resolve_project_id(project_identifier)

        campaign = self.find_campaign(project_id, campaign_name)
        if not campaign:
            campaign = self.create_campaign(
                project_id=project_id,
                name=campaign_name,
                description=f"Test suite: {campaign_name}",
            )

        if not campaign:
            print(f"Failed to find/create campaign: {campaign_name}")
            return None

        campaign_id = campaign["id"]

        test_name = test_class.__name__
        tc = self.find_test_case(project_id, test_name)

        if not tc:
            test_methods = [
                m for m in dir(test_class)
                if m.startswith("mate_") and callable(getattr(test_class, m, None))
            ]

            full_description = description
            if test_methods:
                full_description += "\n\n## Test Methods\n"
                for method in test_methods:
                    full_description += f"- `{method}`\n"

            steps = [
                {"step": i + 1, "action": m, "expected": ""}
                for i, m in enumerate(test_methods)
            ] if test_methods else None

            tc = self.create_test_case(
                project_id=project_id,
                title=test_name,
                description=full_description,
                steps=steps,
            )

        if not tc:
            return None

        detail = self.get_campaign_detail(campaign_id)
        if detail:
            existing_tc_ids = {
                item["test_case_id"] for item in detail.get("items", [])
            }
            if tc["id"] not in existing_tc_ids:
                self.add_to_campaign(campaign_id, tc["id"])

        return BloomTestCaseInfo(
            id=tc["id"],
            tc_id=tc.get("tc_id", ""),
            title=tc.get("title", test_name),
            project_id=project_id,
            description=tc.get("description"),
            status=tc.get("status"),
            steps=tc.get("steps"),
            campaign_id=campaign_id,
            url=f"{self._base_url}/projects/{project_id}/test-cases/{tc['id']}",
        )

    def sync_test_suite(
        self,
        project_identifier: str,
        campaign_name: str,
        test_classes: List[Type],
    ) -> List[BloomTestCaseInfo]:
        """
        Sync multiple test classes to Bloom under a single campaign.

        Args:
            project_identifier: Bloom project prefix or numeric ID.
            campaign_name: Name of the test campaign.
            test_classes: List of test classes to sync.

        Returns:
            List of BloomTestCaseInfo for all synced test cases.
        """
        results = []
        for test_class in test_classes:
            tc_info = self.sync_test_case(
                project_identifier=project_identifier,
                campaign_name=campaign_name,
                test_class=test_class,
            )
            if tc_info:
                results.append(tc_info)
        return results

    def update_test_result(
        self,
        campaign_id: int,
        test_case_id: int,
        passed: bool,
        comment: str = "",
    ) -> bool:
        """
        Update a test case result within a campaign.

        Args:
            campaign_id: Campaign ID containing the test case.
            test_case_id: Test case ID to update.
            passed: Whether the test passed.
            comment: Optional comment on the result.

        Returns:
            True if update was successful.
        """
        detail = self.get_campaign_detail(campaign_id)
        if not detail:
            return False

        for item in detail.get("items", []):
            if item["test_case_id"] == test_case_id:
                return self.update_campaign_item(
                    campaign_id=campaign_id,
                    item_id=item["id"],
                    status="Passed" if passed else "Failed",
                    result=TestStatus.PASS.value if passed else TestStatus.FAIL.value,
                    comment=comment,
                )

        return False
