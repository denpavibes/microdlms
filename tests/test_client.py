"""Tests for AsyncMeterClient using mocked serialx connections (zero real I/O)."""

from __future__ import annotations

import asyncio
from typing import Any, cast
from unittest.mock import patch

import pytest

from microdlms.client import AsyncMeterClient
from microdlms.exceptions import (
    AuthenticationError,
    CommunicationError,
    DataAccessError,
)
from microdlms.hdlc import build_frame, encode_address, make_i_control, wrap_llc
from microdlms.obis import CosemAttribute, ObisCode
from microdlms.session import SessionState
from microdlms.types import (
    ConnectedEvent,
    DataAccessResult,
    DisconnectedEvent,
    GetResponseEvent,
    InterfaceClass,
)


class MockWriter:
    """Mock StreamWriter for testing AsyncMeterClient."""

    def __init__(self) -> None:
        self.written_bytes = bytearray()
        self.closed = False

    def write(self, data: bytes) -> None:
        self.written_bytes.extend(data)

    async def drain(self) -> None:
        pass

    def close(self) -> None:
        self.closed = True

    async def wait_closed(self) -> None:
        pass


class MockReader:
    """Mock StreamReader for feeding simulated frame responses."""

    def __init__(self) -> None:
        self.queue: asyncio.Queue[bytes] = asyncio.Queue()

    async def read(self, size: int = -1) -> bytes:
        return await self.queue.get()

    def feed_bytes(self, data: bytes) -> None:
        self.queue.put_nowait(data)


class EchoingMockWriter(MockWriter):
    """MockWriter that immediately echoes written bytes into MockReader followed by response."""

    def __init__(self, reader: MockReader, responses: list[bytes] | None = None) -> None:
        super().__init__()
        self.reader = reader
        self.responses = list(responses) if responses is not None else []

    def write(self, data: bytes) -> None:
        super().write(data)
        self.reader.feed_bytes(bytes(data))
        if self.responses:
            self.reader.feed_bytes(self.responses.pop(0))


@pytest.fixture
def mock_serial_pair() -> tuple[MockReader, MockWriter]:
    return MockReader(), MockWriter()


def test_client_default_server_physical_address() -> None:
    """Verify server_physical_address defaults to None and can be overridden."""
    client_default = AsyncMeterClient(port="COM1")
    assert client_default.server_physical_address is None
    assert client_default.session.server_physical_address is None

    client_custom = AsyncMeterClient(port="COM1", server_physical_address=42)
    assert client_custom.server_physical_address == 42
    assert client_custom.session.server_physical_address == 42


async def test_client_connect_and_get_lifecycle(
    mock_serial_pair: tuple[MockReader, MockWriter],
) -> None:
    """Test standard connect, get attribute, and disconnect flow."""
    reader, writer = mock_serial_pair

    # Pre-populate responses:
    # 1. UA response to SNRM
    ua_frame = build_frame(encode_address(32), encode_address(1, 42), 0x73)
    reader.feed_bytes(ua_frame)

    # 2. AARE Accepted response to AARQ
    aare_apdu = bytes.fromhex(
        "6129a109060760857405080101a203020100a305a103020100be10040e0800065f1f040000101d00640007"
    )
    aare_frame = build_frame(
        dest_address=encode_address(32),
        src_address=encode_address(1, 42),
        control=make_i_control(send_seq=0, recv_seq=1),
        information=wrap_llc(aare_apdu),
    )
    reader.feed_bytes(aare_frame)

    # 3. Get-Response-Normal with serial number string
    get_response_apdu = bytes.fromhex("c401c0000a083431393230393432")
    get_response_frame = build_frame(
        dest_address=encode_address(32),
        src_address=encode_address(1, 42),
        control=make_i_control(send_seq=1, recv_seq=2),
        information=wrap_llc(get_response_apdu),
    )
    reader.feed_bytes(get_response_frame)

    # 4. UA response to DISC
    disconnect_ua_frame = build_frame(encode_address(32), encode_address(1, 42), 0x73)
    reader.feed_bytes(disconnect_ua_frame)

    with patch("serialx.open_serial_connection", return_value=(reader, writer)):
        client = AsyncMeterClient(
            port="socket://192.168.1.100:8888",
            baudrate=9600,
            password="111111",
            timeout=2.0,
        )
        assert client.is_connected is False

        await client.connect()
        assert client.is_connected is True

        attribute = CosemAttribute(
            interface=InterfaceClass.DATA,
            obis=ObisCode(0, 0, 96, 1, 0, 255),
            attribute=2,
        )
        value = await client.get(attribute)
        assert value == "41920942"

        await client.disconnect()
        assert client.is_connected is False
        assert writer.closed is True


async def test_client_async_context_manager(
    mock_serial_pair: tuple[MockReader, MockWriter],
) -> None:
    """Test AsyncMeterClient as an async context manager."""
    reader, writer = mock_serial_pair

    ua_frame = build_frame(encode_address(32), encode_address(1, 42), 0x73)
    reader.feed_bytes(ua_frame)

    aare_apdu = bytes.fromhex(
        "6129a109060760857405080101a203020100a305a103020100be10040e0800065f1f040000101d00640007"
    )
    aare_frame = build_frame(
        encode_address(32),
        encode_address(1, 42),
        make_i_control(0, 1),
        wrap_llc(aare_apdu),
    )
    reader.feed_bytes(aare_frame)

    disconnect_ua_frame = build_frame(encode_address(32), encode_address(1, 42), 0x73)
    reader.feed_bytes(disconnect_ua_frame)

    with patch("serialx.open_serial_connection", return_value=(reader, writer)):
        async with AsyncMeterClient(port="COM3", password="111111", timeout=2.0) as client:
            assert client.is_connected is True
            assert client.session is not None

        assert client.is_connected is False
        assert writer.closed is True


