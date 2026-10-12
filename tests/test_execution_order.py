"""Tests for running bud_* methods in declaration order."""

import logging

from budtestlibrary import BudTestCase


def _run_order(test_class):
    """Run a test class quietly and return the executed method names."""
    tc = test_class()
    tc.set_loglevel(logging.CRITICAL)
    tc.run()
    return [r.method_name for r in tc.get_results()]


class TestDeclarationOrder:
    def test_unprefixed_methods_run_in_declaration_order(self):
        class DeviceTest(BudTestCase):
            def bud_init(self):
                pass

            def bud_check_state(self):
                pass

            def bud_cleanup(self):
                pass

        assert _run_order(DeviceTest) == ["bud_init", "bud_check_state", "bud_cleanup"]

    def test_prefixed_methods_declared_in_order_keep_their_order(self):
        class PrefixedTest(BudTestCase):
            def bud_01_connect(self):
                pass

            def bud_02_measure(self):
                pass

            def bud_10_disconnect(self):
                pass

        assert _run_order(PrefixedTest) == [
            "bud_01_connect",
            "bud_02_measure",
            "bud_10_disconnect",
        ]

    def test_numeric_prefixes_do_not_reorder(self):
        class OutOfOrderTest(BudTestCase):
            def bud_02_measure(self):
                pass

            def bud_01_connect(self):
                pass

        assert _run_order(OutOfOrderTest) == ["bud_02_measure", "bud_01_connect"]

    def test_helpers_between_steps_do_not_affect_order(self):
        class MixedTest(BudTestCase):
            def bud_last_alphabetically_first_declared(self):
                pass

            def helper(self):
                pass

            def bud_a_second(self):
                pass

        assert _run_order(MixedTest) == [
            "bud_last_alphabetically_first_declared",
            "bud_a_second",
        ]


class TestInheritedOrder:
    def test_subclass_methods_run_before_inherited_ones(self):
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

        assert _run_order(Child) == [
            "bud_child_one",
            "bud_child_two",
            "bud_base_one",
            "bud_base_two",
        ]

    def test_override_runs_in_subclass_position_once(self):
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

        assert _run_order(Child) == ["bud_child", "bud_shared", "bud_base_only"]
        assert calls == ["child", "child_shared", "base_only"]

    def test_multilevel_inheritance_runs_most_derived_first(self):
        class Grand(BudTestCase):
            def bud_grand(self):
                pass

        class Parent(Grand):
            def bud_parent(self):
                pass

        class Child(Parent):
            def bud_child(self):
                pass

        assert _run_order(Child) == ["bud_child", "bud_parent", "bud_grand"]
