"""OBIS code and COSEM attribute representation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Self

from microdlms.types import InterfaceClass

DEFAULT_OBIS_F: Final = 255
OBIS_CODE_LENGTH: Final = 6
OBIS_GROUP_MIN: Final = 0
OBIS_GROUP_MAX: Final = 255
DEFAULT_COSEM_ATTRIBUTE_ID: Final = 2


@dataclass(frozen=True, slots=True, order=True)
class ObisCode:
    """Represents a 6-group OBIS (Object Identification System) code A.B.C.D.E.F."""

    a: int
    b: int
    c: int
    d: int
    e: int
    f: int = DEFAULT_OBIS_F

    def __post_init__(self) -> None:
        for name, value in (
            ("a", self.a),
            ("b", self.b),
            ("c", self.c),
            ("d", self.d),
            ("e", self.e),
            ("f", self.f),
        ):
            if not (OBIS_GROUP_MIN <= value <= OBIS_GROUP_MAX):
                raise ValueError(
                    f"OBIS group {name} must be within "
                    f"{OBIS_GROUP_MIN}..{OBIS_GROUP_MAX}, got {value}"
                )

    @classmethod
    def from_string(cls, text: str) -> Self:
        """Parse OBIS code from dot string ('1.0.31.7.0.255'), IEC format, or Obis(...)."""
        clean = text.strip()
        if clean.startswith("Obis(") and clean.endswith(")"):
            inner = clean[5:-1]
            numbers = [
                int(part.split("=")[-1].strip()) for part in inner.split(",") if part.strip()
            ]
            if len(numbers) == 6:
                return cls(numbers[0], numbers[1], numbers[2], numbers[3], numbers[4], numbers[5])
            if len(numbers) == 5:
                return cls(
                    numbers[0], numbers[1], numbers[2], numbers[3], numbers[4], DEFAULT_OBIS_F
                )

        normalized = clean.replace("-", ".").replace(":", ".").replace("*", ".")
        parts = [int(part.strip()) for part in normalized.split(".")]
        if len(parts) == 6:
            return cls(parts[0], parts[1], parts[2], parts[3], parts[4], parts[5])
        if len(parts) == 5:
            return cls(parts[0], parts[1], parts[2], parts[3], parts[4], DEFAULT_OBIS_F)
        raise ValueError(
            f"Expected 5 or 6 dot-separated parts in OBIS string, got {len(parts)} in {text!r}"
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        """Parse OBIS code from 6 raw bytes."""
        if len(data) != OBIS_CODE_LENGTH:
            raise ValueError(
                f"OBIS code requires exactly {OBIS_CODE_LENGTH} bytes, got {len(data)}"
            )
        return cls(data[0], data[1], data[2], data[3], data[4], data[5])

    def to_bytes(self) -> bytes:
        """Serialize OBIS code into 6 raw bytes."""
        return bytes([self.a, self.b, self.c, self.d, self.e, self.f])

    def __bytes__(self) -> bytes:
        return self.to_bytes()

    def __str__(self) -> str:
        return f"{self.a}.{self.b}.{self.c}.{self.d}.{self.e}.{self.f}"

    def __repr__(self) -> str:
        return f"ObisCode({self.a}, {self.b}, {self.c}, {self.d}, {self.e}, {self.f})"


@dataclass(frozen=True, slots=True)
class CosemAttribute:
    """Represents a COSEM object attribute to query."""

    interface: InterfaceClass | int
    obis: ObisCode
    attribute: int = DEFAULT_COSEM_ATTRIBUTE_ID

    def to_bytes(self) -> bytes:
        """Serialize COSEM attribute descriptor to 9 bytes (class_id + obis + attribute)."""
        class_id = int(self.interface)
        return class_id.to_bytes(2, "big") + self.obis.to_bytes() + bytes([self.attribute])
