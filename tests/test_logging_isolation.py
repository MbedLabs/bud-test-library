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


class TestConsoleEncoding:
    """The console handler writes UTF-8 whatever the stream's own encoding is."""

    def _cp1252_stream(self):
        import io

        return io.TextIOWrapper(
            io.BytesIO(), encoding="cp1252", errors="backslashreplace", newline="\n"
        )

    def test_non_utf8_stream_gets_utf8_bytes(self):
        from budtestlibrary.budtestcase import Utf8StreamHandler

        stream = self._cp1252_stream()
        logger = logging.getLogger("budtestlibrary.test_encoding_cp1252")
        logger.propagate = False
        handler = Utf8StreamHandler(stream)
        logger.addHandler(handler)
        try:
            logger.warning("✓ PASSED ──")
        finally:
            logger.removeHandler(handler)

        raw = stream.buffer.getvalue()
        assert raw.decode("utf-8") == "✓ PASSED ──\n"
        assert b"\u2713" not in raw

    def test_utf8_and_text_only_streams_are_unchanged(self):
        import io

        from budtestlibrary.budtestcase import Utf8StreamHandler

        utf8 = io.TextIOWrapper(io.BytesIO(), encoding="utf-8", newline="\n")
        text_only = io.StringIO()
        logger = logging.getLogger("budtestlibrary.test_encoding_utf8")
        logger.propagate = False
        handlers = [Utf8StreamHandler(utf8), Utf8StreamHandler(text_only)]
        for handler in handlers:
            logger.addHandler(handler)
        try:
            logger.warning("✓ ok")
        finally:
            for handler in handlers:
                logger.removeHandler(handler)

        utf8.flush()
        assert utf8.buffer.getvalue().decode("utf-8") == "✓ ok\n"
        assert text_only.getvalue() == "✓ ok\n"

    def test_console_handler_is_utf8_handler(self):
        from budtestlibrary.budtestcase import Utf8StreamHandler

        class EncodingTest(BudTestCase):
            def bud_check(self):
                self.assertTrue(True, msg="ok")

        tc = EncodingTest()
        tc.set_loglevel(logging.CRITICAL)
        tc.run()
        assert isinstance(tc._console_handler, Utf8StreamHandler)

    def test_timestamp_uses_numeric_utc_offset(self):
        import re

        from budtestlibrary.budtestcase import ColoredFormatter

        record = logging.LogRecord("x", logging.INFO, __file__, 1, "msg", None, None)
        line = ColoredFormatter().format(record)
        assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [+-]\d{4}", line)
