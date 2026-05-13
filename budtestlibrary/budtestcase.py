"""
BudTestCase - Base class for all test cases in the bud test framework.

Provides:
- Test lifecycle management (setUpClass, setUp, tearDown, tearDownClass)
- Assertion-centric reporting and metrics
- High-visibility multi-color console output with bold white timestamps and timezones
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
from pathlib import Path

from budtestlibrary.config import BudConfig

# Color constants for console output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
GRAY = "\033[90m"
WHITE = "\033[97m"
BOLD = "\033[1m"
RESET = "\033[0m"


class ColoredFormatter(logging.Formatter):
    """Custom formatter to color the timestamp and suppress redundant metadata."""

    def __init__(self, show_level=False):
        super().__init__()
        self.show_level = show_level

    def format(self, record):
        # Get timestamp with timezone
        dt = datetime.fromtimestamp(record.created).astimezone()
        timestamp = dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        
        # Bold White timestamp
        colored_ts = f"{BOLD}{WHITE}{timestamp}{RESET}"
        
        # Always include Logger Name (Class Name)
        logger_name = record.name
        
        message = record.getMessage()
        
        if self.show_level:
            # Header format includes Level
            return f"{colored_ts} - {logger_name} - {record.levelname} - {message}"
        else:
            # Clean format for assertions: Timestamp - ClassName - Status/Message
            return f"{colored_ts} - {logger_name} - {message}"


@dataclass
class TestResult:
    """Represents the result of a single test assertion."""

    passed: bool
    message: str
    skipped: bool = False
    assertion_type: str = "Assert"
    expected: Any = None
    actual: Any = None
    result: Any = None
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    source_function: Optional[str] = None
    code_context: Optional[str] = None
    traceback: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "passed": self.passed,
            "message": self.message,
            "skipped": self.skipped,
            "assertion_type": self.assertion_type,
            "expected": str(self.expected) if self.expected is not None else None,
            "actual": str(self.actual) if self.actual is not None else None,
            "result": str(self.result) if self.result is not None else None,
            "source_file": self.source_file,
            "source_line": self.source_line,
            "source_function": self.source_function,
            "code_context": self.code_context,
            "traceback": self.traceback,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class TestMethodResult:
    """Represents the result of a test method (Step) execution."""

    method_name: str
    passed: bool
    skipped: bool = False
    assertions: List[TestResult] = field(default_factory=list)
    duration_seconds: float = 0.0
    error_message: Optional[str] = None
    summary_message: str = ""
    traceback: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "method_name": self.method_name,
            "passed": self.passed,
            "skipped": self.skipped,
            "assertions": [a.to_dict() for a in self.assertions],
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message,
            "summary_message": self.summary_message,
            "traceback": self.traceback,
            "metadata": self.metadata,
        }


class AssertionError(Exception):
    """Raised when an assertion fails with abort_on_fail=True."""

    pass


class BudTestCase(ABC):
    """
    Base class for all test cases in the bud test framework.
    """

    # Class attribute for metadata (set in subclasses)
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
        """Override in subclass for one-time setup."""
        pass

    def tearDownClass(self) -> None:
        """Override in subclass for one-time cleanup."""
        pass

    def run(self) -> bool:
        """Execute the entire test case (file)."""
        # Configure logging with Level info for the header
        self._setup_initial_logging()

        self._start_time = datetime.now()
        all_passed = True

        self.log_info(f"{BOLD}{WHITE}{'=' * 100}{RESET}")
        self.log_info(f"{BOLD}{WHITE}STARTING TEST CASE EXECUTION: {self.__class__.__name__}{RESET}")
        self.log_info(f"{BOLD}{WHITE}{'=' * 100}{RESET}")

        # Transition to clean logging for steps
        self._enable_clean_assertion_logging()

        try:
            self.log_info(f"{BOLD}{MAGENTA}Entering setUpClass: Initializing persistent resources...{RESET}")
            self.setUpClass()
            self.log_info(f"{BOLD}{MAGENTA}setUpClass successfully established global test state.{RESET}")

            test_methods = self._discover_test_methods()

            for method_name, method in test_methods:
                result = self._run_test_method(method_name, method)
                self._results.append(result)
                if not result.passed:
                    all_passed = False

        except Exception as e:
            self._logger.error(f"{RED}CRITICAL SYSTEM ERROR DURING TEST ORCHESTRATION: {e}{RESET}")
            self._logger.error(traceback.format_exc())
            all_passed = False

        finally:
            try:
                self.log_info(f"{BOLD}{MAGENTA}Entering tearDownClass: Purging all persistent resources...{RESET}")
                self.tearDownClass()
                self.log_info(f"{BOLD}{MAGENTA}tearDownClass completed.{RESET}")
            except Exception as e:
                self._logger.error(f"{RED}CLEANUP FAILURE DURING tearDownClass: {e}{RESET}")

        self._end_time = datetime.now()
        duration = (self._end_time - self._start_time).total_seconds()

        # Assertion-based metrics calculation
        total_assertions = 0
        passed_assertions = 0
        failed_assertions = 0
        skipped_assertions = 0
        
        for r in self._results:
            for a in r.assertions:
                total_assertions += 1
                if a.skipped:
                    skipped_assertions += 1
                elif a.passed:
                    passed_assertions += 1
                else:
                    failed_assertions += 1

        status_text = "PASSED" if all_passed else "FAILED"
        status_color = GREEN if all_passed else RED

        self.log_info(f"{BOLD}{WHITE}{'=' * 100}{RESET}")
        self.log_info(f"{BOLD}{WHITE}TEST CASE SUMMARY: {RESET}{BOLD}{status_color}{self.__class__.__name__} - {status_text}{RESET}")
        self.log_info(f"  Elapsed Time: {duration:.2f}s")
        self.log_info(f"  Assertion Pass-Rate:   {GREEN}{passed_assertions} Passed{RESET} | {RED}{failed_assertions} Failed{RESET} | {GRAY}{skipped_assertions} Skipped{RESET} | Total Executed: {total_assertions}")
        self.log_info(f"{BOLD}{WHITE}{'=' * 100}{RESET}")

        return all_passed

    def _discover_test_methods(self) -> List[tuple]:
        methods = []
        for name in dir(self):
            if name.startswith("bud_"):
                method = getattr(self, name)
                if callable(method):
                    methods.append((name, method))
        return sorted(methods, key=lambda x: x[0])

    def _format_assertion_line(
        self, assertion_type: str, msg: str, expected: Any, actual: Any
    ) -> str:
        # Structured for maximum scan-readability with full words and bold gray message
        return (
            f"{BOLD}[{assertion_type}]{RESET} "
            f"{BOLD}{YELLOW}EXPECTED:{RESET} {YELLOW}{expected}{RESET} | "
            f"{BOLD}{CYAN}ACTUAL:{RESET} {CYAN}{actual}{RESET} | "
            f"{BOLD}{GRAY}MESSAGE:{RESET} {BOLD}{GRAY}{msg}{RESET}"
        )

    def _run_test_method(self, method_name: str, method: Callable) -> TestMethodResult:
        self.log_info(f"\n{BLUE}STEP INVOCATION: {method_name}{RESET}")
        self.log_info(f"{BLUE}{'─' * 60}{RESET}")

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
        except Exception as e:
            passed = False
            error_msg = str(e)
            tb = traceback.format_exc()
            self._logger.error(f"{RED}UNHANDLED EXCEPTION DURING STEP EXECUTION: {e}{RESET}")
            self._logger.error(tb)

        duration = time.time() - start_time

        if passed:
            passed = all(a.passed or a.skipped for a in self._current_assertions)

        if not passed and error_msg is None:
            for a in self._current_assertions:
                if not a.passed and not a.skipped:
                    error_msg = self._format_assertion_line_for_storage(a)
                    break
        
        result = TestMethodResult(
            method_name=method_name,
            passed=passed,
            assertions=self._current_assertions.copy(),
            duration_seconds=duration,
            error_message=error_msg,
            summary_message=error_msg if not passed else f"Step Passed",
            traceback=tb,
        )

        if self.bloom_metadata and hasattr(self.bloom_metadata, "get_full_tc_id"):
            result.metadata["tc_id"] = self.bloom_metadata.get_full_tc_id()

        return result

    def _format_assertion_line_for_storage(self, a: TestResult) -> str:
        """Returns a non-ANSI formatted string for database/internal storage."""
        return f"[{a.assertion_type}] EXPECTED: {a.expected} | ACTUAL: {a.actual} | MESSAGE: {a.message}"

    # ==================== Assertion Methods ====================

    def skipAssert(self, msg: str, **kwargs) -> None:
        """Explicitly skip an assertion."""
        callsite = self._get_assertion_callsite()
        result = TestResult(
            passed=True,
            skipped=True,
            message=msg,
            assertion_type="Skip",
            source_file=callsite.get("source_file"),
            source_line=callsite.get("source_line"),
            source_function=callsite.get("source_function"),
            metadata=kwargs,
        )
        self._current_assertions.append(result)
        self.log_info(f"{GRAY}⚠ SKIPPED{RESET}: {BOLD}{GRAY}{msg}{RESET}")

    def assertTrue(
        self,
        condition: bool,
        msg: str = "",
        expected: Any = None,
        actual: Any = None,
        abort_on_fail: bool = False,
        assertion_type: str = "AssertTrue",
        **kwargs,
    ) -> bool:
        callsite = self._get_assertion_callsite()
        result = TestResult(
            passed=bool(condition),
            message=msg,
            assertion_type=assertion_type,
            expected=expected if expected is not None else True,
            actual=actual if actual is not None else condition,
            result=actual if actual is not None else condition,
            source_file=callsite.get("source_file"),
            source_line=callsite.get("source_line"),
            source_function=callsite.get("source_function"),
            code_context=callsite.get("code_context"),
            traceback=callsite.get("traceback"),
            metadata=kwargs,
        )
        self._current_assertions.append(result)

        status_prefix = f"{GREEN}{BOLD}✓ PASSED{RESET}" if condition else f"{RED}{BOLD}✗ FAILED{RESET}"
        
        # High-visibility multi-color formatting
        line = f"{status_prefix}: {self._format_assertion_line(assertion_type, msg, result.expected, result.actual)}"
        
        self._logger.info(line)

        if not condition and abort_on_fail:
            # Raise exception without ANSI codes for clean traceback
            raise AssertionError(f"[{assertion_type}] EXPECTED: {result.expected} | ACTUAL: {result.actual} | MESSAGE: {msg}")

        return condition

    def _get_assertion_callsite(self) -> Dict[str, Any]:
        library_file = Path(__file__).resolve()
        stack = inspect.stack(context=3)
        selected = stack[2] if len(stack) > 2 else stack[-1]
        for frame in stack[1:]:
            try:
                frame_file = Path(frame.filename).resolve()
            except OSError:
                frame_file = Path(frame.filename)
            if frame_file != library_file:
                selected = frame
                break
        return {
            "source_file": selected.filename,
            "source_line": selected.lineno,
            "source_function": selected.function,
        }

    def assertEqual(self, actual: Any, expected: Any, msg: str = "", abort_on_fail: bool = False, **kwargs) -> bool:
        return self.assertTrue(actual == expected, msg=msg, expected=expected, actual=actual, abort_on_fail=abort_on_fail, assertion_type="AssertEqual", **kwargs)

    def assertIn(self, actual: Any = None, expected: Any = None, member: Any = None, container: Any = None, msg: str = "", abort_on_fail: bool = False, **kwargs) -> bool:
        _m = member if member is not None else actual
        _c = container if container is not None else expected
        return self.assertTrue(_m in _c, msg=msg, expected=f"'{_m}' in container", actual=_c, abort_on_fail=abort_on_fail, assertion_type="AssertIn", **kwargs)

    def assertNotIn(self, actual: Any = None, expected: Any = None, member: Any = None, container: Any = None, msg: str = "", abort_on_fail: bool = False, **kwargs) -> bool:
        _m = member if member is not None else actual
        _c = container if container is not None else expected
        return self.assertTrue(_m not in _c, msg=msg, expected=f"'{_m}' NOT in container", actual=_c, abort_on_fail=abort_on_fail, assertion_type="AssertNotIn", **kwargs)

    def assertInTolerance(self, actual: float, expected: float, absolute_tolerance: Optional[float] = None, relative_tolerance: Optional[float] = None, msg: str = "", abort_on_fail: bool = False, **kwargs) -> bool:
        tol = absolute_tolerance or abs(expected * (relative_tolerance or 0))
        cond = (expected - tol) <= actual <= (expected + tol)
        return self.assertTrue(cond, msg=msg, expected=f"{expected}±{tol}", actual=actual, abort_on_fail=abort_on_fail, assertion_type="AssertInTolerance", **kwargs)

    def assertInRange(self, actual: float, lower_bound: float, upper_bound: float, include_bounds: bool = True, msg: str = "", abort_on_fail: bool = False, **kwargs) -> bool:
        cond = (lower_bound <= actual <= upper_bound) if include_bounds else (lower_bound < actual < upper_bound)
        return self.assertTrue(cond, msg=msg, expected=f"[{lower_bound}, {upper_bound}]", actual=actual, abort_on_fail=abort_on_fail, assertion_type="AssertInRange", **kwargs)

    def log_info(self, message: str) -> None:
        self._logger.info(message)

    def _setup_initial_logging(self) -> None:
        """Configures the logger to show LEVEL and NAME for the Test Case header."""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        handler = logging.StreamHandler()
        # Header format: Timestamp - Name - Level - Msg
        formatter = ColoredFormatter(show_level=True)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        root_logger.setLevel(self._log_level)

    def _enable_clean_assertion_logging(self) -> None:
        """Switches to clean formatting (suppressing Level/Name) for assertion lines."""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler):
                # Assertion format: Timestamp - Msg (Status: Type EXP | ACT | MSG)
                handler.setFormatter(ColoredFormatter(show_level=False))

    def set_loglevel(self, level: int) -> None:
        self._log_level = level
        self._logger.setLevel(level)

    def print_variables(self, variables: Dict[str, Any]) -> None:
        for name, value in variables.items():
            self._logger.info(f"  {name}: {value}")

    def get_results(self) -> List[TestMethodResult]:
        return self._results