async def test_client_connection_failure() -> None:
    """Verify CommunicationError when serial transport cannot be opened."""
    with patch("serialx.open_serial_connection", side_effect=OSError("Device not found")):
        client = AsyncMeterClient(port="/dev/ttyUSB0")
        with pytest.raises(CommunicationError, match="Failed to open connection"):
            await client.connect()


async def test_client_authentication_failure(
    mock_serial_pair: tuple[MockReader, MockWriter],
) -> None:
    """Verify AuthenticationError when meter rejects association password."""
    reader, writer = mock_serial_pair

    # 1. UA response to SNRM
    ua_frame = build_frame(encode_address(32), encode_address(1, 42), 0x73)
    reader.feed_bytes(ua_frame)

    # 2. AARE Rejected (AUTHENTICATION_FAILED, diag=13)
    fail_apdu = bytes.fromhex("611fa109060760857405080101a203020101a305a10302010dbe0604040e010601")
    fail_frame = build_frame(
        encode_address(32),
        encode_address(1, 42),
        make_i_control(0, 1),
        wrap_llc(fail_apdu),
    )
    reader.feed_bytes(fail_frame)

    with patch("serialx.open_serial_connection", return_value=(reader, writer)):
        client = AsyncMeterClient(port="COM1", password="wrong", timeout=2.0)
        with pytest.raises(AuthenticationError, match="Association rejected by meter"):
            await client.connect()


async def test_client_data_access_error(
    mock_serial_pair: tuple[MockReader, MockWriter],
) -> None:
    """Verify DataAccessError is raised when meter returns error on attribute get."""
    reader, writer = mock_serial_pair

    # SNRM -> UA
    reader.feed_bytes(build_frame(encode_address(32), encode_address(1, 42), 0x73))
    # AARQ -> AARE Accepted
    aare_apdu = bytes.fromhex(
        "6129a109060760857405080101a203020100a305a103020100be10040e0800065f1f040000101d00640007"
    )
    reader.feed_bytes(
        build_frame(
            encode_address(32),
            encode_address(1, 42),
            make_i_control(0, 1),
            wrap_llc(aare_apdu),
        )
    )

    # Get-Response error: OBJECT_UNDEFINED (4)
    error_apdu = bytes.fromhex("c401c00104")
    reader.feed_bytes(
        build_frame(
            encode_address(32),
            encode_address(1, 42),
            make_i_control(1, 2),
            wrap_llc(error_apdu),
        )
    )

    with patch("serialx.open_serial_connection", return_value=(reader, writer)):
        client = AsyncMeterClient(port="COM1", timeout=2.0)
        await client.connect()

        attribute = CosemAttribute(InterfaceClass.DATA, ObisCode(0, 0, 99, 99, 99, 255), 2)
        with pytest.raises(DataAccessError) as exc_info:
            await client.get(attribute)

        assert exc_info.value.error_code == DataAccessResult.OBJECT_UNDEFINED
        assert "OBJECT_UNDEFINED" in str(exc_info.value)


async def test_client_get_not_connected() -> None:
    """Verify CommunicationError when get() is called without connect()."""
    client = AsyncMeterClient(port="COM1")
    attribute = CosemAttribute(InterfaceClass.DATA, ObisCode(0, 0, 1, 0, 0, 255), 2)
    with pytest.raises(CommunicationError, match="Client is not connected"):
        await client.get(attribute)


async def test_client_timeout_and_eof(
    mock_serial_pair: tuple[MockReader, MockWriter],
) -> None:
    """Verify CommunicationError on read timeout or transport EOF."""
    reader, writer = mock_serial_pair

    # Timeout during connect
    with patch("serialx.open_serial_connection", return_value=(reader, writer)):
        client = AsyncMeterClient(port="COM1", timeout=0.1)
        with pytest.raises(CommunicationError, match="Timeout"):
            await client.connect()

    # EOF during read
    reader_eof = MockReader()
    reader_eof.feed_bytes(b"")  # EOF
    with patch("serialx.open_serial_connection", return_value=(reader_eof, writer)):
        client_eof = AsyncMeterClient(port="COM1", timeout=1.0)
        with pytest.raises(CommunicationError, match="EOF encountered"):
            await client_eof.connect()


