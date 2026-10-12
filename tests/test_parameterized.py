"""Tests for parameterized bud_* methods."""

import logging

import pytest

from budtestlibrary import BudTestCase, parameterized


def _run(test_class):
    """Run a test class quietly and return the test case instance."""
    tc = test_class()
    tc.set_loglevel(logging.CRITICAL)
    tc.run()
    return tc


class TestParameterizedExpansion:
    def test_single_values_give_one_named_result_each(self):
        seen = []

        class VoltageTest(BudTestCase):
            @parameterized(["1.8V", "3.3V", "5V"])
            def bud_test_voltage(self, rail):
                seen.append(rail)
                self.assertTrue(True, msg=f"rail {rail}")

        tc = _run(VoltageTest)
        names = [r.method_name for r in tc.get_results()]
        assert names == [
            "bud_test_voltage[1.8V]",
            "bud_test_voltage[3.3V]",
            "bud_test_voltage[5V]",
        ]
        assert seen == ["1.8V", "3.3V", "5V"]
        assert all(r.passed for r in tc.get_results())
        assert [len(r.assertions) for r in tc.get_results()] == [1, 1, 1]

    def test_tuple_items_are_unpacked_as_positional_arguments(self):
        seen = []

        class TupleTest(BudTestCase):
            @parameterized([(1, 2), (3, 4)])
            def bud_add(self, a, b):
                seen.append((a, b))

        tc = _run(TupleTest)
        assert [r.method_name for r in tc.get_results()] == ["bud_add[1, 2]", "bud_add[3, 4]"]
        assert seen == [(1, 2), (3, 4)]

    def test_dict_items_are_passed_as_keyword_arguments(self):
        seen = []

        class DictTest(BudTestCase):
            @parameterized([{"rail": "3.3V", "limit": 0.1}])
            def bud_rail(self, rail, limit):
                seen.append((rail, limit))

        tc = _run(DictTest)
        assert [r.method_name for r in tc.get_results()] == ["bud_rail[rail=3.3V, limit=0.1]"]
        assert seen == [("3.3V", 0.1)]

    def test_failure_in_one_item_does_not_stop_the_others(self):
        seen = []

        class PartialFailTest(BudTestCase):
            @parameterized([1, 2, 3])
            def bud_value(self, value):
                seen.append(value)
                if value == 2:
                    raise RuntimeError("item 2 broke")
                self.assertEqual(value, value)

        tc = _run(PartialFailTest)
        results = tc.get_results()
        assert seen == [1, 2, 3]
        assert [r.passed for r in results] == [True, False, True]
        assert "item 2 broke" in results[1].error_message

    def test_expanded_steps_take_the_method_position(self):
        class OrderTest(BudTestCase):
            def bud_first(self):
                pass

            @parameterized(["a", "b"])
            def bud_middle(self, item):
                pass

            def bud_last(self):
                pass

        tc = _run(OrderTest)
        assert [r.method_name for r in tc.get_results()] == [
            "bud_first",
            "bud_middle[a]",
            "bud_middle[b]",
            "bud_last",
        ]

    def test_undecorated_methods_are_unchanged(self):
        class PlainTest(BudTestCase):
            def bud_plain(self):
                self.assertTrue(True)

        tc = _run(PlainTest)
        assert [r.method_name for r in tc.get_results()] == ["bud_plain"]

    def test_empty_data_runs_no_step(self):
        class EmptyTest(BudTestCase):
            @parameterized([])
            def bud_nothing(self, item):
                pass

        tc = _run(EmptyTest)
        assert tc.get_results() == []

    def test_data_from_a_generator_is_kept(self):
        class GeneratorTest(BudTestCase):
            @parameterized(x for x in (1, 2))
            def bud_gen(self, item):
                pass

        first = _run(GeneratorTest)
        second = _run(GeneratorTest)
        assert [r.method_name for r in first.get_results()] == ["bud_gen[1]", "bud_gen[2]"]
        assert [r.method_name for r in second.get_results()] == ["bud_gen[1]", "bud_gen[2]"]


class TestStepNames:
    def test_repeated_step_name_fails_the_run_before_any_step(self):
        executed = []

        class RepeatTest(BudTestCase):
            @parameterized([1, "1"])
            def bud_x(self, item):
                executed.append(item)

        tc = RepeatTest()
        tc.set_loglevel(logging.CRITICAL)
        with pytest.raises(ValueError, match=r"bud_x: step name bud_x\[1\] repeats"):
            tc._discover_test_methods()
        assert tc.run() is False
        assert executed == []
        assert tc.get_results() == []

    def test_step_name_over_the_limit_fails_the_run_before_any_step(self):
        from budtestlibrary.budtestcase import MAX_STEP_NAME_LENGTH

        executed = []

        class LongNameTest(BudTestCase):
            def bud_short(self):
                executed.append("short")

            @parameterized(["v" * MAX_STEP_NAME_LENGTH])
            def bud_long(self, value):
                executed.append("long")

        tc = LongNameTest()
        tc.set_loglevel(logging.CRITICAL)
        with pytest.raises(ValueError, match="bud_long: step name is 265 characters"):
            tc._discover_test_methods()
        assert tc.run() is False
        assert executed == []
        assert tc.get_results() == []

    def test_step_name_at_the_limit_runs(self):
        from budtestlibrary.budtestcase import MAX_STEP_NAME_LENGTH

        prefix_length = len("bud_edge[]")

        class EdgeTest(BudTestCase):
            @parameterized(["v" * (MAX_STEP_NAME_LENGTH - prefix_length)])
            def bud_edge(self, value):
                pass

        tc = _run(EdgeTest)
        assert len(tc.get_results()[0].method_name) == MAX_STEP_NAME_LENGTH
