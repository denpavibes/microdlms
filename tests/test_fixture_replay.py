"""Validation and replay tests against physical meter captures in tests/meter_fixtures.py."""

from __future__ import annotations

import re
from typing import Any

import pytest

from microdlms.obis import CosemAttribute, ObisCode
from microdlms.session import DlmsSession, SessionState
from microdlms.types import (
    AssociatedEvent,
    AssociationRejectedEvent,
    AssociationResult,
    ConnectedEvent,
    DataAccessResult,
    DisconnectedEvent,
    GetAccessErrorEvent,
    GetResponseEvent,
)
from tests import meter_fixtures


def _parse_cosem_attribute(cosem_dict: dict[str, Any]) -> CosemAttribute:
    """Helper to convert fixture cosem dict to CosemAttribute."""
    raw_obis = cosem_dict["obis"]
    # Formats in fixtures: "Obis(a=0, b=0, c=42, d=0, e=0, f=255)" or "0.0.42.0.0.255"
    if raw_obis.startswith("Obis("):
        numbers = [int(number_string) for number_string in re.findall(r"\d+", raw_obis)]
        obis = ObisCode(numbers[0], numbers[1], numbers[2], numbers[3], numbers[4], numbers[5])
    else:
        obis = ObisCode.from_string(raw_obis)

    return CosemAttribute(
        interface=cosem_dict["interface_id"],
        obis=obis,
        attribute=cosem_dict["attribute"],
    )


def test_fixture_exchanges_count() -> None:
    """Verify that meter_fixtures.EXCHANGES contains all 46 captured frames."""
    assert len(meter_fixtures.EXCHANGES) == 46


@pytest.mark.parametrize("exchange", meter_fixtures.EXCHANGES, ids=lambda item: str(item["id"]))
def test_replay_individual_exchange_frames(exchange: dict[str, Any]) -> None:
    """Test HDLC request generation and response parsing for each individual fixture exchange."""
    exchange_id = exchange["id"]
    request_hdlc = exchange["req_hdlc"]
    response_hdlc = exchange["resp_hdlc"]

    session = DlmsSession(
        client_logical_address=meter_fixtures.CLIENT_LOGICAL_ADDRESS,
        server_logical_address=meter_fixtures.SERVER_LOGICAL_ADDRESS,
        server_physical_address=meter_fixtures.SERVER_PHYSICAL_ADDRESS,
    )

    if exchange_id in ("snrm_connect", "snrm_connect_auth_session"):
        session.initiate_connect()
        outbound_bytes = session.data_to_send()
        assert outbound_bytes == request_hdlc, (
            f"{exchange_id} request mismatch: {outbound_bytes.hex()} vs {request_hdlc.hex()}"
        )
        events = session.receive_bytes(response_hdlc)
        assert len(events) == 1
        assert isinstance(events[0], ConnectedEvent)

    elif exchange_id == "aarq_associate_success":
        session.initiate_connect()
        session.data_to_send()
        session.receive_bytes(meter_fixtures.SNRM_CONNECT_RESP_HDLC)
        session.initiate_association(
            password="111111",
            system_title=bytes.fromhex("7574691cc56a7264"),
        )
        outbound_bytes = session.data_to_send()
        assert outbound_bytes == request_hdlc, (
            f"{exchange_id} request mismatch: {outbound_bytes.hex()} vs {request_hdlc.hex()}"
        )
        events = session.receive_bytes(response_hdlc)
        assert len(events) == 1
        assert isinstance(events[0], AssociatedEvent)

    elif exchange_id == "aarq_associate_auth_failure":
        session.initiate_connect()
        session.data_to_send()
        session.receive_bytes(meter_fixtures.SNRM_CONNECT_RESP_HDLC)
        session.initiate_association(
            password="wrong!",
            system_title=bytes.fromhex("757469b6a30b1258"),
        )
        outbound_bytes = session.data_to_send()
        assert outbound_bytes == request_hdlc, (
            f"{exchange_id} request mismatch: {outbound_bytes.hex()} vs {request_hdlc.hex()}"
        )
        events = session.receive_bytes(response_hdlc)
        assert len(events) == 1
        assert isinstance(events[0], AssociationRejectedEvent)
        assert events[0].result == AssociationResult.REJECTED_PERMANENT
        assert events[0].diagnostic == 13

    elif exchange_id in ("disc_disconnect", "disc_disconnect_auth_session"):
        session.initiate_disconnect()
        outbound_bytes = session.data_to_send()
        assert outbound_bytes == request_hdlc, (
            f"{exchange_id} request mismatch: {outbound_bytes.hex()} vs {request_hdlc.hex()}"
        )
        events = session.receive_bytes(response_hdlc)
        assert len(events) == 1
        assert isinstance(events[0], DisconnectedEvent)

    else:
        # GET attribute request
        attribute = _parse_cosem_attribute(exchange["cosem"])
        # Set state to associated for individual unit replay
        session._state = SessionState.ASSOCIATED
        # Align send_seq and recv_seq from the request frame's control byte
        control_byte_request = request_hdlc[6]
        session._send_seq = (control_byte_request >> 1) & 0x07
        session._recv_seq = (control_byte_request >> 5) & 0x07
        # Align invoke_id from request_apdu (offset 2 in APDU)
        request_apdu = exchange["req_apdu"]
        session._invoke_id = request_apdu[2] & 0x0F

        allocated_invoke_id = session.request_attribute(attribute)
        outbound_bytes = session.data_to_send()
        assert outbound_bytes == request_hdlc, (
            f"{exchange_id} request mismatch: {outbound_bytes.hex()} vs {request_hdlc.hex()}"
        )

        events = session.receive_bytes(response_hdlc)
        assert len(events) == 1

        if exchange["category"] == "negative_test":
            assert isinstance(events[0], GetAccessErrorEvent)
            assert events[0].error_code == DataAccessResult.OBJECT_UNDEFINED
        else:
            assert isinstance(events[0], GetResponseEvent)
            assert events[0].invoke_id == allocated_invoke_id
            expected = exchange["decoded_value"]
            actual = events[0].value
            if isinstance(expected, dict) and expected.get("type") == "bytes":
                assert actual == bytes.fromhex(expected["hex"])
            else:
                assert actual == expected