async def test_client_reconnect_and_protocol_errors(
    mock_serial_pair: tuple[MockReader, MockWriter],
) -> None:
    """Test re-connect, protocol errors during connect/associate/get, and writer cleanup."""
    reader, writer = mock_serial_pair

    # 1. Re-connect when already connected is a no-op
    ua_frame = build_frame(encode_address(32), encode_address(1, 42), 0x73)
    reader.feed_bytes(ua_frame)
    aare_apdu = bytes.fromhex(
        "6129a109060760857405080101a203020100a305a103020100be10040e0800065f1f040000101d00640007"
    )
    reader.feed_bytes(
        build_frame(
            encode_address(32), encode_address(1, 42), make_i_control(0, 1), wrap_llc(aare_apdu)
        )
    )
    with patch("serialx.open_serial_connection", return_value=(reader, writer)):
        client = AsyncMeterClient(port="COM1", password="111111", timeout=2.0)
        await client.connect()
        assert client.is_connected is True
        # Re-calling connect should return immediately without opening new connection
        await client.connect()
        assert client.is_connected is True

    # 2. ProtocolErrorEvent during HDLC connect
    reader_connect_error, writer_connect_error = MockReader(), MockWriter()
    reader_connect_error.feed_bytes(b"\x7e\xa0\x08\x02\x55\x41\x93\x00\x00\x7e")  # bad FCS
    with patch(
        "serialx.open_serial_connection",
        return_value=(reader_connect_error, writer_connect_error),
    ):
        client_connect_error = AsyncMeterClient(port="COM1", timeout=2.0)
        with pytest.raises(CommunicationError, match="HDLC connect failed"):
            await client_connect_error.connect()

    # 3. ProtocolErrorEvent during association
    reader_association_error, writer_association_error = MockReader(), MockWriter()
    reader_association_error.feed_bytes(ua_frame)
    reader_association_error.feed_bytes(
        b"\x7e\xa0\x08\x02\x55\x41\x93\x00\x00\x7e"
    )  # bad FCS on association
    with patch(
        "serialx.open_serial_connection",
        return_value=(reader_association_error, writer_association_error),
    ):
        client_association_error = AsyncMeterClient(port="COM1", password="111111", timeout=2.0)
        with pytest.raises(CommunicationError, match="Association failed"):
            await client_association_error.connect()

    # 4. ProtocolErrorEvent during get
    reader_get_error, writer_get_error = MockReader(), MockWriter()
    reader_get_error.feed_bytes(ua_frame)
    reader_get_error.feed_bytes(
        build_frame(
            encode_address(32), encode_address(1, 42), make_i_control(0, 1), wrap_llc(aare_apdu)
        )
    )
    reader_get_error.feed_bytes(b"\x7e\xa0\x08\x02\x55\x41\x93\x00\x00\x7e")  # bad frame during get
    with patch(
        "serialx.open_serial_connection",
        return_value=(reader_get_error, writer_get_error),
    ):
        client_get_error = AsyncMeterClient(port="COM1", timeout=2.0, retries=0)
        await client_get_error.connect()
        attribute = CosemAttribute(InterfaceClass.DATA, ObisCode(0, 0, 1, 0, 0, 255), 2)
        with pytest.raises(CommunicationError, match="Protocol error during get"):
            await client_get_error.get(attribute)

    # 5. Unexpected event during get
    reader_unexpected, writer_unexpected = MockReader(), MockWriter()
    reader_unexpected.feed_bytes(ua_frame)
    reader_unexpected.feed_bytes(
        build_frame(
            encode_address(32), encode_address(1, 42), make_i_control(0, 1), wrap_llc(aare_apdu)
        )
    )
    # Feed DISC from meter during get -> delivers DisconnectedEvent instead of GetResponse
    disc_frame = build_frame(encode_address(32), encode_address(1, 42), 0x53)
    reader_unexpected.feed_bytes(disc_frame)
    with patch(
        "serialx.open_serial_connection",
        return_value=(reader_unexpected, writer_unexpected),
    ):
        client_unexpected = AsyncMeterClient(port="COM1", timeout=2.0)
        await client_unexpected.connect()
        attribute = CosemAttribute(InterfaceClass.DATA, ObisCode(0, 0, 1, 0, 0, 255), 2)
        # 5a: DisconnectedEvent received over the wire during wait
        with pytest.raises(CommunicationError, match="Connection disconnected by meter"):
            await client_unexpected.get(attribute)

        # 5b: DisconnectedEvent already in event_queue before read
        client_unexpected._event_queue.append(DisconnectedEvent())
        with pytest.raises(CommunicationError, match="Connection disconnected by meter"):
            await client_unexpected._wait_for_event(GetResponseEvent)

        # 5c: Arbitrary unexpected event
        client_unexpected._session._state = client_unexpected._session._state.ASSOCIATED
        with (
            pytest.raises(CommunicationError, match="Unexpected event"),
            patch.object(client_unexpected, "_wait_for_event", return_value=ConnectedEvent()),
        ):
            await client_unexpected.get(attribute)

        # 5d: Calling connect when writer is not None triggers disconnect() cleanup
        client_unexpected._writer = MockWriter()
        client_unexpected._session._state = client_unexpected._session._state.DISCONNECTED
        reader_reconnected, writer_reconnected = MockReader(), MockWriter()
        reader_reconnected.feed_bytes(ua_frame)
        reader_reconnected.feed_bytes(
            build_frame(
                encode_address(32),
                encode_address(1, 42),
                make_i_control(0, 1),
                wrap_llc(aare_apdu),
            )
        )
        with patch(
            "serialx.open_serial_connection",
            return_value=(reader_reconnected, writer_reconnected),
        ):
            await client_unexpected.connect()
            assert client_unexpected.is_connected is True

    # 6. Reader is not initialized in _wait_for_event
    client_uninitialized_reader = AsyncMeterClient(port="COM1")
    with pytest.raises(CommunicationError, match="Reader is not initialized"):
        await client_uninitialized_reader._wait_for_event(ConnectedEvent)

    # 7. Disconnect with writer raising exceptions in close / wait_closed
    class BrokenWriter(MockWriter):
        async def wait_closed(self) -> None:
            raise OSError("Socket already broken")

    client_broken_writer = AsyncMeterClient(port="COM1")
    client_broken_writer._writer = BrokenWriter()
    reader_broken_writer = MockReader()
    reader_broken_writer.feed_bytes(ua_frame)
    client_broken_writer._reader = cast(asyncio.StreamReader, reader_broken_writer)
    client_broken_writer._session._state = client_broken_writer._session._state.CONNECTED
    # Disconnect should suppress exceptions and cleanly reset _writer
    await client_broken_writer.disconnect()
    assert client_broken_writer._writer is None

    # 8. Event already buffered in _event_queue returned immediately
    client_buffered_event = AsyncMeterClient(port="COM1")
    client_buffered_event._event_queue.append(ConnectedEvent())
    buffered_event = await client_buffered_event._wait_for_event(ConnectedEvent)
    assert isinstance(buffered_event, ConnectedEvent)

    # 9. Disconnect when meter does not respond to DISC times out gracefully
    reader_timeout_disc, writer_timeout_disc = MockReader(), MockWriter()
    client_timeout_disc = AsyncMeterClient(port="COM1")
    client_timeout_disc._writer = writer_timeout_disc
    client_timeout_disc._reader = cast(asyncio.StreamReader, reader_timeout_disc)
    client_timeout_disc._session._state = client_timeout_disc._session._state.CONNECTED
    # reader_timeout_disc is empty, so waiting for DisconnectedEvent times out within 2.0s
    with patch.object(
        client_timeout_disc, "_wait_for_event", side_effect=CommunicationError("Timeout")
    ):
        await client_timeout_disc.disconnect()
    assert client_timeout_disc._writer is None


