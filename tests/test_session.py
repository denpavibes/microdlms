"""Tests for DlmsSession sans-I/O state machine, OBIS representations, and domain types."""

from __future__ import annotations

import datetime

import pytest

from microdlms.apdu import RELEASE_REASON_NORMAL
from microdlms.const import DEFAULT_CLIENT_LOGICAL_ADDRESS, DEFAULT_SERVER_LOGICAL_ADDRESS
from microdlms.exceptions import ProtocolError
from microdlms.hdlc import HdlcControls, build_frame, encode_address, make_i_control, wrap_llc
from microdlms.obis import DEFAULT_COSEM_ATTRIBUTE_ID, CosemAttribute, ObisCode
from microdlms.session import DlmsSession, SessionState
from microdlms.types import (
    AssociatedEvent,
    AssociationRejectedEvent,
    AssociationResult,
    ConnectedEvent,
    CosemDateTime,
    DataAccessResult,
    DisconnectedEvent,
    GetAccessErrorEvent,
    GetResponseEvent,
    InterfaceClass,
    ProtocolErrorEvent,
    ReleasedEvent,
    ScalerUnit,
)


def test_obis_code() -> None:
    """Test ObisCode creation, validation, string parsing, and serialization."""
    obis = ObisCode(1, 0, 31, 7, 0, 255)
    assert str(obis) == "1.0.31.7.0.255"
    assert repr(obis) == "ObisCode(1, 0, 31, 7, 0, 255)"
    assert bytes(obis) == bytes([1, 0, 31, 7, 0, 255])
    assert obis.to_bytes() == bytes([1, 0, 31, 7, 0, 255])

    # Parsing from 6-group string
    parsed_6 = ObisCode.from_string("1.0.31.7.0.255")
    assert parsed_6 == obis

    # Parsing from 5-group string (defaults f=255)
    parsed_5 = ObisCode.from_string("1.0.31.7.0")
    assert parsed_5 == obis
    assert parsed_5.f == 255

    # Parsing from IEC dash/colon/asterisk formats
    assert ObisCode.from_string("1-0:31.7.0.255") == obis
    assert ObisCode.from_string("1-0:31.7.0*255") == obis
    assert ObisCode.from_string("Obis(a=1, b=0, c=31, d=7, e=0, f=255)") == obis
    assert ObisCode.from_string("Obis(1, 0, 31, 7, 0, 255)") == obis
    assert ObisCode.from_string("Obis(1, 0, 31, 7, 0)") == obis

    # Parsing from bytes
    obis_from_bytes = ObisCode.from_bytes(bytes([1, 0, 31, 7, 0, 255]))
    assert obis_from_bytes == obis

    # Validation errors
    with pytest.raises(ValueError, match="must be within 0..255"):
        ObisCode(256, 0, 0, 0, 0, 0)

    with pytest.raises(ValueError, match="must be within 0..255"):
        ObisCode(0, -1, 0, 0, 0, 0)

    with pytest.raises(ValueError, match="Expected 5 or 6"):
        ObisCode.from_string("1.2.3")

    with pytest.raises(ValueError, match="requires exactly 6 bytes"):
        ObisCode.from_bytes(b"\x01\x02\x03")


def test_cosem_attribute() -> None:
    """Test CosemAttribute descriptor serialization."""
    obis = ObisCode(0, 0, 42, 0, 0, 255)
    attribute = CosemAttribute(interface=InterfaceClass.DATA, obis=obis, attribute=2)
    assert attribute.attribute == 2
    descriptor_bytes = attribute.to_bytes()
    assert len(descriptor_bytes) == 9
    assert descriptor_bytes[0:2] == b"\x00\x01"
    assert descriptor_bytes[2:8] == bytes([0, 0, 42, 0, 0, 255])
    assert descriptor_bytes[8] == 2


def test_scaler_unit() -> None:
    """Test ScalerUnit calculation and construction from A-XDR structure."""
    scaler_unit = ScalerUnit(scaler=-2, unit=35)
    assert pytest.approx(scaler_unit.scale(21967), rel=1e-5) == 219.67

    scaler_unit_cubic_meters = ScalerUnit(scaler=-3, unit=33)
    assert pytest.approx(scaler_unit_cubic_meters.scale(2065), rel=1e-5) == 2.065

    # from_structure
    scaler_unit_from_structure = ScalerUnit.from_structure([-2, 35])
    assert scaler_unit_from_structure == scaler_unit

    with pytest.raises(ValueError, match="Expected 2 elements"):
        ScalerUnit.from_structure([1, 2, 3])


