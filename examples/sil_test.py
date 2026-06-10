"""Example Software-in-the-Loop style test."""

from budtestlibrary import BudTestCase


class PricingEngineSILTest(BudTestCase):
    def bud_discount_calculation(self):
        subtotal = 120.0
        discount = 0.10
        total = subtotal * (1 - discount)
        self.assertEqual(total, 108.0, msg="Discounted total is deterministic")

    def bud_risk_score_within_bounds(self):
        risk_score = 0.42
        self.assertInRange(
            actual=risk_score,
            lower_bound=0.0,
            upper_bound=1.0,
            msg="Risk score remains normalized",
        )


if __name__ == "__main__":
    PricingEngineSILTest().run()
