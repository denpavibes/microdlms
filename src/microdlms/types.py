"""DLMS/COSEM enumerations, domain dataclasses, and sans-I/O event types."""

from __future__ import annotations

import datetime
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum, unique
from typing import Any, Final, Self

COSEM_DATE_TIME_LENGTH: Final = 12
YEAR_NOT_SPECIFIED: Final = 0xFFFF
DATE_TIME_FIELD_NOT_SPECIFIED: Final = 0xFF
DEVIATION_NOT_SPECIFIED: Final = -32768
MAX_DEVIATION_MINUTES: Final = 1439
MAX_HUNDREDTHS: Final = 100
HUNDREDTHS_TO_MICROSECONDS: Final = 10000


@unique
class AssociationResult(IntEnum):
    """Result of DLMS association request (AARE result)."""

    ACCEPTED = 0
    REJECTED_PERMANENT = 1
    REJECTED_TRANSIENT = 2


@unique
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


@unique
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


@unique
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


class UnitsOfMeasurement(StrEnum):
    """Units of measurement symbols."""

    NONE = ""
    YEAR = "a"
    MONTH = "mo"
    WEEK = "wk"
    DAY = "d"
    HOUR = "h"
    MINUTE = "min"
    SECOND = "s"
    DEGREE = "°"
    DEGREE_CELSIUS = "°C"
    CURRENCY = "currency"
    METRE = "m"
    METRE_PER_SECOND = "m/s"
    CUBIC_METRE = "m³"
    CUBIC_METRE_PER_HOUR = "m³/h"
    CUBIC_METRE_PER_DAY = "m³/d"
    LITRE = "l"
    KILOGRAM = "kg"
    NEWTON = "N"
    NEWTON_METRE = "Nm"
    PASCAL = "Pa"
    BAR = "bar"
    JOULE = "J"
    JOULE_PER_HOUR = "J/h"
    WATT = "W"
    VOLT_AMPERE = "VA"
    VAR = "var"
    WATT_HOUR = "Wh"
    VOLT_AMPERE_HOUR = "VAh"
    VAR_HOUR = "varh"
    AMPERE = "A"
    COULOMB = "C"
    VOLT = "V"
    VOLT_PER_METRE = "V/m"
    FARAD = "F"
    OHM = "Ω"
    OHM_METRE = "Ω·m"
    WEBER = "Wb"
    TESLA = "T"
    HENRY = "H"
    SIEMENS = "S"
    KELVIN = "K"
    RECIPROCAL_OF_VOLT = "1/V"
    RECIPROCAL_OF_AMPERE = "1/A"
    RECIPROCAL_OF_CUBIC_METRE = "1/m³"
    PERCENT = "%"
    AMPERE_HOUR = "Ah"
    WATT_HOUR_PER_CUBIC_METRE = "Wh/m³"
    JOULE_PER_CUBIC_METRE = "J/m³"
    MOLE_PERCENT = "mol %"
    GRAM_PER_CUBIC_METRE = "g/m³"
    PASCAL_SECOND = "Pa·s"
    JOULE_PER_KILOGRAM = "J/kg"
    DECIBEL_MILLIWATT = "dBm"
    DECIBEL_MICROVOLT = "dB·µV"
    DECIBEL = "dB"
    OTHER = "other"
    COUNT = "count"


