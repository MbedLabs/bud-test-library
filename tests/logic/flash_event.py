"""FlashSuccess, FlashFailure and FlashEvent.execute(): messages, to_dict(), the required failure message, timing, wrapped exceptions, the optional addr argument and the info and result getters."""

from budtestlibrary import BudTestCase, FlashEvent, FlashFailure, FlashSuccess, parameterized
from tests import support


class DemoEvent(FlashEvent):
    """Flash event stub with the Demo project info; subclasses define flash()."""

    def get_project_name(self):
        return "Demo"

    def get_firmware_version(self):
        return "1.0.0"

    def get_release(self):
        return "development"


class LegacyEvent(DemoEvent):
    """A one-argument flash() that always succeeds."""

    def flash(self, firmware_path):
        return FlashSuccess(message=f"Flashed {firmware_path}", metadata={"checksum": "abc123"})


class FailingEvent(DemoEvent):
    """A flash() that returns a recoverable failure."""

    def __init__(self):
        super().__init__()
        self.returned = None

    def flash(self, firmware_path):
        self.returned = FlashFailure(
            message="Connection timeout", error_code=0x0A, recoverable=True
        )
        return self.returned


class ExplodingEvent(DemoEvent):
    """A flash() that raises."""

    def flash(self, firmware_path):
        raise RuntimeError("Hardware disconnected")


class AddressEvent(DemoEvent):
    """A flash() with an optional addr that applies its own default and notes what it received."""

    DEFAULT_ADDR = 0x08000000

    def __init__(self):
        super().__init__()
        self.received = []

    def flash(self, firmware_path, addr=None):
        self.received.append(addr)
        target = self.DEFAULT_ADDR if addr is None else addr
        return FlashSuccess(
            message=f"Flashed {firmware_path} at 0x{target:X}", metadata={"addr": target}
        )


class KwargsEvent(DemoEvent):
    """A flash() that takes **kwargs."""

    def flash(self, firmware_path, **kwargs):
        return FlashSuccess(metadata={"kwargs": dict(kwargs)})


FIRMWARE = "/path/to/demo_firmware.bin"


