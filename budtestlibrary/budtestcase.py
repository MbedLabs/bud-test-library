"""
BudTestCase - Base class for all test cases in the bud test framework.

Provides:
- Test lifecycle management (setUpClass, setUp, tearDown, tearDownClass)
- Assertion-centric reporting and metrics
- High-visibility multi-color console output with bold white timestamps and timezones
"""

import asyncio
import codecs
import functools
import inspect
import logging
import os
import re
import sys
import time
import traceback
from abc import ABC
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from types import FrameType
from typing import Any, Callable, Optional, Union

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

# Maximum length for serialized assertion values (shared with BudTestCase)
_DEFAULT_MAX_RESULT_VALUE_LENGTH = 5000


def _truncate_str(value: str, max_length: int = _DEFAULT_MAX_RESULT_VALUE_LENGTH) -> str:
    """Truncate a string to max_length, appending a marker if truncated."""
    if len(value) > max_length:
        return value[:max_length] + "... <truncated>"
    return value


class ColoredFormatter(logging.Formatter):
    """Custom formatter to color the timestamp and suppress redundant metadata."""

    def __init__(self, show_level=False):
        super().__init__()
        self.show_level = show_level

    def format(self, record):
        # Get timestamp with timezone
        dt = datetime.fromtimestamp(record.created).astimezone()
        timestamp = dt.strftime("%Y-%m-%d %H:%M:%S %z")

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


class Utf8StreamHandler(logging.StreamHandler):
    """Write each record as UTF-8 to the stream's binary buffer when the stream's
    encoding is not UTF-8; write to the stream itself otherwise."""

    def emit(self, record):
        stream = self.stream
        buffer = getattr(stream, "buffer", None)
        if buffer is None or _is_utf8(getattr(stream, "encoding", None)):
            super().emit(record)
            return
        try:
            msg = self.format(record) + self.terminator
            stream.flush()
            buffer.write(msg.encode("utf-8"))
            buffer.flush()
        except RecursionError:
            raise
        except Exception:
            self.handleError(record)


def _is_utf8(encoding: Optional[str]) -> bool:
    """Return whether the encoding name resolves to the UTF-8 codec."""
    if not encoding:
        return False
    try:
        return codecs.lookup(encoding).name == "utf-8"
    except LookupError:
        return False


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
    metadata: dict[str, Any] = field(default_factory=dict)
    max_result_value_length: int = _DEFAULT_MAX_RESULT_VALUE_LENGTH

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "passed": self.passed,
            "message": self.message,
            "skipped": self.skipped,
            "assertion_type": self.assertion_type,
            "expected": (
                _truncate_str(str(self.expected), self.max_result_value_length)
                if self.expected is not None
                else None
            ),
            "actual": (
                _truncate_str(str(self.actual), self.max_result_value_length)
                if self.actual is not None
                else None
            ),
            "result": (
                _truncate_str(str(self.result), self.max_result_value_length)
                if self.result is not None
                else None
            ),
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
    assertions: list[TestResult] = field(default_factory=list)
    duration_seconds: float = 0.0
    error_message: Optional[str] = None
    summary_message: str = ""
    traceback: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
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


class _AssertRaisesContext:
    """Context manager that records whether its block raised the expected exception."""

    def __init__(
        self,
        test_case: "BudTestCase",
        expected_exception: type,
        msg: str,
        abort_on_fail: bool,
    ) -> None:
        self._test_case = test_case
        self._expected_exception = expected_exception
        self._msg = msg
        self._abort_on_fail = abort_on_fail

    def __enter__(self) -> "_AssertRaisesContext":
        return self

    def __exit__(self, exc_type: Optional[type], exc_value: Any, exc_tb: Any) -> bool:
        if exc_type is None:
            raised = False
            actual = "no exception raised"
        else:
            raised = issubclass(exc_type, self._expected_exception)
            if not raised and not issubclass(exc_type, Exception):
                return False
            actual = f"{exc_type.__name__}: {exc_value}"
        self._test_case.assertTrue(
            raised,
            msg=self._msg,
            expected=self._expected_exception.__name__,
            actual=actual,
            abort_on_fail=self._abort_on_fail,
            assertion_type="AssertRaises",
        )
        return exc_type is not None


_PARAMETERS_ATTRIBUTE = "_bud_parameters"

