"""Tests for DLMS Application Protocol Data Unit (APDU) codecs."""

from __future__ import annotations

import pytest

from microdlms.apdu import (
    ACCESS_SELECTION_NONE,
    BER_LENGTH_SINGLE_BYTE,
    DEFAULT_PRIORITY,
    RELEASE_REASON_NORMAL,
    REQUEST_TYPE_NORMAL,
    RESPONSE_TYPE_NORMAL,
    RESULT_TYPE_DATA_ACCESS_RESULT,
    RESULT_TYPE_SUCCESS,
    RLRQ_LENGTH,
    ApduTags,
    decode_aare,
    decode_get_response_normal,
    decode_rlre,
    encode_aarq,
    encode_get_request_normal,
    encode_rlrq,
)
from microdlms.exceptions import ProtocolError
from microdlms.obis import DEFAULT_COSEM_ATTRIBUTE_ID, CosemAttribute, ObisCode
from microdlms.types import AssociationResult, DataAccessResult, InterfaceClass


def test_aarq_encoding() -> None:
    """Test AARQ encoding with LLS password, without password, and with custom system titles."""
    system_title = b"MDL\x01\x02\x03\x04\x05"

    # Default system title
    aarq_default_title = encode_aarq(password="111111")
    assert aarq_default_title[0] == ApduTags.AARQ
    assert b"MDL\x00\x00\x00\x00\x00" in aarq_default_title

    # With LLS password (string)
    aarq_with_password = encode_aarq(password="111111", system_title=system_title)
    assert aarq_with_password[0] == ApduTags.AARQ
    assert b"111111" in aarq_with_password
    assert system_title in aarq_with_password

    # With password as bytes
    aarq_password_bytes = encode_aarq(password=b"111111", system_title=system_title)
    assert aarq_password_bytes == aarq_with_password

    # Without password (no security)
    aarq_no_password = encode_aarq(password=None, system_title=system_title)
    assert aarq_no_password[0] == ApduTags.AARQ
    assert b"111111" not in aarq_no_password
    assert len(aarq_no_password) < len(aarq_with_password)

    # Empty string password also omits auth
    aarq_empty_password = encode_aarq(password="", system_title=system_title)
    assert aarq_empty_password == aarq_no_password

    # Invalid system title length raises ValueError
    with pytest.raises(ValueError, match="System title must be exactly 8 bytes"):
        encode_aarq(password="111111", system_title=b"too_short")


def test_aare_decoding() -> None:
    """Test AARE response parsing for accepted and rejected associations."""
    # AARE Accepted
    success_apdu = bytes.fromhex(
        "6129a109060760857405080101a203020100a305a103020100be10040e0800065f1f040000101d00640007"
    )
    result, diagnostic = decode_aare(success_apdu)
    assert result == AssociationResult.ACCEPTED
    assert diagnostic == 0

    # AARE Rejected (Authentication Failed, diagnostic=13)
    fail_apdu = bytes.fromhex("611fa109060760857405080101a203020101a305a10302010dbe0604040e010601")
    result_fail, diagnostic_fail = decode_aare(fail_apdu)
    assert result_fail == AssociationResult.REJECTED_PERMANENT
    assert diagnostic_fail == 13

    # Malformed AARE tag
    with pytest.raises(ProtocolError, match="Invalid AARE APDU"):
        decode_aare(b"\x60\x05\x00\x00\x00")

    # Too short AARE
    with pytest.raises(ProtocolError, match="Invalid AARE APDU"):
        decode_aare(b"\x61\x01")

    # AARE with multi-byte length encoding and trailing single byte
    aare_multibyte = b"\x61\x81" + bytes([len(success_apdu) - 2]) + success_apdu[2:] + b"\x00"
    result_multibyte, diagnostic_multibyte = decode_aare(aare_multibyte)
    assert result_multibyte == AssociationResult.ACCEPTED
    assert diagnostic_multibyte == 0

    # AARE missing result field
    with pytest.raises(ProtocolError, match="missing result field"):
        decode_aare(b"\x61\x05\xa1\x03\x01\x02\x03")


def test_get_request_normal_encoding() -> None:
    """Test encoding Get-Request-Normal APDU."""
    attribute = CosemAttribute(
        interface=InterfaceClass.DATA,
        obis=ObisCode(0, 0, 42, 0, 0, 255),
        attribute=DEFAULT_COSEM_ATTRIBUTE_ID,
    )
    apdu = encode_get_request_normal(attribute=attribute, invoke_id=3)
    assert len(apdu) == 13
    assert apdu[0] == ApduTags.GET_REQUEST
    assert apdu[1] == REQUEST_TYPE_NORMAL
    assert apdu[2] == DEFAULT_PRIORITY | 3
    assert apdu[3:5] == b"\x00\x01"  # InterfaceClass.DATA = 1
    assert apdu[5:11] == bytes([0, 0, 42, 0, 0, 255])  # OBIS
    assert apdu[11] == DEFAULT_COSEM_ATTRIBUTE_ID
    assert apdu[12] == ACCESS_SELECTION_NONE


