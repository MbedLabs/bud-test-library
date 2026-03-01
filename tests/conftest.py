"""Shared test fixtures for budtestlibrary tests."""

import logging

import pytest

from budtestlibrary import BudTestCase


class MinimalTestCase(BudTestCase):
    """Minimal test case with no test methods."""

    pass


class LifecycleTestCase(BudTestCase):
    """Test case that tracks lifecycle calls."""

    def __init__(self):
        super().__init__()
        self.lifecycle_calls = []

    def setUpClass(self):
        self.lifecycle_calls.append("setUpClass")

    def tearDownClass(self):
        self.lifecycle_calls.append("tearDownClass")

    def bud_step_one(self):
        self.lifecycle_calls.append("bud_step_one")

    def bud_step_two(self):
        self.lifecycle_calls.append("bud_step_two")


class AssertionTestCase(BudTestCase):
    """Test case for exercising assertions."""

    pass


@pytest.fixture
def lifecycle_test():
    return LifecycleTestCase()


@pytest.fixture
def assertion_test():
    tc = AssertionTestCase()
    tc.set_loglevel(logging.CRITICAL)  # suppress output during tests
    return tc