MAX_STEP_NAME_LENGTH = 255


def parameterized(data: Iterable[Any]) -> Callable[[Callable], Callable]:
    """Mark a bud_* method to run once per item of data, each run its own step.

    A single value is passed as one argument, a tuple is unpacked as positional
    arguments and a dict as keyword arguments. Each step is named
    ``<method>[<id>]``: the value itself, the tuple's values joined by ", ", or
    the dict's key=value pairs joined by ", ".
    """
    items = list(data)

    def decorator(func: Callable) -> Callable:
        setattr(func, _PARAMETERS_ATTRIBUTE, items)
        return func

    return decorator


def _parameter_id(item: Any) -> str:
    """Return the bracketed step name part for one parameter item."""
    if isinstance(item, tuple):
        return ", ".join(str(value) for value in item)
    if isinstance(item, dict):
        return ", ".join(f"{key}={value}" for key, value in item.items())
    return str(item)


_LIBRARY_FILE = Path(__file__).resolve()


@functools.cache
def _is_library_file(filename: str) -> bool:
    """Return True when filename is this module's own source file."""
    try:
        return Path(filename).resolve() == _LIBRARY_FILE
    except OSError:
        return Path(filename) == _LIBRARY_FILE


def _is_coroutine_step(method: Callable) -> bool:
    """Return True when a step, or the method a parameterized step wraps, is async."""
    if isinstance(method, functools.partial):
        method = method.func
    return inspect.iscoroutinefunction(method)


def _bind_parameters(method: Callable, item: Any) -> Callable:
    """Return method with one parameter item bound as its arguments."""
    if isinstance(item, tuple):
        return functools.partial(method, *item)
    if isinstance(item, dict):
        return functools.partial(method, **item)
    return functools.partial(method, item)


def _validate_step_name(method_name: str, step_name: str) -> None:
    """Validate a discovered step's maximum name length."""
    if len(step_name) > MAX_STEP_NAME_LENGTH:
        raise ValueError(
            f"{method_name}: step name is {len(step_name)} characters, "
            f"over the {MAX_STEP_NAME_LENGTH}-character limit"
        )


def _expand_test_method(name: str, method: Callable) -> list[tuple]:
    """Return a method's named steps with their parameter items bound."""
    parameters = getattr(method, _PARAMETERS_ATTRIBUTE, None)
    if parameters is None:
        _validate_step_name(name, name)
        return [(name, method)]
    methods = []
    step_names: set[str] = set()
    for item in parameters:
        step_name = f"{name}[{_parameter_id(item)}]"
        if step_name in step_names:
            raise ValueError(f"{name}: step name {step_name} repeats")
        _validate_step_name(name, step_name)
        step_names.add(step_name)
        methods.append((step_name, _bind_parameters(method, item)))
    return methods