class FlashEvents(BudTestCase):
    """FlashSuccess and FlashFailure: their messages and dictionaries, and how execute reports success, failure and an exception."""

    def bud_default_message(self):
        """FlashSuccess() has the default message and is a success."""
        fs = FlashSuccess()
        support.check(
            self,
            fs.message,
            "Flash completed successfully",
            "FlashSuccess() carries the default message Flash completed successfully",
            "FlashSuccess() does not carry the default message Flash completed successfully",
        )
        support.check(
            self,
            fs.is_success(),
            True,
            "FlashSuccess() is a success",
            "FlashSuccess() is not a success",
        )

    def bud_success_to_dict(self):
        """FlashSuccess.to_dict() has status, message, metadata, timestamp and duration, and no failure keys."""
        d = FlashSuccess(message="Done", metadata={"chk": "abc"}).to_dict()
        support.check(
            self,
            sorted(d),
            ["duration_seconds", "message", "metadata", "status", "timestamp"],
            "FlashSuccess.to_dict() has status, message, metadata, timestamp and duration and no failure keys",
            "FlashSuccess.to_dict() does not have exactly the success keys",
        )
        support.check(
            self,
            (d["status"], d["message"], d["metadata"]),
            ("success", "Done", {"chk": "abc"}),
            "FlashSuccess.to_dict() holds the expected status, message and metadata values",
            "FlashSuccess.to_dict() does not hold the expected values",
        )

    def bud_failure_message_required(self):
        """FlashFailure() without a message raises TypeError naming the message argument."""
        exc = support.raised(FlashFailure)
        support.check(
            self,
            support.raised_name(exc),
            "TypeError",
            "FlashFailure() without a message raises TypeError",
            "FlashFailure() without a message did not raise TypeError",
        )
        support.check_in(
            self,
            "'message'",
            str(exc),
            "the TypeError names the missing argument 'message'",
            "the TypeError does not name the missing argument 'message'",
        )

    @parameterized(["empty", "blank"])
    def bud_failure_message_must_not_be_blank(self, kind):
        """FlashFailure with an empty or whitespace-only message raises ValueError."""
        exc = support.raised(FlashFailure, "" if kind == "empty" else "   ")
        support.check(
            self,
            support.raised_name(exc),
            "ValueError",
            f"FlashFailure with a message that is {kind} raises ValueError",
            f"FlashFailure with a message that is {kind} did not raise ValueError",
        )
        support.check_in(
            self,
            "must be a non-empty string",
            str(exc),
            "the ValueError says the message must be a non-empty string",
            "the ValueError does not say the message must be a non-empty string",
        )

    def bud_failure_custom_message(self):
        """FlashFailure keeps its message, exposes it as error_message and is not a success."""
        ff = FlashFailure("Custom error")
        support.check(
            self,
            ff.message,
            "Custom error",
            "FlashFailure keeps its message Custom error",
            "FlashFailure did not keep its message Custom error",
        )
        support.check(
            self,
            ff.error_message,
            "Custom error",
            "FlashFailure exposes its message as error_message",
            "FlashFailure does not expose its message as error_message",
        )
        support.check(
            self,
            ff.is_success(),
            False,
            "FlashFailure is not a success",
            "FlashFailure is a success",
        )

    def bud_failure_to_dict(self):
        """FlashFailure.to_dict() has status, message, error_message, error_code, recoverable, timestamp and duration."""
        d = FlashFailure("Verify failed", error_code=42, recoverable=False).to_dict()
        support.check(
            self,
            sorted(d),
            [
                "duration_seconds",
                "error_code",
                "error_message",
                "message",
                "metadata",
                "recoverable",
                "status",
                "timestamp",
            ],
            "FlashFailure.to_dict() has exactly the failure keys, with error_code and recoverable",
            "FlashFailure.to_dict() does not have exactly the failure keys",
        )
        support.check(
            self,
            (d["status"], d["message"], d["error_message"], d["error_code"], d["recoverable"]),
            ("failure", "Verify failed", "Verify failed", 42, False),
            "FlashFailure.to_dict() holds status failure, the message Verify failed, error_code 42 and recoverable False",
            "FlashFailure.to_dict() does not hold the expected failure values",
        )

    def bud_recoverable_defaults_true(self):
        """recoverable defaults to True, in the object and in to_dict()."""
        ff = FlashFailure("err")
        support.check(
            self,
            ff.recoverable,
            True,
            "a FlashFailure is recoverable by default",
            "a FlashFailure is not recoverable by default",
        )
        support.check(
            self,
            ff.to_dict()["recoverable"],
            True,
            "to_dict() of a default FlashFailure holds recoverable True",
            "to_dict() of a default FlashFailure does not hold recoverable True",
        )

    def bud_successful_execute(self):
        """execute() returns the flash's FlashSuccess with its message and metadata and a non-negative duration."""
        result = LegacyEvent().execute(FIRMWARE)
        support.check(
            self,
            type(result).__name__,
            "FlashSuccess",
            "execute() returns a FlashSuccess for a flash that succeeds",
            "execute() returns another type than FlashSuccess for a flash that succeeds",
        )
        support.check(
            self,
            result.message,
            f"Flashed {FIRMWARE}",
            "the FlashSuccess carries the flash's message Flashed <firmware>",
            "the FlashSuccess does not carry the flash's message",
        )
        support.check(
            self,
            result.metadata,
            {"checksum": "abc123"},
            "the FlashSuccess passes the metadata checksum=abc123 through",
            "the FlashSuccess did not pass the metadata checksum=abc123 through",
        )
        support.check(
            self,
            result.duration_seconds is not None and result.duration_seconds >= 0,
            True,
            "execute() sets a non-negative duration on the result",
            "execute() did not set a non-negative duration on the result",
        )

    def bud_failing_execute(self):
        """execute() returns the flash's own FlashFailure unchanged."""
        event = FailingEvent()
        result = event.execute(FIRMWARE)
        support.check(
            self,
            result is event.returned,
            True,
            "execute() returns the flash's own FlashFailure object unchanged",
            "execute() returned another object than the flash's own FlashFailure",
        )
        support.check(
            self,
            (result.message, result.error_code, result.recoverable),
            ("Connection timeout", 0x0A, True),
            "the returned FlashFailure keeps message Connection timeout, error_code 0x0A and recoverable True",
            "the returned FlashFailure lost its message, error_code or recoverable",
        )

    def bud_exception_wrapped_as_flash_failure(self):
        """An exception from flash() becomes a non-recoverable FlashFailure holding its text, with a duration."""
        result = ExplodingEvent().execute(FIRMWARE)
        support.check(
            self,
            type(result).__name__,
            "FlashFailure",
            "an exception raised by flash() becomes a FlashFailure",
            "an exception raised by flash() did not become a FlashFailure",
        )
        support.check(
            self,
            result.message,
            "Unexpected error: Hardware disconnected",
            "the FlashFailure message is Unexpected error: Hardware disconnected",
            "the FlashFailure message is not Unexpected error: Hardware disconnected",
        )
        support.check(
            self,
            result.recoverable,
            False,
            "the FlashFailure from an exception is not recoverable",
            "the FlashFailure from an exception is recoverable",
        )
        support.check(
            self,
            result.duration_seconds is not None,
            True,
            "the FlashFailure from an exception has a duration",
            "the FlashFailure from an exception has no duration",
        )

    def bud_addr_is_optional_and_defaults_to_none(self):
        """execute(path) passes addr=None and the implementation applies its default."""
        event = AddressEvent()
        result = event.execute(FIRMWARE)
        support.check(
            self,
            event.received,
            [None],
            "execute(path) passes addr=None to flash()",
            "execute(path) did not pass addr=None to flash()",
        )
        support.check(
            self,
            result.metadata["addr"],
            AddressEvent.DEFAULT_ADDR,
            "flash() applies its own default address when addr is None",
            "flash() did not apply its default address when addr is None",
        )

    def bud_addr_forwarded_as_keyword(self):
        """execute(path, addr=...) reaches flash()."""
        result = AddressEvent().execute(FIRMWARE, addr=0x08020000)
        support.check(
            self,
            result.metadata["addr"],
            0x08020000,
            "execute(path, addr=0x08020000) reaches flash() as the address",
            "execute(path, addr=0x08020000) did not reach flash() as the address",
        )
        support.check_in(
            self,
            "0x8020000",
            result.message,
            "the result message names the address 0x8020000",
            "the result message does not name the address 0x8020000",
        )

    def bud_addr_forwarded_as_positional(self):
        """execute(path, addr) with addr as second positional argument reaches flash()."""
        event = AddressEvent()
        result = event.execute(FIRMWARE, 0x08020000)
        support.check(
            self,
            event.received,
            [0x08020000],
            "execute(path, 0x08020000) passes the positional address to flash()",
            "execute(path, 0x08020000) did not pass the positional address to flash()",
        )
        support.check(
            self,
            result.metadata["addr"],
            0x08020000,
            "the result metadata records the address 0x08020000",
            "the result metadata does not record the address 0x08020000",
        )

    def bud_legacy_signature_still_works(self):
        """A one-argument flash() is called by execute(path) and succeeds."""
        support.check(
            self,
            LegacyEvent().execute(FIRMWARE).is_success(),
            True,
            "a one-argument flash() called by execute(path) succeeds",
            "a one-argument flash() called by execute(path) failed",
        )

    def bud_legacy_signature_rejects_explicit_addr(self):
        """A one-argument flash() given an addr yields a non-recoverable FlashFailure naming the class and addr."""
        result = LegacyEvent().execute(FIRMWARE, addr=0x08000000)
        support.check(
            self,
            type(result).__name__,
            "FlashFailure",
            "a one-argument flash() given an addr yields a FlashFailure",
            "a one-argument flash() given an addr did not yield a FlashFailure",
        )
        support.check(
            self,
            result.recoverable,
            False,
            "that FlashFailure is not recoverable",
            "that FlashFailure is recoverable",
        )
        support.check_in(
            self,
            "does not accept an 'addr' keyword argument",
            result.message,
            "the failure message says flash() does not accept an 'addr' keyword argument",
            "the failure message does not explain that addr is not accepted",
        )
        support.check_in(
            self,
            "LegacyEvent",
            result.message,
            "the failure message names the class LegacyEvent",
            "the failure message does not name the class LegacyEvent",
        )

    def bud_var_kwargs_signature_receives_addr(self):
        """A flash(path, **kwargs) receives addr in its keyword arguments."""
        result = KwargsEvent().execute(FIRMWARE, addr=0x1000)
        support.check(
            self,
            result.metadata["kwargs"],
            {"addr": 0x1000},
            "a flash(path, **kwargs) receives addr=0x1000 among its keyword arguments",
            "a flash(path, **kwargs) did not receive addr=0x1000 among its keyword arguments",
        )

    def bud_get_info(self):
        """get_info() returns the three implementation values."""
        support.check(
            self,
            LegacyEvent().get_info(),
            {"project_name": "Demo", "firmware_version": "1.0.0", "release": "development"},
            "get_info() returns project Demo, firmware 1.0.0 and release development",
            "get_info() does not return project Demo, firmware 1.0.0 and release development",
        )

    def bud_get_result_before_execute(self):
        """get_result() is None before any run."""
        support.check(
            self,
            LegacyEvent().get_result(),
            None,
            "get_result() is None before any run",
            "get_result() is not None before any run",
        )

    def bud_get_result_after_execute(self):
        """get_result() is the very result execute() returned."""
        event = LegacyEvent()
        returned = event.execute(FIRMWARE)
        support.check(
            self,
            event.get_result() is returned,
            True,
            "get_result() is the very object execute() returned",
            "get_result() is another object than the one execute() returned",
        )
        support.check(
            self,
            type(event.get_result()).__name__,
            "FlashSuccess",
            "get_result() is a FlashSuccess after a successful run",
            "get_result() is not a FlashSuccess after a successful run",
        )

    def bud_get_duration(self):
        """get_duration() is None before a run and a non-negative number after."""
        event = LegacyEvent()
        support.check(
            self,
            event.get_duration(),
            None,
            "get_duration() is None before any run",
            "get_duration() is not None before any run",
        )
        event.execute(FIRMWARE)
        duration = event.get_duration()
        support.check(
            self,
            isinstance(duration, float) and duration >= 0,
            True,
            "get_duration() is a non-negative number after a run",
            "get_duration() is not a non-negative number after a run",
        )
