"""require(): the AssertRequire entry, the raised AssertionError, metadata from keyword arguments, and a failed requirement that stops only its step."""

from budtestlibrary import BudTestCase
from budtestlibrary.budtestcase import AssertionError as BudAssertionError
from tests import support


class Require(BudTestCase):
    """require() and the step it stops."""

    def bud_true_condition_records_a_passed_entry_and_continues(self):
        """require(True) returns True, records a passed AssertRequire entry and the step goes on."""
        returned = []

        def body(tc):
            returned.append(tc.require(True, msg="connection open"))
            returned.append("after")

        result = support.step(body)
        support.check(
            self,
            returned,
            [True, "after"],
            "require(True) returns True and the step goes on to the next line",
            "require(True) did not return True or the step stopped after it",
        )
        support.check(
            self,
            result.assertions[0].assertion_type,
            "AssertRequire",
            "require(True) records an AssertRequire entry",
            "require(True) recorded another entry type than AssertRequire",
        )
        support.check(
            self,
            result.assertions[0].passed,
            True,
            "require(True) records a passed entry",
            "require(True) recorded a failed entry",
        )

    def bud_false_condition_records_a_failed_entry_and_raises(self):
        """require(False) raises budtestlibrary's AssertionError with the message and records a failed entry."""
        raised = []

        def body(tc):
            try:
                tc.require(False, msg="connection open")
            except BudAssertionError as exc:
                raised.append(str(exc))
                raise

        result = support.step(body)
        support.check(
            self,
            raised,
            ["[AssertRequire] EXPECTED: True | ACTUAL: False | MESSAGE: connection open"],
            "require(False) raises budtestlibrary's AssertionError carrying the entry text",
            "require(False) did not raise budtestlibrary's AssertionError with the entry text",
        )
        support.check(
            self,
            result.assertions[0].assertion_type,
            "AssertRequire",
            "require(False) records an AssertRequire entry",
            "require(False) recorded another entry type than AssertRequire",
        )
        support.check(
            self,
            result.assertions[0].passed,
            False,
            "require(False) records a failed entry",
            "require(False) recorded a passed entry",
        )
        support.check(
            self,
            result.passed,
            False,
            "a step whose require(False) fails is reported as failed",
            "a step whose require(False) fails is reported as passed",
        )

    def bud_extra_keyword_arguments_go_to_metadata(self):
        """Extra keyword arguments become the entry's metadata."""
        result = support.step(lambda tc: tc.require(True, msg="m", station="station-01"))
        support.check(
            self,
            result.assertions[0].metadata,
            {"station": "station-01"},
            "require(..., station='station-01') stores station-01 in the entry's metadata",
            "require(..., station='station-01') did not store exactly station-01 in the entry's metadata",
        )

    def bud_failed_requirement_halts_the_step_without_cascading_errors(self):
        """A failed require stops its step before the line that would fail on None; the next step still passes."""

        class StepTest(BudTestCase):
            def __init__(self):
                super().__init__()
                self.reached = False

            def bud_step(self):
                connection = None
                self.require(connection is not None, msg="connection is open")
                self.reached = True
                connection.send(b"ping")

            def bud_next(self):
                self.assertTrue(support.HOLDS, msg="next step runs")

        case = StepTest()
        _, results = support.run(case)
        first, second = results
        support.check(
            self,
            case.reached,
            False,
            "the failed require stops the step before the line after it",
            "the step went on past the failed require",
        )
        support.check(
            self,
            first.passed,
            False,
            "the step with the failed require is reported as failed",
            "the step with the failed require is reported as passed",
        )
        support.check(
            self,
            first.error_message,
            "[AssertRequire] EXPECTED: True | ACTUAL: False | MESSAGE: connection is open",
            "the failed step's error is the require entry text 'connection is open'",
            "the failed step's error is not the require entry text 'connection is open'",
        )
        support.check_not_in(
            self,
            "AttributeError",
            first.traceback or "",
            "the step never reaches connection.send on None, so no AttributeError is raised",
            "the step went on to connection.send on None and raised AttributeError",
        )
        support.check(
            self,
            [a.assertion_type for a in first.assertions],
            ["AssertRequire"],
            "the stopped step recorded only the require entry",
            "the stopped step recorded other entries besides the require entry",
        )
        support.check(
            self,
            second.passed,
            True,
            "the next step bud_next still runs and passes after the stopped step",
            "the next step bud_next did not pass after the stopped step",
        )
