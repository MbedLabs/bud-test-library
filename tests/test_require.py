"""Tests for the require() precondition helper."""

import logging

import pytest

from budtestlibrary import BudTestCase
from budtestlibrary.budtestcase import AssertionError as BudAssertionError


class RequireTest(BudTestCase):
    """Bare test case for direct require calls."""


@pytest.fixture
def tc():
    """Return a quiet test case with an empty assertion list."""
    case = RequireTest()
    case.set_loglevel(logging.CRITICAL)
    return case


class TestRequire:
    def test_true_condition_records_a_passed_entry_and_continues(self, tc):
        assert tc.require(True, msg="connection open") is True
        entry = tc._current_assertions[0]
        assert entry.assertion_type == "AssertRequire"
        assert entry.passed is True

    def test_false_condition_records_a_failed_entry_and_raises(self, tc):
        with pytest.raises(BudAssertionError, match=r"\[AssertRequire\].*MESSAGE: connection open"):
            tc.require(False, msg="connection open")
        entry = tc._current_assertions[0]
        assert entry.assertion_type == "AssertRequire"
        assert entry.passed is False

    def test_extra_keyword_arguments_go_to_metadata(self, tc):
        tc.require(True, msg="m", station="station-01")
        assert tc._current_assertions[0].metadata == {"station": "station-01"}


class TestRequireInSteps:
    def test_failed_requirement_halts_the_step_without_cascading_errors(self):
        class StepTest(BudTestCase):
            def __init__(self):
                super().__init__()
                self.reached = False

            def bud_step(self):
                connection = None
                self.require(connection is not None, msg="connection is open")
                self.reached = True
                connection.send(b"ping")

            def bud_next(self):
                self.assertTrue(True, msg="next step runs")

        tc = StepTest()
        tc.set_loglevel(logging.CRITICAL)
        tc.run()
        first, second = tc.get_results()
        assert tc.reached is False
        assert first.passed is False
        assert first.error_message == (
            "[AssertRequire] EXPECTED: True | ACTUAL: False | MESSAGE: connection is open"
        )
        assert "AttributeError" not in (first.traceback or "")
        assert [a.assertion_type for a in first.assertions] == ["AssertRequire"]
        assert second.passed is True
