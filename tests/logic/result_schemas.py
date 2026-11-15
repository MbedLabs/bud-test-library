"""TestResult and TestMethodResult to_dict(): keys and values, values as text, None kept, plain text without ANSI codes, skipped entries, truncation and its limits, metadata."""

import re
from datetime import datetime

from budtestlibrary import BudTestCase
from budtestlibrary.budtestcase import TestMethodResult, TestResult
from tests import support

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def strings(value, path="result"):
    """Yield (path, text) for every string inside a nested dict or list."""
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from strings(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from strings(item, f"{path}[{index}]")


class ResultSchemas(BudTestCase):
    """to_dict() of TestResult and TestMethodResult."""

    def bud_passed_result_schema(self):
        """A passed TestResult serialises its fields, with expected and actual as text and an ISO timestamp."""
        d = TestResult(
            passed=True,
            message="all good",
            assertion_type="AssertTrue",
            expected=True,
            actual=True,
            source_file="/path/to/demo_test.py",
            source_line=42,
            source_function="bud_check",
            timestamp=datetime(2026, 5, 20, 12, 0, 0),
        ).to_dict()
        want = {
            "passed": True,
            "message": "all good",
            "skipped": False,
            "assertion_type": "AssertTrue",
            "expected": "True",
            "actual": "True",
            "result": None,
            "source_file": "/path/to/demo_test.py",
            "source_line": 42,
            "source_function": "bud_check",
            "code_context": None,
            "traceback": None,
            "timestamp": "2026-05-20T12:00:00",
            "metadata": {},
        }
        support.check(
            self,
            d,
            want,
            "a passed TestResult serialises every field, with the timestamp as ISO text",
            "the serialised passed TestResult differs from the expected fields",
        )

    def bud_failed_result_schema(self):
        """A failed TestResult with integers serialises them as text."""
        d = TestResult(
            passed=False, message="mismatch", assertion_type="AssertEqual", expected=42, actual=99
        ).to_dict()
        support.check(
            self,
            (d["passed"], d["expected"], d["actual"]),
            (False, "42", "99"),
            "a failed TestResult serialises passed False and its integers 42 and 99 as text",
            "a failed TestResult did not serialise passed False with 42 and 99 as text",
        )

    def bud_no_ansi_in_serialized_output_of_a_real_run(self):
        """No string in the serialised results of failing assertEqual, assertIn and a raising step holds an ANSI code."""

        class ColourCheck(BudTestCase):
            def bud_equal(self):
                self.assertEqual("abc", "xyz", msg="equal fails")

            def bud_member(self):
                self.assertIn(member=9, container=[1, 2], msg="member fails")

            def bud_raises(self):
                raise RuntimeError("step broke")

        _, results = support.run(ColourCheck())
        coloured = [
            path
            for r in results
            for path, text in strings(r.to_dict(), r.method_name)
            if ANSI.search(text)
        ]
        support.check(
            self,
            [r.passed for r in results],
            [False, False, False],
            "the failing assertEqual, the failing assertIn and the raising step give three failed steps",
            "the three steps of ColourCheck did not all fail",
        )
        support.check(
            self,
            coloured,
            [],
            "no string in the serialised results holds an ANSI colour code",
            "some strings in the serialised results hold ANSI colour codes",
        )

    def bud_none_values_serialized_as_none(self):
        """Optional fields that are None serialise as None, not as the text None."""
        d = TestResult(passed=True, message="no values").to_dict()
        for key in (
            "expected",
            "actual",
            "result",
            "source_file",
            "source_line",
            "source_function",
            "code_context",
            "traceback",
        ):
            support.check(
                self,
                d[key],
                None,
                f"the unset field {key} serialises as None, not as the text None",
                f"the unset field {key} does not serialise as None",
            )

    def bud_skipped_result(self):
        """The serialised entry of a real skipAssert is skipped, passed and of type Skip."""
        d = support.step(lambda tc: tc.skipAssert("skip")).assertions[0].to_dict()
        support.check(
            self,
            (d["skipped"], d["passed"], d["assertion_type"]),
            (True, True, "Skip"),
            "the serialised skipAssert entry is skipped, passed and of type Skip",
            "the serialised skipAssert entry is not skipped, passed and of type Skip",
        )

    def bud_truncation_large_values(self):
        """A 6000-character value is cut at the default 5000 characters plus the marker; a short value is kept."""
        d = TestResult(
            passed=False, message="big value", expected="x" * 6000, actual="short"
        ).to_dict()
        support.check(
            self,
            d["expected"],
            "x" * 5000 + "... <truncated>",
            "a 6000-character value is cut after 5000 characters and marked ... <truncated>",
            "a 6000-character value is not cut after 5000 characters with the ... <truncated> marker",
        )
        support.check(
            self,
            len(d["expected"]),
            5015,
            "the cut value is 5015 characters long, 5000 plus the marker",
            "the cut value is not 5015 characters long",
        )
        support.check(
            self,
            d["actual"],
            "short",
            "the short value next to it is kept whole",
            "the short value next to it was changed",
        )

    def bud_truncation_short_values_untouched(self):
        """Short values are serialised unchanged."""
        d = TestResult(passed=True, message="ok", expected="hello", actual="world").to_dict()
        support.check(
            self,
            (d["expected"], d["actual"]),
            ("hello", "world"),
            "short values hello and world serialise unchanged",
            "short values hello and world were changed when serialised",
        )

    def bud_truncation_uses_per_result_limit(self):
        """max_result_value_length=4 cuts both values after four characters."""
        d = TestResult(
            passed=False,
            message="small limit",
            expected="abcdefghij",
            actual="1234567890",
            max_result_value_length=4,
        ).to_dict()
        support.check(
            self,
            (d["expected"], d["actual"]),
            ("abcd... <truncated>", "1234... <truncated>"),
            "max_result_value_length=4 cuts both values after four characters",
            "max_result_value_length=4 did not cut both values after four characters",
        )

    def bud_truncation_keeps_a_value_at_the_limit(self):
        """A value exactly as long as the limit is kept whole."""
        d = TestResult(
            passed=True, message="edge", expected="12345", max_result_value_length=5
        ).to_dict()
        support.check(
            self,
            d["expected"],
            "12345",
            "a value exactly as long as the limit of 5 is kept whole",
            "a value exactly as long as the limit of 5 was cut",
        )

    def bud_metadata_keys_preserved(self):
        """The metadata dict is serialised as given."""
        d = TestResult(
            passed=True, message="with metadata", metadata={"custom_key": "custom_val"}
        ).to_dict()
        support.check(
            self,
            d["metadata"],
            {"custom_key": "custom_val"},
            "the metadata custom_key=custom_val serialises as given",
            "the metadata custom_key=custom_val did not serialise as given",
        )

    def bud_passing_method_schema(self):
        """A passing TestMethodResult serialises its fields with the entry as a dict."""
        entry = TestResult(passed=True, message="all good", assertion_type="AssertTrue")
        d = TestMethodResult(
            method_name="bud_check",
            passed=True,
            assertions=[entry],
            duration_seconds=0.123,
            summary_message="Step Passed",
        ).to_dict()
        support.check(
            self,
            sorted(d),
            [
                "assertions",
                "duration_seconds",
                "error_message",
                "metadata",
                "method_name",
                "passed",
                "skipped",
                "summary_message",
                "traceback",
            ],
            "a serialised TestMethodResult has exactly the expected keys",
            "a serialised TestMethodResult does not have exactly the expected keys",
        )
        support.check(
            self,
            d["assertions"],
            [entry.to_dict()],
            "the step's assertions serialise as the list of their dicts",
            "the step's assertions do not serialise as the list of their dicts",
        )
        support.check(
            self,
            (
                d["method_name"],
                d["passed"],
                d["skipped"],
                d["duration_seconds"],
                d["error_message"],
                d["summary_message"],
                d["traceback"],
                d["metadata"],
            ),
            ("bud_check", True, False, 0.123, None, "Step Passed", None, {}),
            "the passing step bud_check serialises its name, passed, duration 0.123 and summary Step Passed",
            "the passing step bud_check does not serialise the expected name, outcome, duration and summary",
        )

    def bud_failing_method_schema(self):
        """A failing TestMethodResult serialises error, summary, traceback and metadata."""
        d = TestMethodResult(
            method_name="bud_bad",
            passed=False,
            assertions=[TestResult(passed=False, message="fail", assertion_type="AssertTrue")],
            duration_seconds=0.456,
            error_message="test failed",
            summary_message="test failed",
            traceback="Traceback (most recent call last):\n  ...",
            metadata={"tc_id": "PRJ-TC-001"},
        ).to_dict()
        support.check(
            self,
            (d["passed"], d["error_message"], d["summary_message"], d["traceback"], d["metadata"]),
            (
                False,
                "test failed",
                "test failed",
                "Traceback (most recent call last):\n  ...",
                {"tc_id": "PRJ-TC-001"},
            ),
            "the failing step serialises its error, summary, traceback and metadata tc_id PRJ-TC-001",
            "the failing step does not serialise the expected error, summary, traceback and metadata",
        )

    def bud_multiple_assertions_in_method(self):
        """Three entries serialise as three dicts in their order."""
        entries = [
            TestResult(passed=True, message="a"),
            TestResult(passed=False, message="b"),
            TestResult(passed=True, skipped=True, message="c"),
        ]
        d = TestMethodResult(method_name="bud_multi", passed=False, assertions=entries).to_dict()
        support.check(
            self,
            [a["message"] for a in d["assertions"]],
            ["a", "b", "c"],
            "three entries serialise as three dicts in their order a, b, c",
            "the three entries did not serialise in their order a, b, c",
        )

    def bud_budtestcase_max_result_value_length_affects_serialization(self):
        """MAX_RESULT_VALUE_LENGTH = 3 on a case cuts the serialised values of its entries."""

        class ShortResultTest(BudTestCase):
            MAX_RESULT_VALUE_LENGTH = 3

            def bud_check(self):
                self.assertEqual("abcdef", "uvwxyz", msg="truncate")

        _, results = support.run(ShortResultTest())
        d = results[0].assertions[0].to_dict()
        support.check(
            self,
            (d["expected"], d["actual"]),
            ("uvw... <truncated>", "abc... <truncated>"),
            "MAX_RESULT_VALUE_LENGTH = 3 on the case cuts its entries' values after three characters",
            "MAX_RESULT_VALUE_LENGTH = 3 on the case did not cut its entries' values after three characters",
        )
