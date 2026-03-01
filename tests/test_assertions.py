"""Tests for assertions in BudTestCase."""

import pytest

from budtestlibrary.budtestcase import AssertionError


class TestAssertTrue:
    def test_passing_assertion(self, assertion_test):
        assertion_test.assertTrue(True, msg="should pass")
        results = assertion_test._current_assertions
        assert len(results) == 1
        assert results[0].passed
        assert not results[0].skipped
        assert results[0].assertion_type == "AssertTrue"
        assert results[0].message == "should pass"

    def test_failing_assertion(self, assertion_test):
        assertion_test.assertTrue(False, msg="should fail")
        results = assertion_test._current_assertions
        assert len(results) == 1
        assert not results[0].passed
        assert results[0].message == "should fail"

    def test_abort_on_fail_raises(self, assertion_test):
        with pytest.raises(AssertionError):
            assertion_test.assertTrue(False, msg="fatal", abort_on_fail=True)


class TestAssertFalse:
    def test_false_passes(self, assertion_test):
        assertion_test.assertFalse(False, msg="should pass")
        results = assertion_test._current_assertions
        assert len(results) == 1
        assert results[0].passed
        assert results[0].assertion_type == "AssertFalse"

    def test_true_fails(self, assertion_test):
        assertion_test.assertFalse(True, msg="should fail")
        results = assertion_test._current_assertions
        assert not results[0].passed


class TestAssertEqual:
    def test_matching_values(self, assertion_test):
        assertion_test.assertEqual(42, 42, msg="equal")
        assert assertion_test._current_assertions[0].passed

    def test_different_values(self, assertion_test):
        assertion_test.assertEqual(1, 2, msg="not equal")
        assert not assertion_test._current_assertions[0].passed

    def test_with_none(self, assertion_test):
        assertion_test.assertEqual(None, None, msg="both none")
        assert assertion_test._current_assertions[0].passed


class TestAssertNotEqual:
    def test_different_passes(self, assertion_test):
        assertion_test.assertNotEqual(1, 2, msg="different")
        assert assertion_test._current_assertions[0].passed

    def test_same_fails(self, assertion_test):
        assertion_test.assertNotEqual(42, 42, msg="same")
        assert not assertion_test._current_assertions[0].passed


class TestAssertGreater:
    def test_greater_passes(self, assertion_test):
        assertion_test.assertGreater(10, 5, msg="greater")
        assert assertion_test._current_assertions[0].passed

    def test_equal_fails(self, assertion_test):
        assertion_test.assertGreater(5, 5, msg="equal")
        assert not assertion_test._current_assertions[0].passed

    def test_less_fails(self, assertion_test):
        assertion_test.assertGreater(3, 10, msg="less")
        assert not assertion_test._current_assertions[0].passed


class TestAssertLess:
    def test_less_passes(self, assertion_test):
        assertion_test.assertLess(3, 10, msg="less")
        assert assertion_test._current_assertions[0].passed

    def test_equal_fails(self, assertion_test):
        assertion_test.assertLess(5, 5, msg="equal")
        assert not assertion_test._current_assertions[0].passed

    def test_greater_fails(self, assertion_test):
        assertion_test.assertLess(10, 3, msg="greater")
        assert not assertion_test._current_assertions[0].passed


class TestAssertIn:
    def test_member_found_in_list(self, assertion_test):
        assertion_test.assertIn(member=2, container=[1, 2, 3], msg="in list")
        assert assertion_test._current_assertions[0].passed

    def test_member_not_found_in_list(self, assertion_test):
        assertion_test.assertIn(member=99, container=[1, 2, 3], msg="not in list")
        assert not assertion_test._current_assertions[0].passed

    def test_in_string(self, assertion_test):
        assertion_test.assertIn(member="abc", container="xxabcxx", msg="in string")
        assert assertion_test._current_assertions[0].passed

    def test_in_dict_keys(self, assertion_test):
        assertion_test.assertIn(member="key", container={"key": "val"}, msg="in dict")
        assert assertion_test._current_assertions[0].passed

    def test_bad_container_raises_typeerror(self, assertion_test):
        with pytest.raises(TypeError, match="container with __contains__"):
            assertion_test.assertIn(member=1, container=42, msg="bad container")


class TestAssertNotIn:
    def test_member_not_present_passes(self, assertion_test):
        assertion_test.assertNotIn(member=99, container=[1, 2, 3], msg="not present")
        assert assertion_test._current_assertions[0].passed

    def test_member_present_fails(self, assertion_test):
        assertion_test.assertNotIn(member=2, container=[1, 2, 3], msg="present")
        assert not assertion_test._current_assertions[0].passed

    def test_bad_container_raises_typeerror(self, assertion_test):
        with pytest.raises(TypeError, match="container with __contains__"):
            assertion_test.assertNotIn(member=1, container=42, msg="bad container")


