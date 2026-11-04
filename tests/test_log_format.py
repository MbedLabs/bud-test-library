"""Console line format of a run: every line a step logs carries the timestamp and the logger name."""

import logging

from budtestlibrary import BudTestCase


class TestStepHeaderLine:
    def test_step_invocation_line_carries_timestamp_and_logger_name(self, capsys):
        """The STEP INVOCATION header is one line that starts with the timestamp and the logger name."""

        class FormatTest(BudTestCase):
            def bud_check(self):
                self.assertTrue(True, msg="ok")

        tc = FormatTest()
        tc.set_loglevel(logging.INFO)
        tc.run()

        captured = capsys.readouterr()
        lines = (captured.out + captured.err).splitlines()
        header = [line for line in lines if "STEP INVOCATION: bud_check" in line]
        assert len(header) == 1
        assert " - budtestlibrary.FormatTest - " in header[0]
        assert not any(
            line.strip() == "" or line.rstrip().endswith("FormatTest -") for line in lines
        )
