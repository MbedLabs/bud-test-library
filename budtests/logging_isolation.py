"""Logging: the root logger left alone, the case's own logger and handler, coloured assertion lines, UTF-8 on a non-UTF-8 stream, and the timestamp's UTC offset."""

import io
import logging
import re

import support

from budtestlibrary import BudTestCase, parameterized
from budtestlibrary.budtestcase import Utf8StreamHandler

TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} (UTC[+-]\d{1,2}(?::\d{2})?) - ")
ANSI = re.compile(r"\x1b\[[0-9;]*m")
OFFSETS = {
    "Etc/GMT-1": "UTC+1",
    "Etc/GMT-2": "UTC+2",
    "Etc/GMT+3": "UTC-3",
    "Asia/Kolkata": "UTC+5:30",
    "NST3:30": "UTC-3:30",
    "UTC": "UTC+0",
}
CHILD_SUITE = """
    from budtestlibrary import BudTestCase


    class DemoConsoleTest(BudTestCase):
        def bud_check(self):
            self.assertTrue(support.HOLDS, msg="console check")


    DemoConsoleTest().run()
    """


def child_run(name: str, env: dict | None = None) -> support.Done:
    """Run a one-step passing suite in a child process and return its outcome."""
    directory = support.work_dir(name)
    support.write_suite(directory, "demo_console.py", CHILD_SUITE)
    return support.python(directory / "demo_console.py", cwd=directory, env=env)


class Passing(BudTestCase):
    """Inner case with one passing step."""

    def bud_check(self):
        self.assertTrue(support.HOLDS, msg="ok")