async def test_client_get_retry_recovers_from_corrupted_frame(
    mock_serial_pair: tuple[MockReader, MockWriter],
) -> None:
    """Verify that a transient corrupted frame (FCS error) during GET is retried and succeeds."""
    reader, writer = mock_serial_pair

    # 1. Connect frames
    ua_frame = build_frame(encode_address(32), encode_address(1, 42), 0x73)
    reader.feed_bytes(ua_frame)
    aare_apdu = bytes.fromhex(
        "6129a109060760857405080101a203020100a305a103020100be10040e0800065f1f040000101d00640007"
    )
    aare_frame = build_frame(
        dest_address=encode_address(32),
        src_address=encode_address(1, 42),
        control=make_i_control(send_seq=0, recv_seq=1),
        information=wrap_llc(aare_apdu),
    )
    reader.feed_bytes(aare_frame)

    # 2. First attempt: Corrupted frame (bad FCS)
    reader.feed_bytes(b"\x7e\xa0\x08\x02\x55\x41\x93\x00\x00\x7e")

    # 3. Second attempt (retry): Valid Get-Response-Normal
    get_response_apdu = bytes.fromhex("c401c0000a083431393230393432")
    get_response_frame = build_frame(
        dest_address=encode_address(32),
        src_address=encode_address(1, 42),
        control=make_i_control(send_seq=1, recv_seq=2),
        information=wrap_llc(get_response_apdu),
    )
    reader.feed_bytes(get_response_frame)

    with patch("serialx.open_serial_connection", return_value=(reader, writer)):
        client = AsyncMeterClient(port="COM1", timeout=1.0, retries=2, retry_delay=0.01)
        await client.connect()
        assert client.is_connected is True

        attribute = CosemAttribute(
            interface=InterfaceClass.DATA,
            obis=ObisCode(0, 0, 96, 1, 0, 255),
            attribute=2,
        )
        value = await client.get(attribute)
        assert value == "41920942"
        # Connection remained alive and intact
        assert client.is_connected is True


async def test_client_get_retry_recovers_from_timeout(
    mock_serial_pair: tuple[MockReader, MockWriter],
) -> None:
    """Verify that a timeout on the first attempt is retried and succeeds on the second attempt."""
    reader, writer = mock_serial_pair

    ua_frame = build_frame(encode_address(32), encode_address(1, 42), 0x73)
    reader.feed_bytes(ua_frame)
    aare_apdu = bytes.fromhex(
        "6129a109060760857405080101a203020100a305a103020100be10040e0800065f1f040000101d00640007"
    )
    reader.feed_bytes(
        build_frame(
            encode_address(32),
            encode_address(1, 42),
            make_i_control(0, 1),
            wrap_llc(aare_apdu),
        )
    )

    get_response_apdu = bytes.fromhex("c401c0000a083431393230393432")
    get_response_frame = build_frame(
        dest_address=encode_address(32),
        src_address=encode_address(1, 42),
        control=make_i_control(send_seq=1, recv_seq=2),
        information=wrap_llc(get_response_apdu),
    )

    async def delayed_feed() -> None:
        await asyncio.sleep(0.08)
        reader.feed_bytes(get_response_frame)

    with patch("serialx.open_serial_connection", return_value=(reader, writer)):
        client = AsyncMeterClient(port="COM1", timeout=0.04, retries=2)
        await client.connect()

        attribute = CosemAttribute(InterfaceClass.DATA, ObisCode(0, 0, 96, 1, 0, 255), 2)
        delayed_feed_task = asyncio.create_task(delayed_feed())
        try:
            value = await client.get(attribute)
            assert value == "41920942"
        finally:
            await delayed_feed_task


async def test_client_get_retries_aborted_if_disconnected(
    mock_serial_pair: tuple[MockReader, MockWriter],
) -> None:
    """Verify that retries are aborted immediately if session state is disconnected."""
    reader, writer = mock_serial_pair
    client = AsyncMeterClient(port="COM1", timeout=1.0, retries=3)
    client._writer = writer
    client._reader = cast(asyncio.StreamReader, reader)
    client._session._state = SessionState.ASSOCIATED

    attribute = CosemAttribute(InterfaceClass.DATA, ObisCode(0, 0, 96, 1, 0, 255), 2)

    async def fake_wait_fail(*args: Any, **kwargs: Any) -> Any:
        client._session._state = SessionState.DISCONNECTED
        raise CommunicationError("Disconnected mid-request")

    with (
        patch.object(client, "_wait_for_event", side_effect=fake_wait_fail),
        pytest.raises(CommunicationError, match="Disconnected mid-request"),
    ):
        await client.get(attribute)


