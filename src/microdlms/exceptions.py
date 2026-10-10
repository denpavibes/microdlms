"""Exception hierarchy for microdlms client and codec operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from microdlms.types import DataAccessResult


class MicrodlmsError(Exception):
    """Base exception for all microdlms errors."""


class CommunicationError(MicrodlmsError):
    """Raised when transport, serial I/O, or connection timeouts fail."""


class AuthenticationError(MicrodlmsError):
    """Raised when DLMS association authentication fails."""


class DataAccessError(MicrodlmsError):
    """Raised when the meter returns a DataAccessResult error code on attribute access."""

    def __init__(self, error_code: DataAccessResult, message: str | None = None) -> None:
        self.error_code = error_code
        super().__init__(
            message or f"DLMS data access error: {error_code.name} ({error_code.value})"
        )


class ProtocolError(MicrodlmsError):
    """Raised when a framing, sequence, or APDU invariant violation occurs."""
