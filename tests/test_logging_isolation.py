"""Tests to verify BudTestCase does not mutate the root logger."""

import logging

from budtestlibrary import BudTestCase


class TestRootLoggerIsolation:
    def test_root_logger_handlers_unchanged(self):
        """BudTestCase should use its own logger, not modify root logger."""
        root_logger = logging.getLogger()
        root_handlers_before = list(root_logger.handlers)

        class IsolatedTest(BudTestCase):
            def bud_check(self):
                self.assertTrue(True, msg="ok")

        tc = IsolatedTest()
        tc.set_loglevel(logging.CRITICAL)
        tc.run()

        root_handlers_after = list(root_logger.handlers)
        assert len(root_handlers_after) == len(root_handlers_before)
        assert root_handlers_after == root_handlers_before

    def test_root_logger_level_unchanged(self):
        """Root logger level should not change after running a BudTestCase."""
        root_logger = logging.getLogger()
        original_level = root_logger.level

        class LevelTest(BudTestCase):
            def bud_check(self):
                self.assertTrue(True, msg="ok")

        tc = LevelTest()
        tc.set_loglevel(logging.CRITICAL)
        tc.run()

        assert root_logger.level == original_level

    def test_custom_logger_used(self):
        """BudTestCase should use 'budtestlibrary.ClassName' as logger name."""

        class LoggerNameTest(BudTestCase):
            def bud_check(self):
                self.assertTrue(True, msg="ok")

        tc = LoggerNameTest()
        assert tc._logger.name == "budtestlibrary.LoggerNameTest"

    def test_logger_has_its_own_handler(self):
        """The instance logger should have a StreamHandler attached."""

        class HandlerTest(BudTestCase):
            def bud_check(self):
                self.assertTrue(True, msg="ok")

        tc = HandlerTest()
        tc.set_loglevel(logging.INFO)
        tc.run()
        assert any(isinstance(h, logging.StreamHandler) for h in tc._logger.handlers)

    def test_logger_does_not_propagate(self):
        """propagate should be False to avoid log duplication."""

        class PropagationTest(BudTestCase):
            def bud_check(self):
                self.assertTrue(True, msg="ok")

        tc = PropagationTest()
        tc.set_loglevel(logging.INFO)
        tc.run()
        assert not tc._logger.propagate


class TestConsoleColoredLogging:
    def test_header_logging_includes_ansi_colors(self):
        """Console headers should include ANSI color codes for visibility."""
        import io

        class HeaderTest(BudTestCase):
            def bud_check(self):
                self.assertTrue(True, msg="ok")

        tc = HeaderTest()
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        tc._logger.handlers.clear()
        tc._logger.addHandler(handler)
        tc._logger.setLevel(logging.INFO)
        tc._logger.propagate = False
        tc._console_handler = handler
        # Simulate header logging
        from budtestlibrary.budtestcase import BOLD, RESET, WHITE

        tc.log_info(f"{BOLD}{WHITE}TEST HEADER{RESET}")
        output = stream.getvalue()
        assert "\033[" in output  # ANSI escape codes present

    def test_assertion_output_has_colors(self):
        """Console assertion lines should include ANSI colors."""
        import io

        class AssertionOutputTest(BudTestCase):
            pass

        tc = AssertionOutputTest()
        tc.set_loglevel(logging.INFO)

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        tc._logger.handlers.clear()
        tc._logger.addHandler(handler)
        tc._logger.propagate = False
        tc._console_handler = handler

        tc.assertTrue(True, msg="color test")
        output = stream.getvalue()
        assert "\033[" in output