async def test_client_get_zero_retries_and_parameter_override(
    mock_serial_pair: tuple[MockReader, MockWriter],
) -> None:
    """Verify that setting retries=0 suppresses retries and fails on the first error."""
    reader, writer = mock_serial_pair
    client = AsyncMeterClient(port="COM1", timeout=1.0, retries=5)
    client._writer = writer
    client._reader = cast(asyncio.StreamReader, reader)
    client._session._state = SessionState.ASSOCIATED

    attribute = CosemAttribute(InterfaceClass.DATA, ObisCode(0, 0, 96, 1, 0, 255), 2)

    call_count = 0

    async def fake_wait(*args: Any, **kwargs: Any) -> Any:
        nonlocal call_count
        call_count += 1
        raise CommunicationError("Flaky read")

    with (
        patch.object(client, "_wait_for_event", side_effect=fake_wait),
        pytest.raises(CommunicationError, match="Flaky read"),
    ):
        await client.get(attribute, retries=0)

    assert call_count == 1


async def test_client_get_discards_stale_delayed_response_from_previous_get(
    mock_serial_pair: tuple[MockReader, MockWriter],
) -> None:
    """Verify delayed response from previous query is discarded and doesn't corrupt next query."""
    reader, writer = mock_serial_pair

    # Connect frames
    ua_frame = build_frame(encode_address(32), encode_address(1, 42), 0x73)
    reader.feed_bytes(ua_frame)
    aare_apdu = bytes.fromhex(
        "6129a109060760857405080101a203020100a305a103020100be10040e0800065f1f040000101d00640007"
    )
    reader.feed_bytes(
        build_frame(
            dest_address=encode_address(32),
            src_address=encode_address(1, 42),
            control=make_i_control(send_seq=0, recv_seq=1),
            information=wrap_llc(aare_apdu),
        )
    )

    with patch("serialx.open_serial_connection", return_value=(reader, writer)):
        client = AsyncMeterClient(port="COM1", timeout=0.03, retries=0)
        await client.connect()

        attribute_a = CosemAttribute(InterfaceClass.DATA, ObisCode(0, 0, 96, 1, 0, 255), 2)
        # Query A fails with timeout (no bytes fed)
        with pytest.raises(CommunicationError, match="Timeout"):
            await client.get(attribute_a)

        # Delayed response for Query A (invoke_id=0, serial number) arrives
        response_a_apdu = bytes.fromhex(
            "c401c0000a083431393230393432"
        )  # invoke_id 0, value "41920942"
        frame_a = build_frame(
            dest_address=encode_address(32),
            src_address=encode_address(1, 42),
            control=make_i_control(send_seq=1, recv_seq=2),
            information=wrap_llc(response_a_apdu),
        )
        reader.feed_bytes(frame_a)

        # And valid response for Query B (invoke_id=1, value 230 - unsigned 16-bit 0x00E6) arrives
        response_b_apdu = bytes.fromhex("c401c1001200e6")  # invoke_id 1, value 230
        frame_b = build_frame(
            dest_address=encode_address(32),
            src_address=encode_address(1, 42),
            control=make_i_control(send_seq=2, recv_seq=3),
            information=wrap_llc(response_b_apdu),
        )
        reader.feed_bytes(frame_b)

        attribute_b = CosemAttribute(InterfaceClass.REGISTER, ObisCode(1, 0, 32, 7, 0, 255), 2)
        value_b = await client.get(attribute_b, timeout=1.0)
        # Must return Query B's value (230), NOT Query A's stale value ("41920942")!
        assert value_b == 230


async def test_client_get_multiple_retries_mixed_errors_eventual_success(
    mock_serial_pair: tuple[MockReader, MockWriter],
) -> None:
    """Verify get() recovers across retries with timeout followed by bad FCS followed by success."""
    reader, writer = mock_serial_pair

    # Connect frames
    ua_frame = build_frame(encode_address(32), encode_address(1, 42), 0x73)
    reader.feed_bytes(ua_frame)
    aare_apdu = bytes.fromhex(
        "6129a109060760857405080101a203020100a305a103020100be10040e0800065f1f040000101d00640007"
    )
    reader.feed_bytes(
        build_frame(
            dest_address=encode_address(32),
            src_address=encode_address(1, 42),
            control=make_i_control(send_seq=0, recv_seq=1),
            information=wrap_llc(aare_apdu),
        )
    )

    with patch("serialx.open_serial_connection", return_value=(reader, writer)):
        client = AsyncMeterClient(port="COM1", timeout=0.03, retries=2, retry_delay=0.01)
        await client.connect()

        attribute = CosemAttribute(InterfaceClass.DATA, ObisCode(0, 0, 96, 1, 0, 255), 2)

        # Attempt 0: will timeout (no bytes fed in 0.03s)
        # Attempt 1: feed corrupted frame (bad FCS)
        # Attempt 2: feed valid response for attempt 2 (invoke_id 2)
        response_c_apdu = bytes.fromhex("c401c2000a083431393230393432")  # invoke_id 2
        frame_success = build_frame(
            dest_address=encode_address(32),
            src_address=encode_address(1, 42),
            control=make_i_control(send_seq=1, recv_seq=4),
            information=wrap_llc(response_c_apdu),
        )

        async def feed_after_initial_timeout() -> None:
            await asyncio.sleep(0.04)  # Wait for attempt 0 to timeout
            reader.feed_bytes(b"\x7e\xa0\x08\x02\x55\x41\x93\x00\x00\x7e")  # bad FCS for attempt 1
            await asyncio.sleep(0.02)
            reader.feed_bytes(frame_success)  # success for attempt 2

        delayed_feed_task = asyncio.create_task(feed_after_initial_timeout())
        try:
            value = await client.get(attribute)
            assert value == "41920942"
        finally:
            await delayed_feed_task


