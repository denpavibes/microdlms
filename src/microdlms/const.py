"""Shared constants and enums for microdlms."""

from __future__ import annotations

from enum import IntEnum
from typing import Final


class ApduTags(IntEnum):
    """DLMS/COSEM Application Protocol Data Unit (APDU) tags."""

    AARQ = 0x60
    AARE = 0x61
    RLRQ = 0x62
    RLRE = 0x63
    GET_REQUEST = 0xC0
    GET_RESPONSE = 0xC4


class HdlcControls(IntEnum):
    """HDLC unnumbered frame control byte values."""

    SNRM = 0x93
    DISC = 0x53
    UA_FINAL = 0x73
    UA = 0x63
    DM_FINAL = 0x1F
    DM = 0x0F


DEFAULT_CLIENT_LOGICAL_ADDRESS: Final = 32
DEFAULT_SERVER_LOGICAL_ADDRESS: Final = 1
