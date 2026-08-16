"""Tests for FlashEvent, FlashSuccess, FlashFailure."""

import pytest

from budtestlibrary.flash_event import (
    FlashEvent,
    FlashFailure,
    FlashStatus,
    FlashSuccess,
)


class StubFlashEvent(FlashEvent):
    """A minimal flash event that always succeeds."""

    def flash(self, firmware_path):
        return FlashSuccess(
            message=f"Flashed {firmware_path}",
            metadata={"checksum": "abc123"},
        )

    def get_project_name(self):
        return "TestProject"

    def get_firmware_version(self):
        return "1.0.0"

    def get_release(self):
        return "development"


class FailingFlashEvent(FlashEvent):
    """A flash event that always fails."""

    def flash(self, firmware_path):
        return FlashFailure(
            message="Connection timeout",
            error_code=0x0A,
            recoverable=True,
        )

    def get_project_name(self):
        return "BadProject"

    def get_firmware_version(self):
        return "0.0.0"

    def get_release(self):
        return "broken"


class ExplodingFlashEvent(FlashEvent):
    """A flash event whose flash() raises an exception."""

    def flash(self, firmware_path):
        raise RuntimeError("Hardware disconnected")

    def get_project_name(self):
        return "Crash"

    def get_firmware_version(self):
        return "?"

    def get_release(self):
        return "broken"


class AddressAwareFlashEvent(FlashEvent):
    """A flash event that accepts an optional target address."""

    DEFAULT_ADDR = 0x08000000

    def flash(self, firmware_path, addr=None):
        target_addr = self.DEFAULT_ADDR if addr is None else addr
        return FlashSuccess(
            message=f"Flashed {firmware_path} at 0x{target_addr:X}",
            metadata={"addr": target_addr},
        )

    def get_project_name(self):
        return "AddrProject"

    def get_firmware_version(self):
        return "1.0.0"

    def get_release(self):
        return "development"


class VarKwargsFlashEvent(FlashEvent):
    """A flash event that absorbs extra arguments via **kwargs."""

    def flash(self, firmware_path, **kwargs):
        return FlashSuccess(metadata={"addr": kwargs.get("addr")})

    def get_project_name(self):
        return "KwargsProject"

    def get_firmware_version(self):
        return "1.0.0"

    def get_release(self):
        return "development"


class TestFlashSuccess:
    def test_default_message(self):
        fs = FlashSuccess()
        assert fs.message == "Flash completed successfully"
        assert fs.is_success()

    def test_custom_message(self):
        fs = FlashSuccess(message="Custom success")
        assert fs.message == "Custom success"

    def test_to_dict(self):
        fs = FlashSuccess(message="Done", metadata={"chk": "abc"})
        d = fs.to_dict()
        assert d["status"] == "success"
        assert d["message"] == "Done"
        assert d["metadata"] == {"chk": "abc"}
        assert "timestamp" in d
        assert "duration_seconds" in d
        assert "error_message" not in d
        assert "error_code" not in d
        assert "recoverable" not in d


class TestFlashFailure:
    def test_message_required(self):
        with pytest.raises(TypeError, match="missing 1 required positional argument"):
            FlashFailure()  # message is required

    def test_custom_message(self):
        ff = FlashFailure("Custom error")
        assert ff.message == "Custom error"
        assert ff.error_message == "Custom error"
        assert not ff.is_success()

    def test_to_dict(self):
        ff = FlashFailure("Verify failed", error_code=42, recoverable=False)
        d = ff.to_dict()
        assert d["status"] == "failure"
        assert d["message"] == "Verify failed"
        assert d["error_message"] == "Verify failed"
        assert d["error_code"] == 42
        assert d["recoverable"] is False
        assert "timestamp" in d
        assert "duration_seconds" in d

    def test_recoverable_defaults_true(self):
        ff = FlashFailure("err")
        assert ff.recoverable is True
        assert ff.to_dict()["recoverable"] is True


