"""Tests for configurable source path and traceback capture."""

import logging

from budtestlibrary import BudTestCase


class TestSourcePathCapture:
    def test_source_captured_by_default(self):
        class SourceTest(BudTestCase):
            def bud_check(self):
                self.assertTrue(True, msg="captured")

        tc = SourceTest()
        tc.set_loglevel(logging.CRITICAL)
        tc.run()
        result = tc.get_results()[0]
        assertion = result.assertions[0]
        assert assertion.source_file is not None
        assert assertion.source_line is not None
        assert assertion.source_function is not None

    def test_source_suppressed_when_capture_disabled(self):
        class NoSourceTest(BudTestCase):
            CAPTURE_SOURCE_PATH = False

            def bud_check(self):
                self.assertTrue(True, msg="not captured")

        tc = NoSourceTest()
        tc.set_loglevel(logging.CRITICAL)
        tc.run()
        result = tc.get_results()[0]
        assertion = result.assertions[0]
        assert assertion.source_file is None
        assert assertion.source_line is None
        assert assertion.source_function is None

    def test_source_omitted_from_dict_when_none(self):
        class NoSourceTest(BudTestCase):
            CAPTURE_SOURCE_PATH = False

            def bud_check(self):
                self.assertTrue(True, msg="no source")

        tc = NoSourceTest()
        tc.set_loglevel(logging.CRITICAL)
        tc.run()
        result = tc.get_results()[0]
        assertion = result.assertions[0]
        d = assertion.to_dict()
        assert d["source_file"] is None
        assert d["source_line"] is None
        assert d["source_function"] is None


class TestTracebackCapture:
    def test_traceback_not_captured_by_default_for_passing_assertions(self):
        class PassTest(BudTestCase):
            def bud_check(self):
                self.assertTrue(True, msg="pass")

        tc = PassTest()
        tc.set_loglevel(logging.CRITICAL)
        tc.run()
        result = tc.get_results()[0]
        assertion = result.assertions[0]
        # Passing assertions typically don't have tracebacks
        assert assertion.traceback is None

    def test_traceback_captured_for_failed_assertions_by_default(self):
        class FailTest(BudTestCase):
            def bud_check(self):
                self.assertTrue(False, msg="fail")

        tc = FailTest()
        tc.set_loglevel(logging.CRITICAL)
        tc.run()
        assertion = tc.get_results()[0].assertions[0]
        assert assertion.traceback is not None
        assert "bud_check" in assertion.traceback

    def test_traceback_suppressed_when_capture_disabled(self):
        class NoTracebackTest(BudTestCase):
            CAPTURE_TRACEBACK = False

            def bud_check(self):
                self.assertTrue(False, msg="no traceback")

        tc = NoTracebackTest()
        tc.set_loglevel(logging.CRITICAL)
        tc.run()
        result = tc.get_results()[0]
        assertion = result.assertions[0]
        assert assertion.traceback is None
        assert result.traceback is None

    def test_method_traceback_suppressed_when_capture_disabled(self):
        class NoMethodTracebackTest(BudTestCase):
            CAPTURE_TRACEBACK = False

            def bud_check(self):
                raise RuntimeError("boom")

        tc = NoMethodTracebackTest()
        tc.set_loglevel(logging.CRITICAL)
        tc.run()
        result = tc.get_results()[0]
        assert result.traceback is None
        assert result.error_message == "boom"
