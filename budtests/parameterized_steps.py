"""@parameterized: step names and arguments for single values, tuples and dicts, failing items, step position, empty and generator data, repeated and too long step names."""

import logging

import support

from budtestlibrary import BudTestCase, parameterized
from budtestlibrary.budtestcase import MAX_STEP_NAME_LENGTH


def names(results) -> list[str]:
    """Return the step names of a run's results."""
    return [r.method_name for r in results]


class ParameterizedSteps(BudTestCase):
    """@parameterized steps and their results."""

    def bud_single_values_give_one_named_result_each(self):
        """Three single values give three passed steps named with the value, each called with its value and one entry."""
        seen = []

        class VoltageTest(BudTestCase):
            @parameterized(["1.8V", "3.3V", "5V"])
            def bud_test_voltage(self, rail):
                seen.append(rail)
                self.assertTrue(support.HOLDS, msg=f"rail {rail}")

        _, results = support.run(VoltageTest())
        support.check(
            self,
            names(results),
            ["bud_test_voltage[1.8V]", "bud_test_voltage[3.3V]", "bud_test_voltage[5V]"],
            "three single values give three steps named bud_test_voltage[1.8V], [3.3V] and [5V]",
            "the single values did not give the steps bud_test_voltage[1.8V], [3.3V] and [5V]",
        )
        support.check(
            self,
            seen,
            ["1.8V", "3.3V", "5V"],
            "each step is called with its own value, 1.8V, 3.3V, then 5V",
            "the steps were not called with 1.8V, 3.3V and 5V in order",
        )
        support.check(
            self,
            [r.passed for r in results],
            [True, True, True],
            "all three voltage steps pass",
            "not all three voltage steps pass",
        )
        support.check(
            self,
            [len(r.assertions) for r in results],
            [1, 1, 1],
            "each voltage step records exactly one entry",
            "the voltage steps did not record one entry each",
        )

    def bud_tuple_items_are_unpacked_as_positional_arguments(self):
        """Tuples are unpacked as positional arguments and joined by ', ' in the name."""
        seen = []

        class TupleTest(BudTestCase):
            @parameterized([(1, 2), (3, 4)])
            def bud_add(self, a, b):
                seen.append((a, b))

        _, results = support.run(TupleTest())
        support.check(
            self,
            names(results),
            ["bud_add[1, 2]", "bud_add[3, 4]"],
            "tuple items give the steps bud_add[1, 2] and bud_add[3, 4]",
            "tuple items did not give the steps bud_add[1, 2] and bud_add[3, 4]",
        )
        support.check(
            self,
            seen,
            [(1, 2), (3, 4)],
            "each tuple is unpacked into the positional arguments a and b",
            "the tuples were not unpacked into the positional arguments a and b",
        )

    def bud_dict_items_are_passed_as_keyword_arguments(self):
        """A dict is passed as keyword arguments and named key=value."""
        seen = []

        class DictTest(BudTestCase):
            @parameterized([{"rail": "3.3V", "limit": 0.1}])
            def bud_rail(self, rail, limit):
                seen.append((rail, limit))

        _, results = support.run(DictTest())
        support.check(
            self,
            names(results),
            ["bud_rail[rail=3.3V, limit=0.1]"],
            "a dict item gives the step bud_rail[rail=3.3V, limit=0.1]",
            "the dict item did not give the step bud_rail[rail=3.3V, limit=0.1]",
        )
        support.check(
            self,
            seen,
            [("3.3V", 0.1)],
            "the dict is passed as the keyword arguments rail=3.3V and limit=0.1",
            "the dict was not passed as the keyword arguments rail=3.3V and limit=0.1",
        )

    def bud_failure_in_one_item_does_not_stop_the_others(self):
        """A raising item fails alone; the items around it run and pass."""
        seen = []

        class PartialFailTest(BudTestCase):
            @parameterized([1, 2, 3])
            def bud_value(self, value):
                seen.append(value)
                if value == 2:
                    raise RuntimeError("item 2 broke")
                self.assertEqual(value, value)

        _, results = support.run(PartialFailTest())
        support.check(
            self,
            seen,
            [1, 2, 3],
            "items 1, 2 and 3 all run although item 2 raises",
            "not all of items 1, 2 and 3 ran when item 2 raised",
        )
        support.check(
            self,
            [r.passed for r in results],
            [True, False, True],
            "only item 2, which raises, fails; items 1 and 3 pass",
            "the outcome is not item 2 failed and items 1 and 3 passed",
        )
        support.check(
            self,
            results[1].error_message,
            "item 2 broke",
            "item 2's step error is its exception text item 2 broke",
            "item 2's step error is not its exception text item 2 broke",
        )

    def bud_expanded_steps_take_the_method_position(self):
        """The expanded steps sit where the decorated method is declared."""

        class OrderTest(BudTestCase):
            def bud_first(self):
                pass

            @parameterized(["a", "b"])
            def bud_middle(self, item):
                pass

            def bud_last(self):
                pass

        _, results = support.run(OrderTest())
        support.check(
            self,
            names(results),
            ["bud_first", "bud_middle[a]", "bud_middle[b]", "bud_last"],
            "the expanded steps bud_middle[a] and [b] sit where bud_middle is declared, between bud_first and bud_last",
            "the expanded steps did not sit between bud_first and bud_last",
        )

    def bud_empty_data_runs_no_step(self):
        """Empty data gives no step and run() still passes."""

        class EmptyTest(BudTestCase):
            @parameterized([])
            def bud_nothing(self, item):
                pass

        returned, results = support.run(EmptyTest())
        support.check(
            self, results, [], "parameterized([]) gives no step", "parameterized([]) gave steps"
        )
        support.check(
            self,
            returned,
            True,
            "run() returns True for a case whose only step has empty data",
            "run() returns False for a case whose only step has empty data",
        )

    def bud_data_from_a_generator_is_kept(self):
        """Generator data is kept: two runs of the class give the same steps."""

        class GeneratorTest(BudTestCase):
            @parameterized(x for x in (1, 2))
            def bud_gen(self, item):
                pass

        support.check(
            self,
            names(support.run(GeneratorTest())[1]),
            ["bud_gen[1]", "bud_gen[2]"],
            "a first run of generator data gives bud_gen[1] and bud_gen[2]",
            "a first run of generator data did not give bud_gen[1] and bud_gen[2]",
        )
        support.check(
            self,
            names(support.run(GeneratorTest())[1]),
            ["bud_gen[1]", "bud_gen[2]"],
            "a second run of the same class still gives bud_gen[1] and bud_gen[2], so the generator data is kept",
            "a second run lost the generator data and did not give bud_gen[1] and bud_gen[2]",
        )

    def bud_repeated_step_name_fails_the_run_before_any_step(self):
        """Items 1 and '1' both give bud_x[1]: run() is False, nothing runs, no results, and the duplicate is logged."""
        executed = []

        class RepeatTest(BudTestCase):
            @parameterized([1, "1"])
            def bud_x(self, item):
                executed.append(item)

        returned, results, console = support.run_capturing(RepeatTest(), logging.INFO)
        support.check(
            self,
            returned,
            False,
            "run() returns False when items 1 and '1' both give bud_x[1]",
            "run() returns True although items 1 and '1' both give bud_x[1]",
        )
        support.check(
            self,
            executed,
            [],
            "no step runs when a step name repeats",
            "steps ran although a step name repeats",
        )
        support.check(
            self,
            results,
            [],
            "a run refused for a repeated step name has no results",
            "a run refused for a repeated step name has results",
        )
        support.check_in(
            self,
            "bud_x: step name bud_x[1] repeats",
            console,
            "the log says bud_x: step name bud_x[1] repeats",
            "the log does not say bud_x: step name bud_x[1] repeats",
        )

    def bud_step_name_over_the_limit_fails_the_run_before_any_step(self):
        """A 265-character parameterized name: run() is False and no step runs, the short one neither."""
        executed = []

        class LongNameTest(BudTestCase):
            def bud_short(self):
                executed.append("short")

            @parameterized(["v" * MAX_STEP_NAME_LENGTH])
            def bud_long(self, value):
                executed.append("long")

        returned, results, console = support.run_capturing(LongNameTest(), logging.INFO)
        support.check(
            self,
            returned,
            False,
            "run() returns False when a parameterized step name is 265 characters long",
            "run() returns True although a parameterized step name is 265 characters long",
        )
        support.check(
            self,
            executed,
            [],
            "no step runs, not even bud_short, when a step name is over the limit",
            "steps ran although a step name is over the limit",
        )
        support.check(
            self,
            results,
            [],
            "a run refused for a step name over the limit has no results",
            "a run refused for a step name over the limit has results",
        )
        support.check_in(
            self,
            "bud_long: step name is 265 characters, over the 255-character limit",
            console,
            "the log says the step name is 265 characters, over the 255-character limit",
            "the log does not say the step name is 265 characters, over the 255-character limit",
        )

    def bud_step_name_at_the_limit_runs(self):
        """A step name of exactly 255 characters runs."""

        class EdgeTest(BudTestCase):
            @parameterized(["v" * (MAX_STEP_NAME_LENGTH - len("bud_edge[]"))])
            def bud_edge(self, value):
                pass

        returned, results = support.run(EdgeTest())
        support.check(
            self,
            MAX_STEP_NAME_LENGTH,
            255,
            "the step name limit MAX_STEP_NAME_LENGTH is 255",
            "the step name limit MAX_STEP_NAME_LENGTH is not 255",
        )
        support.check(
            self,
            [len(n) for n in names(results)],
            [255],
            "a step name of exactly 255 characters runs as one step",
            "a step name of exactly 255 characters did not run as one step",
        )
        support.check(
            self,
            returned,
            True,
            "run() returns True for a step name of exactly 255 characters",
            "run() returns False for a step name of exactly 255 characters",
        )

    def bud_plain_step_name_over_the_storage_limit_fails_before_execution(self):
        """A plain step of 256 characters: run() is False, nothing runs, no results."""
        executed = []
        name = "bud_" + "x" * 252
        suite = type("LongPlainStep", (BudTestCase,), {name: lambda self: executed.append(True)})
        returned, results, console = support.run_capturing(suite(), logging.INFO)
        support.check(
            self,
            returned,
            False,
            "run() returns False for a plain step name of 256 characters",
            "run() returns True for a plain step name of 256 characters",
        )
        support.check(
            self,
            executed,
            [],
            "the 256-character plain step is not executed",
            "the 256-character plain step was executed",
        )
        support.check(
            self,
            results,
            [],
            "a run refused for a 256-character plain step has no results",
            "a run refused for a 256-character plain step has results",
        )
        support.check_in(
            self,
            "step name is 256 characters",
            console,
            "the log says the step name is 256 characters",
            "the log does not say the step name is 256 characters",
        )
