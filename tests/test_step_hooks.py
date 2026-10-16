"""Tests for the per-step setUp() and tearDown() hooks."""

import logging

from budtestlibrary import BudTestCase


def _run(tc, level=logging.CRITICAL):
    """Run a test case instance at the given log level and return it."""
    tc.set_loglevel(level)
    tc.run()
    return tc


class HookedTest(BudTestCase):
    """Records the order of hooks and steps."""

    def __init__(self):
        super().__init__()
        self.calls = []

    def setUpClass(self):
        self.calls.append("setUpClass")

    def setUp(self):
        self.calls.append("setUp")

    def tearDown(self):
        self.calls.append("tearDown")

    def tearDownClass(self):
        self.calls.append("tearDownClass")

    def bud_one(self):
        self.calls.append("bud_one")
        self.assertTrue(True, msg="one")

    def bud_two(self):
        self.calls.append("bud_two")


class TestHookOrder:
    def test_setup_and_teardown_wrap_each_step(self):
        tc = _run(HookedTest())
        assert tc.calls == [
            "setUpClass",
            "setUp",
            "bud_one",
            "tearDown",
            "setUp",
            "bud_two",
            "tearDown",
            "tearDownClass",
        ]

    def test_default_hooks_do_nothing(self):
        class PlainTest(BudTestCase):
            def bud_step(self):
                self.assertTrue(True)

        tc = _run(PlainTest())
        assert [r.passed for r in tc.get_results()] == [True]


class TestHooksAddNoAssertions:
    def test_assertions_list_holds_only_the_step_assertions(self):
        tc = _run(HookedTest())
        results = {r.method_name: r for r in tc.get_results()}
        assert [a.message for a in results["bud_one"].assertions] == ["one"]
        assert results["bud_two"].assertions == []


class TestHookLogging:
    def test_hook_lines_hidden_at_info(self, caplog):
        tc = HookedTest()
        tc._setup_initial_logging = lambda: None
        tc._logger.propagate = True
        with caplog.at_level(logging.INFO, logger=tc._logger.name):
            tc.set_loglevel(logging.INFO)
            tc.run()
        messages = [r.getMessage() for r in caplog.records]
        assert any("Entering setUpClass" in m for m in messages)
        assert not any("Entering setUp for" in m for m in messages)
        assert not any("Entering tearDown for" in m for m in messages)

    def test_hook_lines_shown_at_debug(self, caplog):
        tc = HookedTest()
        tc._setup_initial_logging = lambda: None
        tc._logger.propagate = True
        with caplog.at_level(logging.DEBUG, logger=tc._logger.name):
            tc.set_loglevel(logging.DEBUG)
            tc.run()
        messages = [r.getMessage() for r in caplog.records]
        assert any("Entering setUp for bud_one" in m for m in messages)
        assert any("Entering tearDown for bud_one" in m for m in messages)


class TestHookFailures:
    def test_teardown_runs_when_the_step_raises(self):
        class RaisingStep(HookedTest):
            def bud_one(self):
                self.calls.append("bud_one")
                raise RuntimeError("step broke")

            def bud_two(self):
                pass

        tc = _run(RaisingStep())
        result = tc.get_results()[0]
        assert tc.calls[:4] == ["setUpClass", "setUp", "bud_one", "tearDown"]
        assert result.passed is False
        assert "step broke" in result.error_message

    def test_setup_failure_skips_the_step_and_runs_teardown(self):
        class FailingSetUp(HookedTest):
            def setUp(self):
                self.calls.append("setUp")
                raise RuntimeError("no device")

            def bud_two(self):
                pass

        tc = _run(FailingSetUp())
        result = tc.get_results()[0]
        assert tc.calls[:3] == ["setUpClass", "setUp", "tearDown"]
        assert "bud_one" not in tc.calls
        assert result.passed is False
        assert result.error_message == "setUp failed: no device"
        assert result.traceback is not None
        assert "no device" in result.traceback

    def test_teardown_failure_is_logged_and_leaves_the_result(self):
        class FailingTearDown(HookedTest):
            def tearDown(self):
                self.calls.append("tearDown")
                raise RuntimeError("cleanup broke")

        tc = _run(FailingTearDown())
        results = tc.get_results()
        assert [r.passed for r in results] == [True, True]
        assert all(r.error_message is None for r in results)
        assert tc.calls.count("tearDown") == 2

    def test_teardown_failure_does_not_hide_a_step_failure(self):
        class BothFail(HookedTest):
            def tearDown(self):
                raise RuntimeError("cleanup broke")

            def bud_one(self):
                raise RuntimeError("step broke")

            def bud_two(self):
                pass

        tc = _run(BothFail())
        result = tc.get_results()[0]
        assert result.passed is False
        assert result.error_message == "step broke"


class TestAssertionsInsideHooks:
    def test_assertions_in_hooks_are_not_recorded_on_the_step(self):
        class AssertingHooks(BudTestCase):
            def setUp(self):
                self.assertTrue(True, msg="in setUp")

            def tearDown(self):
                self.assertTrue(True, msg="in tearDown")

            def bud_step(self):
                self.assertTrue(True, msg="step")

        tc = _run(AssertingHooks())
        assert [a.message for a in tc.get_results()[0].assertions] == ["step"]

    def test_failed_assertion_in_teardown_leaves_a_passing_step_passed(self):
        class FailingTearDownAssert(BudTestCase):
            def tearDown(self):
                self.assertTrue(False, msg="soft")
                self.assertTrue(False, msg="hard", abort_on_fail=True)

            def bud_step(self):
                self.assertTrue(True, msg="step")

        tc = _run(FailingTearDownAssert())
        result = tc.get_results()[0]
        assert result.passed is True
        assert result.error_message is None
        assert [a.message for a in result.assertions] == ["step"]

    def test_soft_failed_assertion_in_setup_is_logged_only(self):
        class SoftSetUpAssert(BudTestCase):
            def setUp(self):
                self.assertTrue(False, msg="soft")

            def bud_step(self):
                self.assertTrue(True, msg="step")

        tc = _run(SoftSetUpAssert())
        result = tc.get_results()[0]
        assert result.passed is True
        assert result.error_message is None
        assert [a.message for a in result.assertions] == ["step"]

    def test_aborting_assertion_in_setup_is_a_setup_failure(self):
        class FailingSetUpAssert(BudTestCase):
            def setUp(self):
                self.assertTrue(False, msg="device present", abort_on_fail=True)

            def bud_step(self):
                self.assertTrue(True, msg="step")

        tc = _run(FailingSetUpAssert())
        result = tc.get_results()[0]
        assert result.passed is False
        assert result.error_message.startswith("setUp failed: ")
        assert "device present" in result.error_message
        assert result.assertions == []
