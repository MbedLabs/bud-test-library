"""run(): the class hooks around the steps, a failing setUpClass, what run() returns, non-callable bud_ attributes, get_results(), the printed summary and an exit code a shell can read."""

import logging
import re

import support

from budtestlibrary import BudTestCase

ANSI = re.compile(r"\x1b\[[0-9;]*m")


class Lifecycle(BudTestCase):
    """The order of setUpClass, setUp, tearDown and tearDownClass, and what run() and get_results() return."""

    def bud_setup_and_teardown_called_in_order(self):
        """setUpClass, the two steps and tearDownClass run in that order."""

        class LifecycleCase(BudTestCase):
            def __init__(self):
                super().__init__()
                self.calls = []

            def setUpClass(self):
                self.calls.append("setUpClass")

            def tearDownClass(self):
                self.calls.append("tearDownClass")

            def bud_step_one(self):
                self.calls.append("bud_step_one")

            def bud_step_two(self):
                self.calls.append("bud_step_two")

        case = LifecycleCase()
        support.run(case)
        support.check(
            self,
            case.calls,
            ["setUpClass", "bud_step_one", "bud_step_two", "tearDownClass"],
            "run() calls setUpClass, the two steps and tearDownClass in that order",
            "run() did not call setUpClass, the two steps and tearDownClass in that order",
        )

    def bud_teardown_class_called_even_on_setup_failure(self):
        """When setUpClass raises, no step runs, tearDownClass still runs and run() returns False."""
        calls = []

        class FailingSetup(BudTestCase):
            def setUpClass(self):
                calls.append("setUpClass")
                raise RuntimeError("setup failure")

            def tearDownClass(self):
                calls.append("tearDownClass")

            def bud_test(self):
                calls.append("bud_test")

        returned, _ = support.run(FailingSetup())
        support.check(
            self,
            calls,
            ["setUpClass", "tearDownClass"],
            "when setUpClass raises, no step runs and tearDownClass still runs",
            "when setUpClass raises, a step ran or tearDownClass did not run",
        )
        support.check(
            self,
            returned,
            False,
            "run() returns False when setUpClass raises",
            "run() returns True although setUpClass raised",
        )

    def bud_setup_class_failure_fails_the_run_and_is_logged(self):
        """A raising setUpClass gives run() False, no results, and logs the orchestration error with its text."""

        class FailingSetup(BudTestCase):
            def setUpClass(self):
                raise RuntimeError("no bench power")

            def bud_test(self):
                pass

        returned, results, console = support.run_capturing(FailingSetup(), logging.INFO)
        support.check(
            self,
            returned,
            False,
            "run() returns False when setUpClass raises RuntimeError('no bench power')",
            "run() returns True although setUpClass raised RuntimeError('no bench power')",
        )
        support.check(
            self,
            results,
            [],
            "a run whose setUpClass raised has no step results",
            "a run whose setUpClass raised still has step results",
        )
        support.check_in(
            self,
            "CRITICAL SYSTEM ERROR DURING TEST ORCHESTRATION: no bench power",
            console,
            "the orchestration error is logged with the text no bench power",
            "the orchestration error with the text no bench power is not logged",
        )

    def bud_run_returns_false_on_failure(self):
        """A failed assertion makes run() return False."""

        class FailingTest(BudTestCase):
            def bud_fail(self):
                self.assertTrue(False, msg="deliberate fail")

        support.check(
            self,
            support.run(FailingTest())[0],
            False,
            "run() returns False when a step has a failed assertion",
            "run() returns True although a step has a failed assertion",
        )

    def bud_run_returns_true_on_all_pass(self):
        """Only passing assertions make run() return True."""

        class PassingTest(BudTestCase):
            def bud_pass(self):
                self.assertTrue(True, msg="passes")

        support.check(
            self,
            support.run(PassingTest())[0],
            True,
            "run() returns True when every assertion passes",
            "run() returns False although every assertion passes",
        )

    def bud_run_returns_true_with_no_tests(self):
        """A case without steps returns True and has no results."""

        class EmptyTest(BudTestCase):
            pass

        returned, results = support.run(EmptyTest())
        support.check(
            self,
            returned,
            True,
            "run() of a case without steps returns True",
            "run() of a case without steps returns False",
        )
        support.check(
            self,
            results,
            [],
            "a case without steps has no results",
            "a case without steps has results",
        )

    def bud_excludes_non_callable_attributes(self):
        """A bud_ class attribute that is not callable is not a step."""

        class NonCallableTest(BudTestCase):
            bud_some_value = 42

        returned, results = support.run(NonCallableTest())
        support.check(
            self,
            results,
            [],
            "the class attribute bud_some_value = 42 is not run as a step",
            "the class attribute bud_some_value = 42 was run as a step",
        )
        support.check(
            self,
            returned,
            True,
            "run() returns True when the only bud_ attribute is not callable",
            "run() returns False when the only bud_ attribute is not callable",
        )

    def bud_get_results_after_run(self):
        """get_results() holds one passed result named after the step, with its two entries."""

        class ResultTest(BudTestCase):
            def bud_check(self):
                self.assertTrue(True, msg="pass1")
                self.assertTrue(True, msg="pass2")

        _, results = support.run(ResultTest())
        support.check(
            self,
            [r.method_name for r in results],
            ["bud_check"],
            "get_results() holds one result, named bud_check",
            "get_results() does not hold exactly one result named bud_check",
        )
        support.check(
            self,
            results[0].passed,
            True,
            "the result of bud_check is passed",
            "the result of bud_check is failed",
        )
        support.check(
            self,
            [a.message for a in results[0].assertions],
            ["pass1", "pass2"],
            "the result of bud_check holds its two entries pass1 and pass2",
            "the result of bud_check does not hold exactly the entries pass1 and pass2",
        )

    def bud_get_results_with_failed_test(self):
        """A step with a passing and a failing entry has a failed result with both entries."""

        class FailResultTest(BudTestCase):
            def bud_mixed(self):
                self.assertTrue(True, msg="pass")
                self.assertTrue(False, msg="fail")

        _, results = support.run(FailResultTest())
        support.check(
            self,
            len(results),
            1,
            "get_results() holds one result for the step bud_mixed",
            "get_results() does not hold exactly one result for bud_mixed",
        )
        support.check(
            self,
            results[0].passed,
            False,
            "the step bud_mixed with one failing entry is a failed result",
            "the step bud_mixed with one failing entry is a passed result",
        )
        support.check(
            self,
            [a.passed for a in results[0].assertions],
            [True, False],
            "the failed result keeps both entries, the passing one then the failing one",
            "the failed result does not keep both entries in order",
        )

    def bud_run_prints_the_summary_and_counts(self):
        """A child run with 2 passed, 1 failed and 1 skipped assertion prints FAILED and those counts."""
        directory = support.work_dir("summary")
        support.write_suite(
            directory,
            "demo_summary.py",
            """
            from budtestlibrary import BudTestCase


            class DemoSummaryTest(BudTestCase):
                def bud_mixed(self):
                    self.assertTrue(True, msg="one")
                    self.assertEqual(2, 2, msg="two")
                    self.assertTrue(False, msg="three")
                    self.skipAssert("four")


            DemoSummaryTest().run()
            """,
        )
        done = support.python(directory / "demo_summary.py", cwd=directory)
        console = ANSI.sub("", done.err)
        support.check_in(
            self,
            "TEST CASE SUMMARY: DemoSummaryTest - FAILED",
            console,
            "the run of demo_summary.py prints the summary DemoSummaryTest - FAILED",
            "the run of demo_summary.py does not print the summary DemoSummaryTest - FAILED",
        )
        support.check_in(
            self,
            "Assertion Pass-Rate:   2 Passed | 1 Failed | 1 Skipped | Total Executed: 4",
            console,
            "the summary counts 2 passed, 1 failed and 1 skipped of 4 executed assertions",
            "the summary does not count 2 passed, 1 failed and 1 skipped of 4 executed assertions",
        )

    def bud_failure_is_visible_to_the_shell(self):
        """A child that exits with run()'s result exits 1 for a failing case and 0 for a passing one."""
        directory = support.work_dir("shell")
        source = """
            import sys

            from budtestlibrary import BudTestCase


            class DemoShellTest(BudTestCase):
                def bud_check(self):
                    self.assertTrue({condition}, msg="check")


            sys.exit(0 if DemoShellTest().run() else 1)
            """
        support.write_suite(directory, "demo_failing.py", source.replace("{condition}", "False"))
        support.write_suite(directory, "demo_passing.py", source.replace("{condition}", "True"))
        failing = support.python(directory / "demo_failing.py", cwd=directory)
        passing = support.python(directory / "demo_passing.py", cwd=directory)
        support.check(
            self,
            failing.code,
            1,
            "a script that exits with run()'s result exits 1 for a failing case",
            f"a script that exits with run()'s result did not exit 1 for a failing case: {failing.err[-300:]!r}",
        )
        support.check(
            self,
            passing.code,
            0,
            "a script that exits with run()'s result exits 0 for a passing case",
            f"a script that exits with run()'s result did not exit 0 for a passing case: {passing.err[-300:]!r}",
        )
