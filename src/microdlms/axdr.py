"""Linear recursive-descent A-XDR codec for DLMS/COSEM."""

from __future__ import annotations

from typing import Any

from microdlms.exceptions import ProtocolError

_INTEGER_TAG_SPECS: dict[int, tuple[int, bool]] = {
    0x05: (4, True),  # double-long (int32 signed)
    0x06: (4, False),  # double-long-unsigned (uint32 unsigned)
    0x0F: (1, True),  # integer (int8 signed)
    0x10: (2, True),  # long (int16 signed)
    0x11: (1, False),  # unsigned (uint8 unsigned)
    0x12: (2, False),  # long-unsigned (uint16 unsigned)
    0x14: (8, True),  # long64 (int64 signed)
    0x15: (8, False),  # long64-unsigned (uint64 unsigned)
    0x16: (1, False),  # enum (uint8 unsigned)
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
        if initial < 0x80:
            return initial
        length_bytes_count = initial & 0x7F
        if length_bytes_count == 0:
            raise ProtocolError("Indefinite length encoding is not allowed in DLMS A-XDR")
        length_bytes = self.read_bytes(length_bytes_count)
        return int.from_bytes(length_bytes, "big", signed=False)

    def decode_value(self) -> Any:
        """Decode the next typed value from the buffer."""
        tag = self.read_byte()

        # 0x00: null-data
        if tag == 0x00:
            return None

        # 0x01: array, 0x02: structure
        if tag in (0x01, 0x02):
            count = self.read_length()
            return [self.decode_value() for _ in range(count)]

        # 0x03: boolean
        if tag == 0x03:
            return self.read_byte() != 0

        # 0x04: bit-string
        if tag == 0x04:
            bit_count = self.read_length()
            byte_count = (bit_count + 7) // 8
            return self.read_bytes(byte_count)

        # 0x09: octet-string, 0x0A: visible-string
        if tag in (0x09, 0x0A):
            length = self.read_length()
            raw = self.read_bytes(length)
            return raw.decode("utf-8", errors="replace") if tag == 0x0A else raw

        int_spec = _INTEGER_TAG_SPECS.get(tag)
        if int_spec is not None:
            byte_length, is_signed = int_spec
            return int.from_bytes(self.read_bytes(byte_length), "big", signed=is_signed)

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
    if length < 0x80:
        return bytes([length])
    length_bytes = length.to_bytes((length.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(length_bytes)]) + length_bytes
