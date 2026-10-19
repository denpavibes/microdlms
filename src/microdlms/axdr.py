"""Linear recursive-descent A-XDR codec for DLMS/COSEM."""

from __future__ import annotations

from enum import IntEnum, unique
from typing import Any, Final, NamedTuple

from microdlms.exceptions import ProtocolError

AXDR_MULTI_BYTE_LENGTH_FLAG: Final = 0x80
AXDR_LENGTH_VALUE_MASK: Final = 0x7F
BITS_PER_BYTE: Final = 8


@unique
class AxdrTags(IntEnum):
    """DLMS/COSEM A-XDR data type tags."""

    NULL_DATA = 0x00
    ARRAY = 0x01
    STRUCTURE = 0x02
    BOOLEAN = 0x03
    BIT_STRING = 0x04
    DOUBLE_LONG = 0x05
    DOUBLE_LONG_UNSIGNED = 0x06
    OCTET_STRING = 0x09
    VISIBLE_STRING = 0x0A
    INTEGER = 0x0F
    LONG = 0x10
    UNSIGNED = 0x11
    LONG_UNSIGNED = 0x12
    LONG64 = 0x14
    LONG64_UNSIGNED = 0x15
    ENUM = 0x16


class TypeSpec(NamedTuple):
    """Represents a type specification."""

    byte_count: int
    is_signed: bool


INTEGER_TYPES: dict[int, TypeSpec] = {
    AxdrTags.DOUBLE_LONG: TypeSpec(byte_count=4, is_signed=True),
    AxdrTags.DOUBLE_LONG_UNSIGNED: TypeSpec(byte_count=4, is_signed=False),
    AxdrTags.INTEGER: TypeSpec(byte_count=1, is_signed=True),
    AxdrTags.LONG: TypeSpec(byte_count=2, is_signed=True),
    AxdrTags.UNSIGNED: TypeSpec(byte_count=1, is_signed=False),
    AxdrTags.LONG_UNSIGNED: TypeSpec(byte_count=2, is_signed=False),
    AxdrTags.LONG64: TypeSpec(byte_count=8, is_signed=True),
    AxdrTags.LONG64_UNSIGNED: TypeSpec(byte_count=8, is_signed=False),
    AxdrTags.ENUM: TypeSpec(byte_count=1, is_signed=False),
}


class AxdrReader:
    """Linear recursive-descent parser for DLMS A-XDR encoded data."""

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._position = 0

    @property
    def remaining(self) -> int:
        """Number of bytes remaining in the buffer."""
        return len(self._data) - self._position

    @property
    def position(self) -> int:
        """Current parse offset."""
        return self._position

    def read_byte(self) -> int:
        """Read a single byte from the buffer."""
        if self._position >= len(self._data):
            raise ProtocolError(f"Unexpected end of data at offset {self._position}")
        byte = self._data[self._position]
        self._position += 1
        return byte

    def read_bytes(self, count: int) -> bytes:
        """Read exact number of bytes from the buffer."""
        if count < 0:
            raise ProtocolError(f"Invalid negative byte count: {count}")
        if self._position + count > len(self._data):
            raise ProtocolError(
                f"Unexpected end of data: needed {count} bytes at offset {self._position}, "
                f"only {self.remaining} available"
            )
        chunk = self._data[self._position : self._position + count]
        self._position += count
        return chunk

    def read_length(self) -> int:
        """Read A-XDR length field supporting single-byte and multi-byte encoding."""
        initial = self.read_byte()
        if initial < AXDR_MULTI_BYTE_LENGTH_FLAG:
            return initial
        length_bytes_count = initial & AXDR_LENGTH_VALUE_MASK
        if length_bytes_count == 0:
            raise ProtocolError("Indefinite length encoding is not allowed in DLMS A-XDR")
        length_bytes = self.read_bytes(length_bytes_count)
        return int.from_bytes(length_bytes, "big", signed=False)

    def decode_value(self) -> Any:
        """Decode the next typed value from the buffer."""
        tag = self.read_byte()
        match tag:
            case AxdrTags.NULL_DATA:
                return None
            case AxdrTags.ARRAY | AxdrTags.STRUCTURE:
                count = self.read_length()
                return [self.decode_value() for _ in range(count)]
            case AxdrTags.BOOLEAN:
                return self.read_byte() != 0
            case AxdrTags.BIT_STRING:
                bit_count = self.read_length()
                byte_count = (bit_count + BITS_PER_BYTE - 1) // BITS_PER_BYTE
                return self.read_bytes(byte_count)
            case AxdrTags.OCTET_STRING | AxdrTags.VISIBLE_STRING:
                length = self.read_length()
                raw = self.read_bytes(length)
                if tag == AxdrTags.OCTET_STRING:
                    return raw

                return raw.decode("utf-8", errors="replace")
            case _ if tag in INTEGER_TYPES:
                byte_count, is_signed = INTEGER_TYPES[tag]
                return int.from_bytes(self.read_bytes(byte_count), "big", signed=is_signed)
            case _:
                raise ProtocolError(
                    f"Unsupported or unknown A-XDR tag 0x{tag:02X} at offset {self._position - 1}"
                )


def decode_axdr(data: bytes) -> Any:
    """Convenience helper to decode a single A-XDR value from bytes."""
    reader = AxdrReader(data)
    value = reader.decode_value()
    return value


def encode_axdr_length(length: int) -> bytes:
    """Encode an A-XDR length value."""
    if length < AXDR_MULTI_BYTE_LENGTH_FLAG:
        return bytes([length])
    length_bytes = length.to_bytes(
        (length.bit_length() + BITS_PER_BYTE - 1) // BITS_PER_BYTE, "big"
    )
    return bytes([AXDR_MULTI_BYTE_LENGTH_FLAG | len(length_bytes)]) + length_bytes
