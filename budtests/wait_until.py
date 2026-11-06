"""waitUntil(): met and unmet conditions, abort_on_fail, the timing metadata, raising conditions and the call site."""

import inspect

import support

from budtestlibrary import BudTestCase
from budtestlibrary.budtestcase import AssertionError as BudAssertionError


def true_after(calls: int):
    """Return a condition that becomes true on the given call number, and its call counter."""
    count = {"n": 0}

    def condition():
        count["n"] += 1
        return count["n"] >= calls

    return condition, count


class WaitUntil(BudTestCase):
    """waitUntil() and the result it records."""

    def bud_condition_met_within_timeout_returns_true_and_passes(self):
        """A condition true on the third call: True returned, a passed AssertWaitUntil entry, three calls."""
        condition, count = true_after(3)
        returned = []
        result = support.step(
            lambda tc: returned.append(
                tc.waitUntil(condition, timeout=2.0, poll_interval=0.01, msg="ready")
            )
        )
        entry = result.assertions[0]
        support.check(
            self,
            returned,
            [True],
            "waitUntil returns True when the condition becomes true on the third call",
            "waitUntil did not return True although the condition became true on the third call",
        )
        support.check(
            self,
            entry.assertion_type,
            "AssertWaitUntil",
            "waitUntil records an AssertWaitUntil entry",
            "waitUntil recorded another entry type than AssertWaitUntil",
        )
        support.check(
            self,
            entry.passed,
            True,
            "the met condition gives a passed entry",
            "the met condition gave a failed entry",
        )
        support.check(
            self,
            entry.message,
            "ready",
            "the entry keeps the message ready",
            "the entry did not keep the message ready",
        )
        support.check(
            self,
            count["n"],
            3,
            "waitUntil stops polling after the third call, when the condition is met",
            "waitUntil did not call the condition exactly three times",
        )

    def bud_condition_never_met_returns_false_and_fails(self):
        """A condition never true: False returned, a failed entry, at least the timeout elapsed."""
        returned = []
        result = support.step(
            lambda tc: returned.append(
                tc.waitUntil(lambda: False, timeout=0.05, poll_interval=0.01)
            )
        )
        entry = result.assertions[0]
        support.check(
            self,
            returned,
            [False],
            "waitUntil returns False when the condition is never met within 0.05 s",
            "waitUntil did not return False for a condition that is never met",
        )
        support.check(
            self,
            entry.passed,
            False,
            "the unmet condition gives a failed entry",
            "the unmet condition gave a passed entry",
        )
        support.check(
            self,
            entry.metadata["elapsed_seconds"] >= 0.05,
            True,
            f"waitUntil waited at least the 0.05 s timeout ({entry.metadata['elapsed_seconds']} s)",
            f"waitUntil gave up before the 0.05 s timeout ({entry.metadata['elapsed_seconds']} s)",
        )
        support.check(
            self,
            result.passed,
            False,
            "the step with the unmet waitUntil is reported as failed",
            "the step with the unmet waitUntil is reported as passed",
        )

    def bud_abort_on_fail_raises_assertion_error(self):
        """On timeout with abort_on_fail=True the AssertionError names AssertWaitUntil and the step stops."""
        seen = []

        def body(tc):
            try:
                tc.waitUntil(lambda: False, timeout=0.02, poll_interval=0.01, abort_on_fail=True)
            except BudAssertionError as exc:
                seen.append(str(exc))
                raise
            seen.append("after")

        result = support.step(body)
        support.check(
            self,
            len(seen),
            1,
            "waitUntil with abort_on_fail=True raises once on timeout and the step stops",
            "waitUntil with abort_on_fail=True did not raise exactly once on timeout",
        )
        support.check(
            self,
            seen[0][: len("[AssertWaitUntil]")],
            "[AssertWaitUntil]",
            "the raised AssertionError text starts with [AssertWaitUntil]",
            "the raised AssertionError text does not start with [AssertWaitUntil]",
        )
        support.check(
            self,
            result.assertions[0].passed,
            False,
            "the timed-out waitUntil records a failed entry",
            "the timed-out waitUntil recorded a passed entry",
        )
        support.check(
            self,
            result.passed,
            False,
            "the step stopped by the aborting waitUntil is reported as failed",
            "the step stopped by the aborting waitUntil is reported as passed",
        )

    def bud_metadata_records_elapsed_time_and_settings(self):
        """The metadata holds exactly elapsed_seconds, timeout_seconds and poll_interval_seconds."""
        metadata = (
            support.step(lambda tc: tc.waitUntil(lambda: True, timeout=1.5, poll_interval=0.25))
            .assertions[0]
            .metadata
        )
        support.check(
            self,
            sorted(metadata),
            ["elapsed_seconds", "poll_interval_seconds", "timeout_seconds"],
            "the waitUntil entry's metadata holds exactly elapsed_seconds, poll_interval_seconds and timeout_seconds",
            "the waitUntil entry's metadata does not hold exactly elapsed_seconds, poll_interval_seconds and timeout_seconds",
        )
        support.check(
            self,
            metadata["timeout_seconds"],
            1.5,
            "the metadata records the timeout of 1.5 s",
            "the metadata does not record the timeout of 1.5 s",
        )
        support.check(
            self,
            metadata["poll_interval_seconds"],
            0.25,
            "the metadata records the poll interval of 0.25 s",
            "the metadata does not record the poll interval of 0.25 s",
        )
        support.check(
            self,
            0 <= metadata["elapsed_seconds"] < 1.5,
            True,
            f"the elapsed time {metadata['elapsed_seconds']} s lies within the 1.5 s timeout",
            f"the elapsed time {metadata['elapsed_seconds']} s does not lie within the 1.5 s timeout",
        )

    def bud_raising_condition_keeps_polling_until_true(self):
        """A condition that raises twice and then returns True passes without last_exception."""
        count = {"n": 0}

        def condition():
            count["n"] += 1
            if count["n"] < 3:
                raise ConnectionError("not up yet")
            return True

        returned = []
        entry = support.step(
            lambda tc: returned.append(tc.waitUntil(condition, timeout=2.0, poll_interval=0.01))
        ).assertions[0]
        support.check(
            self,
            returned,
            [True],
            "waitUntil returns True once the condition stops raising and returns True",
            "waitUntil did not return True for a condition that raises twice and then returns True",
        )
        support.check(
            self,
            entry.passed,
            True,
            "the condition that recovered gives a passed entry",
            "the condition that recovered gave a failed entry",
        )
        support.check_not_in(
            self,
            "last_exception",
            list(entry.metadata),
            "a met condition records no last_exception",
            "a met condition still records a last_exception",
        )

    def bud_last_exception_recorded_on_timeout(self):
        """A condition that always raises: False returned and the last exception recorded."""

        def condition():
            raise ConnectionError("not up yet")

        returned = []
        entry = support.step(
            lambda tc: returned.append(tc.waitUntil(condition, timeout=0.03, poll_interval=0.01))
        ).assertions[0]
        support.check(
            self,
            returned,
            [False],
            "waitUntil returns False for a condition that always raises",
            "waitUntil did not return False for a condition that always raises",
        )
        support.check(
            self,
            entry.metadata.get("last_exception"),
            "ConnectionError: not up yet",
            "the metadata records the last exception ConnectionError: not up yet",
            "the metadata does not record the last exception ConnectionError: not up yet",
        )

    def bud_entry_points_at_the_test_code(self):
        """The entry's source file, function and line are the step's call, not the library's."""
        lines = []

        class SourceTest(BudTestCase):
            def bud_wait(self):
                lines.append(inspect.currentframe().f_lineno + 1)
                self.waitUntil(lambda: True, timeout=0.1)

        _, results = support.run(SourceTest())
        entry = results[0].assertions[0]
        support.check(
            self,
            entry.source_file,
            __file__,
            "the waitUntil entry records this suite file, not the library's",
            "the waitUntil entry records another file than this suite file",
        )
        support.check(
            self,
            entry.source_function,
            "bud_wait",
            "the waitUntil entry records the step bud_wait as its source function",
            "the waitUntil entry records another source function than bud_wait",
        )
        support.check(
            self,
            entry.source_line,
            lines[0],
            "the waitUntil entry records the line of the waitUntil call",
            "the waitUntil entry records another line than the waitUntil call",
        )
