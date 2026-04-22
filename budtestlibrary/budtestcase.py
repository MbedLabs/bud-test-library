"""
BudTestCase - Base class for all test cases in the bud test framework.

Provides:
- Test lifecycle management (setUpClass, tearDownClass, run)
- Assertion methods with rich reporting (assertTrue, assertEqual, assertInTolerance, assertInRange)
- Logging utilities (log_info, set_loglevel, print_variables)
- File upload to bud.embedlabs.de backend
- Automatic test method discovery (bud_* pattern for compatibility)
"""

import logging
import time
import inspect
import traceback
import requests
from abc import ABC
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from budtestlibrary.config import BudConfig


@dataclass
class TestResult:
    """Represents the result of a single test assertion or test method."""
    passed: bool
    message: str
    expected: Any = None
    actual: Any = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "passed": self.passed,
            "message": self.message,
            "expected": str(self.expected) if self.expected is not None else None,
            "actual": str(self.actual) if self.actual is not None else None,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class TestMethodResult:
    """Represents the result of a complete test method execution."""
    method_name: str
    passed: bool
    assertions: List[TestResult] = field(default_factory=list)
    duration_seconds: float = 0.0
    error_message: Optional[str] = None
    traceback: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "method_name": self.method_name,
            "passed": self.passed,
            "assertions": [a.to_dict() for a in self.assertions],
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message,
            "traceback": self.traceback,
        }


class AssertionError(Exception):
    """Raised when an assertion fails with abort_on_fail=True."""
    pass


