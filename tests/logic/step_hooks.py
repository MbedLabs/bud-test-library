"""Per-step setUp() and tearDown(): order around each step, their DEBUG log lines, failures in either hook, and assertions made inside them."""

import logging
import re

from budtestlibrary import BudTestCase
from tests import support

ANSI = re.compile(r"\x1b\[[0-9;]*m")


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
        self.assertTrue(support.HOLDS, msg="one")

    def bud_two(self):
        self.calls.append("bud_two")


class StepHooks(BudTestCase):
    """Per-step setUp() and tearDown() around each step."""

    def bud_setup_and_teardown_wrap_each_step(self):
        """setUp and tearDown run around each step, inside setUpClass and tearDownClass."""
        case = HookedTest()
        support.run(case)
        want = [
            "setUpClass",
            "setUp",
            "bud_one",
            "tearDown",
            "setUp",
            "bud_two",
            "tearDown",
            "tearDownClass",
        ]
        support.check(
            self,
            case.calls,
            want,
            "setUp and tearDown run around each step, inside setUpClass and tearDownClass",
            "setUp and tearDown did not run around each step inside setUpClass and tearDownClass",
        )

    def bud_hook_lines_hidden_at_info(self):
        """At INFO the console shows Entering setUpClass but no per-step setUp or tearDown line."""
        _, _, console = support.run_capturing(HookedTest(), logging.INFO)
        support.check_in(
            self,
            "Entering setUpClass",
            console,
            "at INFO the console shows Entering setUpClass",
            "at INFO the console does not show Entering setUpClass",
        )
        support.check_not_in(
            self,
            "Entering setUp for",
            console,
            "at INFO the console shows no per-step setUp line",
            "at INFO the console shows per-step setUp lines",
        )
        support.check_not_in(
            self,
            "Entering tearDown for",
            console,
            "at INFO the console shows no per-step tearDown line",
            "at INFO the console shows per-step tearDown lines",
        )

    def bud_hook_lines_shown_at_debug(self):
        """At DEBUG the console shows the setUp and tearDown lines of each step."""
        _, _, console = support.run_capturing(HookedTest(), logging.DEBUG)
        support.check_in(
            self,
            "Entering setUp for bud_one",
            console,
            "at DEBUG the console shows Entering setUp for bud_one",
            "at DEBUG the console does not show Entering setUp for bud_one",
        )
        support.check_in(
            self,
            "Entering tearDown for bud_one",
            console,
            "at DEBUG the console shows Entering tearDown for bud_one",
            "at DEBUG the console does not show Entering tearDown for bud_one",
        )

    def bud_teardown_runs_when_the_step_raises(self):
        """tearDown runs after a raising step, which fails with its text."""

        class RaisingStep(HookedTest):
            def bud_one(self):
                self.calls.append("bud_one")
                raise RuntimeError("step broke")

            def bud_two(self):
                pass

        case = RaisingStep()
        _, results = support.run(case)
        support.check(
            self,
            case.calls[:4],
            ["setUpClass", "setUp", "bud_one", "tearDown"],
            "tearDown runs after the step bud_one, which raised",
            "tearDown did not run after the raising step bud_one",
        )
        support.check(
            self,
            results[0].passed,
            False,
            "the raising step is reported as failed",
            "the raising step is reported as passed",
        )
        support.check(
            self,
            results[0].error_message,
            "step broke",
            "the failed step's error is its exception text step broke",
            "the failed step's error is not its exception text step broke",
        )

    def bud_setup_failure_skips_the_step_and_runs_teardown(self):
        """A raising setUp skips the step, runs tearDown and fails the step with setUp failed: <error>."""

        class FailingSetUp(HookedTest):
            def setUp(self):
                self.calls.append("setUp")
                raise RuntimeError("no device")

            def bud_two(self):
                pass

        case = FailingSetUp()
        _, results = support.run(case)
        result = results[0]
        support.check(
            self,
            case.calls[:3],
            ["setUpClass", "setUp", "tearDown"],
            "a raising setUp is followed by tearDown, with no step in between",
            "a raising setUp was not followed directly by tearDown",
        )
        support.check_not_in(
            self,
            "bud_one",
            case.calls,
            "the step bud_one does not run after a raising setUp",
            "the step bud_one ran although setUp raised",
        )
        support.check(
            self,
            result.passed,
            False,
            "the step whose setUp raised is reported as failed",
            "the step whose setUp raised is reported as passed",
        )
        support.check(
            self,
            result.error_message,
            "setUp failed: no device",
            "the step error reads setUp failed: no device",
            "the step error does not read setUp failed: no device",
        )
        support.check_in(
            self,
            "no device",
            result.traceback or "",
            "the traceback holds the setUp error no device",
            "the traceback does not hold the setUp error no device",
        )

    def bud_teardown_failure_is_logged_and_leaves_the_result(self):
        """A raising tearDown leaves both steps passed without error and logs a cleanup failure."""

        class FailingTearDown(HookedTest):
            def tearDown(self):
                self.calls.append("tearDown")
                raise RuntimeError("cleanup broke")

        case = FailingTearDown()
        _, results, console = support.run_capturing(case, logging.INFO)
        support.check(
            self,
            [r.passed for r in results],
            [True, True],
            "both steps pass although tearDown raises after each",
            "a raising tearDown made a step fail",
        )
        support.check(
            self,
            [r.error_message for r in results],
            [None, None],
            "a raising tearDown gives the steps no error message",
            "a raising tearDown gave the steps an error message",
        )
        support.check(
            self,
            case.calls.count("tearDown"),
            2,
            "tearDown runs after each of the two steps",
            "tearDown did not run exactly twice",
        )
        support.check(
            self,
            ANSI.sub("", console).count("CLEANUP FAILURE DURING tearDown: cleanup broke"),
            2,
            "the cleanup failure cleanup broke is logged once per step",
            "the cleanup failure cleanup broke is not logged exactly once per step",
        )

    def bud_teardown_failure_does_not_hide_a_step_failure(self):
        """When both the step and tearDown raise, the step fails with its own message."""

        class BothFail(HookedTest):
            def tearDown(self):
                raise RuntimeError("cleanup broke")

            def bud_one(self):
                raise RuntimeError("step broke")

            def bud_two(self):
                pass

        _, results = support.run(BothFail())
        support.check(
            self,
            results[0].passed,
            False,
            "when both the step and tearDown raise, the step is reported as failed",
            "when both the step and tearDown raise, the step is reported as passed",
        )
        support.check(
            self,
            results[0].error_message,
            "step broke",
            "the step keeps its own error step broke, not tearDown's",
            "the step's error is not its own text step broke",
        )

    def bud_assertions_in_hooks_are_not_recorded_on_the_step(self):
        """Assertions in setUp and tearDown are not entries of the step."""

        class AssertingHooks(BudTestCase):
            def setUp(self):
                self.assertTrue(support.HOLDS, msg="in setUp")

            def tearDown(self):
                self.assertTrue(support.HOLDS, msg="in tearDown")

            def bud_step(self):
                self.assertTrue(support.HOLDS, msg="step")

        _, results = support.run(AssertingHooks())
        support.check(
            self,
            [a.message for a in results[0].assertions],
            ["step"],
            "assertions in setUp and tearDown are not recorded on the step, only the step's own entry",
            "assertions in setUp or tearDown were recorded on the step",
        )

    def bud_failed_assertion_in_teardown_leaves_a_passing_step_passed(self):
        """Failing soft and aborting assertions in tearDown leave a passing step passed with only its entry."""

        class FailingTearDownAssert(BudTestCase):
            def tearDown(self):
                self.assertTrue(support.BREAKS, msg="soft")
                self.assertTrue(support.BREAKS, msg="hard", abort_on_fail=True)

            def bud_step(self):
                self.assertTrue(support.HOLDS, msg="step")

        _, results = support.run(FailingTearDownAssert())
        result = results[0]
        support.check(
            self,
            result.passed,
            True,
            "failing assertions in tearDown leave the passing step passed",
            "failing assertions in tearDown failed the step",
        )
        support.check(
            self,
            result.error_message,
            None,
            "failing assertions in tearDown give the step no error message",
            "failing assertions in tearDown gave the step an error message",
        )
        support.check(
            self,
            [a.message for a in result.assertions],
            ["step"],
            "the step keeps only its own entry when tearDown assertions fail",
            "tearDown's failed assertions were recorded on the step",
        )

    def bud_soft_failed_assertion_in_setup_is_logged_only(self):
        """A failing soft assertion in setUp is logged; the step runs and passes with only its entry."""

        class SoftSetUpAssert(BudTestCase):
            def setUp(self):
                self.assertTrue(support.BREAKS, msg="soft in setUp")

            def bud_step(self):
                self.assertTrue(support.HOLDS, msg="step")

        _, results, console = support.run_capturing(SoftSetUpAssert(), logging.INFO)
        result = results[0]
        support.check(
            self,
            result.passed,
            True,
            "a soft failed assertion in setUp leaves the step passed",
            "a soft failed assertion in setUp failed the step",
        )
        support.check(
            self,
            result.error_message,
            None,
            "a soft failed assertion in setUp gives the step no error message",
            "a soft failed assertion in setUp gave the step an error message",
        )
        support.check(
            self,
            [a.message for a in result.assertions],
            ["step"],
            "the step keeps only its own entry after a soft failure in setUp",
            "setUp's soft failure was recorded on the step",
        )
        support.check_in(
            self,
            "MESSAGE: soft in setUp",
            ANSI.sub("", console),
            "the soft failure soft in setUp is logged",
            "the soft failure soft in setUp is not logged",
        )

    def bud_aborting_assertion_in_setup_is_a_setup_failure(self):
        """An aborting assertion in setUp fails the step as a setup failure naming the message, with no entries."""

        class FailingSetUpAssert(BudTestCase):
            def setUp(self):
                self.assertTrue(support.BREAKS, msg="device present", abort_on_fail=True)

            def bud_step(self):
                self.assertTrue(support.HOLDS, msg="step")

        _, results = support.run(FailingSetUpAssert())
        result = results[0]
        support.check(
            self,
            result.passed,
            False,
            "an aborting assertion in setUp fails the step",
            "an aborting assertion in setUp did not fail the step",
        )
        support.check(
            self,
            result.error_message[: len("setUp failed: ")],
            "setUp failed: ",
            "the step error starts with setUp failed:",
            "the step error does not start with setUp failed:",
        )
        support.check_in(
            self,
            "device present",
            result.error_message,
            "the step error names the aborting assertion's message device present",
            "the step error does not name the message device present",
        )
        support.check(
            self,
            result.assertions,
            [],
            "the setup failure leaves no entries on the step",
            "the setup failure left entries on the step",
        )
