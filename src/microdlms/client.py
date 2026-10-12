"""Asynchronous DLMS meter client powered by serialx."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Callable
from typing import Any, Final, Self

import serialx
from serialx import SerialException

from microdlms.const import (
    DEFAULT_CLIENT_LOGICAL_ADDRESS,
    DEFAULT_SERVER_LOGICAL_ADDRESS,
)
from microdlms.exceptions import (
    AuthenticationError,
    CommunicationError,
    DataAccessError,
)
from microdlms.obis import CosemAttribute
from microdlms.session import DlmsSession, SessionState
from microdlms.types import (
    AssociatedEvent,
    AssociationRejectedEvent,
    ConnectedEvent,
    DisconnectedEvent,
    GetAccessErrorEvent,
    GetResponseEvent,
    ProtocolErrorEvent,
    SessionEvent,
)

DEFAULT_BAUDRATE: Final = 9600
DEFAULT_TIMEOUT: Final = 10.0
DEFAULT_RETRIES: Final = 3
DEFAULT_RETRY_DELAY: Final = 0.0
DISCONNECT_TIMEOUT: Final = 2.0
BUFFER_READ_SIZE: Final = 1024


class AsyncMeterClient:
    """High-level asynchronous client for reading DLMS/COSEM meters over serial or TCP sockets."""

    def __init__(
        self,
        port: str,
        baudrate: int = DEFAULT_BAUDRATE,
        password: str | bytes | None = None,
        client_logical_address: int = DEFAULT_CLIENT_LOGICAL_ADDRESS,
        server_logical_address: int = DEFAULT_SERVER_LOGICAL_ADDRESS,
        server_physical_address: int | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        system_title: bytes | None = None,
        retries: int = DEFAULT_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.password = password
        self.client_logical_address = client_logical_address
        self.server_logical_address = server_logical_address
        self.server_physical_address = server_physical_address
        self.timeout = timeout
        self.system_title = system_title
        self.retries = retries
        self.retry_delay = retry_delay

        self._session = DlmsSession(
            client_logical_address=client_logical_address,
            server_logical_address=server_logical_address,
            server_physical_address=server_physical_address,
            system_title=system_title,
        )
        self._reader: asyncio.StreamReader | None = None
        self._writer: Any = None
        self._event_queue: list[SessionEvent] = []

    @property
    def is_connected(self) -> bool:
        """True if client is connected and application association is active."""
        return self._session.state == SessionState.ASSOCIATED

    @property
    def session(self) -> DlmsSession:
        """Underlying sans-I/O session state machine."""
        return self._session

    async def connect(self) -> None:
        """Establish physical serial/socket connection, HDLC link, and DLMS association."""
        if self._writer is not None:
            if self.is_connected:
                return
            await self.disconnect()

        try:
            self._reader, self._writer = await serialx.open_serial_connection(
                url=self.port,
                baudrate=self.baudrate,
            )
        except Exception as error:
            raise CommunicationError(
                f"Failed to open connection to {self.port}: {error}"
            ) from error

        try:
            # Step 1: Establish HDLC physical link (SNRM -> UA)
            self._session.initiate_connect()
            await self._flush_outbound()
            event = await self._wait_for_event(ConnectedEvent, ProtocolErrorEvent)
            if isinstance(event, ProtocolErrorEvent):
                raise CommunicationError(f"HDLC connect failed: {event.message}")

            # Step 2: Establish application association (AARQ -> AARE)
            self._session.initiate_association(
                password=self.password, system_title=self.system_title
            )
            await self._flush_outbound()
            event = await self._wait_for_event(
                AssociatedEvent,
                AssociationRejectedEvent,
                ProtocolErrorEvent,
            )
            if isinstance(event, AssociationRejectedEvent):
                raise AuthenticationError(
                    f"Association rejected by meter: result={event.result.name} "
                    f"(diagnostic={event.diagnostic})"
                )
            if isinstance(event, ProtocolErrorEvent):
                raise CommunicationError(f"Association failed: {event.message}")
        except Exception:
            await self.disconnect()
            raise

    def _handle_get_response_event(self, event: SessionEvent) -> Any:
        """Process event received in response to attribute get request."""
        if isinstance(event, GetResponseEvent):
            return event.value
        if isinstance(event, GetAccessErrorEvent):
            raise DataAccessError(
                error_code=event.error_code,
                message=f"Meter returned error: {event.error_code.name} ({event.error_code.value})",
            )
        if isinstance(event, ProtocolErrorEvent):
            raise CommunicationError(f"Protocol error during get: {event.message}")
        raise CommunicationError(f"Unexpected event received during get: {type(event).__name__}")

    async def _execute_get_attempt(
        self,
        attribute: CosemAttribute,
        pending_invoke_ids: set[int],
        timeout: float | None,
    ) -> Any:
        """Send a single attribute request and await its response event."""
        invoke_id = self._session.request_attribute(attribute)
        pending_invoke_ids.add(invoke_id)
        await self._flush_outbound()

        event = await self._wait_for_event(
            GetResponseEvent,
            GetAccessErrorEvent,
            ProtocolErrorEvent,
            timeout=timeout,
            predicate=lambda matched_event: (
                not isinstance(matched_event, (GetResponseEvent, GetAccessErrorEvent))
                or matched_event.invoke_id in pending_invoke_ids
            ),
        )
        return self._handle_get_response_event(event)

    async def _prepare_next_retry(self, attempt: int, delay: float) -> None:
        """Wait retry delay and clean transient protocol errors before retrying."""
        if attempt > 0:
            if delay > 0:
                await asyncio.sleep(delay)
            self._event_queue = [
                event for event in self._event_queue if not isinstance(event, ProtocolErrorEvent)
            ]

    def _raise_get_error(
        self,
        error: CommunicationError,
        primary_error: Exception | None,
        attempt: int,
        effective_retries: int,
    ) -> None:
        """Raise primary or current communication error if disconnected or out of retries."""
        if not self.is_connected or attempt == effective_retries:
            final_error = primary_error if primary_error is not None else error
            raise final_error from error

    async def get(
        self,
        attribute: CosemAttribute,
        retries: int | None = None,
        retry_delay: float | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Query a COSEM attribute from the meter and return its decoded Python value."""
        if not self.is_connected:
            raise CommunicationError("Client is not connected. Call connect() first.")

        effective_retries = max(0, self.retries if retries is None else retries)
        effective_delay = self.retry_delay if retry_delay is None else retry_delay
        primary_error: Exception | None = None
        pending_invoke_ids: set[int] = set()

        for attempt in range(effective_retries + 1):
            await self._prepare_next_retry(attempt, effective_delay)
            try:
                return await self._execute_get_attempt(attribute, pending_invoke_ids, timeout)
            except CommunicationError as error:
                if primary_error is None:
                    primary_error = error
                self._raise_get_error(error, primary_error, attempt, effective_retries)

    async def disconnect(self) -> None:
        """Gracefully release HDLC connection and close serial/socket transport."""
        try:
            if self._writer is not None and self._session.state in (
                SessionState.CONNECTED,
                SessionState.ASSOCIATED,
            ):
                self._session.initiate_disconnect()
                await self._flush_outbound()
                with contextlib.suppress(Exception):
                    await self._wait_for_event(
                        DisconnectedEvent, timeout=min(self.timeout, DISCONNECT_TIMEOUT)
                    )
        finally:
            if self._writer is not None:
                with contextlib.suppress(Exception):
                    self._writer.close()
                    await self._writer.wait_closed()
                self._writer = None
                self._reader = None
            self._event_queue.clear()

    async def _flush_outbound(self) -> None:
        """Transmit any pending bytes from the session outbound buffer."""
        outbound_bytes = self._session.data_to_send()
        if outbound_bytes and self._writer is not None:
            self._writer.write(outbound_bytes)
            await self._writer.drain()

    def _extract_matching_event(
        self,
        expected_types: tuple[type[SessionEvent], ...],
        predicate: Callable[[SessionEvent], bool] | None,
    ) -> SessionEvent | None:
        """Scan event queue for an expected event matching predicate or abort on disconnect."""
        index = 0
        while index < len(self._event_queue):
            event = self._event_queue[index]
            if isinstance(event, DisconnectedEvent) and DisconnectedEvent not in expected_types:
                self._event_queue.pop(index)
                raise CommunicationError("Connection disconnected by meter")
            if isinstance(event, expected_types):
                if predicate is None or predicate(event):
                    return self._event_queue.pop(index)
                self._event_queue.pop(index)
                continue
            index += 1
        return None

    async def _wait_for_event(
        self,
        *expected_types: type[SessionEvent],
        timeout: float | None = None,
        predicate: Callable[[SessionEvent], bool] | None = None,
    ) -> SessionEvent:
        """Read incoming serial bytes until an expected session event arrives."""
        cached_event = self._extract_matching_event(expected_types, predicate)
        if cached_event is not None:
            return cached_event

        if self._reader is None:
            raise CommunicationError("Reader is not initialized")

        effective_timeout = timeout if timeout is not None else self.timeout
        try:
            async with asyncio.timeout(effective_timeout):
                while True:
                    data = await self._reader.read(BUFFER_READ_SIZE)
                    if not data:
                        raise CommunicationError("Connection closed by peer / EOF encountered")

                    self._event_queue.extend(self._session.receive_bytes(data))
                    matching = self._extract_matching_event(expected_types, predicate)
                    if matching is not None:
                        return matching
        except TimeoutError as error:
            raise CommunicationError(
                f"Timeout ({effective_timeout}s) waiting for meter response"
            ) from error
        except (SerialException, OSError) as error:
            raise CommunicationError(f"Serial communication error: {error}") from error

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception_value: BaseException | None,
        traceback: Any,
    ) -> None:
        await self.disconnect()