class TestFlashEventExecute:
    def test_successful_execute(self):
        event = StubFlashEvent()
        result = event.execute("/path/to/firmware.bin")
        assert isinstance(result, FlashSuccess)
        assert result.is_success()
        assert result.message.startswith("Flashed")
        assert result.duration_seconds is not None
        assert result.metadata == {"checksum": "abc123"}

    def test_failing_execute(self):
        event = FailingFlashEvent()
        result = event.execute("/path/to/firmware.bin")
        assert isinstance(result, FlashFailure)
        assert not result.is_success()
        assert result.message == "Connection timeout"
        assert result.error_code == 0x0A
        assert result.recoverable is True

    def test_exception_wrapped_as_flash_failure(self):
        event = ExplodingFlashEvent()
        result = event.execute("/path/to/firmware.bin")
        assert isinstance(result, FlashFailure)
        assert "Hardware disconnected" in result.message
        assert result.recoverable is False
        assert result.duration_seconds is not None

    def test_duration_captured(self):
        event = StubFlashEvent()
        result = event.execute("/path/to/firmware.bin")
        assert result.duration_seconds is not None
        assert result.duration_seconds >= 0


class TestFlashEventAddr:
    def test_addr_is_optional_and_defaults_to_none(self):
        event = AddressAwareFlashEvent()
        result = event.execute("/path/to/firmware.bin")
        assert result.is_success()
        assert result.metadata["addr"] == AddressAwareFlashEvent.DEFAULT_ADDR

    def test_addr_forwarded_as_keyword(self):
        event = AddressAwareFlashEvent()
        result = event.execute("/path/to/firmware.bin", addr=0x08020000)
        assert result.is_success()
        assert result.metadata["addr"] == 0x08020000
        assert "0x8020000" in result.message

    def test_addr_forwarded_as_positional(self):
        event = AddressAwareFlashEvent()
        result = event.execute("/path/to/firmware.bin", 0x08020000)
        assert result.metadata["addr"] == 0x08020000

    def test_flash_called_directly_without_addr(self):
        event = AddressAwareFlashEvent()
        result = event.flash("/path/to/firmware.bin")
        assert result.metadata["addr"] == AddressAwareFlashEvent.DEFAULT_ADDR

    def test_legacy_signature_still_works(self):
        """Subclasses without an `addr` parameter keep working unchanged."""
        event = StubFlashEvent()
        assert event._flash_accepts_addr() is False
        result = event.execute("/path/to/firmware.bin")
        assert result.is_success()

    def test_legacy_signature_rejects_explicit_addr(self):
        event = StubFlashEvent()
        result = event.execute("/path/to/firmware.bin", addr=0x08000000)
        assert isinstance(result, FlashFailure)
        assert not result.recoverable
        assert "does not accept an 'addr' keyword argument" in result.message
        assert "StubFlashEvent" in result.message

    def test_var_kwargs_signature_receives_addr(self):
        event = VarKwargsFlashEvent()
        assert event._flash_accepts_addr() is True
        result = event.execute("/path/to/firmware.bin", addr=0x1000)
        assert result.metadata["addr"] == 0x1000


class TestFlashEventInfo:
    def test_get_info(self):
        event = StubFlashEvent()
        info = event.get_info()
        assert info["project_name"] == "TestProject"
        assert info["firmware_version"] == "1.0.0"
        assert info["release"] == "development"

    def test_get_result_before_execute(self):
        event = StubFlashEvent()
        assert event.get_result() is None

    def test_get_result_after_execute(self):
        event = StubFlashEvent()
        event.execute("/path/to/firmware.bin")
        result = event.get_result()
        assert isinstance(result, FlashSuccess)

    def test_get_duration(self):
        event = StubFlashEvent()
        assert event.get_duration() is None
        event.execute("/path/to/firmware.bin")
        assert event.get_duration() is not None
        assert event.get_duration() >= 0


class TestFlashStatus:
    def test_enum_values(self):
        assert FlashStatus.PENDING.value == "pending"
        assert FlashStatus.IN_PROGRESS.value == "in_progress"
        assert FlashStatus.SUCCESS.value == "success"
        assert FlashStatus.FAILURE.value == "failure"