def test_get_response_normal_decoding() -> None:
    """Test decoding Get-Response-Normal for data return and error conditions."""
    # Data return: invoke_id=5, octet-string b"INC123"
    success_apdu = bytes.fromhex("c401c5000906494e43313233")
    invoke_id, is_success, value = decode_get_response_normal(success_apdu)
    assert invoke_id == 5
    assert is_success is True
    assert value == b"INC123"

    # DataAccessResult error: invoke_id=6, error=OBJECT_UNDEFINED (4)
    error_apdu = bytes.fromhex("c401c60104")
    error_invoke_id, is_error_success, error_code = decode_get_response_normal(error_apdu)
    assert error_invoke_id == 6
    assert is_error_success is False
    assert error_code == DataAccessResult.OBJECT_UNDEFINED

    # Malformed APDUs
    with pytest.raises(ProtocolError, match="Invalid Get-Response APDU"):
        decode_get_response_normal(b"\xc0\x01\xc0\x00")

    with pytest.raises(ProtocolError, match="Unsupported Get-Response type"):
        decode_get_response_normal(b"\xc4\x02\xc0\x00")

    with pytest.raises(ProtocolError, match="missing error code"):
        decode_get_response_normal(b"\xc4\x01\xc0\x01")

    with pytest.raises(ProtocolError, match="Unknown GetDataResult choice"):
        decode_get_response_normal(b"\xc4\x01\xc0\x02")


def test_rlrq_and_rlre() -> None:
    """Test ACSE release request and release response codecs."""
    rlrq = encode_rlrq(reason=RELEASE_REASON_NORMAL)
    assert rlrq == b"\x62\x03\x80\x01\x00"

    rlre = bytes.fromhex("6303800100")
    assert decode_rlre(rlre) == RELEASE_REASON_NORMAL

    # Short RLRE without optional reason field defaults to RELEASE_REASON_NORMAL
    assert decode_rlre(b"\x63\x00") == RELEASE_REASON_NORMAL

    # Malformed RLRE
    with pytest.raises(ProtocolError, match="Invalid RLRE APDU"):
        decode_rlre(b"\x62\x03\x80\x01\x00")


def test_aare_multibyte_tag_and_unknown_result() -> None:
    """Test AARE with inner multi-byte BER length tag and unknown result enum."""
    # AARE with an inner user-information tag containing 130 bytes (> 127, length 0x81 0x82)
    # result tag 0xA2, len 3: 02 01 00
    inner_large_tag = b"\xbe\x81\x82" + (b"\x00" * 130)
    result_tag = b"\xa2\x03\x02\x01\x00"
    body = result_tag + inner_large_tag
    aare_apdu = b"\x61\x81" + bytes([len(body)]) + body
    result, diagnostic = decode_aare(aare_apdu)
    assert result == AssociationResult.ACCEPTED

    # AARE with unknown result code (e.g. 99) falls back to REJECTED_PERMANENT
    bad_response_apdu = b"\x61\x05\xa2\x03\x02\x01\x63"
    result_bad, _ = decode_aare(bad_response_apdu)
    assert result_bad == AssociationResult.REJECTED_PERMANENT

    # Get-Response with unrecognized DataAccessResult (e.g. 255) falls back to OTHER_REASON
    unknown_error_apdu = bytes.fromhex("c401c101ff")
    invoke_id, is_success, error_code = decode_get_response_normal(unknown_error_apdu)
    assert is_success is False
    assert error_code == DataAccessResult.OTHER_REASON


def test_apdu_constants() -> None:
    """Verify APDU codec and tag constants."""
    assert RESPONSE_TYPE_NORMAL == 0x01
    assert REQUEST_TYPE_NORMAL == 0x01
    assert RESULT_TYPE_SUCCESS == 0x00
    assert RESULT_TYPE_DATA_ACCESS_RESULT == 0x01
    assert ACCESS_SELECTION_NONE == 0x00
    assert DEFAULT_PRIORITY == 0xC0
    assert RELEASE_REASON_NORMAL == 0
    assert BER_LENGTH_SINGLE_BYTE == 0x01
    assert RLRQ_LENGTH == 0x03
    assert ApduTags.AARQ.value == 0x60
    assert ApduTags.AARE.value == 0x61
    assert ApduTags.RLRQ.value == 0x62
    assert ApduTags.RLRE.value == 0x63
    assert ApduTags.GET_REQUEST.value == 0xC0
    assert ApduTags.GET_RESPONSE.value == 0xC4