def _replay_lifecycle_exchange(session: DlmsSession, exchange: dict[str, Any]) -> bool:
    """Handle connection, association, or disconnection exchanges."""
    exchange_id = exchange["id"]
    if exchange_id in ("snrm_connect", "snrm_connect_auth_session"):
        session.initiate_connect()
        expected_type: type = ConnectedEvent
    elif exchange_id == "aarq_associate_success":
        session.initiate_association(
            password="111111",
            system_title=bytes.fromhex("7574691cc56a7264"),
        )
        expected_type = AssociatedEvent
    elif exchange_id in ("disc_disconnect", "disc_disconnect_auth_session"):
        session.initiate_disconnect()
        expected_type = DisconnectedEvent
    elif exchange_id == "aarq_associate_auth_failure":
        session.initiate_association(
            password="wrong!",
            system_title=bytes.fromhex("757469b6a30b1258"),
        )
        expected_type = AssociationRejectedEvent
    else:
        return False

    assert session.data_to_send() == exchange["req_hdlc"]
    events = session.receive_bytes(exchange["resp_hdlc"])
    assert any(isinstance(event, expected_type) for event in events)
    return True


def _replay_attribute_read_exchange(session: DlmsSession, exchange: dict[str, Any]) -> None:
    """Handle single attribute read exchange."""
    attribute = _parse_cosem_attribute(exchange["cosem"])
    session.request_attribute(attribute)
    assert session.data_to_send() == exchange["req_hdlc"]
    events = session.receive_bytes(exchange["resp_hdlc"])
    assert len(events) == 1
    if exchange["category"] == "negative_test":
        assert isinstance(events[0], GetAccessErrorEvent)
        assert events[0].error_code == DataAccessResult.OBJECT_UNDEFINED
    else:
        assert isinstance(events[0], GetResponseEvent)


def test_full_continuous_session_replay() -> None:
    """Replay all 46 exchanges in continuous chronological order through a single DlmsSession."""
    session = DlmsSession(
        client_logical_address=meter_fixtures.CLIENT_LOGICAL_ADDRESS,
        server_logical_address=meter_fixtures.SERVER_LOGICAL_ADDRESS,
        server_physical_address=meter_fixtures.SERVER_PHYSICAL_ADDRESS,
    )

    for exchange in meter_fixtures.EXCHANGES:
        if not _replay_lifecycle_exchange(session, exchange):
            _replay_attribute_read_exchange(session, exchange)