def test_cosem_date_time() -> None:
    """Test CosemDateTime parsing of 12-byte DLMS octet strings into Python datetime."""
    # 2026-10-10 19:23:35 UTC+3 (deviation = 180 min = 0x00B4)
    data = bytes.fromhex("07ea0a0a061317230000b400")
    cosem_date_time = CosemDateTime.from_bytes(data)
    assert cosem_date_time.year == 2026
    assert cosem_date_time.month == 10
    assert cosem_date_time.day == 10
    assert cosem_date_time.day_of_week == 6
    assert cosem_date_time.hour == 19
    assert cosem_date_time.minute == 23
    assert cosem_date_time.second == 35
    assert cosem_date_time.hundredths == 0
    assert cosem_date_time.deviation == 180
    assert cosem_date_time.status == 0

    date_time_value = cosem_date_time.as_datetime()
    assert date_time_value is not None
    assert date_time_value.year == 2026
    assert date_time_value.month == 10
    assert date_time_value.day == 10
    assert date_time_value.hour == 19
    assert date_time_value.minute == 23
    assert date_time_value.second == 35
    assert date_time_value.tzinfo == datetime.timezone(datetime.timedelta(minutes=180))
    assert cosem_date_time.to_datetime() == date_time_value

    # Unspecified date returns None
    unspecified_data = bytes.fromhex("ffffffffffffffff0000b400")
    cosem_date_time_unspecified = CosemDateTime.from_bytes(unspecified_data)
    assert cosem_date_time_unspecified.as_datetime() is None

    # Deviation unspecified (-32768) uses UTC
    data_no_deviation = bytes.fromhex("07ea0a0a0613172300800000")
    cosem_date_time_no_deviation = CosemDateTime.from_bytes(data_no_deviation)
    assert cosem_date_time_no_deviation.deviation is None
    date_time_utc = cosem_date_time_no_deviation.as_datetime()
    assert date_time_utc is not None
    assert date_time_utc.tzinfo == datetime.UTC

    # Out-of-bounds hundredths (>99) clamped to 0 microsecond
    data_bad_hundredths = bytes.fromhex("07ea0a0a06131723c8000000")  # hundredths = 200 (0xC8)
    cosem_date_time_bad_hundredths = CosemDateTime.from_bytes(data_bad_hundredths)
    date_time_bad_hundredths = cosem_date_time_bad_hundredths.as_datetime()
    assert date_time_bad_hundredths is not None
    assert date_time_bad_hundredths.microsecond == 0

    # Out-of-bounds deviation (> 1439 min) falls back to UTC
    data_huge_dev = bytes.fromhex("07ea0a0a061317230007d000")  # dev = 2000 min
    cosem_date_time_huge_dev = CosemDateTime.from_bytes(data_huge_dev)
    date_time_huge_dev = cosem_date_time_huge_dev.as_datetime()
    assert date_time_huge_dev is not None
    assert date_time_huge_dev.tzinfo == datetime.UTC

    # Invalid length
    with pytest.raises(ValueError, match="requires 12 bytes"):
        CosemDateTime.from_bytes(b"\x00" * 10)