DLMS_UNITS: dict[int, UnitsOfMeasurement] = {
    0: UnitsOfMeasurement.NONE,
    1: UnitsOfMeasurement.YEAR,
    2: UnitsOfMeasurement.MONTH,
    3: UnitsOfMeasurement.WEEK,
    4: UnitsOfMeasurement.DAY,
    5: UnitsOfMeasurement.HOUR,
    6: UnitsOfMeasurement.MINUTE,
    7: UnitsOfMeasurement.SECOND,
    8: UnitsOfMeasurement.DEGREE,
    9: UnitsOfMeasurement.DEGREE_CELSIUS,
    10: UnitsOfMeasurement.CURRENCY,
    11: UnitsOfMeasurement.METRE,
    12: UnitsOfMeasurement.METRE_PER_SECOND,
    13: UnitsOfMeasurement.CUBIC_METRE,
    14: UnitsOfMeasurement.CUBIC_METRE,
    15: UnitsOfMeasurement.CUBIC_METRE_PER_HOUR,
    16: UnitsOfMeasurement.CUBIC_METRE_PER_HOUR,
    17: UnitsOfMeasurement.CUBIC_METRE_PER_DAY,
    18: UnitsOfMeasurement.CUBIC_METRE_PER_DAY,
    19: UnitsOfMeasurement.LITRE,
    20: UnitsOfMeasurement.KILOGRAM,
    21: UnitsOfMeasurement.NEWTON,
    22: UnitsOfMeasurement.NEWTON_METRE,
    23: UnitsOfMeasurement.PASCAL,
    24: UnitsOfMeasurement.BAR,
    25: UnitsOfMeasurement.JOULE,
    26: UnitsOfMeasurement.JOULE_PER_HOUR,
    27: UnitsOfMeasurement.WATT,
    28: UnitsOfMeasurement.VOLT_AMPERE,
    29: UnitsOfMeasurement.VAR,
    30: UnitsOfMeasurement.WATT_HOUR,
    31: UnitsOfMeasurement.VOLT_AMPERE_HOUR,
    32: UnitsOfMeasurement.VAR_HOUR,
    33: UnitsOfMeasurement.AMPERE,
    34: UnitsOfMeasurement.COULOMB,
    35: UnitsOfMeasurement.VOLT,
    36: UnitsOfMeasurement.VOLT_PER_METRE,
    37: UnitsOfMeasurement.FARAD,
    38: UnitsOfMeasurement.OHM,
    39: UnitsOfMeasurement.OHM_METRE,
    40: UnitsOfMeasurement.WEBER,
    41: UnitsOfMeasurement.TESLA,
    42: UnitsOfMeasurement.HENRY,
    43: UnitsOfMeasurement.SIEMENS,
    44: UnitsOfMeasurement.KELVIN,
    45: UnitsOfMeasurement.RECIPROCAL_OF_VOLT,
    46: UnitsOfMeasurement.RECIPROCAL_OF_AMPERE,
    47: UnitsOfMeasurement.RECIPROCAL_OF_CUBIC_METRE,
    48: UnitsOfMeasurement.PERCENT,
    49: UnitsOfMeasurement.AMPERE_HOUR,
    50: UnitsOfMeasurement.WATT_HOUR_PER_CUBIC_METRE,
    51: UnitsOfMeasurement.JOULE_PER_CUBIC_METRE,
    52: UnitsOfMeasurement.MOLE_PERCENT,
    53: UnitsOfMeasurement.GRAM_PER_CUBIC_METRE,
    54: UnitsOfMeasurement.PASCAL_SECOND,
    55: UnitsOfMeasurement.JOULE_PER_KILOGRAM,
    56: UnitsOfMeasurement.DECIBEL_MILLIWATT,
    57: UnitsOfMeasurement.DECIBEL_MICROVOLT,
    58: UnitsOfMeasurement.DECIBEL,
    253: UnitsOfMeasurement.OTHER,
    254: UnitsOfMeasurement.COUNT,
    255: UnitsOfMeasurement.NONE,
}


@dataclass(frozen=True, slots=True)
class UnitOfMeasurement:
    """Represents a unit of measurement."""

    code: int
    unit: UnitsOfMeasurement = field(init=False)

    def __post_init__(self) -> None:
        """Determine and assign unit of measurement symbol."""
        unit = DLMS_UNITS.get(self.code, UnitsOfMeasurement.NONE)
        object.__setattr__(self, "unit", unit)

    def __str__(self) -> str:
        """Return a unit of measurement symbol."""
        return self.unit.value


@dataclass(frozen=True, slots=True)
class ScalerUnit:
    """COSEM scaler and unit pair representing measurement scale and engineering unit."""

    scaler: int
    unit_of_measurement: UnitOfMeasurement

    @classmethod
    def from_structure(cls, data: Sequence[Any]) -> Self:
        """Construct ScalerUnit from an A-XDR decoded structure [scaler, unit]."""
        if len(data) != 2:
            raise ValueError(f"Expected 2 elements for scaler_unit structure, got {len(data)}")

        return cls(scaler=int(data[0]), unit_of_measurement=UnitOfMeasurement(int(data[1])))

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
        if len(data) != COSEM_DATE_TIME_LENGTH:
            raise ValueError(
                f"COSEM date-time requires {COSEM_DATE_TIME_LENGTH} bytes, got {len(data)}"
            )
        year = int.from_bytes(data[0:2], "big")
        month = data[2]
        day = data[3]
        day_of_week = data[4]
        hour = data[5]
        minute = data[6]
        second = data[7]
        hundredths = data[8]
        raw_deviation = int.from_bytes(data[9:11], "big", signed=True)
        deviation = None if raw_deviation == DEVIATION_NOT_SPECIFIED else raw_deviation
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
        if (
            self.year == YEAR_NOT_SPECIFIED
            or self.month == DATE_TIME_FIELD_NOT_SPECIFIED
            or self.day == DATE_TIME_FIELD_NOT_SPECIFIED
        ):
            return None
        time_zone = (
            datetime.timezone(datetime.timedelta(minutes=self.deviation))
            if (
                self.deviation is not None
                and -MAX_DEVIATION_MINUTES <= self.deviation <= MAX_DEVIATION_MINUTES
            )
            else datetime.UTC
        )
        microsecond = (
            (self.hundredths * HUNDREDTHS_TO_MICROSECONDS)
            if (0 <= self.hundredths < MAX_HUNDREDTHS)
            else 0
        )
        return datetime.datetime(
            year=self.year,
            month=self.month,
            day=self.day,
            hour=self.hour if self.hour != DATE_TIME_FIELD_NOT_SPECIFIED else 0,
            minute=self.minute if self.minute != DATE_TIME_FIELD_NOT_SPECIFIED else 0,
            second=self.second if self.second != DATE_TIME_FIELD_NOT_SPECIFIED else 0,
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
