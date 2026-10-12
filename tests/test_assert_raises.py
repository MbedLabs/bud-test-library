"""Tests for the assertRaises context manager."""

import asyncio
import logging
import sys

import pytest

from budtestlibrary import BudTestCase
from budtestlibrary.budtestcase import AssertionError as BudAssertionError


class RaisesTest(BudTestCase):
    """Bare test case for direct assertRaises calls."""


@pytest.fixture
def tc():
    """Return a quiet test case with an empty assertion list."""
    case = RaisesTest()
    case.set_loglevel(logging.CRITICAL)
    return case


class TestAssertRaises:
    def test_expected_exception_passes_and_is_suppressed(self, tc):
        with tc.assertRaises(ValueError, msg="bad value rejected"):
            raise ValueError("bad value")
        entry = tc._current_assertions[0]
        assert entry.assertion_type == "AssertRaises"
        assert entry.passed is True
        assert entry.expected == "ValueError"
        assert entry.actual == "ValueError: bad value"
        assert entry.message == "bad value rejected"

    def test_subclass_of_expected_exception_passes(self, tc):
        with tc.assertRaises(LookupError):
            raise KeyError("k")
        assert tc._current_assertions[0].passed is True

    def test_no_exception_fails(self, tc):
        with tc.assertRaises(ValueError):
            pass
        entry = tc._current_assertions[0]
        assert entry.passed is False
        assert entry.expected == "ValueError"
        assert entry.actual == "no exception raised"

    def test_unexpected_exception_fails_and_is_suppressed(self, tc):
        reached = []
        with tc.assertRaises(ValueError):
            raise KeyError("wrong")
        reached.append(True)
        entry = tc._current_assertions[0]
        assert entry.passed is False
        assert entry.expected == "ValueError"
        assert entry.actual == "KeyError: 'wrong'"
        assert reached == [True]

    def test_abort_on_fail_raises_assertion_error(self, tc):
        with pytest.raises(BudAssertionError, match=r"\[AssertRaises\] EXPECTED: ValueError"):
            with tc.assertRaises(ValueError, abort_on_fail=True):
                pass
        assert tc._current_assertions[0].passed is False

    def test_abort_on_fail_does_not_raise_when_expected_is_raised(self, tc):
        with tc.assertRaises(ValueError, abort_on_fail=True):
            raise ValueError("ok")
        assert tc._current_assertions[0].passed is True

    def test_keyboard_interrupt_is_not_swallowed(self, tc):
        with pytest.raises(KeyboardInterrupt):
            with tc.assertRaises(ValueError):
                raise KeyboardInterrupt
        assert tc._current_assertions == []

    def test_expected_system_exit_passes(self, tc):
        with tc.assertRaises(SystemExit, msg="cli exits"):
            sys.exit(2)
        entry = tc._current_assertions[0]
        assert entry.passed is True
        assert entry.actual == "SystemExit: 2"

    def test_unexpected_base_exception_passes_through(self, tc):
        with pytest.raises(asyncio.CancelledError):
            with tc.assertRaises(ValueError):
                raise asyncio.CancelledError()
        assert tc._current_assertions == []

    def test_entry_points_at_the_test_code(self, tc):
        with tc.assertRaises(ValueError):
            raise ValueError("x")
        entry = tc._current_assertions[0]
        assert entry.source_file == __file__
        assert entry.source_function == "test_entry_points_at_the_test_code"


class TestAssertRaisesInSteps:
    def test_step_fails_when_nothing_is_raised_and_continues(self):
        class StepTest(BudTestCase):
            def __init__(self):
                super().__init__()
                self.after = False

            def bud_step(self):
                with self.assertRaises(ValueError):
                    pass
                self.after = True

        tc = StepTest()
        tc.set_loglevel(logging.CRITICAL)
        tc.run()
        result = tc.get_results()[0]
        assert tc.after is True
        assert result.passed is False
        assert "[AssertRaises] EXPECTED: ValueError | ACTUAL: no exception raised" in (
            result.error_message
        )