class TestAssertInTolerance:
    def test_within_absolute_tolerance(self, assertion_test):
        assertion_test.assertInTolerance(actual=42.5, expected=42.0, absolute_tolerance=0.5)
        assert assertion_test._current_assertions[0].passed

    def test_outside_absolute_tolerance(self, assertion_test):
        assertion_test.assertInTolerance(actual=43.0, expected=42.0, absolute_tolerance=0.5)
        assert not assertion_test._current_assertions[0].passed

    def test_zero_tolerance_requires_exact(self, assertion_test):
        """absolute_tolerance=0 should be respected — it means exact match required."""
        assertion_test.assertInTolerance(actual=42.1, expected=42.0, absolute_tolerance=0.0)
        assert not assertion_test._current_assertions[0].passed

        assertion_test._current_assertions.clear()
        assertion_test.assertInTolerance(actual=42.0, expected=42.0, absolute_tolerance=0.0)
        assert assertion_test._current_assertions[0].passed

    def test_zero_tolerance_falsy_guard(self, assertion_test):
        """False-equivalent 0 tolerance must not fall through to relative_tolerance."""
        assertion_test.assertInTolerance(actual=41.9, expected=42.0, absolute_tolerance=0.0)
        assert not assertion_test._current_assertions[0].passed

    def test_relative_tolerance(self, assertion_test):
        assertion_test.assertInTolerance(actual=105.0, expected=100.0, relative_tolerance=0.1)
        assert assertion_test._current_assertions[0].passed

    def test_no_tolerance_given_defaults_to_zero(self, assertion_test):
        """When no tolerance is given, tol should be 0 (exact match)."""
        assertion_test.assertInTolerance(actual=42.0, expected=42.0)
        assert assertion_test._current_assertions[0].passed

        assertion_test._current_assertions.clear()
        assertion_test.assertInTolerance(actual=42.1, expected=42.0)
        assert not assertion_test._current_assertions[0].passed


class TestAssertInRange:
    def test_within_range_inclusive(self, assertion_test):
        assertion_test.assertInRange(actual=5.0, lower_bound=0.0, upper_bound=10.0)
        assert assertion_test._current_assertions[0].passed

        assertion_test._current_assertions.clear()
        assertion_test.assertInRange(actual=0.0, lower_bound=0.0, upper_bound=10.0)
        assert assertion_test._current_assertions[0].passed

        assertion_test._current_assertions.clear()
        assertion_test.assertInRange(actual=10.0, lower_bound=0.0, upper_bound=10.0)
        assert assertion_test._current_assertions[0].passed

    def test_outside_range(self, assertion_test):
        assertion_test.assertInRange(actual=11.0, lower_bound=0.0, upper_bound=10.0)
        assert not assertion_test._current_assertions[0].passed

    def test_exclusive_bounds(self, assertion_test):
        assertion_test.assertInRange(
            actual=0.0, lower_bound=0.0, upper_bound=10.0, include_bounds=False
        )
        assert not assertion_test._current_assertions[0].passed

        assertion_test._current_assertions.clear()
        assertion_test.assertInRange(
            actual=5.0, lower_bound=0.0, upper_bound=10.0, include_bounds=False
        )
        assert assertion_test._current_assertions[0].passed

    def test_lower_bound_only(self, assertion_test):
        assertion_test.assertInRange(actual=10.0, lower_bound=5.0)
        assert assertion_test._current_assertions[0].passed

        assertion_test._current_assertions.clear()
        assertion_test.assertInRange(actual=3.0, lower_bound=5.0)
        assert not assertion_test._current_assertions[0].passed


class TestAssertRegex:
    def test_pattern_matches(self, assertion_test):
        assertion_test.assertRegex(text="hello world", pattern=r"hello", msg="matches")
        assert assertion_test._current_assertions[0].passed

    def test_pattern_does_not_match(self, assertion_test):
        assertion_test.assertRegex(text="hello world", pattern=r"goodbye", msg="no match")
        assert not assertion_test._current_assertions[0].passed

    def test_complex_pattern(self, assertion_test):
        assertion_test.assertRegex(text="foo123bar", pattern=r"\d+", msg="digits found")
        assert assertion_test._current_assertions[0].passed


class TestSkipAssert:
    def test_skip_assert(self, assertion_test):
        assertion_test.skipAssert(msg="skipping this")
        results = assertion_test._current_assertions
        assert len(results) == 1
        assert results[0].passed
        assert results[0].skipped
        assert results[0].assertion_type == "Skip"
