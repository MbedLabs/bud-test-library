"""Tests for BudTestCase lifecycle methods and discovery."""

import logging


class TestLifecycle:
    def test_setup_and_teardown_called_in_order(self, lifecycle_test):
        lifecycle_test.set_loglevel(logging.CRITICAL)
        lifecycle_test.run()
        expected = ["setUpClass", "bud_step_one", "bud_step_two", "tearDownClass"]
        assert lifecycle_test.lifecycle_calls == expected

    def test_teardown_class_called_even_on_setup_failure(self):
        from budtestlibrary import BudTestCase

        calls = []

        class FailingSetup(BudTestCase):
            def setUpClass(self):
                calls.append("setUpClass")
                raise RuntimeError("setup failure")

            def tearDownClass(self):
                calls.append("tearDownClass")

            def bud_test(self):
                calls.append("bud_test")

        tc = FailingSetup()
        tc.set_loglevel(logging.CRITICAL)
        tc.run()
        assert "tearDownClass" in calls
        assert "bud_test" not in calls

    def test_run_returns_false_on_failure(self):
        from budtestlibrary import BudTestCase

        class FailingTest(BudTestCase):
            def bud_fail(self):
                self.assertTrue(False, msg="deliberate fail")

        tc = FailingTest()
        tc.set_loglevel(logging.CRITICAL)
        result = tc.run()
        assert result is False

    def test_run_returns_true_on_all_pass(self):
        from budtestlibrary import BudTestCase

        class PassingTest(BudTestCase):
            def bud_pass(self):
                self.assertTrue(True, msg="passes")

        tc = PassingTest()
        tc.set_loglevel(logging.CRITICAL)
        result = tc.run()
        assert result is True

    def test_run_returns_true_with_no_tests(self):
        from budtestlibrary import BudTestCase

        class EmptyTest(BudTestCase):
            pass

        tc = EmptyTest()
        tc.set_loglevel(logging.CRITICAL)
        result = tc.run()
        assert result is True


class TestDiscovery:
    def test_discovers_bud_prefixed_methods(self):
        from budtestlibrary import BudTestCase

        class MixedTest(BudTestCase):
            def bud_alpha(self):
                pass

            def bud_beta(self):
                pass

            def not_a_test(self):
                pass

            def some_helper(self):
                pass

            def bud_gamma(self):
                pass

        tc = MixedTest()
        methods = tc._discover_test_methods()
        names = [name for name, _ in methods]
        assert names == ["bud_alpha", "bud_beta", "bud_gamma"]

    def test_discovery_sorts_alphabetically(self):
        from budtestlibrary import BudTestCase

        class SortTest(BudTestCase):
            def bud_zebra(self):
                pass

            def bud_alpha(self):
                pass

            def bud_middle(self):
                pass

        tc = SortTest()
        methods = tc._discover_test_methods()
        names = [name for name, _ in methods]
        assert names == ["bud_alpha", "bud_middle", "bud_zebra"]

    def test_excludes_non_callable_attributes(self):
        from budtestlibrary import BudTestCase

        class NonCallableTest(BudTestCase):
            bud_some_value = 42

        tc = NonCallableTest()
        methods = tc._discover_test_methods()
        assert len(methods) == 0

    def test_run_executes_discovered_methods_in_order(self):
        from budtestlibrary import BudTestCase

        order = []

        class OrderedTest(BudTestCase):
            def bud_second(self):
                order.append("second")

            def bud_first(self):
                order.append("first")

            def bud_third(self):
                order.append("third")

        tc = OrderedTest()
        tc.set_loglevel(logging.CRITICAL)
        tc.run()
        assert order == ["first", "second", "third"]


class TestGetResults:
    def test_get_results_after_run(self):
        from budtestlibrary import BudTestCase

        class ResultTest(BudTestCase):
            def bud_check(self):
                self.assertTrue(True, msg="pass1")
                self.assertTrue(True, msg="pass2")

        tc = ResultTest()
        tc.set_loglevel(logging.CRITICAL)
        tc.run()
        results = tc.get_results()
        assert len(results) == 1
        assert results[0].method_name == "bud_check"
        assert results[0].passed
        assert len(results[0].assertions) == 2

    def test_get_results_with_failed_test(self):
        from budtestlibrary import BudTestCase

        class FailResultTest(BudTestCase):
            def bud_mixed(self):
                self.assertTrue(True, msg="pass")
                self.assertTrue(False, msg="fail")

        tc = FailResultTest()
        tc.set_loglevel(logging.CRITICAL)
        tc.run()
        results = tc.get_results()
        assert len(results) == 1
        assert not results[0].passed
        assert len(results[0].assertions) == 2
