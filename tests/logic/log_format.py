"""Console line format of a run: the step header is one line with the timestamp and the logger name."""

import re

from budtestlibrary import BudTestCase
from tests import support

ANSI = re.compile(r"\x1b\[[0-9;]*m")
TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC[+-]\d{1,2}(?::\d{2})? - ")


class LogFormat(BudTestCase):
    """The console line of a step header."""

    def bud_step_invocation_line_carries_timestamp_and_logger_name(self):
        """In a child run the STEP INVOCATION header is one line that starts with the timestamp and the logger name; no blank or name-only line."""
        directory = support.work_dir("log-format")
        support.write_suite(
            directory,
            "demo_format.py",
            """
            from budtestlibrary import BudTestCase


            class FormatTest(BudTestCase):
                def bud_check(self):
                    self.assertTrue(True, msg="ok")


            FormatTest().run()
            """,
        )
        done = support.python(directory / "demo_format.py", cwd=directory)
        lines = [ANSI.sub("", line) for line in (done.out + done.err).splitlines()]
        header = [line for line in lines if "STEP INVOCATION: bud_check" in line]
        support.check(
            self,
            len(header),
            1,
            "running demo_format.py prints exactly one STEP INVOCATION line for bud_check",
            "running demo_format.py did not print exactly one STEP INVOCATION line for bud_check",
        )
        support.check(
            self,
            bool(TIMESTAMP.match(header[0])),
            True,
            "the STEP INVOCATION line starts with the timestamp",
            f"the STEP INVOCATION line does not start with the timestamp: {header[0]!r}",
        )
        support.check_in(
            self,
            " - budtestlibrary.FormatTest - STEP INVOCATION: bud_check",
            header[0],
            "the logger name budtestlibrary.FormatTest stands between the timestamp and the step text",
            "the logger name budtestlibrary.FormatTest does not stand between the timestamp and the step text",
        )
        support.check(
            self,
            [line for line in lines if line.strip() == ""],
            [],
            "the run of demo_format.py prints no blank line",
            "the run of demo_format.py printed blank lines",
        )
        support.check(
            self,
            [line for line in lines if line.rstrip().endswith("FormatTest -")],
            [],
            "no printed line holds only the timestamp and the logger name",
            "some printed lines hold only the timestamp and the logger name, with no text",
        )
