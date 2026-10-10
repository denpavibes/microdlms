"""Tests for DLMS A-XDR linear recursive-descent codec."""

from __future__ import annotations

import pytest

from microdlms.axdr import AxdrReader, decode_axdr, encode_axdr_length
from microdlms.exceptions import ProtocolError


def test_axdr_primitive_integer_types() -> None:
    """Test all DLMS integer tags: signed/unsigned 8, 16, 32, and 64 bits."""
    # 0x0F: integer (int8)
    assert decode_axdr(b"\x0f\x00") == 0
    assert decode_axdr(b"\x0f\x7f") == 127
    assert decode_axdr(b"\x0f\x80") == -128
    assert decode_axdr(b"\x0f\xfe") == -2

    # 0x11: unsigned (uint8)
    assert decode_axdr(b"\x11\x00") == 0
    assert decode_axdr(b"\x11\xff") == 255

    # 0x10: long (int16)
    assert decode_axdr(b"\x10\x00\x00") == 0
    assert decode_axdr(b"\x10\x7f\xff") == 32767
    assert decode_axdr(b"\x10\x80\x00") == -32768
    assert decode_axdr(b"\x10\x02\xd9") == 729

    # 0x12: long-unsigned (uint16)
    assert decode_axdr(b"\x12\x00\x00") == 0
    assert decode_axdr(b"\x12\xff\xff") == 65535
    assert decode_axdr(b"\x12\x55\xcf") == 21967

    # 0x05: double-long (int32)
    assert decode_axdr(b"\x05\x00\x00\x00\x00") == 0
    assert decode_axdr(b"\x05\x7f\xff\xff\xff") == 2147483647
    assert decode_axdr(b"\x05\x80\x00\x00\x00") == -2147483648
    assert decode_axdr(b"\x05\x00\x00\xe9\x8e") == 59790

    # 0x06: double-long-unsigned (uint32)
    assert decode_axdr(b"\x06\x00\x00\x00\x00") == 0
    assert decode_axdr(b"\x06\xff\xff\xff\xff") == 4294967295
    assert decode_axdr(b"\x06\x00\x00\x08\x11") == 2065

    # 0x14: long64 (int64)
    assert decode_axdr(b"\x14\x00\x00\x00\x00\x00\x00\x00\x01") == 1
    assert decode_axdr(b"\x14\xff\xff\xff\xff\xff\xff\xff\xff") == -1

    # 0x15: long64-unsigned (uint64)
    assert decode_axdr(b"\x15\x00\x00\x00\x00\x00\x00\x00\x02") == 2

    # 0x16: enum (uint8)
    assert decode_axdr(b"\x16\x23") == 35


def test_axdr_string_and_bytes_types() -> None:
    """Test octet-string, visible-string, and boolean types."""
    # 0x00: null-data
    assert decode_axdr(b"\x00") is None

    # 0x03: boolean
    assert decode_axdr(b"\x03\x01") is True
    assert decode_axdr(b"\x03\x00") is False

    # 0x04: bit-string (count in bits)
    # 8 bits = 1 byte
    assert decode_axdr(b"\x04\x08\xab") == b"\xab"

    # 0x09: octet-string
    assert decode_axdr(b"\x09\x00") == b""
    assert decode_axdr(b"\x09\x04\xde\xad\xbe\xef") == b"\xde\xad\xbe\xef"

    # 0x0A: visible-string
    assert decode_axdr(b"\x0a\x00") == ""
    assert decode_axdr(b"\x0a\x0841920942") == "41920942"


def test_axdr_composite_types() -> None:
    """Test array and structure decoding including scaler-unit structures."""
    # 0x02: structure of 2 items: int8 (-2) and enum (35)
    scaler_unit_bytes = b"\x02\x02\x0f\xfe\x16\x23"
    assert decode_axdr(scaler_unit_bytes) == [-2, 35]

    # 0x01: array of 3 elements
    array_bytes = b"\x01\x03\x11\x0a\x11\x0b\x11\x0c"
    assert decode_axdr(array_bytes) == [10, 11, 12]

    # Nested structure
    nested = b"\x02\x02\x01\x02\x11\x01\x11\x02\x0a\x02OK"
    assert decode_axdr(nested) == [[1, 2], "OK"]


def test_axdr_length_encoding() -> None:
    """Test single-byte and multi-byte A-XDR length encodings."""
    # Single byte
    assert encode_axdr_length(0) == b"\x00"
    assert encode_axdr_length(127) == b"\x7f"

    # Multi-byte: 128 -> 0x81, 0x80
    assert encode_axdr_length(128) == b"\x81\x80"
    assert encode_axdr_length(300) == b"\x82\x01\x2c"

    # Reader parses multi-byte length
    reader = AxdrReader(b"\x81\x80" + b"\x00" * 128)
    assert reader.position == 0
    assert reader.read_length() == 128
    assert reader.position == 2
    assert reader.remaining == 128

    reader_multibyte = AxdrReader(b"\x82\x01\x2c")
    assert reader_multibyte.read_length() == 300


def test_axdr_error_handling() -> None:
    """Verify ProtocolError is raised on malformed or truncated A-XDR input."""
    # Truncated buffer
    with pytest.raises(ProtocolError, match="Unexpected end of data"):
        decode_axdr(b"")

    # Incomplete int16
    with pytest.raises(ProtocolError, match="Unexpected end of data"):
        decode_axdr(b"\x10\x01")

    # Incomplete octet-string
    with pytest.raises(ProtocolError, match="Unexpected end of data"):
        decode_axdr(b"\x09\x05\x01\x02")

    # Indefinite length byte (0x80)
    with pytest.raises(ProtocolError, match="Indefinite length"):
        reader = AxdrReader(b"\x80")
        reader.read_length()

    # Unknown tag
    with pytest.raises(ProtocolError, match="Unsupported or unknown A-XDR tag"):
        decode_axdr(b"\xee\x01")

    # Negative read bytes
    reader = AxdrReader(b"\x01\x02")
    with pytest.raises(ProtocolError, match="Invalid negative"):
        reader.read_bytes(-1)
