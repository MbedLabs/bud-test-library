"""Assertion call site: source file, line and function of the caller, code context and traceback of a failed assertion, the two capture switches, and no inspect.stack()."""

import inspect

import support

from budtestlibrary import BudTestCase


def line_after() -> int:
    """Return the line number following the caller's current line."""
    return inspect.currentframe().f_back.f_lineno + 1


class Callsite(BudTestCase):
    """The call site recorded for passing and failing assertions."""

    def bud_direct_assertion_records_the_calling_line(self):
        """assertTrue records the suite file, the calling line and the step name."""
        lines = []

        class DirectTest(BudTestCase):
            def bud_direct(self):
                lines.append(line_after())
                self.assertTrue(support.HOLDS, msg="direct")

        _, results = support.run(DirectTest())
        entry = results[0].assertions[0]
        support.check(
            self,
            entry.source_file,
            __file__,
            "a direct assertion records this suite file as its source file",
            "a direct assertion records another source file than this suite file",
        )
        support.check(
            self,
            entry.source_line,
            lines[0],
            "a direct assertion records the line of its call",
            "a direct assertion records another line than the line of its call",
        )
        support.check(
            self,
            entry.source_function,
            "bud_direct",
            "a direct assertion records bud_direct as its source function",
            "a direct assertion records another source function than bud_direct",
        )

    def bud_wrapper_assertions_record_the_test_line(self):
        """assertEqual and assertInTolerance record the step's lines, not the library's."""
        lines = []

        class WrapperTest(BudTestCase):
            def bud_wrappers(self):
                lines.append(line_after())
                self.assertEqual(1, 1)
                self.assertInTolerance(1.0, expected=1.0, absolute_tolerance=0.1)

        _, results = support.run(WrapperTest())
        first, second = results[0].assertions
        support.check(
            self,
            (first.source_file, first.source_line),
            (__file__, lines[0]),
            "assertEqual records the step's file and line, not the library's",
            "assertEqual records the library's file or line instead of the step's",
        )
        support.check(
            self,
            (second.source_file, second.source_line),
            (__file__, lines[0] + 1),
            "assertInTolerance records the step's file and line, not the library's",
            "assertInTolerance records the library's file or line instead of the step's",
        )

    def bud_skip_records_the_calling_line(self):
        """skipAssert records the calling line."""
        lines = []

        class SkipTest(BudTestCase):
            def bud_skip(self):
                lines.append(line_after())
                self.skipAssert("not applicable")

        _, results = support.run(SkipTest())
        support.check(
            self,
            results[0].assertions[0].source_line,
            lines[0],
            "skipAssert records the line of its call in the step",
            "skipAssert records another line than the line of its call",
        )

    def bud_passing_assertion_has_no_code_context_or_traceback(self):
        """A passing entry carries neither code context nor traceback."""
        entry = support.step(lambda tc: tc.assertTrue(support.HOLDS, msg="passes")).assertions[0]
        support.check(
            self,
            entry.code_context,
            None,
            "a passing entry carries no code context",
            "a passing entry carries a code context",
        )
        support.check(
            self,
            entry.traceback,
            None,
            "a passing entry carries no traceback",
            "a passing entry carries a traceback",
        )

    def bud_failing_assertion_has_code_context_and_traceback(self):
        """A failed entry carries the calling source line and a traceback that names the step and ends in assertTrue."""

        class FailTest(BudTestCase):
            def bud_fails(self):
                self.assertTrue(support.BREAKS, msg="fails here")

        _, results = support.run(FailTest())
        entry = results[0].assertions[0]
        support.check_in(
            self,
            'self.assertTrue(support.BREAKS, msg="fails here")',
            entry.code_context or "",
            'the failed entry\'s code context holds the calling line self.assertTrue(support.BREAKS, msg="fails here")',
            "the failed entry's code context does not hold the calling line",
        )
        support.check_in(
            self,
            "bud_fails",
            entry.traceback or "",
            "the failed entry's traceback names the step bud_fails",
            "the failed entry's traceback does not name the step bud_fails",
        )
        support.check_in(
            self,
            "in assertTrue",
            (entry.traceback or "\n").splitlines()[-2],
            "the failed entry's traceback ends in assertTrue",
            "the failed entry's traceback does not end in assertTrue",
        )

    def bud_source_path_off_disables_frame_inspection(self):
        """CAPTURE_SOURCE_PATH=False: no file, line, function or code context; the traceback is kept."""
        entry = support.step(
            lambda tc: tc.assertTrue(support.BREAKS, msg="fails"), CAPTURE_SOURCE_PATH=False
        ).assertions[0]
        support.check(
            self,
            entry.source_file,
            None,
            "with CAPTURE_SOURCE_PATH=False the entry records no source file",
            "with CAPTURE_SOURCE_PATH=False the entry still records a source file",
        )
        support.check(
            self,
            entry.source_line,
            None,
            "with CAPTURE_SOURCE_PATH=False the entry records no source line",
            "with CAPTURE_SOURCE_PATH=False the entry still records a source line",
        )
        support.check(
            self,
            entry.source_function,
            None,
            "with CAPTURE_SOURCE_PATH=False the entry records no source function",
            "with CAPTURE_SOURCE_PATH=False the entry still records a source function",
        )
        support.check(
            self,
            entry.code_context,
            None,
            "with CAPTURE_SOURCE_PATH=False the entry records no code context",
            "with CAPTURE_SOURCE_PATH=False the entry still records a code context",
        )
        support.check(
            self,
            entry.traceback is not None,
            True,
            "with CAPTURE_SOURCE_PATH=False the failed entry keeps its traceback",
            "with CAPTURE_SOURCE_PATH=False the failed entry lost its traceback",
        )

    def bud_traceback_off_keeps_code_context(self):
        """CAPTURE_TRACEBACK=False: no traceback; the code context is kept."""
        entry = support.step(
            lambda tc: tc.assertTrue(support.BREAKS, msg="fails"), CAPTURE_TRACEBACK=False
        ).assertions[0]
        support.check(
            self,
            entry.traceback,
            None,
            "with CAPTURE_TRACEBACK=False the failed entry records no traceback",
            "with CAPTURE_TRACEBACK=False the failed entry still records a traceback",
        )
        support.check(
            self,
            entry.code_context is not None,
            True,
            "with CAPTURE_TRACEBACK=False the failed entry keeps its code context",
            "with CAPTURE_TRACEBACK=False the failed entry lost its code context",
        )

    def bud_inspect_stack_is_not_called(self):
        """With inspect.stack() raising, a passing and a failing assertion are both recorded."""

        def forbidden(*args, **kwargs):
            raise RuntimeError("inspect.stack called")

        def body(tc):
            tc.assertTrue(support.HOLDS)
            tc.assertTrue(support.BREAKS)

        saved = inspect.stack
        inspect.stack = forbidden
        try:
            result = support.step(body)
        finally:
            inspect.stack = saved
        support.check(
            self,
            [a.passed for a in result.assertions],
            [True, False],
            "with inspect.stack() raising, the passing and the failing assertion are both recorded",
            "with inspect.stack() raising, the passing and failing assertions were not both recorded",
        )
        support.check(
            self,
            result.error_message is not None and "inspect.stack" not in result.error_message,
            True,
            "the step's error comes from the failed assertion, not from inspect.stack()",
            "the step's error is missing or comes from inspect.stack()",
        )
