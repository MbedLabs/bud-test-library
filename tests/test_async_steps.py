"""Tests for async def bud_* steps."""

import asyncio
import logging

from budtestlibrary import BudTestCase, parameterized


def _run(tc):
    """Run a test case instance quietly and return it."""
    tc.set_loglevel(logging.CRITICAL)
    tc.run()
    return tc


class TestAsyncSteps:
    def test_async_step_runs_its_awaited_work(self):
        class AsyncTest(BudTestCase):
            def __init__(self):
                super().__init__()
                self.done = []

            async def bud_wait(self):
                await asyncio.sleep(0)
                self.done.append("after await")

        tc = _run(AsyncTest())
        assert tc.done == ["after await"]
        assert tc.get_results()[0].passed is True

    def test_assertions_in_async_step_are_captured(self):
        class AsyncAssertTest(BudTestCase):
            async def bud_check(self):
                await asyncio.sleep(0)
                self.assertEqual(1, 1, msg="equal")
                self.assertTrue(False, msg="fails")

        result = _run(AsyncAssertTest()).get_results()[0]
        assert [a.message for a in result.assertions] == ["equal", "fails"]
        assert result.passed is False

    def test_unhandled_exception_in_async_step_is_captured(self):
        class AsyncRaiseTest(BudTestCase):
            async def bud_raise(self):
                await asyncio.sleep(0)
                raise RuntimeError("async broke")

        result = _run(AsyncRaiseTest()).get_results()[0]
        assert result.passed is False
        assert result.error_message == "async broke"
        assert "RuntimeError: async broke" in result.traceback
        assert "bud_raise" in result.traceback

    def test_abort_on_fail_in_async_step_stops_it(self):
        class AsyncAbortTest(BudTestCase):
            def __init__(self):
                super().__init__()
                self.reached = False

            async def bud_abort(self):
                self.assertTrue(False, msg="stop", abort_on_fail=True)
                self.reached = True

        tc = _run(AsyncAbortTest())
        result = tc.get_results()[0]
        assert tc.reached is False
        assert result.passed is False
        assert "MESSAGE: stop" in result.error_message

    def test_parameterized_async_step_is_awaited(self):
        class AsyncParamTest(BudTestCase):
            def __init__(self):
                super().__init__()
                self.seen = []

            @parameterized([1, 2])
            async def bud_item(self, item):
                await asyncio.sleep(0)
                self.seen.append(item)

        tc = _run(AsyncParamTest())
        assert tc.seen == [1, 2]
        assert [r.passed for r in tc.get_results()] == [True, True]

    def test_async_step_inside_a_running_loop_fails_with_the_runtime_error(self):
        class AsyncTest(BudTestCase):
            async def bud_wait(self):
                await asyncio.sleep(0)

        async def main():
            return _run(AsyncTest())

        result = asyncio.run(main()).get_results()[0]
        assert result.passed is False
        assert "cannot be called from a running event loop" in result.error_message

    def test_sync_steps_are_unchanged(self):
        class SyncTest(BudTestCase):
            def bud_sync(self):
                self.assertTrue(True)

        assert _run(SyncTest()).get_results()[0].passed is True