def test_dlms_session_full_lifecycle() -> None:
    """Test complete sans-I/O session lifecycle: connect -> associate -> get -> disconnect."""

    def assert_state(current_session: DlmsSession, expected: SessionState) -> None:
        assert current_session.state == expected

    session = DlmsSession(client_address=32, server_logical_address=1, server_physical_address=42)
    assert_state(session, SessionState.DISCONNECTED)

    # 1. Initiate connect (SNRM)
    session.initiate_connect()
    assert_state(session, SessionState.CONNECTING)
    snrm_bytes = session.data_to_send()
    assert len(snrm_bytes) > 0
    assert len(session.data_to_send()) == 0  # outbound buffer drained

    # Meter responds with UA
    ua_frame = build_frame(encode_address(32), encode_address(1, 42), HdlcControls.UA_FINAL)
    events = session.receive_bytes(ua_frame)
    assert_state(session, SessionState.CONNECTED)
    assert len(events) == 1
    assert isinstance(events[0], ConnectedEvent)
    assert session.send_seq == 0
    assert session.recv_seq == 0

    # 2. Initiate association (AARQ)
    session.initiate_association(password="111111")
    assert_state(session, SessionState.ASSOCIATING)
    aarq_frame = session.data_to_send()
    assert len(aarq_frame) > 0
    assert session.send_seq == 1

    # Meter responds with AARE Accepted
    aare_apdu = bytes.fromhex(
        "6129a109060760857405080101a203020100a305a103020100be10040e0800065f1f040000101d00640007"
    )
    aare_frame = build_frame(
        dest_address=encode_address(32),
        src_address=encode_address(1, 42),
        control=make_i_control(send_seq=0, recv_seq=1),
        information=wrap_llc(aare_apdu),
    )
    events = session.receive_bytes(aare_frame)
    assert_state(session, SessionState.ASSOCIATED)
    assert len(events) == 1
    assert isinstance(events[0], AssociatedEvent)
    assert session.recv_seq == 1

    # 3. Query attribute
    attribute = CosemAttribute(
        interface=InterfaceClass.DATA,
        obis=ObisCode(0, 0, 42, 0, 0, 255),
        attribute=DEFAULT_COSEM_ATTRIBUTE_ID,
    )
    invoke_id = session.request_attribute(attribute)
    assert invoke_id == 0
    get_request_frame = session.data_to_send()
    assert len(get_request_frame) > 0
    assert session.send_seq == 2

    # Meter responds with Get-Response-Normal (serial string)
    get_response_apdu = bytes.fromhex("c401c0000a083431393230393432")
    get_response_frame = build_frame(
        dest_address=encode_address(32),
        src_address=encode_address(1, 42),
        control=make_i_control(send_seq=1, recv_seq=2),
        information=wrap_llc(get_response_apdu),
    )
    events = session.receive_bytes(get_response_frame)
    assert len(events) == 1
    assert isinstance(events[0], GetResponseEvent)
    assert events[0].invoke_id == 0
    assert events[0].value == "41920942"
    assert session.recv_seq == 2

    # 4. Initiate release
    session.initiate_release(reason=RELEASE_REASON_NORMAL)
    rlrq_frame = session.data_to_send()
    assert len(rlrq_frame) > 0

    rlre_apdu = bytes.fromhex("6303800100")
    rlre_frame = build_frame(
        dest_address=encode_address(32),
        src_address=encode_address(1, 42),
        control=make_i_control(send_seq=2, recv_seq=3),
        information=wrap_llc(rlre_apdu),
    )
    events = session.receive_bytes(rlre_frame)
    assert len(events) == 1
    assert isinstance(events[0], ReleasedEvent)
    assert_state(session, SessionState.CONNECTED)

    # 5. Initiate disconnect
    session.initiate_disconnect()
    assert_state(session, SessionState.DISCONNECTING)
    disc_frame = session.data_to_send()
    assert len(disc_frame) > 0

    ua_disconnect_frame = build_frame(
        encode_address(32), encode_address(1, 42), HdlcControls.UA_FINAL
    )
    events = session.receive_bytes(ua_disconnect_frame)
    assert_state(session, SessionState.DISCONNECTED)
    assert len(events) == 1
    assert isinstance(events[0], DisconnectedEvent)


def test_session_default_server_physical_address() -> None:
    """Verify default addresses and server_physical_address defaults to None on DlmsSession."""
    session_default = DlmsSession()
    assert session_default.client_address == DEFAULT_CLIENT_LOGICAL_ADDRESS
    assert session_default.server_logical_address == DEFAULT_SERVER_LOGICAL_ADDRESS
    assert session_default.server_physical_address is None

    session_custom = DlmsSession(server_physical_address=42)
    assert session_custom.server_physical_address == 42


