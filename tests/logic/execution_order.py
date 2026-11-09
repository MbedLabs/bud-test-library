"""Step order: declaration order, not alphabetical, numeric prefixes, helpers between steps, inherited steps, overrides and several levels of inheritance."""

from budtestlibrary import BudTestCase
from tests import support


def run_order(cls) -> list[str]:
    """Run cls quietly and return the names of its steps in the order they ran."""
    return [r.method_name for r in support.run(cls())[1]]


class ExecutionOrder(BudTestCase):
    """The order in which run() calls the bud_ steps."""

    def bud_unprefixed_methods_run_in_declaration_order(self):
        """init, check_state, cleanup run as declared, not alphabetically."""

        class LifecycleOrder(BudTestCase):
            def bud_init(self):
                pass

            def bud_check_state(self):
                pass

            def bud_cleanup(self):
                pass

        support.check(
            self,
            run_order(LifecycleOrder),
            ["bud_init", "bud_check_state", "bud_cleanup"],
            "the steps of LifecycleOrder run in the order they are declared",
            "the steps of LifecycleOrder do not run in the order they are declared",
        )

    def bud_prefixed_methods_keep_their_declared_order(self):
        """bud_10, bud_02, bud_01 declared in that order run in that order, which a sort would change."""

        class Prefixed(BudTestCase):
            def bud_10_last(self):
                pass

            def bud_02_middle(self):
                pass

            def bud_01_first(self):
                pass

        support.check(
            self,
            run_order(Prefixed),
            ["bud_10_last", "bud_02_middle", "bud_01_first"],
            "numbered step names run in declaration order, not sorted by their numbers",
            "numbered step names were not run in declaration order",
        )

    def bud_numeric_prefixes_do_not_reorder(self):
        """bud_02 declared before bud_01 runs first."""

        class OutOfOrderTest(BudTestCase):
            def bud_02_measure(self):
                pass

            def bud_01_connect(self):
                pass

        support.check(
            self,
            run_order(OutOfOrderTest),
            ["bud_02_measure", "bud_01_connect"],
            "bud_02_measure, declared first, runs before bud_01_connect",
            "bud_02_measure and bud_01_connect did not run in declaration order",
        )

    def bud_helpers_between_steps_do_not_affect_order(self):
        """A method without the bud_ prefix between two steps is not run and does not move them."""
        called = []

        class MixedTest(BudTestCase):
            def bud_last_alphabetically_first_declared(self):
                pass

            def helper(self):
                called.append("helper")

            def bud_a_second(self):
                pass

        support.check(
            self,
            run_order(MixedTest),
            ["bud_last_alphabetically_first_declared", "bud_a_second"],
            "only the two bud_ steps run, in declaration order, around the helper method",
            "the steps around the helper method did not run as exactly the two bud_ steps in declaration order",
        )
        support.check(
            self,
            called,
            [],
            "the method helper, which has no bud_ prefix, is not run",
            "the method helper, which has no bud_ prefix, was run",
        )

    def bud_subclass_methods_run_before_inherited_ones(self):
        """The child's steps run first, then the base's, each in declaration order."""

        class Base(BudTestCase):
            def bud_base_one(self):
                pass

            def bud_base_two(self):
                pass

        class Child(Base):
            def bud_child_one(self):
                pass

            def bud_child_two(self):
                pass

        support.check(
            self,
            run_order(Child),
            ["bud_child_one", "bud_child_two", "bud_base_one", "bud_base_two"],
            "the child class's steps run before the inherited ones, each group in declaration order",
            "the child class's steps did not run before the inherited ones in declaration order",
        )

    def bud_override_runs_in_subclass_position_once(self):
        """An override runs once, in the subclass's position, with the child's body."""
        calls = []

        class Base(BudTestCase):
            def bud_shared(self):
                calls.append("base")

            def bud_base_only(self):
                calls.append("base_only")

        class Child(Base):
            def bud_child(self):
                calls.append("child")

            def bud_shared(self):
                calls.append("child_shared")

        support.check(
            self,
            run_order(Child),
            ["bud_child", "bud_shared", "bud_base_only"],
            "the overridden step bud_shared runs once, in the child's position",
            "the overridden step bud_shared did not run once in the child's position",
        )
        support.check(
            self,
            calls,
            ["child", "child_shared", "base_only"],
            "bud_shared runs the child's body, not the base's",
            "bud_shared did not run the child's body alone",
        )

    def bud_multilevel_inheritance_runs_most_derived_first(self):
        """With three levels, the most derived class's steps run first."""

        class Grand(BudTestCase):
            def bud_grand(self):
                pass

        class Parent(Grand):
            def bud_parent(self):
                pass

        class Child(Parent):
            def bud_child(self):
                pass

        support.check(
            self,
            run_order(Child),
            ["bud_child", "bud_parent", "bud_grand"],
            "with three levels the most derived class's steps run first, then the parent's, then the grandparent's",
            "with three levels the steps did not run most derived first",
        )
