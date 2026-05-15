"""
FlashEvent - Abstract base class for firmware flashing operations.

Provides a standardized interface for implementing firmware flash
functionality across different hardware platforms.

Usage:
    class MyFlashEvent(FlashEvent):
        def flash(self, firmware_path):
            # Perform flashing
            if success:
                return FlashSuccess()
            else:
                return FlashFailure("Flash verification failed")
        
        def get_project_name(self) -> str:
            return "MyProject"
        
        def get_firmware_version(self) -> str:
            return "1.2.3"
        
        def get_release(self) -> str:
            return "production"
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime
from enum import Enum


class FlashStatus(Enum):
    """Status of a flash operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass
class FlashResult:
    """Base class for flash operation results."""
    status: FlashStatus
    timestamp: datetime = field(default_factory=datetime.now)
    duration_seconds: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_success(self) -> bool:
        """Check if the flash was successful."""
        return self.status == FlashStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata,
        }


@dataclass
class FlashSuccess(FlashResult):
    """
    Indicates a successful flash operation.
    
    Usage:
        return FlashSuccess()
        return FlashSuccess(metadata={"checksum": "abc123"})
    """
    status: FlashStatus = field(default=FlashStatus.SUCCESS, init=False)
    message: str = "Flash completed successfully"

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result["message"] = self.message
        return result


@dataclass
class FlashFailure(FlashResult):
    """
    Indicates a failed flash operation.
    
    Usage:
        return FlashFailure("Connection timeout")
        return FlashFailure("Verification failed", error_code=0x0A)
    """
    status: FlashStatus = field(default=FlashStatus.FAILURE, init=False)
    message: str = "Flash failed"
    error_code: Optional[int] = None
    recoverable: bool = True

    @property
    def error_message(self) -> str:
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result["message"] = self.message
        result["error_message"] = self.message
        result["error_code"] = self.error_code
        result["recoverable"] = self.recoverable
        return result


class FlashEvent(ABC):
    """
    Abstract base class for firmware flashing events.
    
    Implement this class to define custom flash behavior for your
    hardware platform.
    
    Required methods to implement:
        - flash(): Perform the flash operation
        - get_project_name(): Return the project name
        - get_firmware_version(): Return the firmware version
        - get_release(): Return the release type/status
    """

    def __init__(self):
        """Initialize the flash event."""
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None
        self._result: Optional[FlashResult] = None

    @abstractmethod
    def flash(self, firmware_path: str) -> FlashResult:
        """
        Perform the firmware flash operation.
        
        This method should:
        1. Connect to the target device
        2. Erase the target memory (if needed)
        3. Program the firmware
        4. Verify the flash (if supported)
        
        Args:
            firmware_path: Path to the firmware file to flash.
        
        Returns:
            FlashSuccess if the flash completed successfully.
            FlashFailure if the flash failed, with error details.
        """
        pass

    @abstractmethod
    def get_project_name(self) -> str:
        """
        Get the project name for the firmware.
        
        Returns:
            Project name string (e.g., "BMS_Master", "BigPack").
        """
        pass

    @abstractmethod
    def get_firmware_version(self) -> str:
        """
        Get the firmware version being flashed.
        
        Returns:
            Version string (e.g., "1.2.3", "2.0.0-beta").
        """
        pass

    @abstractmethod
    def get_release(self) -> str:
        """
        Get the release type or status.
        
        Returns:
            Release type string (e.g., "development", "staging", "production").
        """
        pass

    def execute(self, firmware_path: str) -> FlashResult:
        """
        Execute the flash operation with timing.
        
        This is the main entry point for running a flash.
        It wraps the flash() method with timing and error handling.
        
        Args:
            firmware_path: Path to the firmware file to flash.
        
        Returns:
            FlashResult with success or failure details.
        """
        self._start_time = datetime.now()
        
        try:
            self._result = self.flash(firmware_path)
        except Exception as e:
            self._result = FlashFailure(
                message=f"Unexpected error: {str(e)}",
                recoverable=False,
            )
        
        self._end_time = datetime.now()
        
        if self._result:
            self._result.duration_seconds = (
                self._end_time - self._start_time
            ).total_seconds()
        
        return self._result

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the flash event.
        
        Returns:
            Dictionary with project, version, and release info.
        """
        return {
            "project_name": self.get_project_name(),
            "firmware_version": self.get_firmware_version(),
            "release": self.get_release(),
        }

    def get_result(self) -> Optional[FlashResult]:
        """Get the result of the last flash operation."""
        return self._result

    def get_duration(self) -> Optional[float]:
        """Get the duration of the last flash operation in seconds."""
        if self._start_time and self._end_time:
            return (self._end_time - self._start_time).total_seconds()
        return None
