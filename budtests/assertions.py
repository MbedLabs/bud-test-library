"""The assertion methods: the entry each records (type, passed, skipped, message, expected, actual), boundaries, tolerance, range, regex, skip, and bad containers."""

import support

from budtestlibrary import BudTestCase, parameterized
from budtestlibrary.budtestcase import AssertionError as BudAssertionError

RECORDED_VALUES = {
    "assertEqual(None, None)": ("assertEqual", None, None, True, None, None),
    "assertEqual(5, None)": ("assertEqual", 5, None, False, None, 5),
    "assertEqual(None, 5)": ("assertEqual", None, 5, False, 5, None),
    "assertEqual(0, 0)": ("assertEqual", 0, 0, True, 0, 0),
    "assertEqual('', '')": ("assertEqual", "", "", True, "", ""),
    "assertEqual(False, False)": ("assertEqual", False, False, True, False, False),
    "assertNotEqual(None, None)": ("assertNotEqual", None, None, False, "!= None", None),
}


class BareCase(BudTestCase):
    """Inner case whose assertion methods are called directly, without run()."""


def entries(body):
    """Return the entries an inner step running body(case) recorded."""
    return support.step(body).assertions


class Assertions(BudTestCase):
    """The assertion methods: what each records as passed or failed, the values it keeps, and abort_on_fail."""

    def _one(self, body, passed: bool, assertion_type: str, what: str):
        """Run body in an inner step and check it recorded one entry of the type with the passed flag."""
        recorded = entries(body)
        support.check(
            self,
            len(recorded),
            1,
            f"{what} records exactly one assertion entry",
            f"{what} did not record exactly one assertion entry",
        )
        support.check(
            self,
            recorded[0].assertion_type,
            assertion_type,
            f"{what} records an {assertion_type} entry",
            f"{what} recorded another entry type than {assertion_type}",
        )
        outcome, opposite = ("passed", "failed") if passed else ("failed", "passed")
        support.check(
            self,
            recorded[0].passed,
            passed,
            f"{what} records a {outcome} entry",
            f"{what} recorded a {opposite} entry where a {outcome} one was expected",
        )
        return recorded[0]

    def bud_passing_assertion(self):
        """assertTrue(True) records one passed, not skipped AssertTrue entry with its message."""
        entry = self._one(
            lambda tc: tc.assertTrue(support.HOLDS, msg="should pass"),
            True,
            "AssertTrue",
            "assertTrue(True)",
        )
        support.check(
            self,
            entry.skipped,
            False,
            "assertTrue(True) records an entry that is not marked skipped",
            "assertTrue(True) recorded an entry marked skipped",
        )
        support.check(
            self,
            entry.message,
            "should pass",
            "assertTrue(True) keeps its message 'should pass' in the entry",
            "assertTrue(True) did not keep its message 'should pass' in the entry",
        )

    def bud_failing_assertion(self):
        """assertTrue(False) records one failed entry with its message, and the step fails."""
        result = support.step(lambda tc: tc.assertTrue(support.BREAKS, msg="should fail"))
        support.check(
            self,
            len(result.assertions),
            1,
            "assertTrue(False) records exactly one assertion entry",
            "assertTrue(False) did not record exactly one assertion entry",
        )
        support.check(
            self,
            result.assertions[0].passed,
            False,
            "assertTrue(False) records a failed entry",
            "assertTrue(False) recorded a passed entry",
        )
        support.check(
            self,
            result.assertions[0].message,
            "should fail",
            "assertTrue(False) keeps its message 'should fail' in the entry",
            "assertTrue(False) did not keep its message 'should fail' in the entry",
        )
        support.check(
            self,
            result.passed,
            False,
            "a step whose assertTrue(False) fails is reported as failed",
            "a step whose assertTrue(False) fails is reported as passed",
        )

    def bud_abort_on_fail_raises(self):
        """assertTrue(False, abort_on_fail=True) raises budtestlibrary's AssertionError with the entry text."""
        exc = support.raised(
            support.quiet(BareCase()).assertTrue, False, msg="fatal", abort_on_fail=True
        )
        support.check(
            self,
            type(exc),
            BudAssertionError,
            "assertTrue(False, abort_on_fail=True) raises budtestlibrary's AssertionError",
            "assertTrue(False, abort_on_fail=True) did not raise budtestlibrary's AssertionError",
        )
        support.check(
            self,
            str(exc),
            "[AssertTrue] EXPECTED: True | ACTUAL: False | MESSAGE: fatal",
            "the raised AssertionError carries the entry text with expected, actual and message",
            "the raised AssertionError does not carry the entry text with expected, actual and message",
        )

    def bud_false_passes(self):
        """assertFalse(False) records a passed AssertFalse entry."""
        self._one(
            lambda tc: tc.assertFalse(support.BREAKS, msg="should pass"),
            True,
            "AssertFalse",
            "assertFalse(False)",
        )

    def bud_true_fails(self):
        """assertFalse(True) records a failed AssertFalse entry."""
        self._one(
            lambda tc: tc.assertFalse(support.HOLDS, msg="should fail"),
            False,
            "AssertFalse",
            "assertFalse(True)",
        )

    def bud_matching_values(self):
        """assertEqual(42, 42) passes and records expected 42 and actual 42."""
        entry = self._one(
            lambda tc: tc.assertEqual(42, 42, msg="equal"),
            True,
            "AssertEqual",
            "assertEqual(42, 42)",
        )
        support.check(
            self,
            entry.expected,
            42,
            "assertEqual(42, 42) records expected 42",
            "assertEqual(42, 42) recorded another expected value than 42",
        )
        support.check(
            self,
            entry.actual,
            42,
            "assertEqual(42, 42) records actual 42",
            "assertEqual(42, 42) recorded another actual value than 42",
        )

    def bud_different_values(self):
        """assertEqual(1, 2) fails and records expected 2 and actual 1."""
        entry = self._one(
            lambda tc: tc.assertEqual(1, 2, msg="not equal"),
            False,
            "AssertEqual",
            "assertEqual(1, 2)",
        )
        support.check(
            self,
            entry.expected,
            2,
            "assertEqual(1, 2) records expected 2",
            "assertEqual(1, 2) recorded another expected value than 2",
        )
        support.check(
            self,
            entry.actual,
            1,
            "assertEqual(1, 2) records actual 1",
            "assertEqual(1, 2) recorded another actual value than 1",
        )

    @parameterized(list(RECORDED_VALUES))
    def bud_recorded_values_keep_none_and_falsy_values(self, call):
        """The entry carries the compared values as given, None and falsy values included, and the step error shows them."""
        method, actual, expected, passed, want_expected, want_actual = RECORDED_VALUES[call]
        result = support.step(lambda tc: getattr(tc, method)(actual, expected, msg="m"))
        entry = result.assertions[0]
        outcome, opposite = ("passes", "fails") if passed else ("fails", "passes")
        support.check(
            self,
            entry.passed,
            passed,
            f"{call} {outcome}",
            f"{call} {opposite} where it should {outcome[:-1]}",
        )
        support.check(
            self,
            entry.expected,
            want_expected,
            f"{call} wrote expected={want_expected!r} into its report entry, the value it was called with",
            f"{call} wrote expected={entry.expected!r} into its report entry instead of the {want_expected!r} it was called with",
        )
        support.check(
            self,
            entry.actual,
            want_actual,
            f"{call} wrote actual={want_actual!r} into its report entry, the value it was called with",
            f"{call} wrote actual={entry.actual!r} into its report entry instead of the {want_actual!r} it was called with",
        )
        if not passed:
            kind = "AssertEqual" if method == "assertEqual" else "AssertNotEqual"
            line = f"[{kind}] EXPECTED: {want_expected} | ACTUAL: {want_actual} | MESSAGE: m"
            support.check(
                self,
                result.error_message,
                line,
                f"the failed step's error after {call} shows the compared values as given",
                f"the failed step's error after {call} does not show the compared values as given",
            )

    def bud_different_passes(self):
        """assertNotEqual(1, 2) passes."""
        self._one(
            lambda tc: tc.assertNotEqual(1, 2, msg="different"),
            True,
            "AssertNotEqual",
            "assertNotEqual(1, 2)",
        )

    def bud_same_fails(self):
        """assertNotEqual(42, 42) fails."""
        self._one(
            lambda tc: tc.assertNotEqual(42, 42, msg="same"),
            False,
            "AssertNotEqual",
            "assertNotEqual(42, 42)",
        )

    def bud_greater_passes(self):
        """assertGreater(10, 5) passes."""
        self._one(
            lambda tc: tc.assertGreater(10, 5, msg="greater"),
            True,
            "AssertGreater",
            "assertGreater(10, 5)",
        )

    def bud_greater_equal_fails(self):
        """assertGreater(5, 5) fails: the comparison is strict."""
        self._one(
            lambda tc: tc.assertGreater(5, 5, msg="equal"),
            False,
            "AssertGreater",
            "assertGreater(5, 5)",
        )

    def bud_greater_less_fails(self):
        """assertGreater(3, 10) fails."""
        self._one(
            lambda tc: tc.assertGreater(3, 10, msg="less"),
            False,
            "AssertGreater",
            "assertGreater(3, 10)",
        )

    def bud_less_passes(self):
        """assertLess(3, 10) passes."""
        self._one(
            lambda tc: tc.assertLess(3, 10, msg="less"), True, "AssertLess", "assertLess(3, 10)"
        )

    def bud_less_equal_fails(self):
        """assertLess(5, 5) fails: the comparison is strict."""
        self._one(
            lambda tc: tc.assertLess(5, 5, msg="equal"), False, "AssertLess", "assertLess(5, 5)"
        )

    def bud_less_greater_fails(self):
        """assertLess(10, 3) fails."""
        self._one(
            lambda tc: tc.assertLess(10, 3, msg="greater"), False, "AssertLess", "assertLess(10, 3)"
        )

    def bud_member_found_in_list(self):
        """assertIn(member=2, container=[1, 2, 3]) passes."""
        self._one(
            lambda tc: tc.assertIn(member=2, container=[1, 2, 3], msg="in list"),
            True,
            "AssertIn",
            "assertIn(member=2, container=[1, 2, 3])",
        )

    def bud_member_not_found_in_list(self):
        """assertIn(member=99, container=[1, 2, 3]) fails."""
        self._one(
            lambda tc: tc.assertIn(member=99, container=[1, 2, 3], msg="not in list"),
            False,
            "AssertIn",
            "assertIn(member=99, container=[1, 2, 3])",
        )

    def bud_in_string(self):
        """assertIn finds a substring."""
        self._one(
            lambda tc: tc.assertIn(member="abc", container="xxabcxx", msg="in string"),
            True,
            "AssertIn",
            "assertIn(member='abc', container='xxabcxx')",
        )

    def bud_in_dict_keys(self):
        """assertIn finds a dict key."""
        self._one(
            lambda tc: tc.assertIn(member="key", container={"key": "val"}, msg="in dict"),
            True,
            "AssertIn",
            "assertIn(member='key', container={'key': 'val'})",
        )

    def bud_in_bad_container_raises_typeerror(self):
        """assertIn with a container that has no __contains__ raises TypeError naming the requirement and the type."""
        exc = support.raised(
            support.quiet(BareCase()).assertIn, member=1, container=42, msg="bad container"
        )
        support.check(
            self,
            type(exc),
            TypeError,
            "assertIn(member=1, container=42) raises TypeError",
            "assertIn(member=1, container=42) did not raise TypeError",
        )
        support.check_in(
            self,
            "container with __contains__",
            str(exc),
            "the TypeError says a container with __contains__ is required",
            "the TypeError does not say a container with __contains__ is required",
        )
        support.check(
            self,
            str(exc)[-len("got int") :],
            "got int",
            "the TypeError ends by naming the type given, int",
            "the TypeError does not end by naming the type given, int",
        )

    def bud_member_not_present_passes(self):
        """assertNotIn(member=99, container=[1, 2, 3]) passes."""
        self._one(
            lambda tc: tc.assertNotIn(member=99, container=[1, 2, 3], msg="not present"),
            True,
            "AssertNotIn",
            "assertNotIn(member=99, container=[1, 2, 3])",
        )

    def bud_member_present_fails(self):
        """assertNotIn(member=2, container=[1, 2, 3]) fails."""
        self._one(
            lambda tc: tc.assertNotIn(member=2, container=[1, 2, 3], msg="present"),
            False,
            "AssertNotIn",
            "assertNotIn(member=2, container=[1, 2, 3])",
        )

    def bud_not_in_bad_container_raises_typeerror(self):
        """assertNotIn with a container that has no __contains__ raises TypeError."""
        exc = support.raised(
            support.quiet(BareCase()).assertNotIn, member=1, container=42, msg="bad container"
        )
        support.check(
            self,
            type(exc),
            TypeError,
            "assertNotIn(member=1, container=42) raises TypeError",
            "assertNotIn(member=1, container=42) did not raise TypeError",
        )
        support.check_in(
            self,
            "container with __contains__",
            str(exc),
            "the TypeError says a container with __contains__ is required",
            "the TypeError does not say a container with __contains__ is required",
        )

    def bud_within_absolute_tolerance(self):
        """42.5 is within 42.0 +/- 0.5 (upper edge)."""
        self._one(
            lambda tc: tc.assertInTolerance(actual=42.5, expected=42.0, absolute_tolerance=0.5),
            True,
            "AssertInTolerance",
            "assertInTolerance(actual=42.5, expected=42.0, absolute_tolerance=0.5)",
        )

    def bud_outside_absolute_tolerance(self):
        """43.0 is outside 42.0 +/- 0.5."""
        self._one(
            lambda tc: tc.assertInTolerance(actual=43.0, expected=42.0, absolute_tolerance=0.5),
            False,
            "AssertInTolerance",
            "assertInTolerance(actual=43.0, expected=42.0, absolute_tolerance=0.5)",
        )

    def bud_zero_absolute_tolerance_requires_exact_and_does_not_fall_through(self):
        """absolute_tolerance=0.0 means exact, also when relative_tolerance is given: 42.1 and 41.9 refused, 42.0 accepted."""

        def body(tc):
            tc.assertInTolerance(
                actual=42.1, expected=42.0, absolute_tolerance=0.0, relative_tolerance=0.5
            )
            tc.assertInTolerance(
                actual=41.9, expected=42.0, absolute_tolerance=0.0, relative_tolerance=0.5
            )
            tc.assertInTolerance(
                actual=42.0, expected=42.0, absolute_tolerance=0.0, relative_tolerance=0.5
            )

        support.check(
            self,
            [e.passed for e in entries(body)],
            [False, False, True],
            "absolute_tolerance=0.0 refuses 42.1 and 41.9 and accepts 42.0, whatever relative_tolerance says",
            "absolute_tolerance=0.0 did not refuse 42.1 and 41.9 and accept only 42.0; relative_tolerance leaked through",
        )

    def bud_relative_tolerance(self):
        """relative_tolerance=0.1 of 100 accepts 105 and refuses 111."""

        def body(tc):
            tc.assertInTolerance(actual=105.0, expected=100.0, relative_tolerance=0.1)
            tc.assertInTolerance(actual=111.0, expected=100.0, relative_tolerance=0.1)

        support.check(
            self,
            [e.passed for e in entries(body)],
            [True, False],
            "relative_tolerance=0.1 around 100 accepts 105 and refuses 111",
            "relative_tolerance=0.1 around 100 did not accept 105 and refuse 111",
        )

    def bud_no_tolerance_given_defaults_to_zero(self):
        """Without a tolerance the match is exact: 42.0 accepted, 42.1 refused."""

        def body(tc):
            tc.assertInTolerance(actual=42.0, expected=42.0)
            tc.assertInTolerance(actual=42.1, expected=42.0)

        support.check(
            self,
            [e.passed for e in entries(body)],
            [True, False],
            "assertInTolerance without a tolerance accepts exactly 42.0 and refuses 42.1",
            "assertInTolerance without a tolerance did not accept exactly 42.0 and refuse 42.1",
        )

    def bud_within_range_inclusive(self):
        """5, the lower edge 0 and the upper edge 10 are inside [0, 10]."""

        def body(tc):
            for value in (5.0, 0.0, 10.0):
                tc.assertInRange(actual=value, lower_bound=0.0, upper_bound=10.0)

        recorded = entries(body)
        support.check(
            self,
            [e.passed for e in recorded],
            [True, True, True],
            "assertInRange over [0, 10] accepts 5 and both edges, 0 and 10",
            "assertInRange over [0, 10] refused 5 or one of the edges 0 and 10",
        )
        support.check(
            self,
            [e.assertion_type for e in recorded],
            ["AssertInRange"] * 3,
            "each of the three range checks records an AssertInRange entry",
            "a range check recorded another entry type than AssertInRange",
        )

    def bud_outside_range(self):
        """11 above and -1 below [0, 10] are refused."""

        def body(tc):
            tc.assertInRange(actual=11.0, lower_bound=0.0, upper_bound=10.0)
            tc.assertInRange(actual=-1.0, lower_bound=0.0, upper_bound=10.0)

        support.check(
            self,
            [e.passed for e in entries(body)],
            [False, False],
            "assertInRange over [0, 10] refuses 11 above and -1 below",
            "assertInRange over [0, 10] accepted 11 or -1",
        )

    def bud_exclusive_bounds(self):
        """With include_bounds=False the edges 0 and 10 are refused and 5 is accepted."""

        def body(tc):
            for value in (0.0, 5.0, 10.0):
                tc.assertInRange(
                    actual=value, lower_bound=0.0, upper_bound=10.0, include_bounds=False
                )

        support.check(
            self,
            [e.passed for e in entries(body)],
            [False, True, False],
            "include_bounds=False refuses the edges 0 and 10 and accepts 5",
            "include_bounds=False did not refuse the edges 0 and 10 and accept 5",
        )

    def bud_lower_bound_only(self):
        """Without an upper bound: 10 and 5 accepted and 3 refused for >= 5; 5 refused and 6 accepted for > 5."""

        def body(tc):
            tc.assertInRange(actual=10.0, lower_bound=5.0)
            tc.assertInRange(actual=5.0, lower_bound=5.0)
            tc.assertInRange(actual=3.0, lower_bound=5.0)
            tc.assertInRange(actual=5.0, lower_bound=5.0, include_bounds=False)
            tc.assertInRange(actual=6.0, lower_bound=5.0, include_bounds=False)

        support.check(
            self,
            [e.passed for e in entries(body)],
            [True, True, False, False, True],
            "with only lower_bound=5, >= 5 accepts 10 and 5 and refuses 3, and > 5 refuses 5 and accepts 6",
            "with only lower_bound=5, the accepted and refused values differ from 10, 5 in and 3 out (>= 5) and 5 out, 6 in (> 5)",
        )

    def bud_pattern_matches(self):
        """assertRegex passes when the pattern is found."""
        self._one(
            lambda tc: tc.assertRegex(text="hello world", pattern=r"hello", msg="matches"),
            True,
            "AssertRegex",
            "assertRegex(text='hello world', pattern='hello')",
        )

    def bud_pattern_does_not_match(self):
        """assertRegex fails when the pattern is not found."""
        self._one(
            lambda tc: tc.assertRegex(text="hello world", pattern=r"goodbye", msg="no match"),
            False,
            "AssertRegex",
            "assertRegex(text='hello world', pattern='goodbye')",
        )

    def bud_complex_pattern(self):
        r"""assertRegex finds \d+ inside a string."""
        self._one(
            lambda tc: tc.assertRegex(text="foo123bar", pattern=r"\d+", msg="digits found"),
            True,
            "AssertRegex",
            r"assertRegex(text='foo123bar', pattern='\d+')",
        )

    def bud_skip_assert(self):
        """skipAssert records a passed, skipped Skip entry and the step still passes."""
        result = support.step(lambda tc: tc.skipAssert(msg="skipping this"))
        support.check(
            self,
            len(result.assertions),
            1,
            "skipAssert records exactly one entry",
            "skipAssert did not record exactly one entry",
        )
        entry = result.assertions[0]
        support.check(
            self,
            entry.passed,
            True,
            "skipAssert records a passed entry",
            "skipAssert recorded a failed entry",
        )
        support.check(
            self,
            entry.skipped,
            True,
            "skipAssert marks its entry as skipped",
            "skipAssert did not mark its entry as skipped",
        )
        support.check(
            self,
            entry.assertion_type,
            "Skip",
            "skipAssert records a Skip entry",
            "skipAssert recorded another entry type than Skip",
        )
        support.check(
            self,
            entry.message,
            "skipping this",
            "skipAssert keeps its message 'skipping this' in the entry",
            "skipAssert did not keep its message 'skipping this' in the entry",
        )
        support.check(
            self,
            result.passed,
            True,
            "a step holding only a skipAssert is reported as passed",
            "a step holding only a skipAssert is reported as failed",
        )
