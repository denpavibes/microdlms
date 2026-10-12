"""Pure sans-I/O DLMS/COSEM state machine and session engine."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum, auto
from functools import cached_property
from typing import Final

from microdlms.apdu import (
    ApduTags,
    decode_aare,
    decode_get_response_normal,
    decode_rlre,
    encode_aarq,
    encode_get_request_normal,
    encode_rlrq,
)
from microdlms.const import DEFAULT_CLIENT_LOGICAL_ADDRESS, DEFAULT_SERVER_LOGICAL_ADDRESS
from microdlms.exceptions import ProtocolError
from microdlms.hdlc import (
    HdlcControls,
    HdlcFrame,
    build_frame,
    encode_address,
    make_i_control,
    parse_hdlc_frame,
    slice_hdlc_frames,
    unwrap_llc,
    wrap_llc,
)
from microdlms.obis import CosemAttribute
from microdlms.types import (
    AssociatedEvent,
    AssociationRejectedEvent,
    AssociationResult,
    ConnectedEvent,
    DisconnectedEvent,
    GetAccessErrorEvent,
    GetResponseEvent,
    ProtocolErrorEvent,
    ReleasedEvent,
    SessionEvent,
)

HDLC_SEQUENCE_MODULO: Final = 8
INVOKE_ID_MODULO: Final = 16


class SessionState(Enum):
    """Internal states for DlmsSession state machine."""

    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    ASSOCIATING = auto()
    ASSOCIATED = auto()
    DISCONNECTING = auto()


class DlmsSession:
    """Pure sans-I/O state machine managing HDLC framing and DLMS session lifecycles."""

    def __init__(
        self,
        client_logical_address: int = DEFAULT_CLIENT_LOGICAL_ADDRESS,
        server_logical_address: int = DEFAULT_SERVER_LOGICAL_ADDRESS,
        server_physical_address: int | None = None,
        system_title: bytes | None = None,
    ) -> None:
        self.client_logical_address = client_logical_address
        self.server_logical_address = server_logical_address
        self.server_physical_address = server_physical_address
        self.system_title = system_title

        self._destination_address_bytes = encode_address(
            server_logical_address, server_physical_address
        )
        self._source_address_bytes = encode_address(client_logical_address)

        self._state = SessionState.DISCONNECTED
        self._send_seq = 0
        self._recv_seq = 0
        self._invoke_id = 0

        self._inbound_buffer = bytearray()
        self._outbound_buffer = bytearray()

    @property
    def state(self) -> SessionState:
        """Current session connection and association state."""
        return self._state

    @property
    def send_seq(self) -> int:
        """Current client send sequence number N(S) (0..7)."""
        return self._send_seq

    @property
    def recv_seq(self) -> int:
        """Current expected server sequence number N(R) (0..7)."""
        return self._recv_seq

    @property
    def invoke_id(self) -> int:
        """Current invoke ID counter (0..15)."""
        return self._invoke_id

    def initiate_connect(self) -> None:
        """Prepare an HDLC SNRM frame to establish physical data link connection."""
        self._send_seq = 0
        self._recv_seq = 0
        self._invoke_id = 0

        snrm_frame = build_frame(
            dest_address=self._destination_address_bytes,
            src_address=self._source_address_bytes,
            control=HdlcControls.SNRM,
            information=None,
        )
        self._outbound_buffer.extend(snrm_frame)
        self._state = SessionState.CONNECTING

    def initiate_association(
        self,
        password: str | bytes | None = None,
        system_title: bytes | None = None,
    ) -> None:
        """Prepare an AARQ APDU wrapped in an HDLC I-frame for application association."""
        if self._state not in (SessionState.CONNECTED, SessionState.DISCONNECTED):
            raise ProtocolError(f"Cannot initiate association in state {self._state.name}")

        effective_system_title = system_title if system_title is not None else self.system_title
        aarq_apdu = encode_aarq(password=password, system_title=effective_system_title)
        info = wrap_llc(aarq_apdu)

        control = make_i_control(send_seq=self._send_seq, recv_seq=self._recv_seq, poll=True)
        frame = build_frame(
            dest_address=self._destination_address_bytes,
            src_address=self._source_address_bytes,
            control=control,
            information=info,
        )
        self._send_seq = (self._send_seq + 1) % HDLC_SEQUENCE_MODULO
        self._outbound_buffer.extend(frame)
        self._state = SessionState.ASSOCIATING

    def request_attribute(self, attribute: CosemAttribute) -> int:
        """Prepare a Get-Request-Normal frame for a COSEM attribute. Returns allocated invoke_id."""
        if self._state != SessionState.ASSOCIATED:
            raise ProtocolError(
                f"Cannot request attribute in state {self._state.name}; must be ASSOCIATED"
            )

        current_invoke_id = self._invoke_id
        self._invoke_id = (self._invoke_id + 1) % INVOKE_ID_MODULO

        get_apdu = encode_get_request_normal(attribute=attribute, invoke_id=current_invoke_id)
        info = wrap_llc(get_apdu)

        control = make_i_control(send_seq=self._send_seq, recv_seq=self._recv_seq, poll=True)
        frame = build_frame(
            dest_address=self._destination_address_bytes,
            src_address=self._source_address_bytes,
            control=control,
            information=info,
        )
        self._send_seq = (self._send_seq + 1) % HDLC_SEQUENCE_MODULO
        self._outbound_buffer.extend(frame)
        return current_invoke_id

    def initiate_release(self, reason: int = 0) -> None:
        """Prepare an ACSE Release Request (RLRQ) frame."""
        rlrq_apdu = encode_rlrq(reason=reason)
        info = wrap_llc(rlrq_apdu)
        control = make_i_control(send_seq=self._send_seq, recv_seq=self._recv_seq, poll=True)
        frame = build_frame(
            dest_address=self._destination_address_bytes,
            src_address=self._source_address_bytes,
            control=control,
            information=info,
        )
        self._send_seq = (self._send_seq + 1) % HDLC_SEQUENCE_MODULO
        self._outbound_buffer.extend(frame)

    def initiate_disconnect(self) -> None:
        """Prepare an HDLC DISC frame to terminate physical connection."""
        disc_frame = build_frame(
            dest_address=self._destination_address_bytes,
            src_address=self._source_address_bytes,
            control=HdlcControls.DISC,
            information=None,
        )
        self._outbound_buffer.extend(disc_frame)
        self._state = SessionState.DISCONNECTING

    def data_to_send(self) -> bytes:
        """Retrieve and drain all outbound serial bytes queued for transmission."""
        outbound_data = bytes(self._outbound_buffer)
        self._outbound_buffer.clear()
        return outbound_data

    def _handle_aare_apdu(self, apdu: bytes) -> SessionEvent:
        """Decode AARE APDU and update association state."""
        try:
            result, diagnostic = decode_aare(apdu)
            if result == AssociationResult.ACCEPTED:
                self._state = SessionState.ASSOCIATED
                return AssociatedEvent()
            return AssociationRejectedEvent(result=result, diagnostic=diagnostic)
        except Exception as error:
            return ProtocolErrorEvent(f"Failed to decode AARE APDU: {error}")

    def _handle_get_response_apdu(self, apdu: bytes) -> SessionEvent:
        """Decode Get-Response APDU and return response or error event."""
        try:
            invoke_id, is_success, value = decode_get_response_normal(apdu)
            if is_success:
                return GetResponseEvent(invoke_id=invoke_id, value=value)
            return GetAccessErrorEvent(invoke_id=invoke_id, error_code=value)
        except Exception as error:
            return ProtocolErrorEvent(f"Failed to decode Get-Response APDU: {error}")

    def _handle_rlre_apdu(self, apdu: bytes) -> SessionEvent:
        """Decode RLRE APDU and revert to connected state."""
        try:
            reason = decode_rlre(apdu)
            self._state = SessionState.CONNECTED
            return ReleasedEvent(reason=reason)
        except Exception as error:
            return ProtocolErrorEvent(f"Failed to decode RLRE APDU: {error}")

    def _handle_iframe(self, frame: HdlcFrame) -> SessionEvent:
        """Process incoming I-frame: update seq counter, unwrap LLC, and dispatch APDU."""
        if frame.send_seq is not None:
            self._recv_seq = (frame.send_seq + 1) % HDLC_SEQUENCE_MODULO

        if not frame.information:
            return ProtocolErrorEvent("Information field missing in received I-frame")

        try:
            apdu = unwrap_llc(frame.information)
        except ProtocolError as error:
            return ProtocolErrorEvent(str(error))

        if not apdu:
            return ProtocolErrorEvent("Empty APDU in received I-frame")

        tag = apdu[0]
        if not (handler := self._iframe_handlers.get(tag)):
            return ProtocolErrorEvent(f"Unsupported APDU tag 0x{tag:02X}")

        return handler(apdu)

    @cached_property
    def _iframe_handlers(self) -> dict[int, Callable[[bytes], SessionEvent]]:
        """I-frame handler lookup table."""
        return {
            ApduTags.AARE: self._handle_aare_apdu,
            ApduTags.GET_RESPONSE: self._handle_get_response_apdu,
            ApduTags.RLRE: self._handle_rlre_apdu,
        }

    def _handle_uframe(self, frame: HdlcFrame) -> SessionEvent:
        """Process incoming unnumbered control frame (UA, DM, DISC)."""
        control = frame.control
        if control in (HdlcControls.UA_FINAL, HdlcControls.UA):
            if self._state == SessionState.CONNECTING:
                self._state = SessionState.CONNECTED
                self._send_seq = 0
                self._recv_seq = 0
                return ConnectedEvent()
            if self._state == SessionState.DISCONNECTING:
                self._state = SessionState.DISCONNECTED
                return DisconnectedEvent()
            return ConnectedEvent()

        if control in (HdlcControls.DM_FINAL, HdlcControls.DM, HdlcControls.DISC):
            self._state = SessionState.DISCONNECTED
            return DisconnectedEvent()

        return ProtocolErrorEvent(f"Unexpected HDLC control byte: 0x{control:02X}")

    def _handle_sframe(self, frame: HdlcFrame) -> SessionEvent:
        """Process incoming supervisory frame (RR, RNR, REJ), resyncing send sequence counter."""
        if frame.recv_seq is not None:
            self._send_seq = frame.recv_seq

        supervisory_name = (
            frame.supervisory_type.name if frame.supervisory_type is not None else "UNKNOWN"
        )
        return ProtocolErrorEvent(
            f"Supervisory frame received: {supervisory_name} N(R)={frame.recv_seq}"
        )

    def receive_bytes(self, data: bytes) -> list[SessionEvent]:
        """Ingest incoming raw serial bytes, decode HDLC frames, and yield resulting events."""
        self._inbound_buffer.extend(data)
        frames = slice_hdlc_frames(self._inbound_buffer)
        events: list[SessionEvent] = []

        for raw_frame in frames:
            try:
                frame = parse_hdlc_frame(raw_frame)
            except ProtocolError as error:
                events.append(ProtocolErrorEvent(str(error)))
                continue

            if frame.is_iframe:
                event = self._handle_iframe(frame)
            elif frame.is_sframe:
                event = self._handle_sframe(frame)
            else:
                event = self._handle_uframe(frame)
            events.append(event)

        return events
