"""
OpenProjectSync - Synchronize test cases to OpenProject Work Packages.

Creates and updates Work Packages in OpenProject (pm.embedlabs.de) to track
test case definitions and execution results.

Structure:
    Project
    └── Test Suite (Work Package, type: "Test Suite")
        ├── Test Case 1 (Work Package, type: "Test Case")
        ├── Test Case 2 (Work Package, type: "Test Case")
        └── ...

Custom Fields:
    - test_status: Pass/Fail/Skipped/NotRun
    - last_run_date: Date of last execution
    - last_run_url: Link to bud.embedlabs.de result
    - pass_count: Total passed runs
    - fail_count: Total failed runs

Usage:
    sync = OpenProjectSync()
    
    # Sync a test class
    sync.sync_test_case(
        project_id="bms-project",
        suite_name="HIL Tests",
        test_class=MyTestClass,
    )
    
    # Update with results
    sync.update_test_result(
        work_package_id="1234",
        passed=True,
        run_url="https://bud.embedlabs.de/runs/123",
    )
"""

import requests
from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from budtestlibrary.config import BudConfig


class TestStatus(Enum):
    """Test execution status for OpenProject custom field."""
    NOT_RUN = "NotRun"
    PASS = "Pass"
    FAIL = "Fail"
    SKIPPED = "Skipped"


@dataclass
class WorkPackageInfo:
    """Information about an OpenProject Work Package."""
    id: int
    subject: str
    work_package_type: str
    project_id: str
    parent_id: Optional[int] = None
    status: Optional[str] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "subject": self.subject,
            "type": self.work_package_type,
            "project_id": self.project_id,
            "parent_id": self.parent_id,
            "status": self.status,
            "custom_fields": self.custom_fields,
            "url": self.url,
        }