class LoggingIsolation(BudTestCase):
    """The loggers and handlers a case uses and leaves alone."""

    def bud_root_logger_handlers_unchanged(self):
        """The root logger has the same handlers after a run."""
        root = logging.getLogger()
        before = list(root.handlers)
        support.run(Passing())
        support.check(
            self,
            list(root.handlers),
            before,
            "a run leaves the root logger with the same handlers it had before",
            "a run changed the handlers of the root logger",
        )

    def bud_root_logger_level_unchanged(self):
        """The root logger keeps its level after a run."""
        root = logging.getLogger()
        before = root.level
        support.run(Passing())
        support.check(
            self,
            root.level,
            before,
            "a run leaves the root logger at the level it had before",
            "a run changed the level of the root logger",
        )

    def bud_custom_logger_used(self):
        """The case logs through the logger budtestlibrary.<class name>, which has a handler after the run."""

        class LoggerNameTest(BudTestCase):
            def bud_check(self):
                self.assertTrue(support.HOLDS, msg="ok")

        logging.getLogger("budtestlibrary.LoggerNameTest").handlers.clear()
        support.run(LoggerNameTest())
        support.check(
            self,
            len(logging.getLogger("budtestlibrary.LoggerNameTest").handlers),
            1,
            "after a run the logger budtestlibrary.LoggerNameTest has exactly one handler",
            "after a run the logger budtestlibrary.LoggerNameTest does not have exactly one handler",
        )

    def bud_logger_has_its_own_handler(self):
        """After a run the case logger has a StreamHandler."""

        class HandlerTest(BudTestCase):
            def bud_check(self):
                self.assertTrue(support.HOLDS, msg="ok")

        support.run(HandlerTest(), logging.INFO)
        handlers = logging.getLogger("budtestlibrary.HandlerTest").handlers
        support.check(
            self,
            any(isinstance(h, logging.StreamHandler) for h in handlers),
            True,
            "the logger budtestlibrary.HandlerTest writes to the console through a StreamHandler",
            "the logger budtestlibrary.HandlerTest has no StreamHandler",
        )

    def bud_logger_does_not_propagate(self):
        """After a run the case logger does not propagate to the root logger."""

        class PropagationTest(BudTestCase):
            def bud_check(self):
                self.assertTrue(support.HOLDS, msg="ok")

        support.run(PropagationTest(), logging.INFO)
        support.check(
            self,
            logging.getLogger("budtestlibrary.PropagationTest").propagate,
            False,
            "the case logger does not pass its lines on to the root logger (propagate is False)",
            "the case logger passes its lines on to the root logger (propagate is True)",
        )

    def bud_assertion_output_has_colors(self):
        """The console line of an assertion carries ANSI colour codes."""
        done = child_run("colours")
        lines = [line for line in done.err.splitlines() if "console check" in line]
        support.check(
            self,
            len(lines),
            1,
            "the child run prints exactly one console line for the assertion 'console check'",
            f"the child run did not print exactly one console line for 'console check': {done.err!r}",
        )
        support.check_in(
            self,
            "\x1b[",
            lines[0],
            "the console line of the assertion carries ANSI colour codes",
            "the console line of the assertion carries no ANSI colour code",
        )

    def bud_non_utf8_stream_gets_utf8_bytes(self):
        """With a cp1252 stderr the console bytes are UTF-8 and keep the check mark and the rule."""
        done = child_run("cp1252", env={"PYTHONIOENCODING": "cp1252"})
        text = done.raw_err.decode("utf-8")
        support.check(
            self,
            done.code,
            0,
            "the child run with a cp1252 stderr exits 0",
            f"the child run with a cp1252 stderr did not exit 0: {done.err!r}",
        )
        support.check_in(
            self,
            "✓ PASSED",
            text,
            "with a cp1252 stderr the check mark of ✓ PASSED is written as UTF-8",
            "with a cp1252 stderr the check mark of ✓ PASSED is not written as UTF-8",
        )
        support.check_in(
            self,
            "─" * 60,
            text,
            "with a cp1252 stderr the 60-character rule is written as UTF-8",
            "with a cp1252 stderr the 60-character rule is not written as UTF-8",
        )
        support.check_not_in(
            self,
            "\\u2713",
            text,
            "with a cp1252 stderr the check mark is not written as the escape \\u2713",
            "with a cp1252 stderr the check mark is written as the escape \\u2713",
        )

    def bud_utf8_and_text_only_streams_are_unchanged(self):
        """Utf8StreamHandler writes the plain text to a UTF-8 stream and to a text-only stream."""
        utf8 = io.TextIOWrapper(io.BytesIO(), encoding="utf-8", newline="\n")
        text_only = io.StringIO()
        logger = logging.getLogger("budtests.utf8_streams")
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
        support.check(
            self,
            utf8.buffer.getvalue().decode("utf-8"),
            "✓ ok\n",
            "Utf8StreamHandler writes ✓ ok unchanged to a UTF-8 stream",
            "Utf8StreamHandler changed ✓ ok on a UTF-8 stream",
        )
        support.check(
            self,
            text_only.getvalue(),
            "✓ ok\n",
            "Utf8StreamHandler writes ✓ ok unchanged to a text-only stream",
            "Utf8StreamHandler changed ✓ ok on a text-only stream",
        )

    def bud_console_handler_is_utf8_handler(self):
        """After a run the case logger's only handler is a Utf8StreamHandler."""

        class EncodingTest(BudTestCase):
            def bud_check(self):
                self.assertTrue(support.HOLDS, msg="ok")

        support.run(EncodingTest())
        handlers = logging.getLogger("budtestlibrary.EncodingTest").handlers
        support.check(
            self,
            [type(h).__name__ for h in handlers],
            ["Utf8StreamHandler"],
            "after a run the case logger's only handler is a Utf8StreamHandler",
            "after a run the case logger's handlers are not exactly one Utf8StreamHandler",
        )

    def bud_timestamp_uses_utc_offset(self):
        """Every console line of a run starts with date, time and the UTC offset as UTC+H or UTC+H:MM."""
        done = child_run("timestamp", env={"TZ": "Etc/GMT-1"})
        lines = [ANSI.sub("", line) for line in done.err.splitlines() if line]
        support.check(
            self,
            len(lines) > 0,
            True,
            "the child run with TZ=Etc/GMT-1 writes console lines",
            f"the child run with TZ=Etc/GMT-1 wrote no console line: {done.err!r}",
        )
        support.check(
            self,
            [line for line in lines if not TIMESTAMP.match(line)],
            [],
            "every console line starts with date, time and the UTC offset",
            "some console lines do not start with date, time and the UTC offset",
        )

    @parameterized(list(OFFSETS))
    def bud_utc_offset_label(self, zone):
        """The offset label follows the time zone: whole hours as UTC+H, part hours as UTC+H:MM."""
        done = child_run("offset", env={"TZ": zone})
        header = [ANSI.sub("", line) for line in done.err.splitlines() if "STEP INVOCATION" in line]
        support.check(
            self,
            len(header),
            1,
            f"the child run with TZ={zone} prints exactly one STEP INVOCATION line",
            f"the child run with TZ={zone} did not print exactly one STEP INVOCATION line: {done.err!r}",
        )
        match = TIMESTAMP.match(header[0])
        support.check(
            self,
            match.group(1) if match else header[0],
            OFFSETS[zone],
            f"with TZ={zone} the timestamp ends with the offset label {OFFSETS[zone]}",
            f"with TZ={zone} the timestamp does not end with the offset label {OFFSETS[zone]}",
        )
