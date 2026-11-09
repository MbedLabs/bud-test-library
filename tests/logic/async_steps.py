"""async def bud_ steps: awaited work, captured assertions and exceptions, abort_on_fail, parameterized async steps, and a case started inside a running event loop."""

import asyncio

from budtestlibrary import BudTestCase, parameterized
from tests import support


class AsyncSteps(BudTestCase):
    """async bud_ steps and what run() records for them."""

    def bud_async_step_runs_its_awaited_work(self):
        """The work after an await runs and the step passes."""

        class AsyncTest(BudTestCase):
            def __init__(self):
                super().__init__()
                self.done = []

            async def bud_wait(self):
                await asyncio.sleep(0)
                self.done.append("after await")

        case = AsyncTest()
        _, results = support.run(case)
        support.check(
            self,
            case.done,
            ["after await"],
            "the async step runs the line after its await",
            "the async step did not run the line after its await",
        )
        support.check(
            self,
            results[0].passed,
            True,
            "the async step that awaits and finishes is reported as passed",
            "the async step that awaits and finishes is reported as failed",
        )

    def bud_assertions_in_async_step_are_captured(self):
        """A passing and a failing assertion after an await are recorded in order and fail the step."""

        class AsyncAssertTest(BudTestCase):
            async def bud_check(self):
                await asyncio.sleep(0)
                self.assertEqual(1, 1, msg="equal")
                self.assertTrue(support.BREAKS, msg="fails")

        _, results = support.run(AsyncAssertTest())
        support.check(
            self,
            [a.message for a in results[0].assertions],
            ["equal", "fails"],
            "both assertions after the await are recorded, 'equal' then 'fails'",
            "the assertions after the await were not recorded as 'equal' then 'fails'",
        )
        support.check(
            self,
            results[0].passed,
            False,
            "the async step with a failing assertion is reported as failed",
            "the async step with a failing assertion is reported as passed",
        )

    def bud_unhandled_exception_in_async_step_is_captured(self):
        """An exception raised after an await fails the step with its text and a traceback naming the step."""

        class AsyncRaiseTest(BudTestCase):
            async def bud_raise(self):
                await asyncio.sleep(0)
                raise RuntimeError("async broke")

        _, results = support.run(AsyncRaiseTest())
        result = results[0]
        support.check(
            self,
            result.passed,
            False,
            "the async step raising RuntimeError after its await is reported as failed",
            "the async step raising RuntimeError after its await is reported as passed",
        )
        support.check(
            self,
            result.error_message,
            "async broke",
            "the failed async step's error message is the exception text 'async broke'",
            "the failed async step's error message is not the exception text 'async broke'",
        )
        support.check_in(
            self,
            "RuntimeError: async broke",
            result.traceback,
            "the traceback holds RuntimeError: async broke",
            "the traceback does not hold RuntimeError: async broke",
        )
        support.check_in(
            self,
            "bud_raise",
            result.traceback,
            "the traceback names the step bud_raise",
            "the traceback does not name the step bud_raise",
        )

    def bud_abort_on_fail_in_async_step_stops_it(self):
        """An aborting assertion stops the async step; the error message holds the assertion's message."""

        class AsyncAbortTest(BudTestCase):
            def __init__(self):
                super().__init__()
                self.reached = False

            async def bud_abort(self):
                self.assertTrue(support.BREAKS, msg="stop", abort_on_fail=True)
                self.reached = True

        case = AsyncAbortTest()
        _, results = support.run(case)
        support.check(
            self,
            case.reached,
            False,
            "an aborting assertion stops the async step before its next line",
            "the async step went on past the aborting assertion",
        )
        support.check(
            self,
            results[0].passed,
            False,
            "the async step stopped by an aborting assertion is reported as failed",
            "the async step stopped by an aborting assertion is reported as passed",
        )
        support.check_in(
            self,
            "MESSAGE: stop",
            results[0].error_message,
            "the step's error message holds the aborting assertion's message 'stop'",
            "the step's error message does not hold the aborting assertion's message 'stop'",
        )

    def bud_parameterized_async_step_is_awaited(self):
        """Each item of a parameterized async step is awaited, in order, as its own passing step."""

        class AsyncParamTest(BudTestCase):
            def __init__(self):
                super().__init__()
                self.seen = []

            @parameterized([1, 2])
            async def bud_item(self, item):
                await asyncio.sleep(0)
                self.seen.append(item)

        case = AsyncParamTest()
        _, results = support.run(case)
        support.check(
            self,
            case.seen,
            [1, 2],
            "the parameterized async step awaits item 1, then item 2",
            "the parameterized async step did not await items 1 and 2 in order",
        )
        support.check(
            self,
            [r.passed for r in results],
            [True, True],
            "each item of the parameterized async step is reported as its own passed step",
            "the parameterized async step's items were not reported as two passed steps",
        )

    async def bud_async_step_inside_a_running_loop_fails_with_the_runtime_error(self):
        """A case run from inside a running event loop fails its async step with asyncio.run()'s RuntimeError."""

        class AsyncTest(BudTestCase):
            async def bud_wait(self):
                await asyncio.sleep(0)

        _, results = support.run(AsyncTest())
        support.check(
            self,
            results[0].passed,
            False,
            "an async step run from inside a running event loop is reported as failed",
            "an async step run from inside a running event loop is reported as passed",
        )
        support.check_in(
            self,
            "cannot be called from a running event loop",
            results[0].error_message,
            "the error says asyncio.run() cannot be called from a running event loop",
            "the error does not say asyncio.run() cannot be called from a running event loop",
        )