class OpenProjectSync:
    """
    Synchronizes test cases with OpenProject Work Packages.
    
    Manages the creation and updating of Work Packages for test suites
    and individual test cases, including custom field updates for
    test execution results.
    """

    # Default Work Package type names (configurable via OpenProject admin)
    TYPE_TEST_SUITE = "Test Suite"
    TYPE_TEST_CASE = "Test Case"

    def __init__(self, config: Optional[BudConfig] = None):
        """
        Initialize the OpenProject sync client.
        
        Args:
            config: BudConfig instance. Uses default if not provided.
        """
        self._config = config or BudConfig()
        self._base_url = self._config.pm_url.rstrip("/")
        self._api_url = f"{self._base_url}/api/v3"
        self._session = requests.Session()
        
        if self._config.pm_token:
            self._session.headers["Authorization"] = f"Bearer {self._config.pm_token}"
        
        self._session.headers["Content-Type"] = "application/json"

    # ==================== Project Methods ====================

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get project information by ID or identifier.
        
        Args:
            project_id: Project ID or identifier string.
        
        Returns:
            Project data dict or None if not found.
        """
        try:
            response = self._session.get(
                f"{self._api_url}/projects/{project_id}",
                timeout=30,
            )
            if response.status_code == 200:
                return response.json()
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching project: {e}")
            return None

    # ==================== Work Package Methods ====================

    def find_work_package(
        self,
        project_id: str,
        subject: str,
        wp_type: Optional[str] = None,
        parent_id: Optional[int] = None,
    ) -> Optional[WorkPackageInfo]:
        """
        Find a Work Package by subject within a project.
        
        Args:
            project_id: Project ID or identifier.
            subject: Work Package subject to search for.
            wp_type: Optional Work Package type to filter.
            parent_id: Optional parent Work Package ID.
        
        Returns:
            WorkPackageInfo if found, None otherwise.
        """
        try:
            filters = [
                {"project": {"operator": "=", "values": [project_id]}},
                {"subject": {"operator": "=", "values": [subject]}},
            ]
            
            if wp_type:
                filters.append({"type": {"operator": "=", "values": [wp_type]}})
            
            if parent_id:
                filters.append({"parent": {"operator": "=", "values": [str(parent_id)]}})
            
            response = self._session.get(
                f"{self._api_url}/work_packages",
                params={"filters": str(filters)},
                timeout=30,
            )
            
            if response.status_code == 200:
                data = response.json()
                elements = data.get("_embedded", {}).get("elements", [])
                if elements:
                    wp = elements[0]
                    return self._parse_work_package(wp, project_id)
            
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error finding work package: {e}")
            return None

    def create_work_package(
        self,
        project_id: str,
        subject: str,
        wp_type: str,
        description: str = "",
        parent_id: Optional[int] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
    ) -> Optional[WorkPackageInfo]:
        """
        Create a new Work Package in OpenProject.
        
        Args:
            project_id: Project ID or identifier.
            subject: Work Package subject/title.
            wp_type: Work Package type (e.g., "Test Suite", "Test Case").
            description: Optional description.
            parent_id: Optional parent Work Package ID.
            custom_fields: Optional custom field values.
        
        Returns:
            WorkPackageInfo for the created Work Package, or None on failure.
        """
        try:
            payload = {
                "subject": subject,
                "_links": {
                    "type": {"href": f"/api/v3/types/{self._get_type_id(wp_type)}"},
                    "project": {"href": f"/api/v3/projects/{project_id}"},
                },
                "description": {
                    "format": "markdown",
                    "raw": description,
                },
            }
            
            if parent_id:
                payload["_links"]["parent"] = {"href": f"/api/v3/work_packages/{parent_id}"}
            
            if custom_fields:
                for field_name, value in custom_fields.items():
                    payload[field_name] = value
            
            response = self._session.post(
                f"{self._api_url}/projects/{project_id}/work_packages",
                json=payload,
                timeout=30,
            )
            
            if response.status_code in (200, 201):
                wp = response.json()
                return self._parse_work_package(wp, project_id)
            else:
                print(f"Error creating work package: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error creating work package: {e}")
            return None

    def update_work_package(
        self,
        work_package_id: int,
        updates: Dict[str, Any],
    ) -> bool:
        """
        Update an existing Work Package.
        
        Args:
            work_package_id: Work Package ID.
            updates: Dictionary of fields to update.
        
        Returns:
            True if update was successful.
        """
        try:
            # First get the current lock version
            response = self._session.get(
                f"{self._api_url}/work_packages/{work_package_id}",
                timeout=30,
            )
            
            if response.status_code != 200:
                return False
            
            current = response.json()
            lock_version = current.get("lockVersion", 0)
            
            # Update with lock version
            updates["lockVersion"] = lock_version
            
            response = self._session.patch(
                f"{self._api_url}/work_packages/{work_package_id}",
                json=updates,
                timeout=30,
            )
            
            return response.status_code == 200
            
        except requests.exceptions.RequestException as e:
            print(f"Error updating work package: {e}")
            return False

    # ==================== Test Sync Methods ====================

    def sync_test_case(
        self,
        project_id: str,
        suite_name: str,
        test_class: Type,
        description: str = "",
    ) -> Optional[WorkPackageInfo]:
        """
        Sync a test class to OpenProject as a Work Package.
        
        Creates or updates a Test Case Work Package under the specified
        Test Suite. Creates the Test Suite if it doesn't exist.
        
        Args:
            project_id: OpenProject project identifier.
            suite_name: Name of the test suite (parent Work Package).
            test_class: The test class to sync.
            description: Optional description for the test case.
        
        Returns:
            WorkPackageInfo for the test case Work Package.
        """
        # Find or create the test suite
        suite_wp = self.find_work_package(
            project_id=project_id,
            subject=suite_name,
            wp_type=self.TYPE_TEST_SUITE,
        )
        
        if not suite_wp:
            suite_wp = self.create_work_package(
                project_id=project_id,
                subject=suite_name,
                wp_type=self.TYPE_TEST_SUITE,
                description=f"Test suite: {suite_name}",
            )
        
        if not suite_wp:
            print(f"Failed to find/create test suite: {suite_name}")
            return None
        
        # Find or create the test case
        test_name = test_class.__name__
        test_wp = self.find_work_package(
            project_id=project_id,
            subject=test_name,
            wp_type=self.TYPE_TEST_CASE,
            parent_id=suite_wp.id,
        )
        
        if not test_wp:
            # Extract test methods for description
            test_methods = [
                m for m in dir(test_class)
                if m.startswith("mate_") and callable(getattr(test_class, m, None))
            ]
            
            full_description = description
            if test_methods:
                full_description += "\n\n## Test Methods\n"
                for method in test_methods:
                    full_description += f"- `{method}`\n"
            
            test_wp = self.create_work_package(
                project_id=project_id,
                subject=test_name,
                wp_type=self.TYPE_TEST_CASE,
                description=full_description,
                parent_id=suite_wp.id,
                custom_fields={
                    "customField1": TestStatus.NOT_RUN.value,  # test_status
                },
            )
        
        return test_wp

    def update_test_result(
        self,
        work_package_id: int,
        passed: bool,
        run_url: str,
        run_date: Optional[datetime] = None,
    ) -> bool:
        """
        Update a test case Work Package with execution results.
        
        Updates custom fields:
        - test_status: Pass or Fail
        - last_run_date: Date of execution
        - last_run_url: Link to the test run
        - pass_count / fail_count: Incremented
        
        Args:
            work_package_id: Work Package ID of the test case.
            passed: Whether the test passed.
            run_url: URL to the test run results.
            run_date: Date of the run (defaults to now).
        
        Returns:
            True if update was successful.
        """
        if run_date is None:
            run_date = datetime.now()
        
        status = TestStatus.PASS.value if passed else TestStatus.FAIL.value
        
        # Get current counts
        try:
            response = self._session.get(
                f"{self._api_url}/work_packages/{work_package_id}",
                timeout=30,
            )
            
            if response.status_code != 200:
                return False
            
            current = response.json()
            pass_count = current.get("customField4", 0) or 0  # pass_count field
            fail_count = current.get("customField5", 0) or 0  # fail_count field
            
            if passed:
                pass_count += 1
            else:
                fail_count += 1
            
            updates = {
                "customField1": status,  # test_status
                "customField2": run_date.strftime("%Y-%m-%d"),  # last_run_date
                "customField3": run_url,  # last_run_url
                "customField4": pass_count,
                "customField5": fail_count,
            }
            
            return self.update_work_package(work_package_id, updates)
            
        except requests.exceptions.RequestException as e:
            print(f"Error updating test result: {e}")
            return False

    def sync_test_suite(
        self,
        project_id: str,
        suite_name: str,
        test_classes: List[Type],
    ) -> List[WorkPackageInfo]:
        """
        Sync multiple test classes to OpenProject under a single suite.
        
        Args:
            project_id: OpenProject project identifier.
            suite_name: Name of the test suite.
            test_classes: List of test classes to sync.
        
        Returns:
            List of WorkPackageInfo for all synced test cases.
        """
        results = []
        for test_class in test_classes:
            wp = self.sync_test_case(
                project_id=project_id,
                suite_name=suite_name,
                test_class=test_class,
            )
            if wp:
                results.append(wp)
        return results

    # ==================== Helper Methods ====================

    def _get_type_id(self, type_name: str) -> str:
        """
        Get the type ID for a Work Package type name.
        
        Note: In a real implementation, this should query the API
        to get the actual type ID. For now, we use placeholder IDs.
        """
        type_mapping = {
            self.TYPE_TEST_SUITE: "1",  # Configure in OpenProject admin
            self.TYPE_TEST_CASE: "2",   # Configure in OpenProject admin
        }
        return type_mapping.get(type_name, "1")

    def _parse_work_package(self, wp: Dict[str, Any], project_id: str) -> WorkPackageInfo:
        """Parse API response into WorkPackageInfo."""
        return WorkPackageInfo(
            id=wp.get("id"),
            subject=wp.get("subject", ""),
            work_package_type=wp.get("_embedded", {}).get("type", {}).get("name", ""),
            project_id=project_id,
            parent_id=wp.get("_embedded", {}).get("parent", {}).get("id"),
            status=wp.get("_embedded", {}).get("status", {}).get("name"),
            custom_fields={
                "test_status": wp.get("customField1"),
                "last_run_date": wp.get("customField2"),
                "last_run_url": wp.get("customField3"),
                "pass_count": wp.get("customField4"),
                "fail_count": wp.get("customField5"),
            },
            url=f"{self._base_url}/work_packages/{wp.get('id')}",
        )
