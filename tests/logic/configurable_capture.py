"""CAPTURE_SOURCE_PATH and CAPTURE_TRACEBACK through run(): source fields recorded by default, suppressed when off, their to_dict() keys, and the step traceback of a raising step."""

import inspect

from budtestlibrary import BudTestCase
from tests import support


class ConfigurableCapture(BudTestCase):
    """The source and traceback capture switches through run()."""

    def bud_source_captured_by_default(self):
        """By default the entry records the suite file, the calling line and the step name."""
        lines = []

        class SourceTest(BudTestCase):
            def bud_check(self):
                lines.append(inspect.currentframe().f_lineno + 1)
                self.assertTrue(support.HOLDS, msg="captured")

        _, results = support.run(SourceTest())
        entry = results[0].assertions[0]
        support.check(
            self,
            entry.source_file,
            __file__,
            "the entry records this suite file as its source file",
            "the entry records another source file than this suite file",
        )
        support.check(
            self,
            entry.source_line,
            lines[0],
            "the entry records the line of the assertTrue call as its source line",
            "the entry records another source line than the line of the assertTrue call",
        )
        support.check(
            self,
            entry.source_function,
            "bud_check",
            "the entry records bud_check as its source function",
            "the entry records another source function than bud_check",
        )

    def bud_source_suppressed_when_capture_disabled(self):
        """With CAPTURE_SOURCE_PATH = False the three source fields are None."""
        entry = support.step(
            lambda tc: tc.assertTrue(support.HOLDS, msg="not captured"), CAPTURE_SOURCE_PATH=False
        ).assertions[0]
        support.check(
            self,
            (entry.source_file, entry.source_line, entry.source_function),
            (None, None, None),
            "with CAPTURE_SOURCE_PATH = False the entry has no source file, line or function",
            "with CAPTURE_SOURCE_PATH = False the entry still records a source file, line or function",
        )

    def bud_source_keys_are_none_in_dict_when_capture_disabled(self):
        """With CAPTURE_SOURCE_PATH = False, to_dict() has the three source keys with value None."""
        d = (
            support.step(
                lambda tc: tc.assertTrue(support.HOLDS, msg="no source"), CAPTURE_SOURCE_PATH=False
            )
            .assertions[0]
            .to_dict()
        )
        for key in ("source_file", "source_line", "source_function"):
            support.check_in(
                self,
                key,
                list(d),
                f"to_dict() keeps the key {key} when CAPTURE_SOURCE_PATH = False",
                f"to_dict() drops the key {key} when CAPTURE_SOURCE_PATH = False",
            )
            support.check(
                self,
                d[key],
                None,
                f"to_dict() gives {key} the value None when CAPTURE_SOURCE_PATH = False",
                f"to_dict() gives {key} a value other than None when CAPTURE_SOURCE_PATH = False",
            )

    def bud_method_traceback_suppressed_when_capture_disabled(self):
        """A raising step has a traceback by default and none with CAPTURE_TRACEBACK = False; the error text is kept."""

        def body(tc):
            raise RuntimeError("boom")

        with_traceback = support.step(body)
        without = support.step(body, CAPTURE_TRACEBACK=False)
        support.check_in(
            self,
            "RuntimeError: boom",
            with_traceback.traceback or "",
            "a step raising RuntimeError('boom') records a traceback by default",
            "a step raising RuntimeError('boom') records no traceback by default",
        )
        support.check(
            self,
            without.traceback,
            None,
            "with CAPTURE_TRACEBACK = False the raising step records no traceback",
            "with CAPTURE_TRACEBACK = False the raising step still records a traceback",
        )
        support.check(
            self,
            without.error_message,
            "boom",
            "with CAPTURE_TRACEBACK = False the raising step keeps its error message 'boom'",
            "with CAPTURE_TRACEBACK = False the raising step lost its error message 'boom'",
        )
