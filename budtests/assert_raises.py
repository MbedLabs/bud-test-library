"""assertRaises: the AssertRaises entry, subclasses, a missing or different exception, abort_on_fail, exceptions that pass through, the call site."""

import asyncio
import inspect
import sys

import support

from budtestlibrary import BudTestCase, parameterized
from budtestlibrary.budtestcase import AssertionError as BudAssertionError

PASS_THROUGH = {
    "KeyboardInterrupt": KeyboardInterrupt,
    "SystemExit": SystemExit,
    "CancelledError": asyncio.CancelledError,
    "GeneratorExit": GeneratorExit,
}


class ReachTest(BudTestCase):
    """Inner case whose bud_step runs the block given to it and notes the lines it reached."""

    def __init__(self, block):
        super().__init__()
        self.block = block
        self.reached = []

    def bud_step(self):
        self.block(self)


class AssertRaises(BudTestCase):
    """assertRaises on expected, subclassed, missing and unexpected exceptions."""

    def bud_expected_exception_passes_and_is_suppressed(self):
        """The expected exception is suppressed and recorded as a passed AssertRaises entry."""

        def block(tc):
            with tc.assertRaises(ValueError, msg="bad value rejected"):
                raise ValueError("bad value")
            tc.reached.append("after")

        case = ReachTest(block)
        _, results = support.run(case)
        entries = results[0].assertions
        support.check(
            self,
            len(entries),
            1,
            "assertRaises(ValueError) around a raising block records exactly one entry",
            "assertRaises(ValueError) did not record exactly one entry",
        )
        support.check(
            self,
            entries[0].assertion_type,
            "AssertRaises",
            "the entry is an AssertRaises entry",
            "the entry is of another type than AssertRaises",
        )
        support.check(
            self,
            entries[0].passed,
            True,
            "the raised ValueError gives a passed entry",
            "the raised ValueError gave a failed entry",
        )
        support.check(
            self,
            entries[0].expected,
            "ValueError",
            "the entry's expected value is the class name ValueError",
            "the entry's expected value is not the class name ValueError",
        )
        support.check(
            self,
            entries[0].actual,
            "ValueError: bad value",
            "the entry's actual value is the raised exception ValueError: bad value",
            "the entry's actual value is not ValueError: bad value",
        )
        support.check(
            self,
            entries[0].message,
            "bad value rejected",
            "the entry keeps the message bad value rejected",
            "the entry did not keep the message bad value rejected",
        )
        support.check(
            self,
            case.reached,
            ["after"],
            "the step goes on after the with block",
            "the step did not go on after the with block",
        )
        support.check(
            self,
            results[0].passed,
            True,
            "the step with the suppressed ValueError passes",
            "the step with the suppressed ValueError failed",
        )

    def bud_subclass_of_expected_exception_passes(self):
        """A subclass of the expected exception passes."""

        def block(tc):
            with tc.assertRaises(LookupError):
                raise KeyError("k")

        _, results = support.run(ReachTest(block))
        support.check(
            self,
            results[0].assertions[0].passed,
            True,
            "KeyError passes assertRaises(LookupError), as a subclass",
            "KeyError did not pass assertRaises(LookupError)",
        )
        support.check(
            self,
            results[0].assertions[0].actual,
            "KeyError: 'k'",
            "the entry's actual value names the subclass KeyError: 'k'",
            "the entry's actual value does not name KeyError: 'k'",
        )

    def bud_no_exception_fails(self):
        """A block that raises nothing records a failed entry."""

        def block(tc):
            with tc.assertRaises(ValueError):
                pass

        _, results = support.run(ReachTest(block))
        entry = results[0].assertions[0]
        support.check(
            self,
            entry.passed,
            False,
            "a block that raises nothing gives a failed entry",
            "a block that raises nothing gave a passed entry",
        )
        support.check(
            self,
            entry.expected,
            "ValueError",
            "the entry's expected value is ValueError",
            "the entry's expected value is not ValueError",
        )
        support.check(
            self,
            entry.actual,
            "no exception raised",
            "the entry's actual value says no exception raised",
            "the entry's actual value does not say no exception raised",
        )
        support.check(
            self,
            results[0].passed,
            False,
            "the step whose block raised nothing is reported as failed",
            "the step whose block raised nothing is reported as passed",
        )

    def bud_unexpected_exception_fails_and_is_suppressed(self):
        """A different exception fails the entry, is suppressed, and the step goes on."""

        def block(tc):
            with tc.assertRaises(ValueError):
                raise KeyError("wrong")
            tc.reached.append("after")

        case = ReachTest(block)
        _, results = support.run(case)
        entry = results[0].assertions[0]
        support.check(
            self,
            entry.passed,
            False,
            "a block raising KeyError instead of ValueError gives a failed entry",
            "a block raising KeyError instead of ValueError gave a passed entry",
        )
        support.check(
            self,
            entry.expected,
            "ValueError",
            "the entry's expected value is ValueError",
            "the entry's expected value is not ValueError",
        )
        support.check(
            self,
            entry.actual,
            "KeyError: 'wrong'",
            "the entry's actual value is the raised KeyError: 'wrong'",
            "the entry's actual value is not KeyError: 'wrong'",
        )
        support.check(
            self,
            case.reached,
            ["after"],
            "the KeyError is suppressed and the code after the block runs",
            "the code after the block did not run",
        )
        support.check(
            self,
            results[0].passed,
            False,
            "the step with the wrong exception is reported as failed",
            "the step with the wrong exception is reported as passed",
        )

    def bud_abort_on_fail_raises_assertion_error(self):
        """abort_on_fail=True with no exception raises budtestlibrary's AssertionError and stops the step."""

        def block(tc):
            try:
                with tc.assertRaises(ValueError, abort_on_fail=True):
                    pass
            except BudAssertionError as exc:
                tc.reached.append(str(exc))
                raise
            tc.reached.append("after")

        case = ReachTest(block)
        _, results = support.run(case)
        support.check(
            self,
            len(case.reached),
            1,
            "abort_on_fail=True with no exception raises once and nothing after it runs",
            "abort_on_fail=True did not stop the step at the with block",
        )
        support.check(
            self,
            case.reached[0][: len("[AssertRaises] EXPECTED: ValueError")],
            "[AssertRaises] EXPECTED: ValueError",
            "the raised AssertionError text starts with the entry [AssertRaises] EXPECTED: ValueError",
            "the raised AssertionError text does not start with the entry",
        )
        support.check(
            self,
            results[0].passed,
            False,
            "the aborted step is reported as failed",
            "the aborted step is reported as passed",
        )
        support.check(
            self,
            results[0].assertions[0].passed,
            False,
            "the aborted step's entry is failed",
            "the aborted step's entry is passed",
        )
        support.check(
            self,
            results[0].error_message[: len("[AssertRaises] EXPECTED: ValueError")],
            "[AssertRaises] EXPECTED: ValueError",
            "the step's error message starts with the entry [AssertRaises] EXPECTED: ValueError",
            "the step's error message does not start with the entry",
        )

    def bud_abort_on_fail_does_not_raise_when_expected_is_raised(self):
        """abort_on_fail=True with the expected exception passes and the step continues."""

        def block(tc):
            with tc.assertRaises(ValueError, abort_on_fail=True):
                raise ValueError("ok")
            tc.reached.append("after")

        case = ReachTest(block)
        _, results = support.run(case)
        support.check(
            self,
            results[0].assertions[0].passed,
            True,
            "abort_on_fail=True with the expected exception gives a passed entry",
            "abort_on_fail=True with the expected exception gave a failed entry",
        )
        support.check(
            self,
            case.reached,
            ["after"],
            "the step goes on after the passing aborting block",
            "the step did not go on after the passing aborting block",
        )

    @parameterized(list(PASS_THROUGH))
    def bud_unexpected_base_exception_passes_through(self, name):
        """An unexpected exception that is not an Exception subclass leaves the block and records no entry."""
        exception = PASS_THROUGH[name]

        def block(tc):
            try:
                with tc.assertRaises(ValueError):
                    raise exception()
            except exception:
                tc.reached.append("escaped")

        case = ReachTest(block)
        _, results = support.run(case)
        support.check(
            self,
            case.reached,
            ["escaped"],
            f"{name} is not caught by assertRaises(ValueError) and leaves the block",
            f"{name} was caught inside assertRaises(ValueError)",
        )
        support.check(
            self,
            results[0].assertions,
            [],
            f"no entry is recorded for {name}",
            f"an entry was recorded for {name}",
        )

    def bud_expected_system_exit_passes(self):
        """assertRaises(SystemExit) around exit code 2 passes with actual SystemExit: 2."""

        def block(tc):
            with tc.assertRaises(SystemExit, msg="cli exits"):
                sys.exit(2)

        _, results = support.run(ReachTest(block))
        support.check(
            self,
            results[0].assertions[0].passed,
            True,
            "assertRaises(SystemExit) around exit code 2 gives a passed entry",
            "assertRaises(SystemExit) around exit code 2 gave a failed entry",
        )
        support.check(
            self,
            results[0].assertions[0].actual,
            "SystemExit: 2",
            "the entry's actual value is SystemExit: 2",
            "the entry's actual value is not SystemExit: 2",
        )

    def bud_entry_points_at_the_test_code(self):
        """The entry's source file, function and line are those of the with statement in the step."""
        lines = []

        class SourceTest(BudTestCase):
            def bud_check(self):
                lines.append(inspect.currentframe().f_lineno + 1)
                with self.assertRaises(ValueError):
                    raise ValueError("x")

        _, results = support.run(SourceTest())
        entry = results[0].assertions[0]
        support.check(
            self,
            entry.source_file,
            __file__,
            "the entry records this suite file as its source",
            "the entry records another source file than this suite",
        )
        support.check(
            self,
            entry.source_function,
            "bud_check",
            "the entry records the step bud_check as its source function",
            "the entry records another source function than bud_check",
        )
        support.check(
            self,
            entry.source_line,
            lines[0],
            "the entry records the line of the with statement",
            "the entry records another line than the with statement",
        )

    def bud_step_fails_when_nothing_is_raised_and_continues(self):
        """Through run(): the step fails, later code runs, the error message holds the entry text."""

        def block(tc):
            with tc.assertRaises(ValueError):
                pass
            tc.reached.append("after")

        case = ReachTest(block)
        _, results = support.run(case)
        support.check(
            self,
            case.reached,
            ["after"],
            "through run() the code after the failed block still runs",
            "through run() the code after the failed block did not run",
        )
        support.check(
            self,
            results[0].passed,
            False,
            "through run() the step with the failed block is reported as failed",
            "through run() the step with the failed block is reported as passed",
        )
        support.check_in(
            self,
            "[AssertRaises] EXPECTED: ValueError | ACTUAL: no exception raised",
            results[0].error_message,
            "through run() the step's error message holds the entry text",
            "through run() the step's error message does not hold the entry text",
        )
