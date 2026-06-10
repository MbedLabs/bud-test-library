"""Example demonstrating BloomMetaData integration."""

from budtestlibrary import BudTestCase, BloomMetaData


class MotorControllerTest(BudTestCase):
    bloom_metadata = BloomMetaData(project="MCU", tc_id_suffix="001")

    def bud_speed_control(self):
        # Simulated motor speed reading
        measured_speed = 1498.5  # RPM
        target_speed = 1500.0
        self.assertInTolerance(
            actual=measured_speed,
            expected=target_speed,
            absolute_tolerance=5.0,
            msg="Motor speed within ±5 RPM of target",
        )

    def bud_current_draw(self):
        measured_current = 1.2  # Amps
        max_current = 2.0
        self.assertLess(
            actual=measured_current,
            expected=max_current,
            msg="Current draw within safe limit",
        )
        self.assertGreater(measured_current, 0.0, msg="Current is positive")


if __name__ == "__main__":
    test = MotorControllerTest()
    test.run()
    results = test.get_results()
    for r in results:
        print(f"\nMethod: {r.method_name}")
        print(f"  Passed: {r.passed}")
        print(f"  Duration: {r.duration_seconds:.3f}s")
        print(f"  TC ID: {r.metadata.get('tc_id', 'N/A')}")
