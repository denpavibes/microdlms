"""DLMS/COSEM enumerations, domain dataclasses, and sans-I/O event types."""

from __future__ import annotations

import datetime
from collections.abc import Sequence
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Self


class AssociationResult(IntEnum):
    """Result of DLMS association request (AARE result)."""

    ACCEPTED = 0
    REJECTED_PERMANENT = 1
    REJECTED_TRANSIENT = 2


class AssociationDiagnostic(IntEnum):
    """Diagnostic reasons for DLMS association rejection."""

    NO_REASON_GIVEN = 0
    APPLICATION_CONTEXT_NAME_NOT_SUPPORTED = 1
    CALLING_AP_TITLE_NOT_RECOGNIZED = 2
    CALLING_AP_INVOCATION_IDENTIFIER_NOT_RECOGNIZED = 3
    CALLING_AE_QUALIFIER_NOT_RECOGNIZED = 4
    CALLING_AE_INVOCATION_IDENTIFIER_NOT_RECOGNIZED = 5
    CALLED_AP_TITLE_NOT_RECOGNIZED = 6
    CALLED_AP_INVOCATION_IDENTIFIER_NOT_RECOGNIZED = 7
    CALLED_AE_QUALIFIER_NOT_RECOGNIZED = 8
    CALLED_AE_INVOCATION_IDENTIFIER_NOT_RECOGNIZED = 9
    AUTHENTICATION_MECHANISM_NAME_NOT_RECOGNIZED = 11
    AUTHENTICATION_MECHANISM_NAME_REQUIRED = 12
    AUTHENTICATION_FAILURE = 13
    AUTHENTICATION_REQUIRED = 14


class DataAccessResult(IntEnum):
    """Result error codes for DLMS Get/Set data access requests."""

    SUCCESS = 0
    HARDWARE_FAULT = 1
    TEMPORARY_FAILURE = 2
    READ_WRITE_DENIED = 3
    OBJECT_UNDEFINED = 4
    OBJECT_CLASS_INCONSISTENT = 9
    OBJECT_UNAVAILABLE = 11
    TYPE_UNMATCHED = 12
    SCOPE_OF_ACCESS_VIOLATED = 13
    DATA_BLOCK_UNAVAILABLE = 14
    LONG_GET_ABORTED = 15
    NO_LONG_GET_IN_PROGRESS = 16
    LONG_SET_ABORTED = 17
    NO_LONG_SET_IN_PROGRESS = 18
    DATA_BLOCK_NUMBER_INVALID = 19
    OTHER_REASON = 250


class InterfaceClass(IntEnum):
    """Standard DLMS/COSEM interface class identifiers."""

    DATA = 1
    REGISTER = 3
    EXTENDED_REGISTER = 4
    DEMAND_REGISTER = 5
    REGISTER_ACTIVATION = 6
    PROFILE_GENERIC = 7
    CLOCK = 8
    SCRIPT_TABLE = 9
    SCHEDULE = 10
    SPECIAL_DAYS_TABLE = 11
    ASSOCIATION_SN = 12
    ASSOCIATION_LN = 15
    SAP_ASSIGNMENT = 17
    IMAGE_TRANSFER = 18
    IEC_LOCAL_PORT_SETUP = 19
    ACTIVITY_CALENDAR = 20
    REGISTER_MONITOR = 21
    SINGLE_ACTION_SCHEDULE = 22
    TCP_UDP_SETUP = 25
    IPV4_SETUP = 27
    ETHERNET_SETUP = 28
    PUSH_SETUP = 40
    GPRS_SETUP = 45
    GSM_DIAGNOSTICS = 47
    DISCONNECT_CONTROL = 70
    LIMITER = 71
    MBUS_CLIENT = 72


