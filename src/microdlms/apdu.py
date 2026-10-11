"""DLMS/COSEM Application Protocol Data Unit (APDU) codecs."""

from __future__ import annotations

from enum import IntEnum
from typing import Any, Final

from microdlms.axdr import decode_axdr, encode_axdr_length
from microdlms.exceptions import ProtocolError
from microdlms.obis import CosemAttribute
from microdlms.types import AssociationResult, DataAccessResult

DEFAULT_SYSTEM_TITLE: Final = b"MDL\x00\x00\x00\x00\x00"
SYSTEM_TITLE_LENGTH: Final = 8

APP_CONTEXT_LN_NO_CIPHER: Final = bytes.fromhex("060760857405080101")
MECHANISM_NAME_LLS: Final = bytes.fromhex("60857405080201")
DEFAULT_INITIATE_REQUEST: Final = bytes.fromhex("01000000065f1f040020525fffff")

BER_MULTI_BYTE_LENGTH_FLAG: Final = 0x80
BER_LENGTH_VALUE_MASK: Final = 0x7F

BER_TAG_OCTET_STRING: Final = 0x04
BER_TAG_INTEGER: Final = 0x02
BER_TAG_AARQ_APP_CONTEXT: Final = 0xA1
BER_TAG_AARQ_CALLING_AP_TITLE: Final = 0xA6
BER_TAG_AARQ_ACSE_REQUIREMENTS: Final = 0x8A
BER_TAG_AARQ_MECHANISM_NAME: Final = 0x8B
BER_TAG_AARQ_AUTHENTICATION_VALUE: Final = 0xAC
BER_TAG_AARQ_AUTHENTICATION_VALUE_PRIMITIVE: Final = 0x80
BER_TAG_AARQ_USER_INFORMATION: Final = 0xBE
BER_TAG_AARE_RESULT: Final = 0xA2
BER_TAG_AARE_DIAGNOSTIC: Final = 0xA3
BER_TAG_RELEASE_REASON: Final = 0x80

ACSE_REQUIREMENTS_AUTHENTICATION: Final = b"\x02\x07\x80"
RELEASE_REASON_NORMAL: Final = 0

BER_LENGTH_SINGLE_BYTE: Final = 0x01
RLRQ_LENGTH: Final = 0x03

REQUEST_TYPE_NORMAL: Final = 0x01
RESPONSE_TYPE_NORMAL: Final = 0x01
RESULT_TYPE_SUCCESS: Final = 0x00
RESULT_TYPE_DATA_ACCESS_RESULT: Final = 0x01
ACCESS_SELECTION_NONE: Final = 0x00
DEFAULT_PRIORITY: Final = 0xC0
INVOKE_ID_MASK: Final = 0x0F
PRIORITY_MASK: Final = 0xF0


class ApduTags(IntEnum):
    """DLMS/COSEM Application Protocol Data Unit (APDU) tags."""

    AARQ = 0x60
    AARE = 0x61
    RLRQ = 0x62
    RLRE = 0x63
    GET_REQUEST = 0xC0
    GET_RESPONSE = 0xC4


def encode_aarq(
    password: str | bytes | None = None,
    system_title: bytes | None = None,
) -> bytes:
    """Encode an Application Association Request (AARQ) APDU."""
    effective_system_title = system_title if system_title is not None else DEFAULT_SYSTEM_TITLE
    if len(effective_system_title) != SYSTEM_TITLE_LENGTH:
        raise ValueError(
            f"System title must be exactly {SYSTEM_TITLE_LENGTH} bytes, "
            f"got {len(effective_system_title)}"
        )

    parts: list[bytes] = []

    parts.append(
        bytes([BER_TAG_AARQ_APP_CONTEXT, len(APP_CONTEXT_LN_NO_CIPHER)]) + APP_CONTEXT_LN_NO_CIPHER
    )

    calling_ap_title_field = (
        bytes([BER_TAG_OCTET_STRING, len(effective_system_title)]) + effective_system_title
    )
    parts.append(
        bytes([BER_TAG_AARQ_CALLING_AP_TITLE, len(calling_ap_title_field)]) + calling_ap_title_field
    )

    if password is not None:
        password_bytes = password.encode("utf-8") if isinstance(password, str) else password
        if len(password_bytes) > 0:
            parts.append(bytes([BER_TAG_AARQ_ACSE_REQUIREMENTS]) + ACSE_REQUIREMENTS_AUTHENTICATION)
            parts.append(
                bytes([BER_TAG_AARQ_MECHANISM_NAME, len(MECHANISM_NAME_LLS)]) + MECHANISM_NAME_LLS
            )
            value_field = (
                bytes([BER_TAG_AARQ_AUTHENTICATION_VALUE_PRIMITIVE])
                + encode_axdr_length(len(password_bytes))
                + password_bytes
            )
            parts.append(
                bytes([BER_TAG_AARQ_AUTHENTICATION_VALUE])
                + encode_axdr_length(len(value_field))
                + value_field
            )

    user_information = (
        bytes([BER_TAG_OCTET_STRING])
        + encode_axdr_length(len(DEFAULT_INITIATE_REQUEST))
        + DEFAULT_INITIATE_REQUEST
    )
    parts.append(
        bytes([BER_TAG_AARQ_USER_INFORMATION])
        + encode_axdr_length(len(user_information))
        + user_information
    )

    body = b"".join(parts)
    return bytes([ApduTags.AARQ]) + encode_axdr_length(len(body)) + body


