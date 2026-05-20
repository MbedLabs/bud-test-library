"""Example demonstrating FlashEvent for firmware flashing."""

from budtestlibrary import FlashEvent, FlashSuccess, FlashFailure


class ESP32FlashEvent(FlashEvent):
    """Example flash event for an ESP32 device."""

    def flash(self, firmware_path):
        # Simulated flash operation
        if not firmware_path.endswith(".bin"):
            return FlashFailure(
                "Unsupported firmware format",
                error_code=0x01,
                recoverable=False,
            )
        # Simulate successful flash
        return FlashSuccess(
            message=f"Flashed {firmware_path} to ESP32",
            metadata={"checksum": "a1b2c3", "size_bytes": 1048576},
        )

    def get_project_name(self):
        return "ESP32-SensorHub"

    def get_firmware_version(self):
        return "2.1.0"

    def get_release(self):
        return "production"


if __name__ == "__main__":
    event = ESP32FlashEvent()

    # Successful flash
    result = event.execute("/path/to/firmware.bin")
    print(f"Success: {result.is_success()}")
    print(f"Duration: {event.get_duration():.3f}s")
    print(f"Result: {result.to_dict()}")

    # Failed flash
    result2 = event.execute("invalid_file.txt")
    print(f"\nSuccess: {result2.is_success()}")
    print(f"Recoverable: {result2.recoverable}")

    # Flash info
    info = event.get_info()
    print(f"\nProject: {info['project_name']}")
    print(f"Version: {info['firmware_version']}")
    print(f"Release: {info['release']}")