async def test_client_get_stale_data_access_error_ignored(
    mock_serial_pair: tuple[MockReader, MockWriter],
) -> None:
    """Verify that a stale GetAccessErrorEvent with non-matching invoke ID is ignored."""
    reader, writer = mock_serial_pair
    client = AsyncMeterClient(port="COM1", timeout=1.0)
    client._writer = writer
    client._reader = cast(asyncio.StreamReader, reader)
    client._session._state = SessionState.ASSOCIATED

    # Feed unexpected event and stale error for invoke_id=99 into event queue
    from microdlms.types import ConnectedEvent, GetAccessErrorEvent

    client._event_queue.append(ConnectedEvent())
    client._event_queue.append(
        GetAccessErrorEvent(invoke_id=99, error_code=DataAccessResult.HARDWARE_FAULT)
    )

    attribute = CosemAttribute(InterfaceClass.DATA, ObisCode(0, 0, 96, 1, 0, 255), 2)

    # Feed unexpected frame over the wire (UA -> ConnectedEvent), followed by valid response
    ua_frame = build_frame(encode_address(32), encode_address(1, 42), 0x73)
    reader.feed_bytes(ua_frame)

    # Valid response for invoke_id=0
    response_apdu = bytes.fromhex("c401c0000a083431393230393432")
    frame = build_frame(
        dest_address=encode_address(32),
        src_address=encode_address(1, 42),
        control=make_i_control(send_seq=1, recv_seq=2),
        information=wrap_llc(response_apdu),
    )
    reader.feed_bytes(frame)

    value = await client.get(attribute)
    assert value == "41920942"


