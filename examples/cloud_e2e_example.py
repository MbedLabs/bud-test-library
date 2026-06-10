"""Example cloud / end-to-end style test."""

from budtestlibrary import BudTestCase, BloomMetaData


class DeviceProvisioningE2ETest(BudTestCase):
    bloom_metadata = BloomMetaData("E2E", "301")

    def bud_device_provisions(self):
        provisioning_state = "connected"
        self.assertEqual(
            provisioning_state,
            "connected",
            msg="Device reaches the connected state in the cloud",
        )

    def bud_event_reaches_pipeline(self):
        pipeline_latency_seconds = 1.8
        self.assertLess(
            actual=pipeline_latency_seconds,
            expected=5.0,
            msg="Telemetry reaches the processing pipeline within SLA",
        )


if __name__ == "__main__":
    DeviceProvisioningE2ETest().run()
