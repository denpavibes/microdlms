"""Tests for DLMS A-XDR linear recursive-descent codec."""

from __future__ import annotations

import pytest

from microdlms.axdr import AxdrReader, AxdrTags, decode_axdr, encode_axdr_length
from microdlms.exceptions import ProtocolError


def test_axdr_primitive_integer_types() -> None:
    """Test all DLMS integer tags: signed/unsigned 8, 16, 32, and 64 bits."""
    assert decode_axdr(bytes([AxdrTags.INTEGER, 0x00])) == 0
    assert decode_axdr(bytes([AxdrTags.INTEGER, 0x7F])) == 127
    assert decode_axdr(bytes([AxdrTags.INTEGER, 0x80])) == -128
    assert decode_axdr(bytes([AxdrTags.INTEGER, 0xFE])) == -2

    assert decode_axdr(bytes([AxdrTags.UNSIGNED, 0x00])) == 0
    assert decode_axdr(bytes([AxdrTags.UNSIGNED, 0xFF])) == 255

    assert decode_axdr(bytes([AxdrTags.LONG, 0x00, 0x00])) == 0
    assert decode_axdr(bytes([AxdrTags.LONG, 0x7F, 0xFF])) == 32767
    assert decode_axdr(bytes([AxdrTags.LONG, 0x80, 0x00])) == -32768
    assert decode_axdr(bytes([AxdrTags.LONG, 0x02, 0xD9])) == 729

    assert decode_axdr(bytes([AxdrTags.LONG_UNSIGNED, 0x00, 0x00])) == 0
    assert decode_axdr(bytes([AxdrTags.LONG_UNSIGNED, 0xFF, 0xFF])) == 65535
    assert decode_axdr(bytes([AxdrTags.LONG_UNSIGNED, 0x55, 0xCF])) == 21967

    assert decode_axdr(bytes([AxdrTags.DOUBLE_LONG, 0x00, 0x00, 0x00, 0x00])) == 0
    assert decode_axdr(bytes([AxdrTags.DOUBLE_LONG, 0x7F, 0xFF, 0xFF, 0xFF])) == 2147483647
    assert decode_axdr(bytes([AxdrTags.DOUBLE_LONG, 0x80, 0x00, 0x00, 0x00])) == -2147483648
    assert decode_axdr(bytes([AxdrTags.DOUBLE_LONG, 0x00, 0x00, 0xE9, 0x8E])) == 59790

    assert decode_axdr(bytes([AxdrTags.DOUBLE_LONG_UNSIGNED, 0x00, 0x00, 0x00, 0x00])) == 0
    assert decode_axdr(bytes([AxdrTags.DOUBLE_LONG_UNSIGNED, 0xFF, 0xFF, 0xFF, 0xFF])) == 4294967295
    assert decode_axdr(bytes([AxdrTags.DOUBLE_LONG_UNSIGNED, 0x00, 0x00, 0x08, 0x11])) == 2065

    assert decode_axdr(bytes([AxdrTags.LONG64, 0, 0, 0, 0, 0, 0, 0, 1])) == 1
    assert decode_axdr(bytes([AxdrTags.LONG64]) + (b"\xff" * 8)) == -1

    assert decode_axdr(bytes([AxdrTags.LONG64_UNSIGNED, 0, 0, 0, 0, 0, 0, 0, 2])) == 2

    assert decode_axdr(bytes([AxdrTags.ENUM, 0x23])) == 35


def test_axdr_string_and_bytes_types() -> None:
    """Test octet-string, visible-string, and boolean types."""
    assert decode_axdr(bytes([AxdrTags.NULL_DATA])) is None

    assert decode_axdr(bytes([AxdrTags.BOOLEAN, 0x01])) is True
    assert decode_axdr(bytes([AxdrTags.BOOLEAN, 0x00])) is False

    assert decode_axdr(bytes([AxdrTags.BIT_STRING, 8, 0xAB])) == b"\xab"

    assert decode_axdr(bytes([AxdrTags.OCTET_STRING, 0])) == b""
    assert (
        decode_axdr(bytes([AxdrTags.OCTET_STRING, 4, 0xDE, 0xAD, 0xBE, 0xEF]))
        == b"\xde\xad\xbe\xef"
    )

    assert decode_axdr(bytes([AxdrTags.VISIBLE_STRING, 0])) == ""
    assert decode_axdr(bytes([AxdrTags.VISIBLE_STRING, 8]) + b"41920942") == "41920942"


def test_axdr_composite_types() -> None:
    """Test array and structure decoding including scaler-unit structures."""
    scaler_unit_bytes = bytes([AxdrTags.STRUCTURE, 2, AxdrTags.INTEGER, 0xFE, AxdrTags.ENUM, 0x23])
    assert decode_axdr(scaler_unit_bytes) == [-2, 35]

    array_bytes = bytes(
        [
            AxdrTags.ARRAY,
            3,
            AxdrTags.UNSIGNED,
            10,
            AxdrTags.UNSIGNED,
            11,
            AxdrTags.UNSIGNED,
            12,
        ]
    )
    assert decode_axdr(array_bytes) == [10, 11, 12]

    nested = (
        bytes(
            [
                AxdrTags.STRUCTURE,
                2,
                AxdrTags.ARRAY,
                2,
                AxdrTags.UNSIGNED,
                1,
                AxdrTags.UNSIGNED,
                2,
                AxdrTags.VISIBLE_STRING,
                2,
            ]
        )
        + b"OK"
    )
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


def test_axdr_tags_enum() -> None:
    """Verify AxdrTags IntEnum members and values."""
    assert AxdrTags.NULL_DATA.value == 0x00
    assert AxdrTags.ARRAY.value == 0x01
    assert AxdrTags.STRUCTURE.value == 0x02
    assert AxdrTags.BOOLEAN.value == 0x03
    assert AxdrTags.BIT_STRING.value == 0x04
    assert AxdrTags.DOUBLE_LONG.value == 0x05
    assert AxdrTags.DOUBLE_LONG_UNSIGNED.value == 0x06
    assert AxdrTags.OCTET_STRING.value == 0x09
    assert AxdrTags.VISIBLE_STRING.value == 0x0A
    assert AxdrTags.INTEGER.value == 0x0F
    assert AxdrTags.LONG.value == 0x10
    assert AxdrTags.UNSIGNED.value == 0x11
    assert AxdrTags.LONG_UNSIGNED.value == 0x12
    assert AxdrTags.LONG64.value == 0x14
    assert AxdrTags.LONG64_UNSIGNED.value == 0x15
    assert AxdrTags.ENUM.value == 0x16
