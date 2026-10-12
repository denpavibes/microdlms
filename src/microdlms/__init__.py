"""microdlms: Zero-core-dependency DLMS/COSEM meter client for Python 3.14+."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from microdlms.apdu import ApduTags
from microdlms.axdr import AxdrTags, decode_axdr
from microdlms.client import AsyncMeterClient
from microdlms.const import DEFAULT_CLIENT_LOGICAL_ADDRESS, DEFAULT_SERVER_LOGICAL_ADDRESS
from microdlms.exceptions import (
    AuthenticationError,
    CommunicationError,
    DataAccessError,
    MicrodlmsError,
    ProtocolError,
)
from microdlms.hdlc import HdlcControls, HdlcSupervisoryTypes
from microdlms.obis import CosemAttribute, ObisCode
from microdlms.session import DlmsSession, SessionState
from microdlms.types import (
    AssociatedEvent,
    AssociationDiagnostic,
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
    SessionEvent,
)

try:
    __version__ = version("microdlms")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = [
    "__version__",
    "AsyncMeterClient",
    "DlmsSession",
    "SessionState",
    "ObisCode",
    "CosemAttribute",
    "InterfaceClass",
    "ScalerUnit",
    "CosemDateTime",
    "AssociationResult",
    "AssociationDiagnostic",
    "DataAccessResult",
    "ConnectedEvent",
    "AssociatedEvent",
    "AssociationRejectedEvent",
    "GetResponseEvent",
    "GetAccessErrorEvent",
    "ReleasedEvent",
    "DisconnectedEvent",
    "ProtocolErrorEvent",
    "SessionEvent",
    "MicrodlmsError",
    "CommunicationError",
    "AuthenticationError",
    "DataAccessError",
    "ProtocolError",
    "decode_axdr",
    "AxdrTags",
    "ApduTags",
    "HdlcControls",
    "HdlcSupervisoryTypes",
    "DEFAULT_CLIENT_LOGICAL_ADDRESS",
    "DEFAULT_SERVER_LOGICAL_ADDRESS",
]