def test_session_state_invariants() -> None:
    """Verify that operations in invalid states raise ProtocolError."""
    session = DlmsSession()

    # Cannot request attribute when DISCONNECTED
    attribute = CosemAttribute(InterfaceClass.DATA, ObisCode(0, 0, 42, 0, 0, 255), 2)
    with pytest.raises(ProtocolError, match="must be ASSOCIATED"):
        session.request_attribute(attribute)

    # Cannot initiate association when already CONNECTING
    session.initiate_connect()
    with pytest.raises(ProtocolError, match="Cannot initiate association in state CONNECTING"):
        session.initiate_association()


def test_session_sequence_and_invoke_id_wrapping() -> None:
    """Test N(S), N(R), and invoke_id modulo wrapping."""
    session = DlmsSession()
    session.initiate_connect()
    session.receive_bytes(
        build_frame(encode_address(32), encode_address(1, 42), HdlcControls.UA_FINAL)
    )
    session.initiate_association(password="111111")
    session.receive_bytes(
        build_frame(
            encode_address(32),
            encode_address(1, 42),
            make_i_control(0, 1),
            wrap_llc(
                bytes.fromhex(
                    "6129a109060760857405080101a203020100a305a103020100be10040e0800065f1f040000101d00640007"
                )
            ),
        )
    )

    attribute = CosemAttribute(
        InterfaceClass.DATA,
        ObisCode(0, 0, 42, 0, 0, 255),
        DEFAULT_COSEM_ATTRIBUTE_ID,
    )
    # Perform 16 requests to verify invoke_id starts at 0 and wraps 0..15 -> 0
    for expected_invoke_id in range(16):
        invoke_id = session.request_attribute(attribute)
        assert invoke_id == expected_invoke_id
    assert session.invoke_id == 0

    # 17th request wraps back to 0
    invoke_id_wrapped = session.request_attribute(attribute)
    assert invoke_id_wrapped == 0
    assert session.invoke_id == 1

    # Verify send_seq wraps modulo 8
    # 1 (from associate) + 16 (loop) + 1 (17th request) = 18 I-frames sent -> 18 % 8 = 2
    assert session.send_seq == 2


