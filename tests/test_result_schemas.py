"""Tests for TestResult and TestMethodResult serialization (to_dict)."""

import re
from datetime import datetime

from budtestlibrary.budtestcase import TestMethodResult, TestResult, _truncate_str


class TestResultDict:
    def test_passed_result_schema(self):
        r = TestResult(
            passed=True,
            message="all good",
            assertion_type="AssertTrue",
            expected=True,
            actual=True,
            source_file="/path/to/test.py",
            source_line=42,
            source_function="bud_check",
            timestamp=datetime(2026, 5, 20, 12, 0, 0),
        )
        d = r.to_dict()
        assert d["passed"] is True
        assert d["message"] == "all good"
        assert d["skipped"] is False
        assert d["assertion_type"] == "AssertTrue"
        assert d["expected"] == "True"
        assert d["actual"] == "True"
        assert d["source_file"] == "/path/to/test.py"
        assert d["source_line"] == 42
        assert d["source_function"] == "bud_check"
        assert d["timestamp"] == "2026-05-20T12:00:00"
        assert "metadata" in d

    def test_failed_result_schema(self):
        r = TestResult(
            passed=False,
            message="mismatch",
            assertion_type="AssertEqual",
            expected=42,
            actual=99,
        )
        d = r.to_dict()
        assert d["passed"] is False
        assert d["expected"] == "42"
        assert d["actual"] == "99"

    def test_no_ansi_in_serialized_output(self):
        """Stored result data should be plain text — no ANSI color codes."""
        r = TestResult(
            passed=False,
            message="some message",
            assertion_type="AssertTrue",
            expected="EXPECTED",
            actual="ACTUAL",
        )
        d = r.to_dict()
        ansi_pattern = re.compile(r"\x1b\[[0-9;]*m")
        for key, value in d.items():
            if isinstance(value, str):
                assert not ansi_pattern.search(value), f"ANSI found in key '{key}': {value!r}"
            elif isinstance(value, dict):
                for sub_key, sub_val in value.items():
                    if isinstance(sub_val, str):
                        assert not ansi_pattern.search(
                            sub_val
                        ), f"ANSI found in metadata.{sub_key}: {sub_val!r}"

    def test_none_values_serialized_as_none(self):
        r = TestResult(
            passed=True,
            message="no values",
            expected=None,
            actual=None,
            result=None,
            source_file=None,
            source_line=None,
            source_function=None,
            code_context=None,
            traceback=None,
        )
        d = r.to_dict()
        assert d["expected"] is None
        assert d["actual"] is None
        assert d["result"] is None
        assert d["source_file"] is None
        assert d["source_line"] is None
        assert d["source_function"] is None
        assert d["code_context"] is None
        assert d["traceback"] is None

    def test_skipped_result(self):
        r = TestResult(passed=True, skipped=True, message="skip", assertion_type="Skip")
        d = r.to_dict()
        assert d["skipped"] is True
        assert d["passed"] is True

    def test_truncation_large_values(self):
        """Large assertion values should be truncated to avoid bloated reports."""
        huge_value = "x" * 6000
        r = TestResult(
            passed=False,
            message="big value",
            expected=huge_value,
            actual="short",
        )
        d = r.to_dict()
        assert len(d["expected"]) <= 5100  # max_length + "... <truncated>" overhead
        assert "... <truncated>" in d["expected"]
        assert d["actual"] == "short"  # small values untouched

    def test_truncation_short_values_untouched(self):
        r = TestResult(passed=True, message="ok", expected="hello", actual="world")
        d = r.to_dict()
        assert d["expected"] == "hello"
        assert d["actual"] == "world"

    def test_metadata_keys_preserved(self):
        r = TestResult(
            passed=True,
            message="with metadata",
            metadata={"custom_key": "custom_val"},
        )
        d = r.to_dict()
        assert d["metadata"] == {"custom_key": "custom_val"}


class TestMethodResultDict:
    def test_passing_method_schema(self):
        assertion = TestResult(
            passed=True,
            message="all good",
            assertion_type="AssertTrue",
        )
        mr = TestMethodResult(
            method_name="bud_check",
            passed=True,
            assertions=[assertion],
            duration_seconds=0.123,
            summary_message="Step Passed",
        )
        d = mr.to_dict()
        assert d["method_name"] == "bud_check"
        assert d["passed"] is True
        assert d["skipped"] is False
        assert len(d["assertions"]) == 1
        assert isinstance(d["assertions"][0], dict)
        assert d["duration_seconds"] == 0.123
        assert d["error_message"] is None
        assert d["summary_message"] == "Step Passed"
        assert d["traceback"] is None
        assert isinstance(d["metadata"], dict)

    def test_failing_method_schema(self):
        assertion = TestResult(
            passed=False,
            message="fail",
            assertion_type="AssertTrue",
        )
        mr = TestMethodResult(
            method_name="bud_bad",
            passed=False,
            assertions=[assertion],
            duration_seconds=0.456,
            error_message="test failed",
            summary_message="test failed",
            traceback="Traceback (most recent call last):\n  ...",
            metadata={"tc_id": "PROJ-TC-001"},
        )
        d = mr.to_dict()
        assert d["passed"] is False
        assert d["error_message"] == "test failed"
        assert d["summary_message"] == "test failed"
        assert d["traceback"] == "Traceback (most recent call last):\n  ..."
        assert d["metadata"] == {"tc_id": "PROJ-TC-001"}

    def test_multiple_assertions_in_method(self):
        assertions = [
            TestResult(passed=True, message="a"),
            TestResult(passed=False, message="b"),
            TestResult(passed=True, skipped=True, message="c"),
        ]
        mr = TestMethodResult(
            method_name="bud_multi",
            passed=False,
            assertions=assertions,
        )
        d = mr.to_dict()
        assert len(d["assertions"]) == 3

    def test_no_ansi_in_summary_or_error(self):
        """Summary and error messages in stored results should be ANSI-free."""
        assertion = TestResult(passed=False, message="plain", assertion_type="AssertTrue")
        mr = TestMethodResult(
            method_name="bud_check",
            passed=False,
            assertions=[assertion],
            error_message="[AssertTrue] EXPECTED: True | ACTUAL: False",
            summary_message="[AssertTrue] EXPECTED: True | ACTUAL: False",
        )
        d = mr.to_dict()
        ansi_pattern = re.compile(r"\x1b\[[0-9;]*m")
        assert not ansi_pattern.search(d["error_message"])
        assert not ansi_pattern.search(d["summary_message"])


class TestTruncateHelper:
    def test_truncate_long(self):
        result = _truncate_str("x" * 6000, max_length=10)
        assert result == "x" * 10 + "... <truncated>"

    def test_no_truncate_short(self):
        result = _truncate_str("hello", max_length=100)
        assert result == "hello"

    def test_exact_boundary(self):
        result = _truncate_str("12345", max_length=5)
        assert result == "12345"
