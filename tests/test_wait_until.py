"""Tests for the waitUntil polling helper."""

import logging

import pytest

from budtestlibrary import BudTestCase
from budtestlibrary.budtestcase import AssertionError as BudAssertionError


class WaitTest(BudTestCase):
    """Bare test case for direct waitUntil calls."""


@pytest.fixture
def tc():
    """Return a quiet test case with an empty assertion list."""
    case = WaitTest()
    case.set_loglevel(logging.CRITICAL)
    return case


def _true_after(calls):
    """Return a condition that becomes true on the given call number."""
    count = {"n": 0}

    def condition():
        count["n"] += 1
        return count["n"] >= calls

    return condition, count


class TestWaitUntil:
    def test_condition_met_within_timeout_returns_true_and_passes(self, tc):
        condition, count = _true_after(3)
        assert tc.waitUntil(condition, timeout=2.0, poll_interval=0.01, msg="ready") is True
        entry = tc._current_assertions[0]
        assert entry.assertion_type == "AssertWaitUntil"
        assert entry.passed is True
        assert entry.message == "ready"
        assert count["n"] == 3

    def test_condition_never_met_returns_false_and_fails(self, tc):
        assert tc.waitUntil(lambda: False, timeout=0.05, poll_interval=0.01) is False
        entry = tc._current_assertions[0]
        assert entry.passed is False
        assert entry.metadata["elapsed_seconds"] >= 0.05

    def test_abort_on_fail_raises_assertion_error(self, tc):
        with pytest.raises(BudAssertionError, match=r"\[AssertWaitUntil\]"):
            tc.waitUntil(lambda: False, timeout=0.02, poll_interval=0.01, abort_on_fail=True)
        assert tc._current_assertions[0].passed is False

    def test_metadata_records_elapsed_time_and_settings(self, tc):
        tc.waitUntil(lambda: True, timeout=1.5, poll_interval=0.25)
        metadata = tc._current_assertions[0].metadata
        assert set(metadata) == {"elapsed_seconds", "timeout_seconds", "poll_interval_seconds"}
        assert metadata["timeout_seconds"] == 1.5
        assert metadata["poll_interval_seconds"] == 0.25
        assert 0 <= metadata["elapsed_seconds"] < 1.5

    def test_raising_condition_keeps_polling_until_true(self, tc):
        count = {"n": 0}

        def condition():
            count["n"] += 1
            if count["n"] < 3:
                raise ConnectionError("not up yet")
            return True

        assert tc.waitUntil(condition, timeout=2.0, poll_interval=0.01) is True
        entry = tc._current_assertions[0]
        assert entry.passed is True
        assert "last_exception" not in entry.metadata

    def test_last_exception_recorded_on_timeout(self, tc):
        def condition():
            raise ConnectionError("not up yet")

        assert tc.waitUntil(condition, timeout=0.03, poll_interval=0.01) is False
        entry = tc._current_assertions[0]
        assert entry.metadata["last_exception"] == "ConnectionError: not up yet"

    def test_entry_points_at_the_test_code(self, tc):
        tc.waitUntil(lambda: True, timeout=0.1)
        entry = tc._current_assertions[0]
        assert entry.source_file == __file__
        assert entry.source_function == "test_entry_points_at_the_test_code"
