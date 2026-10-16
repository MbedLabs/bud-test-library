"""Tests for assertion callsite capture through frame walking."""

import inspect
import logging

import pytest

from budtestlibrary import BudTestCase


class CallsiteTest(BudTestCase):
    """Bare test case for direct assertion calls."""


@pytest.fixture
def tc():
    """Return a quiet test case with an empty assertion list."""
    case = CallsiteTest()
    case.set_loglevel(logging.CRITICAL)
    return case


def _line_after():
    """Return the line number following the caller's current line."""
    return inspect.currentframe().f_back.f_lineno + 1


class TestSourceLocation:
    def test_direct_assertion_records_the_calling_line(self, tc):
        line = _line_after()
        tc.assertTrue(True, msg="direct")
        result = tc._current_assertions[0]
        assert result.source_file == __file__
        assert result.source_line == line
        assert result.source_function == "test_direct_assertion_records_the_calling_line"

    def test_wrapper_assertions_record_the_test_line(self, tc):
        line = _line_after()
        tc.assertEqual(1, 1)
        tc.assertInTolerance(1.0, expected=1.0, absolute_tolerance=0.1)
        first, second = tc._current_assertions
        assert (first.source_file, first.source_line) == (__file__, line)
        assert (second.source_file, second.source_line) == (__file__, line + 1)

    def test_skip_records_the_calling_line(self, tc):
        line = _line_after()
        tc.skipAssert("not applicable")
        assert tc._current_assertions[0].source_line == line


class TestFailureDetail:
    def test_passing_assertion_has_no_code_context_or_traceback(self, tc):
        tc.assertTrue(True, msg="passes")
        result = tc._current_assertions[0]
        assert result.code_context is None
        assert result.traceback is None

    def test_failing_assertion_has_code_context_and_traceback(self, tc):
        tc.assertTrue(False, msg="fails here")
        result = tc._current_assertions[0]
        assert 'tc.assertTrue(False, msg="fails here")' in result.code_context
        assert "test_failing_assertion_has_code_context_and_traceback" in result.traceback
        assert "in assertTrue" in result.traceback.splitlines()[-2]

    def test_source_path_off_disables_frame_inspection(self, tc):
        tc.CAPTURE_SOURCE_PATH = False
        tc.assertTrue(False, msg="fails")
        result = tc._current_assertions[0]
        assert result.source_file is None
        assert result.source_line is None
        assert result.source_function is None
        assert result.code_context is None
        assert result.traceback is not None

    def test_traceback_off_keeps_code_context(self, tc):
        tc.CAPTURE_TRACEBACK = False
        tc.assertTrue(False, msg="fails")
        result = tc._current_assertions[0]
        assert result.traceback is None
        assert result.code_context is not None


class TestNoFullStackInspection:
    def test_inspect_stack_is_not_called(self, tc, monkeypatch):
        def _forbidden(*args, **kwargs):
            raise RuntimeError("inspect.stack called")

        monkeypatch.setattr(inspect, "stack", _forbidden)
        tc.assertTrue(True)
        tc.assertTrue(False)
        assert [a.passed for a in tc._current_assertions] == [True, False]