@dataclass(frozen=True, slots=True)
class ScalerUnit:
    """COSEM scaler and unit pair representing measurement scale and engineering unit."""

    scaler: int
    unit: int

    @classmethod
    def from_structure(cls, data: Sequence[Any]) -> Self:
        """Construct ScalerUnit from an A-XDR decoded structure [scaler, unit]."""
        if len(data) != 2:
            raise ValueError(f"Expected 2 elements for scaler_unit structure, got {len(data)}")
        return cls(scaler=int(data[0]), unit=int(data[1]))

    def scale(self, value: int | float) -> float:
        """Apply scaler factor to convert raw integer to scaled measurement value."""
        return float(value) * (10.0**self.scaler)


@dataclass(frozen=True, slots=True)
class CosemDateTime:
    """Represents a 12-byte DLMS/COSEM date-time field."""

    year: int
    month: int
    day: int
    day_of_week: int
    hour: int
    minute: int
    second: int
    hundredths: int
    deviation: int | None
    status: int

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        """Parse DLMS 12-byte octet string into CosemDateTime."""
        if len(data) != 12:
            raise ValueError(f"COSEM date-time requires 12 bytes, got {len(data)}")
        year = int.from_bytes(data[0:2], "big")
        month = data[2]
        day = data[3]
        day_of_week = data[4]
        hour = data[5]
        minute = data[6]
        second = data[7]
        hundredths = data[8]
        raw_deviation = int.from_bytes(data[9:11], "big", signed=True)
        deviation = None if raw_deviation == -32768 else raw_deviation
        status = data[11]
        return cls(
            year=year,
            month=month,
            day=day,
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            second=second,
            hundredths=hundredths,
            deviation=deviation,
            status=status,
        )

    def as_datetime(self) -> datetime.datetime | None:
        """Convert to standard Python datetime with timezone offset if date is specified."""
        if self.year == 0xFFFF or self.month == 0xFF or self.day == 0xFF:
            return None
        time_zone = (
            datetime.timezone(datetime.timedelta(minutes=self.deviation))
            if (self.deviation is not None and -1439 <= self.deviation <= 1439)
            else datetime.UTC
        )
        microsecond = (self.hundredths * 10000) if (0 <= self.hundredths < 100) else 0
        return datetime.datetime(
            year=self.year,
            month=self.month,
            day=self.day,
            hour=self.hour if self.hour != 0xFF else 0,
            minute=self.minute if self.minute != 0xFF else 0,
            second=self.second if self.second != 0xFF else 0,
            microsecond=microsecond,
            tzinfo=time_zone,
        )

    def to_datetime(self) -> datetime.datetime | None:
        """Alias for as_datetime()."""
        return self.as_datetime()


# Sans-I/O Session Event Types


@dataclass(frozen=True, slots=True)
class ConnectedEvent:
    """Emitted when HDLC connection is established (UA received in response to SNRM)."""


@dataclass(frozen=True, slots=True)
class AssociatedEvent:
    """Emitted when application association is successfully established (AARE Accepted)."""


@dataclass(frozen=True, slots=True)
class AssociationRejectedEvent:
    """Emitted when association is rejected by meter."""

    result: AssociationResult
    diagnostic: int


@dataclass(frozen=True, slots=True)
class GetResponseEvent:
    """Emitted when a Get-Response-Normal returns successfully with attribute data."""

    invoke_id: int
    value: Any


@dataclass(frozen=True, slots=True)
class GetAccessErrorEvent:
    """Emitted when a Get-Response-Normal returns a DataAccessResult error code."""

    invoke_id: int
    error_code: DataAccessResult


@dataclass(frozen=True, slots=True)
class ReleasedEvent:
    """Emitted when application association is released (RLRE received)."""

    reason: int = 0


@dataclass(frozen=True, slots=True)
class DisconnectedEvent:
    """Emitted when HDLC connection is disconnected (UA received in response to DISC)."""


@dataclass(frozen=True, slots=True)
class ProtocolErrorEvent:
    """Emitted when a protocol invariant violation, framing error, or CRC error occurs."""

    message: str


type SessionEvent = (
    ConnectedEvent
    | AssociatedEvent
    | AssociationRejectedEvent
    | GetResponseEvent
    | GetAccessErrorEvent
    | ReleasedEvent
    | DisconnectedEvent
    | ProtocolErrorEvent
)