async def test_client_echo_filter_exact_echo_stripped_lifecycle(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify optical probe echoes are stripped across connect, associate, get, and disconnect."""
    ua_frame = build_frame(encode_address(32), encode_address(1, 42), 0x73)
    aare_apdu = bytes.fromhex(
        "6129a109060760857405080101a203020100a305a103020100be10040e0800065f1f040000101d00640007"
    )
    aare_frame = build_frame(
        dest_address=encode_address(32),
        src_address=encode_address(1, 42),
        control=make_i_control(send_seq=0, recv_seq=1),
        information=wrap_llc(aare_apdu),
    )
    get_response_apdu = bytes.fromhex("c401c0000a083431393230393432")
    get_response_frame = build_frame(
        dest_address=encode_address(32),
        src_address=encode_address(1, 42),
        control=make_i_control(send_seq=1, recv_seq=2),
        information=wrap_llc(get_response_apdu),
    )
    disconnect_ua_frame = build_frame(encode_address(32), encode_address(1, 42), 0x73)

    reader = MockReader()
    writer = EchoingMockWriter(
        reader, [ua_frame, aare_frame, get_response_frame, disconnect_ua_frame]
    )

    with (
        patch("serialx.open_serial_connection", return_value=(reader, writer)),
        caplog.at_level("DEBUG"),
    ):
        client = AsyncMeterClient(
            port="COM1",
            password="111111",
            timeout=2.0,
            echo_filter=True,
        )
        assert client.echo_filter is True
        assert len(client._pending_echo) == 0

        await client.connect()
        assert client.is_connected is True
        assert len(client._pending_echo) == 0

        attribute = CosemAttribute(
            interface=InterfaceClass.DATA,
            obis=ObisCode(0, 0, 96, 1, 0, 255),
            attribute=2,
        )
        value = await client.get(attribute)
        assert value == "41920942"
        assert len(client._pending_echo) == 0

        await client.disconnect()
        assert client.is_connected is False
        assert len(client._pending_echo) == 0

    assert "Discarded" in caplog.text


async def test_client_echo_filter_combined_chunk_exact_echo_stripped(
    mock_serial_pair: tuple[MockReader, MockWriter],
) -> None:
    """Verify that exact echo prepended to valid response in a single read chunk is stripped."""
    reader, writer = mock_serial_pair

    # Pre-build frames
    # SNRM outbound frame for client_logical=32, server_logical=1, server_physical=42
    snrm_frame = build_frame(
        dest_address=encode_address(1, 42),
        src_address=encode_address(32),
        control=0x93,
    )
    ua_frame = build_frame(encode_address(32), encode_address(1, 42), 0x73)

    # Deliver combined chunk (exact echo + meter response) in one read
    reader.feed_bytes(snrm_frame + ua_frame)

    # Association frames
    from microdlms.apdu import encode_aarq

    aarq_apdu = encode_aarq(password="111111")
    aarq_frame = build_frame(
        dest_address=encode_address(1, 42),
        src_address=encode_address(32),
        control=make_i_control(send_seq=0, recv_seq=0),
        information=wrap_llc(aarq_apdu),
    )
    aare_apdu = bytes.fromhex(
        "6129a109060760857405080101a203020100a305a103020100be10040e0800065f1f040000101d00640007"
    )
    aare_frame = build_frame(
        dest_address=encode_address(32),
        src_address=encode_address(1, 42),
        control=make_i_control(send_seq=0, recv_seq=1),
        information=wrap_llc(aare_apdu),
    )
    reader.feed_bytes(aarq_frame + aare_frame)

    with patch("serialx.open_serial_connection", return_value=(reader, writer)):
        client = AsyncMeterClient(
            port="COM1",
            password="111111",
            server_physical_address=42,
            timeout=2.0,
            echo_filter=True,
        )
        await client.connect()
        assert client.is_connected is True


async def test_client_echo_filter_partial_and_mismatched_echo(
    mock_serial_pair: tuple[MockReader, MockWriter],
) -> None:
    """Verify partial or mismatched echoes clear echo buffer and preserve valid response frames."""
    reader, writer = mock_serial_pair

    # 1. Partial echo in single chunk for connect:
    snrm_frame = build_frame(
        dest_address=encode_address(1, 42),
        src_address=encode_address(32),
        control=0x93,
    )
    ua_frame = build_frame(encode_address(32), encode_address(1, 42), 0x73)
    # Feed partial echo (first 4 bytes of SNRM) immediately followed by UA frame
    reader.feed_bytes(snrm_frame[:4] + ua_frame)

    # 2. Association: partial echo delivered in separate read chunk, followed by AARE frame
    from microdlms.apdu import encode_aarq

    aarq_apdu = encode_aarq(password="111111")
    aarq_frame = build_frame(
        dest_address=encode_address(1, 42),
        src_address=encode_address(32),
        control=make_i_control(send_seq=0, recv_seq=0),
        information=wrap_llc(aarq_apdu),
    )
    aare_apdu = bytes.fromhex(
        "6129a109060760857405080101a203020100a305a103020100be10040e0800065f1f040000101d00640007"
    )
    aare_frame = build_frame(
        dest_address=encode_address(32),
        src_address=encode_address(1, 42),
        control=make_i_control(send_seq=0, recv_seq=1),
        information=wrap_llc(aare_apdu),
    )
    # Chunk 1: partial echo (5 bytes)
    reader.feed_bytes(aarq_frame[:5])
    # Chunk 2: full AARE response (first byte 0x7E mismatches 6th byte of AARQ frame)
    reader.feed_bytes(aare_frame)

    # 3. Get attribute: completely mismatched echo bytes (e.g. noise prefix)
    get_response_apdu = bytes.fromhex("c401c0000a083431393230393432")
    get_response_frame = build_frame(
        dest_address=encode_address(32),
        src_address=encode_address(1, 42),
        control=make_i_control(send_seq=1, recv_seq=2),
        information=wrap_llc(get_response_apdu),
    )
    # Noise mismatch: 3 garbage bytes followed by get_response_frame
    reader.feed_bytes(b"\x00\x01\x02" + get_response_frame)

    with patch("serialx.open_serial_connection", return_value=(reader, writer)):
        client = AsyncMeterClient(
            port="COM1",
            password="111111",
            server_physical_address=42,
            timeout=2.0,
            echo_filter=True,
        )
        await client.connect()
        assert client.is_connected is True

        attribute = CosemAttribute(
            interface=InterfaceClass.DATA,
            obis=ObisCode(0, 0, 96, 1, 0, 255),
            attribute=2,
        )
        value = await client.get(attribute)
        assert value == "41920942"


async def test_client_echo_filter_retry_recovery() -> None:
    """Verify that retries recover from corrupted frame when echo filter is enabled."""
    ua_frame = build_frame(encode_address(32), encode_address(1, 42), 0x73)
    aare_apdu = bytes.fromhex(
        "6129a109060760857405080101a203020100a305a103020100be10040e0800065f1f040000101d00640007"
    )
    aare_frame = build_frame(
        dest_address=encode_address(32),
        src_address=encode_address(1, 42),
        control=make_i_control(send_seq=0, recv_seq=1),
        information=wrap_llc(aare_apdu),
    )
    # Attempt 0: corrupt frame (bad FCS)
    corrupt_frame = b"\x7e\xa0\x08\x02\x55\x41\x93\x00\x00\x7e"
    # Attempt 1: successful response
    get_response_apdu = bytes.fromhex("c401c0000a083431393230393432")
    get_response_frame = build_frame(
        dest_address=encode_address(32),
        src_address=encode_address(1, 42),
        control=make_i_control(send_seq=1, recv_seq=2),
        information=wrap_llc(get_response_apdu),
    )

    reader = MockReader()
    writer = EchoingMockWriter(reader, [ua_frame, aare_frame, corrupt_frame, get_response_frame])

    with patch("serialx.open_serial_connection", return_value=(reader, writer)):
        client = AsyncMeterClient(
            port="COM1",
            timeout=1.0,
            retries=2,
            retry_delay=0.01,
            echo_filter=True,
        )
        await client.connect()

        attribute = CosemAttribute(
            interface=InterfaceClass.DATA,
            obis=ObisCode(0, 0, 96, 1, 0, 255),
            attribute=2,
        )
        value = await client.get(attribute)
        assert value == "41920942"
        assert len(client._pending_echo) == 0


async def test_client_default_echo_filter_false_preserves_raw_stream(
    mock_serial_pair: tuple[MockReader, MockWriter],
) -> None:
    """Verify default echo_filter=False preserves raw stream and fails on optical reflection."""
    reader, writer = mock_serial_pair
    client = AsyncMeterClient(port="COM1")
    assert client.echo_filter is False
    assert len(client._pending_echo) == 0

    client._writer = writer
    client._session.initiate_connect()
    await client._flush_outbound()

    # Outbound bytes transmitted, but _pending_echo remains empty when echo_filter is False
    assert len(client._pending_echo) == 0
    assert len(writer.written_bytes) > 0

    # _strip_pending_echo returns raw data unchanged
    test_stream = b"\x7e\xa0\x08\x01\x02\x03\x7e"
    assert client._strip_pending_echo(test_stream) == test_stream

    # Connect with echoing writer fails when echo_filter=False because raw echo breaks HDLC
    echo_reader = MockReader()
    ua_frame = build_frame(encode_address(32), encode_address(1, 42), 0x73)
    echoing_writer = EchoingMockWriter(echo_reader, [ua_frame])
    with (
        patch("serialx.open_serial_connection", return_value=(echo_reader, echoing_writer)),
        pytest.raises(CommunicationError, match="HDLC connect failed"),
    ):
        raw_client = AsyncMeterClient(port="COM1", echo_filter=False, timeout=1.0)
        await raw_client.connect()


async def test_client_pending_echo_buffer_cleared_on_disconnect_and_reconnect() -> None:
    """Verify pending echo buffer is cleared during disconnect, reconnect, and retry preparation."""
    client = AsyncMeterClient(port="COM1", echo_filter=True)

    # 1. Retry preparation clears buffer on both attempt 0 and retry attempt > 0
    client._pending_echo = bytearray(b"stale_bytes")
    client._inbound_echo_buffer = bytearray(b"stale_inbound")
    await client._prepare_next_retry(attempt=0, delay=0.0)
    assert len(client._pending_echo) == 0
    assert len(client._inbound_echo_buffer) == 0

    client._pending_echo = bytearray(b"stale_bytes")
    client._inbound_echo_buffer = bytearray(b"stale_inbound")
    await client._prepare_next_retry(attempt=1, delay=0.0)
    assert len(client._pending_echo) == 0
    assert len(client._inbound_echo_buffer) == 0

    # 2. Disconnect clears buffer
    client._pending_echo = bytearray(b"stale_bytes")
    client._inbound_echo_buffer = bytearray(b"stale_inbound")
    await client.disconnect()
    assert len(client._pending_echo) == 0
    assert len(client._inbound_echo_buffer) == 0

    # 3. Connection opening failure clears buffer
    client._pending_echo = bytearray(b"stale_bytes")
    client._inbound_echo_buffer = bytearray(b"stale_inbound")
    with (
        patch("serialx.open_serial_connection", side_effect=OSError("Serial open failed")),
        pytest.raises(CommunicationError, match="Serial open failed"),
    ):
        await client.connect()
    assert len(client._pending_echo) == 0
    assert len(client._inbound_echo_buffer) == 0

    # 4. Reconnect path with existing writer clears buffer and connects
    reader = MockReader()
    ua_frame = build_frame(encode_address(32), encode_address(1, 42), 0x73)
    aare_apdu = bytes.fromhex(
        "6129a109060760857405080101a203020100a305a103020100be10040e0800065f1f040000101d00640007"
    )
    aare_frame = build_frame(
        encode_address(32),
        encode_address(1, 42),
        make_i_control(0, 1),
        wrap_llc(aare_apdu),
    )
    writer = EchoingMockWriter(reader, [ua_frame, aare_frame])
    client._writer = writer
    client._session._state = SessionState.DISCONNECTED
    client._pending_echo = bytearray(b"stale_bytes")
    client._inbound_echo_buffer = bytearray(b"stale_inbound")

    with patch("serialx.open_serial_connection", return_value=(reader, writer)):
        await client.connect()
        assert client.is_connected is True
        assert len(client._pending_echo) == 0
        assert len(client._inbound_echo_buffer) == 0


async def test_client_echo_filter_multi_chunk_fragmentation() -> None:
    """Verify that exact echo split across multiple arbitrary read chunks is completely stripped."""
    snrm_frame = build_frame(
        dest_address=encode_address(1, 42),
        src_address=encode_address(32),
        control=0x93,
    )
    ua_frame = build_frame(encode_address(32), encode_address(1, 42), 0x73)

    from microdlms.apdu import encode_aarq

    aarq_apdu = encode_aarq(password="111111")
    aarq_frame = build_frame(
        dest_address=encode_address(1, 42),
        src_address=encode_address(32),
        control=make_i_control(send_seq=0, recv_seq=0),
        information=wrap_llc(aarq_apdu),
    )
    aare_apdu = bytes.fromhex(
        "6129a109060760857405080101a203020100a305a103020100be10040e0800065f1f040000101d00640007"
    )
    aare_frame = build_frame(
        dest_address=encode_address(32),
        src_address=encode_address(1, 42),
        control=make_i_control(send_seq=0, recv_seq=1),
        information=wrap_llc(aare_apdu),
    )

    get_response_apdu = bytes.fromhex("c401c0000a083431393230393432")
    get_response_frame = build_frame(
        dest_address=encode_address(32),
        src_address=encode_address(1, 42),
        control=make_i_control(send_seq=1, recv_seq=2),
        information=wrap_llc(get_response_apdu),
    )

    reader = MockReader()
    writer = MockWriter()

    # Feed SNRM echo in 3 chunks, followed by UA frame
    reader.feed_bytes(snrm_frame[:3])
    reader.feed_bytes(snrm_frame[3:6])
    reader.feed_bytes(snrm_frame[6:])
    reader.feed_bytes(ua_frame)

    # Feed AARQ echo in 3 chunks, followed by AARE frame
    reader.feed_bytes(aarq_frame[:4])
    reader.feed_bytes(aarq_frame[4:8])
    reader.feed_bytes(aarq_frame[8:])
    reader.feed_bytes(aare_frame)

    with patch("serialx.open_serial_connection", return_value=(reader, writer)):
        client = AsyncMeterClient(
            port="COM1",
            password="111111",
            server_physical_address=42,
            timeout=2.0,
            echo_filter=True,
        )
        await client.connect()
        assert client.is_connected is True

        # Pre-feed get echo in 2 chunks followed by get response
        get_request_frame = build_frame(
            dest_address=encode_address(1, 42),
            src_address=encode_address(32),
            control=make_i_control(send_seq=1, recv_seq=1),
            information=wrap_llc(bytes.fromhex("c001c000010000600100ff02")),
        )
        reader.feed_bytes(get_request_frame[:5])
        reader.feed_bytes(get_request_frame[5:])
        reader.feed_bytes(get_response_frame)

        attribute = CosemAttribute(
            interface=InterfaceClass.DATA,
            obis=ObisCode(0, 0, 96, 1, 0, 255),
            attribute=2,
        )
        value = await client.get(attribute)
        assert value == "41920942"
        assert len(client._pending_echo) == 0

        # Boundary check: passing empty bytes to _strip_pending_echo is a safe no-op
        assert client._strip_pending_echo(b"") == b""