class BudTestCase(ABC):
    """
    Base class for all test cases in the bud test framework.
    
    Usage:
        class MyTest(BudTestCase):
            def setUpClass(self):
                # Initialize test resources
                pass
            
            def bud_my_test_method(self):
                # Test implementation
                self.assertTrue(condition, msg="Check condition")
            
            def tearDownClass(self):
                # Cleanup resources
                pass
        
        if __name__ == "__main__":
            test = MyTest()
            test.set_loglevel(logging.INFO)
            test.run()
    """

    # Class attribute for requirement metadata (set in subclasses)
    bloom_metadata = None

    def __init__(self):
        """Initialize the test case."""
        self._config = BudConfig()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._log_level = logging.INFO
        self._results: List[TestMethodResult] = []
        self._current_assertions: List[TestResult] = []
        self._uploaded_files: List[str] = []
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None

    # ==================== Lifecycle Methods ====================

    def setUpClass(self) -> None:
        """
        Called once before all test methods.
        Override in subclass to initialize test resources.
        """
        pass

    def tearDownClass(self) -> None:
        """
        Called once after all test methods.
        Override in subclass to cleanup resources.
        """
        pass

    def run(self) -> bool:
        """
        Execute the test case.
        
        Discovers all test methods (bud_* pattern), runs them in order,
        and collects results.
        
        Returns:
            bool: True if all tests passed, False otherwise.
        """
        self._start_time = datetime.now()
        all_passed = True

        self.log_info(f"{'=' * 60}")
        self.log_info(f"Starting test case: {self.__class__.__name__}")
        self.log_info(f"{'=' * 60}")

        try:
            # Setup
            self.log_info("Running setUpClass...")
            self.setUpClass()

            # Discover and run test methods
            test_methods = self._discover_test_methods()
            self.log_info(f"Discovered {len(test_methods)} test method(s)")

            for method_name, method in test_methods:
                result = self._run_test_method(method_name, method)
                self._results.append(result)
                if not result.passed:
                    all_passed = False

        except Exception as e:
            self._logger.error(f"Error during test execution: {e}")
            self._logger.error(traceback.format_exc())
            all_passed = False

        finally:
            # Teardown
            try:
                self.log_info("Running tearDownClass...")
                self.tearDownClass()
            except Exception as e:
                self._logger.error(f"Error during tearDownClass: {e}")
                self._logger.error(traceback.format_exc())

        self._end_time = datetime.now()
        duration = (self._end_time - self._start_time).total_seconds()

        # Summary
        passed_count = sum(1 for r in self._results if r.passed)
        failed_count = len(self._results) - passed_count

        self.log_info(f"{'=' * 60}")
        self.log_info(f"Test case completed: {self.__class__.__name__}")
        self.log_info(f"Duration: {duration:.2f}s")
        self.log_info(f"Results: {passed_count} passed, {failed_count} failed")
        self.log_info(f"{'=' * 60}")

        return all_passed

    def _discover_test_methods(self) -> List[tuple]:
        """
        Discover all test methods in the class.
        
        Test methods must start with 'bud_' prefix (for compatibility with
        existing test suites).
        
        Returns:
            List of (method_name, method) tuples.
        """
        methods = []
        for name in dir(self):
            if name.startswith("bud_"):
                method = getattr(self, name)
                if callable(method):
                    methods.append((name, method))
        return sorted(methods, key=lambda x: x[0])

    def _run_test_method(self, method_name: str, method: Callable) -> TestMethodResult:
        """
        Run a single test method and collect results.
        
        Args:
            method_name: Name of the test method.
            method: The method to execute.
        
        Returns:
            TestMethodResult with execution details.
        """
        self.log_info(f"\n{'─' * 40}")
        self.log_info(f"Running: {method_name}")
        self.log_info(f"{'─' * 40}")

        self._current_assertions = []
        start_time = time.time()
        error_msg = None
        tb = None
        passed = True

        try:
            method()
        except AssertionError as e:
            passed = False
            error_msg = str(e)
            tb = traceback.format_exc()
            self._logger.error(f"Assertion failed: {e}")
        except Exception as e:
            passed = False
            error_msg = str(e)
            tb = traceback.format_exc()
            self._logger.error(f"Test method error: {e}")
            self._logger.error(tb)

        duration = time.time() - start_time

        # Check if any assertions failed
        if passed:
            passed = all(a.passed for a in self._current_assertions)

        result = TestMethodResult(
            method_name=method_name,
            passed=passed,
            assertions=self._current_assertions.copy(),
            duration_seconds=duration,
            error_message=error_msg,
            traceback=tb,
        )

        status = "✓ PASSED" if passed else "✗ FAILED"
        self.log_info(f"{status} ({duration:.2f}s)")

        return result

    # ==================== Assertion Methods ====================

    def assertTrue(
        self,
        condition: bool,
        msg: str = "",
        expected: Any = None,
        actual: Any = None,
        abort_on_fail: bool = False,
        **kwargs
    ) -> bool:
        """
        Assert that a condition is True.
        
        Args:
            condition: The condition to check.
            msg: Message describing the assertion.
            expected: Expected value (for reporting).
            actual: Actual value (for reporting).
            abort_on_fail: If True, raise AssertionError on failure.
            **kwargs: Additional metadata for reporting (e.g., cell=, tolerance=).
        
        Returns:
            bool: The condition value.
        """
        result = TestResult(
            passed=bool(condition),
            message=msg,
            expected=expected if expected is not None else True,
            actual=actual if actual is not None else condition,
            metadata=kwargs,
        )
        self._current_assertions.append(result)

        if condition:
            self._logger.debug(f"✓ {msg}")
        else:
            self._logger.warning(f"✗ ASSERTION FAILED: {msg}")
            if expected is not None or actual is not None:
                self._logger.warning(f"  Expected: {expected}, Actual: {actual}")
            if abort_on_fail:
                raise AssertionError(msg)

        return condition

    def assertEqual(
        self,
        actual: Any,
        expected: Any,
        msg: str = "",
        abort_on_fail: bool = False,
        **kwargs
    ) -> bool:
        """
        Assert that two values are equal.
        
        Args:
            actual: The actual value.
            expected: The expected value.
            msg: Message describing the assertion.
            abort_on_fail: If True, raise AssertionError on failure.
            **kwargs: Additional metadata for reporting.
        
        Returns:
            bool: True if values are equal.
        """
        condition = actual == expected
        full_msg = f"{msg} (expected={expected}, actual={actual})" if msg else f"Expected {expected}, got {actual}"
        
        return self.assertTrue(
            condition,
            msg=full_msg,
            expected=expected,
            actual=actual,
            abort_on_fail=abort_on_fail,
            **kwargs
        )

    def assertInTolerance(
        self,
        actual: float,
        expected: float,
        absolute_tolerance: Optional[float] = None,
        relative_tolerance: Optional[float] = None,
        msg: str = "",
        abort_on_fail: bool = False,
        **kwargs
    ) -> bool:
        """
        Assert that a value is within tolerance of an expected value.
        
        Args:
            actual: The actual value.
            expected: The expected value.
            absolute_tolerance: Absolute tolerance (±value).
            relative_tolerance: Relative tolerance (0.05 = 5%).
            msg: Message describing the assertion.
            abort_on_fail: If True, raise AssertionError on failure.
            **kwargs: Additional metadata for reporting (e.g., cell=, current_tolerance=).
        
        Returns:
            bool: True if value is within tolerance.
        """
        if absolute_tolerance is None and relative_tolerance is None:
            raise ValueError("Must specify either absolute_tolerance or relative_tolerance")

        tolerance_value = 0.0
        if absolute_tolerance is not None:
            tolerance_value = absolute_tolerance
        if relative_tolerance is not None:
            tolerance_value = max(tolerance_value, abs(expected * relative_tolerance))

        lower_bound = expected - tolerance_value
        upper_bound = expected + tolerance_value
        condition = lower_bound <= actual <= upper_bound

        tolerance_str = ""
        if absolute_tolerance is not None:
            tolerance_str += f"±{absolute_tolerance}"
        if relative_tolerance is not None:
            tolerance_str += f" ({relative_tolerance * 100:.1f}%)"

        full_msg = f"{msg} " if msg else ""
        full_msg += f"(expected={expected}{tolerance_str}, actual={actual})"

        kwargs["tolerance"] = tolerance_str
        kwargs["lower_bound"] = lower_bound
        kwargs["upper_bound"] = upper_bound

        return self.assertTrue(
            condition,
            msg=full_msg,
            expected=f"{expected}{tolerance_str}",
            actual=actual,
            abort_on_fail=abort_on_fail,
            **kwargs
        )

    def assertInRange(
        self,
        actual: float,
        lower_bound: float,
        upper_bound: float,
        include_bounds: bool = True,
        msg: str = "",
        measurement_time: Optional[float] = None,
        measurement_count: Optional[int] = None,
        abort_on_fail: bool = False,
        **kwargs
    ) -> bool:
        """
        Assert that a value is within a specified range.
        
        Args:
            actual: The actual value.
            lower_bound: Lower bound of the range.
            upper_bound: Upper bound of the range.
            include_bounds: If True, bounds are inclusive.
            msg: Message describing the assertion.
            measurement_time: Optional measurement time for reporting.
            measurement_count: Optional measurement count for reporting.
            abort_on_fail: If True, raise AssertionError on failure.
            **kwargs: Additional metadata for reporting.
        
        Returns:
            bool: True if value is within range.
        """
        if include_bounds:
            condition = lower_bound <= actual <= upper_bound
            range_str = f"[{lower_bound}, {upper_bound}]"
        else:
            condition = lower_bound < actual < upper_bound
            range_str = f"({lower_bound}, {upper_bound})"

        full_msg = f"{msg} " if msg else ""
        full_msg += f"(expected in {range_str}, actual={actual})"

        kwargs["lower_bound"] = lower_bound
        kwargs["upper_bound"] = upper_bound
        kwargs["include_bounds"] = include_bounds
        if measurement_time is not None:
            kwargs["measurement_time"] = measurement_time
        if measurement_count is not None:
            kwargs["measurement_count"] = measurement_count

        return self.assertTrue(
            condition,
            msg=full_msg,
            expected=range_str,
            actual=actual,
            abort_on_fail=abort_on_fail,
            **kwargs
        )

    # ==================== Logging Methods ====================

    def log_info(self, message: str) -> None:
        """
        Log an info message.
        
        Args:
            message: The message to log.
        """
        self._logger.info(message)

    def set_loglevel(self, level: int) -> None:
        """
        Set the logging level.
        
        Args:
            level: Logging level (e.g., logging.INFO, logging.DEBUG).
        """
        self._log_level = level
        self._logger.setLevel(level)
        
        # Also configure the root logger if not already configured
        if not logging.getLogger().handlers:
            logging.basicConfig(
                level=level,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

    def print_variables(self, variables: Dict[str, Any]) -> None:
        """
        Print/log variables for debugging and reporting.
        
        Args:
            variables: Dictionary of variable names to values.
        """
        for name, value in variables.items():
            self._logger.info(f"  {name}: {value}")

    # ==================== File Upload Methods ====================

    def upload(self, file_path: str) -> bool:
        """
        Upload a file to the bud.embedlabs.de backend.
        
        Args:
            file_path: Path to the file to upload.
        
        Returns:
            bool: True if upload was successful.
        """
        upload_url = f"{self._config.backend_url}api/uploads"
        
        try:
            headers = {}
            if self._config.bud_token:
                headers["Authorization"] = f"Bearer {self._config.bud_token}"

            with open(file_path, "rb") as f:
                files = {"file": f}
                data = {
                    "test_case": self.__class__.__name__,
                    "timestamp": datetime.now().isoformat(),
                }
                
                response = requests.post(
                    upload_url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=60,
                )

            if response.status_code == 200:
                self._uploaded_files.append(file_path)
                self.log_info(f"✓ Uploaded: {file_path}")
                return True
            else:
                self._logger.warning(
                    f"Upload failed ({response.status_code}): {file_path}"
                )
                return False

        except requests.exceptions.RequestException as e:
            self._logger.error(f"Upload error: {e}")
            return False
        except FileNotFoundError:
            self._logger.error(f"File not found: {file_path}")
            return False

    # ==================== Result Access Methods ====================

    def get_results(self) -> List[TestMethodResult]:
        """Get all test method results."""
        return self._results

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the test execution.
        
        Returns:
            Dictionary with test summary information.
        """
        passed_count = sum(1 for r in self._results if r.passed)
        failed_count = len(self._results) - passed_count
        total_assertions = sum(len(r.assertions) for r in self._results)
        passed_assertions = sum(
            sum(1 for a in r.assertions if a.passed) for r in self._results
        )

        return {
            "test_case": self.__class__.__name__,
            "bloom_metadata": (
                self.bloom_metadata.to_dict()
                if self.bloom_metadata
                else None
            ),
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "end_time": self._end_time.isoformat() if self._end_time else None,
            "duration_seconds": (
                (self._end_time - self._start_time).total_seconds()
                if self._start_time and self._end_time
                else None
            ),
            "total_methods": len(self._results),
            "passed_methods": passed_count,
            "failed_methods": failed_count,
            "total_assertions": total_assertions,
            "passed_assertions": passed_assertions,
            "failed_assertions": total_assertions - passed_assertions,
            "uploaded_files": self._uploaded_files,
            "results": [r.to_dict() for r in self._results],
        }

    def to_junit_xml(self) -> str:
        """
        Generate JUnit XML format for CI/CD integration.
        
        Returns:
            JUnit XML string.
        """
        from xml.etree.ElementTree import Element, SubElement, tostring
        from xml.dom import minidom

        testsuite = Element("testsuite")
        testsuite.set("name", self.__class__.__name__)
        testsuite.set("tests", str(len(self._results)))
        testsuite.set("failures", str(sum(1 for r in self._results if not r.passed)))
        testsuite.set("errors", "0")
        
        if self._start_time and self._end_time:
            testsuite.set(
                "time", str((self._end_time - self._start_time).total_seconds())
            )
            testsuite.set("timestamp", self._start_time.isoformat())

        for result in self._results:
            testcase = SubElement(testsuite, "testcase")
            testcase.set("name", result.method_name)
            testcase.set("classname", self.__class__.__name__)
            testcase.set("time", str(result.duration_seconds))

            if not result.passed:
                failure = SubElement(testcase, "failure")
                failure.set("message", result.error_message or "Assertion failed")
                if result.traceback:
                    failure.text = result.traceback

        xml_str = tostring(testsuite, encoding="unicode")
        return minidom.parseString(xml_str).toprettyxml(indent="  ")
