"""DLMS/COSEM Application Protocol Data Unit (APDU) codecs."""

from __future__ import annotations

from typing import Any, Final

from microdlms.axdr import decode_axdr, encode_axdr_length
from microdlms.exceptions import ProtocolError
from microdlms.obis import CosemAttribute
from microdlms.types import AssociationResult, DataAccessResult

TAG_AARQ: Final = 0x60
TAG_AARE: Final = 0x61
TAG_RLRQ: Final = 0x62
TAG_RLRE: Final = 0x63
TAG_GET_REQUEST: Final = 0xC0
TAG_GET_RESPONSE: Final = 0xC4

# Default system title matching captured fixtures if none provided
DEFAULT_SYSTEM_TITLE: Final = bytes.fromhex("7574691cc56a7264")

# Logical Name referencing without ciphering OID: 2.16.756.5.8.1.1
APP_CONTEXT_LN_NO_CIPHER: Final = bytes.fromhex("060760857405080101")

# Low-Level Security (LLS) Mechanism name OID: 2.16.756.5.8.2.1
MECHANISM_NAME_LLS: Final = bytes.fromhex("60857405080201")

# Default proposed xDLMS InitiateRequest conformance: 00 20 52, max receive PDU 24575
DEFAULT_INITIATE_REQUEST: Final = bytes.fromhex("01000000065f1f040020525fffff")


def encode_aarq(
    password: str | bytes | None = None,
    system_title: bytes | None = None,
) -> bytes:
    """Encode an Application Association Request (AARQ) APDU."""
    effective_system_title = system_title if system_title is not None else DEFAULT_SYSTEM_TITLE
    if len(effective_system_title) != 8:
        message = f"System title must be exactly 8 bytes, got {len(effective_system_title)}"
        raise ValueError(message)

    parts: list[bytes] = []

    # 1. Application-context-name [1]
    parts.append(b"\xa1\x09" + APP_CONTEXT_LN_NO_CIPHER)

    # 2. Calling-AP-title [6]
    parts.append(b"\xa6\x0a\x04\x08" + effective_system_title)

    # 3. Authentication (Low-Level Security if password provided)
    if password is not None:
        password_bytes = password.encode("utf-8") if isinstance(password, str) else password
        if len(password_bytes) > 0:
            # ACSE requirements [10]: authentication bit
            parts.append(b"\x8a\x02\x07\x80")
            # Mechanism-name [11]: LLS OID
            parts.append(b"\x8b\x07" + MECHANISM_NAME_LLS)
            # Calling-authentication-value [12] -> [0] primitive
            value_field = b"\x80" + encode_axdr_length(len(password_bytes)) + password_bytes
            parts.append(b"\xac" + encode_axdr_length(len(value_field)) + value_field)

    # 4. User-information [30] -> OCTET STRING wrapping xDLMS InitiateRequest
    user_information = (
        b"\x04" + encode_axdr_length(len(DEFAULT_INITIATE_REQUEST)) + DEFAULT_INITIATE_REQUEST
    )
    parts.append(b"\xbe" + encode_axdr_length(len(user_information)) + user_information)

    body = b"".join(parts)
    return bytes([TAG_AARQ]) + encode_axdr_length(len(body)) + body


def _read_ber_tlv(data: bytes, position: int) -> tuple[int, bytes, int] | None:
    """Read a single BER TLV element returning (tag, value_bytes, next_position) or None."""
    if position + 2 > len(data):
        return None
    tag = data[position]
    position += 1
    length_byte = data[position]
    position += 1
    if length_byte < 0x80:
        length = length_byte
    else:
        length_bytes_count = length_byte & 0x7F
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
    if len(chunk) >= 5 and chunk[2] == 0x02 and chunk[3] == 0x01:
        return chunk[4]
    return 0


def decode_aare(apdu: bytes) -> tuple[AssociationResult, int]:
    """Decode an Application Association Response (AARE) APDU into (result, diagnostic)."""
    if len(apdu) < 3 or apdu[0] != TAG_AARE:
        message = f"Invalid AARE APDU: {apdu.hex()}"
        raise ProtocolError(message)

    position = 1
    # Read length of AARE
    initial_length = apdu[position]
    position += 1
    if initial_length >= 0x80:
        length_bytes_count = initial_length & 0x7F
        position += length_bytes_count

    result: AssociationResult | None = None
    diagnostic: int = 0

    while position < len(apdu):
        tlv = _read_ber_tlv(apdu, position)
        if tlv is None:
            break
        tag, chunk, position = tlv

        if tag == 0xA2:  # result [2]
            result = _parse_aare_result(chunk)
        elif tag == 0xA3:  # result-source-diagnostic [3]
            diagnostic = _parse_aare_diagnostic(chunk)

    if result is None:
        message = f"AARE APDU missing result field: {apdu.hex()}"
        raise ProtocolError(message)

    return result, diagnostic


def encode_get_request_normal(
    attribute: CosemAttribute,
    invoke_id: int = 0,
    priority: int = 0xC0,
) -> bytes:
    """Encode a Get-Request-Normal APDU querying a COSEM attribute."""
    invoke_id_byte = (priority & 0xF0) | (invoke_id & 0x0F)
    # Tag 0xC0 (Get-Request), Choice 0x01 (Get-Request-Normal)
    # Followed by invoke_id_and_priority (1B), attribute descriptor (9B), access_selection (1B)
    return bytes([TAG_GET_REQUEST, 0x01, invoke_id_byte]) + attribute.to_bytes() + bytes([0x00])


def decode_get_response_normal(apdu: bytes) -> tuple[int, bool, Any]:
    """Decode a Get-Response-Normal APDU into (invoke_id, is_success, value_or_error_code)."""
    if len(apdu) < 4 or apdu[0] != TAG_GET_RESPONSE:
        message = f"Invalid Get-Response APDU: {apdu.hex()}"
        raise ProtocolError(message)

    choice = apdu[1]
    if choice != 0x01:
        message = f"Unsupported Get-Response type 0x{choice:02X} (only Normal=0x01 is supported)"
        raise ProtocolError(message)

    invoke_id = apdu[2] & 0x0F
    result_type = apdu[3]

    if result_type == 0x00:
        # Success: A-XDR data follows immediately at offset 4
        decoded_value = decode_axdr(apdu[4:])
        return invoke_id, True, decoded_value

    if result_type == 0x01:
        # DataAccessResult error code at offset 4
        if len(apdu) < 5:
            message = "Get-Response-Normal error result missing error code"
            raise ProtocolError(message)
        try:
            error_code = DataAccessResult(apdu[4])
        except ValueError:
            error_code = DataAccessResult.OTHER_REASON
        return invoke_id, False, error_code

    message = f"Unknown GetDataResult choice: 0x{result_type:02X}"
    raise ProtocolError(message)


def encode_rlrq(reason: int = 0) -> bytes:
    """Encode an ACSE Release Request (RLRQ) APDU."""
    return bytes([TAG_RLRQ, 0x03, 0x80, 0x01, reason])


def decode_rlre(apdu: bytes) -> int:
    """Decode an ACSE Release Response (RLRE) APDU into release reason code."""
    if len(apdu) < 2 or apdu[0] != TAG_RLRE:
        message = f"Invalid RLRE APDU: {apdu.hex()}"
        raise ProtocolError(message)
    if len(apdu) >= 5 and apdu[2] == 0x80 and apdu[3] == 0x01:
        return apdu[4]
    return 0