def test_session_error_handling() -> None:
    """Test session behavior on association rejection, access error, and protocol errors."""
    session = DlmsSession()
    session.initiate_connect()
    session.receive_bytes(
        build_frame(encode_address(32), encode_address(1, 42), HdlcControls.UA_FINAL)
    )

    # 1. Association rejected
    session.initiate_association(password="wrong")
    fail_apdu = bytes.fromhex("611fa109060760857405080101a203020101a305a10302010dbe0604040e010601")
    fail_frame = build_frame(
        encode_address(32),
        encode_address(1, 42),
        make_i_control(0, 1),
        wrap_llc(fail_apdu),
    )
    events = session.receive_bytes(fail_frame)
    assert len(events) == 1
    assert isinstance(events[0], AssociationRejectedEvent)
    assert events[0].result == AssociationResult.REJECTED_PERMANENT
    assert events[0].diagnostic == 13

    # Force associated for next test
    session._state = SessionState.ASSOCIATED

    # 2. Get Access Error (OBJECT_UNDEFINED)
    session.request_attribute(
        CosemAttribute(
            InterfaceClass.DATA,
            ObisCode(0, 0, 99, 99, 99, 255),
            DEFAULT_COSEM_ATTRIBUTE_ID,
        )
    )
    error_apdu = bytes.fromhex("c401c10104")
    error_frame = build_frame(
        encode_address(32),
        encode_address(1, 42),
        make_i_control(1, 2),
        wrap_llc(error_apdu),
    )
    events = session.receive_bytes(error_frame)
    assert len(events) == 1
    assert isinstance(events[0], GetAccessErrorEvent)
    assert events[0].error_code == DataAccessResult.OBJECT_UNDEFINED

    # 3. Corrupted frame delivers ProtocolErrorEvent
    bad_frame = b"\x7e\xa0\x08\x02\x55\x41\x93\x00\x00\x7e"
    events = session.receive_bytes(bad_frame)
    assert len(events) == 1
    assert isinstance(events[0], ProtocolErrorEvent)

    # 4. DM frame delivers DisconnectedEvent (both DM_FINAL and DM)
    dm_frame = build_frame(encode_address(32), encode_address(1, 42), HdlcControls.DM_FINAL)
    events = session.receive_bytes(dm_frame)
    assert len(events) == 1
    assert isinstance(events[0], DisconnectedEvent)
    assert session.state == SessionState.DISCONNECTED

    dm_frame_no_final = build_frame(encode_address(32), encode_address(1, 42), HdlcControls.DM)
    events = session.receive_bytes(dm_frame_no_final)
    assert len(events) == 1
    assert isinstance(events[0], DisconnectedEvent)

    # 5. DISC frame sent by meter disconnects session
    disc_frame = build_frame(encode_address(32), encode_address(1, 42), HdlcControls.DISC)
    events = session.receive_bytes(disc_frame)
    assert len(events) == 1
    assert isinstance(events[0], DisconnectedEvent)

    # 6. Unexpected control byte delivers ProtocolErrorEvent
    unknown_control_frame = build_frame(
        encode_address(32), encode_address(1, 42), HdlcControls.SNRM
    )  # unexpected SNRM from meter
    session._state = SessionState.ASSOCIATED
    events = session.receive_bytes(unknown_control_frame)
    assert len(events) == 1
    assert isinstance(events[0], ProtocolErrorEvent)

    # 7. I-frame with empty info field
    iframe_empty_info = build_frame(
        encode_address(32), encode_address(1, 42), make_i_control(2, 3), b""
    )
    # For build_frame with b"", it has no info. When parsed, information is None
    events = session.receive_bytes(iframe_empty_info)
    assert any(isinstance(event, ProtocolErrorEvent) for event in events)

    # 8. I-frame with invalid LLC header
    bad_llc_frame = build_frame(
        encode_address(32),
        encode_address(1, 42),
        make_i_control(2, 3),
        b"\x00\x00\x00\xc4\x01",
    )
    events = session.receive_bytes(bad_llc_frame)
    assert any(isinstance(event, ProtocolErrorEvent) for event in events)

    # 9. I-frame with empty APDU (only 3 bytes LLC, no APDU)
    empty_apdu_frame = build_frame(
        encode_address(32),
        encode_address(1, 42),
        make_i_control(2, 3),
        b"\xe6\xe7\x00",
    )
    events = session.receive_bytes(empty_apdu_frame)
    assert any(isinstance(event, ProtocolErrorEvent) for event in events)

    # 10. I-frame with unsupported APDU tag
    unknown_apdu_frame = build_frame(
        encode_address(32),
        encode_address(1, 42),
        make_i_control(2, 3),
        wrap_llc(b"\xd0\x01\x02"),
    )
    events = session.receive_bytes(unknown_apdu_frame)
    assert any(isinstance(event, ProtocolErrorEvent) for event in events)

    # 11. I-frame with malformed AARE
    bad_aare_frame = build_frame(
        encode_address(32),
        encode_address(1, 42),
        make_i_control(2, 3),
        wrap_llc(b"\x61\x02\xff\xff"),
    )
    events = session.receive_bytes(bad_aare_frame)
    assert any(isinstance(event, ProtocolErrorEvent) for event in events)

    # 12. I-frame with malformed Get-Response
    bad_get_frame = build_frame(
        encode_address(32),
        encode_address(1, 42),
        make_i_control(2, 3),
        wrap_llc(b"\xc4\x02\xff\xff"),
    )
    events = session.receive_bytes(bad_get_frame)
    assert any(isinstance(event, ProtocolErrorEvent) for event in events)

    # 13. I-frame with malformed RLRE (truncated RLRE APDU)
    bad_rlre_frame = build_frame(
        encode_address(32),
        encode_address(1, 42),
        make_i_control(2, 3),
        wrap_llc(b"\x63"),
    )
    events = session.receive_bytes(bad_rlre_frame)
    assert any(isinstance(event, ProtocolErrorEvent) for event in events)

    # 14. UA received while CONNECTED (spontaneous UA keepalive)
    session._state = SessionState.CONNECTED
    spontaneous_ua = build_frame(encode_address(32), encode_address(1, 42), HdlcControls.UA_FINAL)
    events = session.receive_bytes(spontaneous_ua)
    assert len(events) == 1
    assert isinstance(events[0], ConnectedEvent)
