"""Example Hardware-in-the-Loop style test."""

from budtestlibrary import BloomMetaData, BudTestCase


class PowerRailHILTest(BudTestCase):
    bloom_metadata = BloomMetaData("PWR", "101")

    def setUpClass(self):
        self.log_info("Opening serial session to the target board")

    def bud_3v3_rail_stable(self):
        measured_voltage = 3.31
        self.assertInTolerance(
            actual=measured_voltage,
            expected=3.30,
            absolute_tolerance=0.05,
            msg="3V3 rail stays within tolerance under load",
        )

    def bud_boot_banner_present(self):
        boot_log = "BOOT OK - firmware 2026.06"
        self.assertRegex(
            text=boot_log,
            pattern=r"BOOT OK",
            msg="Target board publishes the expected boot banner",
        )


if __name__ == "__main__":
    PowerRailHILTest().run()
