"""Example demonstrating FlashEvent for firmware flashing."""

from budtestlibrary import FlashEvent, FlashFailure, FlashSuccess


class ESP32FlashEvent(FlashEvent):
    """Example flash event for an ESP32 device."""

    DEFAULT_ADDR = 0x10000

    def flash(self, firmware_path, addr=None):
        # Simulated flash operation
        if not firmware_path.endswith(".bin"):
            return FlashFailure(
                "Unsupported firmware format",
                error_code=0x01,
                recoverable=False,
            )
        # addr is optional: fall back to the platform default when omitted
        target_addr = self.DEFAULT_ADDR if addr is None else addr
        # Simulate successful flash
        return FlashSuccess(
            message=f"Flashed {firmware_path} to ESP32 at 0x{target_addr:X}",
            metadata={
                "checksum": "a1b2c3",
                "size_bytes": 1048576,
                "addr": target_addr,
            },
        )

    def get_project_name(self):
        return "ESP32-SensorHub"

    def get_firmware_version(self):
        return "2.1.0"

    def get_release(self):
        return "production"


if __name__ == "__main__":
    event = ESP32FlashEvent()

    # Successful flash at the platform default address
    result = event.execute("/path/to/firmware.bin")
    print(f"Success: {result.is_success()}")
    print(f"Duration: {event.get_duration():.3f}s")
    print(f"Result: {result.to_dict()}")

    # Successful flash at an explicit address
    result_at_addr = event.execute("/path/to/bootloader.bin", addr=0x1000)
    print(f"\nFlashed at address: 0x{result_at_addr.metadata['addr']:X}")

    # Failed flash
    result2 = event.execute("invalid_file.txt")
    print(f"\nSuccess: {result2.is_success()}")
    print(f"Recoverable: {result2.recoverable}")

    # Flash info
    info = event.get_info()
    print(f"\nProject: {info['project_name']}")
    print(f"Version: {info['firmware_version']}")
    print(f"Release: {info['release']}")