def _read_ber_tlv(data: bytes, position: int) -> tuple[int, bytes, int] | None:
    """Read a single BER TLV element returning (tag, value_bytes, next_position) or None."""
    if position + 2 > len(data):
        return None
    tag = data[position]
    position += 1
    length_byte = data[position]
    position += 1
    if length_byte < BER_MULTI_BYTE_LENGTH_FLAG:
        length = length_byte
    else:
        length_bytes_count = length_byte & BER_LENGTH_VALUE_MASK
        if position + length_bytes_count > len(data):
            return None
        length = int.from_bytes(data[position : position + length_bytes_count], "big")
        position += length_bytes_count

    if position + length > len(data):
        return None
    chunk = data[position : position + length]
    return tag, chunk, position + length


def _parse_aare_result(chunk: bytes) -> AssociationResult:
    """Parse AssociationResult enum from result field bytes."""
    try:
        return AssociationResult(chunk[2])
    except ValueError, IndexError:
        return AssociationResult.REJECTED_PERMANENT


def _parse_aare_diagnostic(chunk: bytes) -> int:
    """Parse diagnostic integer from result-source-diagnostic field bytes."""
    if len(chunk) >= 5 and chunk[2] == BER_TAG_INTEGER and chunk[3] == BER_LENGTH_SINGLE_BYTE:
        return chunk[4]
    return 0


def decode_aare(apdu: bytes) -> tuple[AssociationResult, int]:
    """Decode an Application Association Response (AARE) APDU into (result, diagnostic)."""
    if len(apdu) < 3 or apdu[0] != ApduTags.AARE:
        raise ProtocolError(f"Invalid AARE APDU: {apdu.hex()}")

    position = 1
    initial_length = apdu[position]
    position += 1
    if initial_length >= BER_MULTI_BYTE_LENGTH_FLAG:
        length_bytes_count = initial_length & BER_LENGTH_VALUE_MASK
        position += length_bytes_count

    result: AssociationResult | None = None
    diagnostic: int = 0

    while position < len(apdu):
        tlv = _read_ber_tlv(apdu, position)
        if tlv is None:
            break
        tag, chunk, position = tlv

        if tag == BER_TAG_AARE_RESULT:
            result = _parse_aare_result(chunk)
        elif tag == BER_TAG_AARE_DIAGNOSTIC:
            diagnostic = _parse_aare_diagnostic(chunk)

    if result is None:
        raise ProtocolError(f"AARE APDU missing result field: {apdu.hex()}")

    return result, diagnostic


def encode_get_request_normal(
    attribute: CosemAttribute,
    invoke_id: int = 0,
    priority: int = DEFAULT_PRIORITY,
) -> bytes:
    """Encode a Get-Request-Normal APDU querying a COSEM attribute."""
    invoke_id_byte = (priority & PRIORITY_MASK) | (invoke_id & INVOKE_ID_MASK)
    return (
        bytes([ApduTags.GET_REQUEST, REQUEST_TYPE_NORMAL, invoke_id_byte])
        + attribute.to_bytes()
        + bytes([ACCESS_SELECTION_NONE])
    )


def decode_get_response_normal(apdu: bytes) -> tuple[int, bool, Any]:
    """Decode a Get-Response-Normal APDU into (invoke_id, is_success, value_or_error_code)."""
    if len(apdu) < 4 or apdu[0] != ApduTags.GET_RESPONSE:
        raise ProtocolError(f"Invalid Get-Response APDU: {apdu.hex()}")

    choice = apdu[1]
    if choice != RESPONSE_TYPE_NORMAL:
        raise ProtocolError(
            f"Unsupported Get-Response type 0x{choice:02X} "
            f"(only Normal=0x{RESPONSE_TYPE_NORMAL:02X} is supported)"
        )

    invoke_id = apdu[2] & INVOKE_ID_MASK
    result_type = apdu[3]

    if result_type == RESULT_TYPE_SUCCESS:
        decoded_value = decode_axdr(apdu[4:])
        return invoke_id, True, decoded_value

    if result_type == RESULT_TYPE_DATA_ACCESS_RESULT:
        if len(apdu) < 5:
            raise ProtocolError("Get-Response-Normal error result missing error code")
        try:
            error_code = DataAccessResult(apdu[4])
        except ValueError:
            error_code = DataAccessResult.OTHER_REASON
        return invoke_id, False, error_code

    raise ProtocolError(f"Unknown GetDataResult choice: 0x{result_type:02X}")


def encode_rlrq(reason: int = RELEASE_REASON_NORMAL) -> bytes:
    """Encode an ACSE Release Request (RLRQ) APDU."""
    return bytes(
        [
            ApduTags.RLRQ,
            RLRQ_LENGTH,
            BER_TAG_RELEASE_REASON,
            BER_LENGTH_SINGLE_BYTE,
            reason,
        ]
    )


def decode_rlre(apdu: bytes) -> int:
    """Decode an ACSE Release Response (RLRE) APDU into release reason code."""
    if len(apdu) < 2 or apdu[0] != ApduTags.RLRE:
        raise ProtocolError(f"Invalid RLRE APDU: {apdu.hex()}")
    if len(apdu) >= 5 and apdu[2] == BER_TAG_RELEASE_REASON and apdu[3] == BER_LENGTH_SINGLE_BYTE:
        return apdu[4]
    return RELEASE_REASON_NORMAL
