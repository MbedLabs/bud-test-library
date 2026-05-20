"""Minimal example demonstrating BudTestCase usage."""

from budtestlibrary import BudTestCase


class HelloWorldTest(BudTestCase):
    def bud_hello(self):
        self.assertTrue(True, msg="Hello, world!")

    def bud_numbers(self):
        self.assertEqual(2 + 2, 4, msg="Basic arithmetic works")
        self.assertGreater(10, 5, msg="Ten is greater than five")
        self.assertLess(3, 10, msg="Three is less than ten")

    def bud_collections(self):
        self.assertIn(member="apple", container=["apple", "banana", "cherry"], msg="Found apple")
        self.assertNotIn(member=99, container=[1, 2, 3], msg="99 not in list")

    def bud_regex(self):
        self.assertRegex(
            text="Error: timeout on port 443",
            pattern=r"timeout",
            msg="Error message contains timeout",
        )

    def bud_tolerance(self):
        self.assertInTolerance(
            actual=9.95,
            expected=10.0,
            absolute_tolerance=0.1,
            msg="Within 0.1 of 10.0",
        )
        # Zero tolerance means exact match
        self.assertInTolerance(
            actual=42.0,
            expected=42.0,
            absolute_tolerance=0.0,
            msg="Exact match required",
        )


if __name__ == "__main__":
    test = HelloWorldTest()
    test.run()
