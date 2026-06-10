"""Example API test using BudTestCase assertions."""

from budtestlibrary import BudTestCase


class ExampleAPITest(BudTestCase):
    def bud_health_endpoint(self):
        fake_status_code = 200
        fake_payload = {"status": "ok", "version": "2026.06"}

        self.assertEqual(fake_status_code, 200, msg="Health endpoint returns HTTP 200")
        self.assertEqual(fake_payload["status"], "ok", msg="Health payload reports ok status")
        self.assertRegex(
            text=fake_payload["version"],
            pattern=r"^\d{4}\.\d{2}$",
            msg="Version string uses YYYY.MM format",
        )


if __name__ == "__main__":
    ExampleAPITest().run()