class BudTestCase(ABC):  # noqa: B024
    """
    Base class for all test cases in the bud test framework.
    """

    # Class attribute for metadata (set in subclasses)
    bloom_metadata = None

    # Maximum length for assertion values stored in results (to avoid bloated reports)
    MAX_RESULT_VALUE_LENGTH: int = 5000

    # Whether to capture source file/line/function in assertion results
    CAPTURE_SOURCE_PATH: bool = True

    # Whether to capture tracebacks in assertion results
    CAPTURE_TRACEBACK: bool = True

    def __init__(self):
        """Initialize the test case."""
        self._config = BudConfig()
        self._logger = logging.getLogger(f"budtestlibrary.{self.__class__.__name__}")
        self._log_level = logging.INFO
        self._results: list[TestMethodResult] = []
        self._current_assertions: list[TestResult] = []
        self._uploaded_files: list[str] = []
        self._current_artifacts: list[dict[str, str]] = []
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None
        self._console_handler: Optional[logging.Handler] = None

    # ==================== Lifecycle Methods ====================

    def setUpClass(self) -> None:  # noqa: B027
        """Override in subclass for one-time setup."""
        pass

    def tearDownClass(self) -> None:  # noqa: B027
        """Override in subclass for one-time cleanup."""
        pass

    def setUp(self) -> None:  # noqa: B027
        """Override in subclass for setup run before each bud_* step."""
        pass

    def tearDown(self) -> None:  # noqa: B027
        """Override in subclass for cleanup run after each bud_* step."""
        pass

    def run(self) -> bool:
        """Execute the entire test case (file)."""
        # Configure logging with Level info for the header
        self._setup_initial_logging()

        self._start_time = datetime.now()
        all_passed = True

        self.log_info(f"{BOLD}{WHITE}{'=' * 100}{RESET}")
        self.log_info(
            f"{BOLD}{WHITE}STARTING TEST CASE EXECUTION: {self.__class__.__name__}{RESET}"
        )
        self.log_info(f"{BOLD}{WHITE}{'=' * 100}{RESET}")

        # Transition to clean logging for steps
        self._enable_clean_assertion_logging()

        try:
            self.log_info(
                f"{BOLD}{MAGENTA}Entering setUpClass: Initializing persistent resources...{RESET}"
            )
            self.setUpClass()
            self.log_info(
                f"{BOLD}{MAGENTA}setUpClass successfully established global test state.{RESET}"
            )

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
                self.log_info(
                    f"{BOLD}{MAGENTA}Entering tearDownClass: Purging all persistent resources...{RESET}"
                )
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
        self.log_info(
            f"{BOLD}{WHITE}TEST CASE SUMMARY: {RESET}{BOLD}{status_color}{self.__class__.__name__} - {status_text}{RESET}"
        )
        self.log_info(f"  Elapsed Time: {duration:.2f}s")
        self.log_info(
            f"  Assertion Pass-Rate:   {GREEN}{passed_assertions} Passed{RESET} | {RED}{failed_assertions} Failed{RESET} | {GRAY}{skipped_assertions} Skipped{RESET} | Total Executed: {total_assertions}"
        )
        self.log_info(f"{BOLD}{WHITE}{'=' * 100}{RESET}")

        return all_passed

    def _discover_test_methods(self) -> list[tuple]:
        """Return (name, bound method) for each bud_* method in declaration order.

        The class's own methods come first, then those inherited from each base
        class in method resolution order; an override keeps the subclass position.
        Raises ValueError when a parameterized step name repeats or any step is longer than
        MAX_STEP_NAME_LENGTH.
        """
        methods = []
        seen: set[str] = set()
        for cls in type(self).__mro__:
            for name in vars(cls):
                if not name.startswith("bud_") or name in seen:
                    continue
                seen.add(name)
                method = getattr(self, name)
                if not callable(method):
                    continue
                methods.extend(_expand_test_method(name, method))
        return methods

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
        self._current_artifacts = []
        start_time = time.time()
        try:
            passed, error_msg, tb = self._execute_step(method_name, method)
        finally:
            self._tear_down_step(method_name)

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
            summary_message=error_msg if not passed else "Step Passed",
            traceback=tb,
        )

        if self.bloom_metadata and hasattr(self.bloom_metadata, "get_full_tc_id"):
            result.metadata["tc_id"] = self.bloom_metadata.get_full_tc_id()

        if self._current_artifacts:
            result.metadata["artifacts"] = list(self._current_artifacts)

        return result

    def _execute_step(self, method_name: str, method: Callable) -> tuple:
        """Execute setup and the step, returning its pass state, error and traceback."""
        try:
            self._logger.debug(f"{MAGENTA}Entering setUp for {method_name}{RESET}")
            self._call_hook(self.setUp)
            self._logger.debug(f"{MAGENTA}setUp completed for {method_name}{RESET}")
        except Exception as e:
            full_tb = traceback.format_exc()
            self._logger.error(f"{RED}SETUP FAILURE BEFORE STEP {method_name}: {e}{RESET}")
            self._logger.error(full_tb)
            return False, f"setUp failed: {e}", full_tb if self.CAPTURE_TRACEBACK else None

        try:
            if _is_coroutine_step(method):
                coroutine = method()
                try:
                    asyncio.run(coroutine)
                finally:
                    coroutine.close()
            else:
                method()
        except AssertionError as e:
            return False, str(e), traceback.format_exc() if self.CAPTURE_TRACEBACK else None
        except Exception as e:
            full_tb = traceback.format_exc()
            self._logger.error(f"{RED}UNHANDLED EXCEPTION DURING STEP EXECUTION: {e}{RESET}")
            self._logger.error(full_tb)
            return False, str(e), full_tb if self.CAPTURE_TRACEBACK else None
        return True, None, None

    def _tear_down_step(self, method_name: str) -> None:
        """Run teardown and log cleanup failures."""
        try:
            self._logger.debug(f"{MAGENTA}Entering tearDown for {method_name}{RESET}")
            self._call_hook(self.tearDown)
            self._logger.debug(f"{MAGENTA}tearDown completed for {method_name}{RESET}")
        except Exception as e:
            self._logger.error(f"{RED}CLEANUP FAILURE DURING tearDown: {e}{RESET}")

    def _call_hook(self, hook: Callable[[], None]) -> None:
        """Call a per-step hook with assertion entries kept out of the step."""
        step_assertions = self._current_assertions
        self._current_assertions = []
        try:
            hook()
        finally:
            self._current_assertions = step_assertions

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
            max_result_value_length=self.MAX_RESULT_VALUE_LENGTH,
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
        callsite = self._get_assertion_callsite(failed=not condition)
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
            max_result_value_length=self.MAX_RESULT_VALUE_LENGTH,
        )
        self._current_assertions.append(result)

        status_prefix = (
            f"{GREEN}{BOLD}✓ PASSED{RESET}" if condition else f"{RED}{BOLD}✗ FAILED{RESET}"
        )

        # High-visibility multi-color formatting
        line = f"{status_prefix}: {self._format_assertion_line(assertion_type, msg, result.expected, result.actual)}"

        self._logger.info(line)

        if not condition and abort_on_fail:
            # Raise exception without ANSI codes for clean traceback
            raise AssertionError(
                f"[{assertion_type}] EXPECTED: {result.expected} | ACTUAL: {result.actual} | MESSAGE: {msg}"
            )

        return condition

    def assertRaises(
        self, expected_exception: type, msg: str = "", abort_on_fail: bool = False
    ) -> _AssertRaisesContext:
        """Return a context manager recording an AssertRaises entry for its block.

        The entry passes when the block raises expected_exception. When the block
        raises nothing or another exception, the entry fails and the exception is
        suppressed; with abort_on_fail=True the failure raises AssertionError.
        """
        return _AssertRaisesContext(self, expected_exception, msg, abort_on_fail)

    def _get_assertion_callsite(self, failed: bool = False) -> dict[str, Any]:
        """Return source file, line and function of the first caller outside the library.

        Code context and, with CAPTURE_TRACEBACK, the traceback are added only for a
        failed assertion.
        """
        callsite: dict[str, Any] = {}
        if self.CAPTURE_SOURCE_PATH:
            frame: Optional[FrameType] = sys._getframe(1)
            selected = None
            while frame is not None:
                if not _is_library_file(frame.f_code.co_filename):
                    selected = frame
                    break
                frame = frame.f_back
            if selected is None:
                selected = sys._getframe(2)
            callsite = {
                "source_file": selected.f_code.co_filename,
                "source_line": selected.f_lineno,
                "source_function": selected.f_code.co_name,
            }
            if failed:
                context = inspect.getframeinfo(selected, context=3).code_context
                callsite["code_context"] = "".join(context).strip() if context else None

        if failed and self.CAPTURE_TRACEBACK:
            callsite["traceback"] = "".join(traceback.format_stack(sys._getframe(1))).strip()

        return callsite

    def _format_value(self, value: Any) -> str:
        """Convert a value to a truncated string for storage."""
        return self._truncate_value(str(value))

    def assertEqual(
        self, actual: Any, expected: Any, msg: str = "", abort_on_fail: bool = False, **kwargs
    ) -> bool:
        return self.assertTrue(
            actual == expected,
            msg=msg,
            expected=expected,
            actual=actual,
            abort_on_fail=abort_on_fail,
            assertion_type="AssertEqual",
            **kwargs,
        )

    def assertIn(
        self,
        actual: Any = None,
        expected: Any = None,
        member: Any = None,
        container: Any = None,
        msg: str = "",
        abort_on_fail: bool = False,
        **kwargs,
    ) -> bool:
        _m = member if member is not None else actual
        _c = container if container is not None else expected
        if not hasattr(_c, "__contains__"):
            raise TypeError(
                f"assertIn requires a container with __contains__ (list, dict, set, str, etc.), "
                f"got {type(_c).__name__}"
            )
        return self.assertTrue(
            _m in _c,
            msg=msg,
            expected=f"'{_m}' in container",
            actual=_c,
            abort_on_fail=abort_on_fail,
            assertion_type="AssertIn",
            **kwargs,
        )

    def assertNotIn(
        self,
        actual: Any = None,
        expected: Any = None,
        member: Any = None,
        container: Any = None,
        msg: str = "",
        abort_on_fail: bool = False,
        **kwargs,
    ) -> bool:
        _m = member if member is not None else actual
        _c = container if container is not None else expected
        if not hasattr(_c, "__contains__"):
            raise TypeError(
                f"assertNotIn requires a container with __contains__ (list, dict, set, str, etc.), "
                f"got {type(_c).__name__}"
            )
        return self.assertTrue(
            _m not in _c,
            msg=msg,
            expected=f"'{_m}' NOT in container",
            actual=_c,
            abort_on_fail=abort_on_fail,
            assertion_type="AssertNotIn",
            **kwargs,
        )

    def assertInTolerance(
        self,
        actual: float,
        expected: float,
        absolute_tolerance: Optional[float] = None,
        relative_tolerance: Optional[float] = None,
        msg: str = "",
        abort_on_fail: bool = False,
        **kwargs,
    ) -> bool:
        if absolute_tolerance is not None:
            tol = absolute_tolerance
        elif relative_tolerance is not None:
            tol = abs(expected * relative_tolerance)
        else:
            tol = 0.0
        cond = (expected - tol) <= actual <= (expected + tol)
        return self.assertTrue(
            cond,
            msg=msg,
            expected=f"{expected}±{tol}",
            actual=actual,
            abort_on_fail=abort_on_fail,
            assertion_type="AssertInTolerance",
            **kwargs,
        )

    def assertInRange(
        self,
        actual: float,
        lower_bound: float,
        upper_bound: Optional[float] = None,
        include_bounds: bool = True,
        msg: str = "",
        abort_on_fail: bool = False,
        **kwargs,
    ) -> bool:
        if upper_bound is not None:
            cond = (
                (lower_bound <= actual <= upper_bound)
                if include_bounds
                else (lower_bound < actual < upper_bound)
            )
            expected = f"[{lower_bound}, {upper_bound}]"
        else:
            cond = (actual >= lower_bound) if include_bounds else (actual > lower_bound)
            expected = f">= {lower_bound}" if include_bounds else f"> {lower_bound}"
        return self.assertTrue(
            cond,
            msg=msg,
            expected=expected,
            actual=actual,
            abort_on_fail=abort_on_fail,
            assertion_type="AssertInRange",
            **kwargs,
        )

    def assertFalse(
        self,
        condition: bool,
        msg: str = "",
        abort_on_fail: bool = False,
        **kwargs,
    ) -> bool:
        return self.assertTrue(
            not condition,
            msg=msg,
            expected=False,
            actual=bool(condition),
            abort_on_fail=abort_on_fail,
            assertion_type="AssertFalse",
            **kwargs,
        )

    def assertNotEqual(
        self,
        actual: Any,
        expected: Any,
        msg: str = "",
        abort_on_fail: bool = False,
        **kwargs,
    ) -> bool:
        return self.assertTrue(
            actual != expected,
            msg=msg,
            expected=f"!= {expected}",
            actual=actual,
            abort_on_fail=abort_on_fail,
            assertion_type="AssertNotEqual",
            **kwargs,
        )

    def assertGreater(
        self,
        actual: Any,
        expected: Any,
        msg: str = "",
        abort_on_fail: bool = False,
        **kwargs,
    ) -> bool:
        return self.assertTrue(
            actual > expected,
            msg=msg,
            expected=f"> {expected}",
            actual=actual,
            abort_on_fail=abort_on_fail,
            assertion_type="AssertGreater",
            **kwargs,
        )

    def assertLess(
        self,
        actual: Any,
        expected: Any,
        msg: str = "",
        abort_on_fail: bool = False,
        **kwargs,
    ) -> bool:
        return self.assertTrue(
            actual < expected,
            msg=msg,
            expected=f"< {expected}",
            actual=actual,
            abort_on_fail=abort_on_fail,
            assertion_type="AssertLess",
            **kwargs,
        )

    def assertRegex(
        self,
        text: str,
        pattern: str,
        msg: str = "",
        abort_on_fail: bool = False,
        **kwargs,
    ) -> bool:
        cond = bool(re.search(pattern, text))
        return self.assertTrue(
            cond,
            msg=msg,
            expected=f"matches '{pattern}'",
            actual=text,
            abort_on_fail=abort_on_fail,
            assertion_type="AssertRegex",
            **kwargs,
        )

    def require(self, condition: bool, msg: str = "", **kwargs) -> bool:
        """Record an AssertRequire entry and stop the step when condition is false."""
        return self.assertTrue(
            condition,
            msg=msg,
            abort_on_fail=True,
            assertion_type="AssertRequire",
            **kwargs,
        )

    def attach_artifact(self, path: Union[str, Path], name: Optional[str] = None) -> None:
        """Record an existing file as an artifact of the current step.

        The absolute path and the name, the file name by default, are added to
        the step result's metadata["artifacts"]. A path that is not an existing
        file records a failed AttachArtifact entry and raises AssertionError.
        """
        file_path = Path(os.path.abspath(path))
        if not file_path.is_file():
            self.assertTrue(
                False,
                msg=f"Artifact file not found: {path}",
                expected="existing file",
                actual=str(file_path),
                abort_on_fail=True,
                assertion_type="AttachArtifact",
            )
        self._current_artifacts.append({"path": str(file_path), "name": name or file_path.name})

    def waitUntil(
        self,
        condition_fn: Callable[[], bool],
        timeout: float = 10.0,
        poll_interval: float = 0.5,
        msg: str = "",
        abort_on_fail: bool = False,
    ) -> bool:
        """Poll condition_fn until it returns True or timeout seconds pass.

        Records an AssertWaitUntil entry whose metadata holds elapsed_seconds,
        timeout_seconds and poll_interval_seconds. An exception raised by
        condition_fn counts as not yet true; on timeout the last one is recorded
        as last_exception.
        """
        start = time.monotonic()
        last_exception: Optional[Exception] = None
        while True:
            try:
                met = bool(condition_fn())
            except Exception as e:
                met = False
                last_exception = e
            elapsed = time.monotonic() - start
            if met or elapsed >= timeout:
                break
            time.sleep(min(poll_interval, timeout - elapsed))
        metadata: dict[str, Any] = {
            "elapsed_seconds": round(elapsed, 3),
            "timeout_seconds": timeout,
            "poll_interval_seconds": poll_interval,
        }
        if not met and last_exception is not None:
            metadata["last_exception"] = f"{type(last_exception).__name__}: {last_exception}"
        return self.assertTrue(
            met,
            msg=msg,
            expected=f"condition true within {timeout}s",
            actual=f"{'true' if met else 'not true'} after {elapsed:.3f}s",
            abort_on_fail=abort_on_fail,
            assertion_type="AssertWaitUntil",
            **metadata,
        )

    def _truncate_value(self, value: str) -> str:
        """Truncate a value string to MAX_RESULT_VALUE_LENGTH."""
        if len(value) > self.MAX_RESULT_VALUE_LENGTH:
            return value[: self.MAX_RESULT_VALUE_LENGTH] + "... <truncated>"
        return value

    def log_info(self, message: str) -> None:
        self._logger.info(message)

    def _setup_initial_logging(self) -> None:
        """Configures the instance logger to show LEVEL and NAME for the Test Case header."""
        logger = self._logger
        logger.handlers.clear()
        handler = Utf8StreamHandler()
        handler.setFormatter(ColoredFormatter(show_level=True))
        logger.addHandler(handler)
        logger.setLevel(self._log_level)
        logger.propagate = False
        self._console_handler = handler

    def _enable_clean_assertion_logging(self) -> None:
        """Switches to clean formatting (suppressing Level/Name) for assertion lines."""
        if self._console_handler and isinstance(self._console_handler, logging.StreamHandler):
            self._console_handler.setFormatter(ColoredFormatter(show_level=False))

    def set_loglevel(self, level: int) -> None:
        self._log_level = level
        self._logger.setLevel(level)

    def print_variables(self, variables: dict[str, Any]) -> None:
        for name, value in variables.items():
            self._logger.info(f"  {name}: {value}")

    def get_results(self) -> list[TestMethodResult]:
        return self._results
