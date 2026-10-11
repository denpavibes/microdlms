"""HDLC (High-Level Data Link Control) framing, addressing, LLC sublayer, and CRC-16."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from microdlms.exceptions import ProtocolError

HDLC_FLAG: Final = 0x7E
LLC_REQ_HEADER: Final = b"\xe6\xe6\x00"
LLC_RESP_HEADER: Final = b"\xe6\xe7\x00"

# Precomputed CRC-16-CCITT / X.25 lookup table (polynomial 0x8408 reversed)
# fmt: off
_CRC16_TABLE: Final[list[int]] = [
    0x0000, 0x1189, 0x2312, 0x329B, 0x4624, 0x57AD, 0x6536, 0x74BF,
    0x8C48, 0x9DC1, 0xAF5A, 0xBED3, 0xCA6C, 0xDBE5, 0xE97E, 0xF8F7,
    0x1081, 0x0108, 0x3393, 0x221A, 0x56A5, 0x472C, 0x75B7, 0x643E,
    0x9CC9, 0x8D40, 0xBFDB, 0xAE52, 0xDAED, 0xCB64, 0xF9FF, 0xE876,
    0x2102, 0x308B, 0x0210, 0x1399, 0x6726, 0x76AF, 0x4434, 0x55BD,
    0xAD4A, 0xBCC3, 0x8E58, 0x9FD1, 0xEB6E, 0xFAE7, 0xC87C, 0xD9F5,
    0x3183, 0x200A, 0x1291, 0x0318, 0x77A7, 0x662E, 0x54B5, 0x453C,
    0xBDCB, 0xAC42, 0x9ED9, 0x8F50, 0xFBEF, 0xEA66, 0xD8FD, 0xC974,
    0x4204, 0x538D, 0x6116, 0x709F, 0x0420, 0x15A9, 0x2732, 0x36BB,
    0xCE4C, 0xDFC5, 0xED5E, 0xFCD7, 0x8868, 0x99E1, 0xAB7A, 0xBAF3,
    0x5285, 0x430C, 0x7197, 0x601E, 0x14A1, 0x0528, 0x37B3, 0x263A,
    0xDECD, 0xCF44, 0xFDDF, 0xEC56, 0x98E9, 0x8960, 0xBBFB, 0xAA72,
    0x6306, 0x728F, 0x4014, 0x519D, 0x2522, 0x34AB, 0x0630, 0x17B9,
    0xEF4E, 0xFEC7, 0xCC5C, 0xDDD5, 0xA96A, 0xB8E3, 0x8A78, 0x9BF1,
    0x7387, 0x620E, 0x5095, 0x411C, 0x35A3, 0x242A, 0x16B1, 0x0738,
    0xFFCF, 0xEE46, 0xDCDD, 0xCD54, 0xB9EB, 0xA862, 0x9AF9, 0x8B70,
    0x8408, 0x9581, 0xA71A, 0xB693, 0xC22C, 0xD3A5, 0xE13E, 0xF0B7,
    0x0840, 0x19C9, 0x2B52, 0x3ADB, 0x4E64, 0x5FED, 0x6D76, 0x7CFF,
    0x9489, 0x8500, 0xB79B, 0xA612, 0xD2AD, 0xC324, 0xF1BF, 0xE036,
    0x18C1, 0x0948, 0x3BD3, 0x2A5A, 0x5EE5, 0x4F6C, 0x7DF7, 0x6C7E,
    0xA50A, 0xB483, 0x8618, 0x9791, 0xE32E, 0xF2A7, 0xC03C, 0xD1B5,
    0x2942, 0x38CB, 0x0A50, 0x1BD9, 0x6F66, 0x7EEF, 0x4C74, 0x5DFD,
    0xB58B, 0xA402, 0x9699, 0x8710, 0xF3AF, 0xE226, 0xD0BD, 0xC134,
    0x39C3, 0x284A, 0x1AD1, 0x0B58, 0x7FE7, 0x6E6E, 0x5CF5, 0x4D7C,
    0xC60C, 0xD785, 0xE51E, 0xF497, 0x8028, 0x91A1, 0xA33A, 0xB2B3,
    0x4A44, 0x5BCD, 0x6956, 0x78DF, 0x0C60, 0x1DE9, 0x2F72, 0x3EFB,
    0xD68D, 0xC704, 0xF59F, 0xE416, 0x90A9, 0x8120, 0xB3BB, 0xA232,
    0x5AC5, 0x4B4C, 0x79D7, 0x685E, 0x1CE1, 0x0D68, 0x3FF3, 0x2E7A,
    0xE70E, 0xF687, 0xC41C, 0xD595, 0xA12A, 0xB0A3, 0x8238, 0x93B1,
    0x6B46, 0x7ACF, 0x4854, 0x59DD, 0x2D62, 0x3CEB, 0x0E70, 0x1FF9,
    0xF78F, 0xE606, 0xD49D, 0xC514, 0xB1AB, 0xA022, 0x92B9, 0x8330,
    0x7BC7, 0x6A4E, 0x58D5, 0x495C, 0x3DE3, 0x2C6A, 0x1EF1, 0x0F78,
]
# fmt: on


def calculate_crc16(data: bytes | bytearray) -> int:
    """Calculate 16-bit CRC-CCITT (X.25) checksum over data."""
    crc = 0xFFFF
    for byte_value in data:
        crc = (crc >> 8) ^ _CRC16_TABLE[(crc ^ byte_value) & 0xFF]
    return (~crc) & 0xFFFF


def check_crc16(data_with_crc: bytes | bytearray) -> bool:
    """Verify that CRC computed over data including its little-endian CRC equals residue 0xF0B8."""
    crc = 0xFFFF
    for byte_value in data_with_crc:
        crc = (crc >> 8) ^ _CRC16_TABLE[(crc ^ byte_value) & 0xFF]
    return crc == 0xF0B8


def _encode_address_component(value: int, is_last: bool = False) -> bytes:
    """Encode an integer address component using 7 bits per byte with extension bits."""
    if value < 0x80:
        byte_value = (value << 1) & 0xFE
        if is_last:
            byte_value |= 1
        return bytes([byte_value])

    chunks: list[int] = []
    remaining_value = value
    while remaining_value > 0:
        chunks.append(remaining_value & 0x7F)
        remaining_value >>= 7
    chunks.reverse()

    output_bytes = bytearray()
    for index, chunk in enumerate(chunks):
        byte_value = (chunk << 1) & 0xFE
        if is_last and (index == len(chunks) - 1):
            byte_value |= 1
        output_bytes.append(byte_value)
    return bytes(output_bytes)


def encode_address(logical: int, physical: int | None = None) -> bytes:
    """Encode HDLC logical and physical addresses into bytes."""
    if physical is None:
        return _encode_address_component(logical, is_last=True)
    return _encode_address_component(logical, is_last=False) + _encode_address_component(
        physical, is_last=True
    )


def decode_address(data: bytes, offset: int = 0) -> tuple[bytes, int]:
    """Decode variable-length HDLC address bytes starting at offset."""
    start_offset = offset
    while offset < len(data):
        byte_value = data[offset]
        offset += 1
        if byte_value & 1:
            return data[start_offset:offset], offset
    raise ProtocolError(f"Incomplete HDLC address at offset {start_offset}")


def make_i_control(send_seq: int, recv_seq: int, poll: bool = True) -> int:
    """Pack HDLC Information frame control byte with N(S), N(R), and Poll bit."""
    poll_bit = 1 if poll else 0
    return ((recv_seq & 0x07) << 5) | (poll_bit << 4) | ((send_seq & 0x07) << 1)


@dataclass(frozen=True, slots=True)
class HdlcFrame:
    """Parsed HDLC frame structure."""

    format_type: int
    segmented: bool
    length: int
    dest_address: bytes
    src_address: bytes
    control: int
    hcs: bytes | None
    information: bytes | None
    fcs: bytes

    @property
    def is_iframe(self) -> bool:
        """True if control byte indicates an Information frame."""
        return (self.control & 1) == 0

    @property
    def send_seq(self) -> int | None:
        """N(S) send sequence number for I-frames."""
        return (self.control >> 1) & 0x07 if self.is_iframe else None

    @property
    def recv_seq(self) -> int | None:
        """N(R) receive sequence number for I-frames or S-frames."""
        if self.is_iframe or ((self.control & 0x03) == 0x01):
            return (self.control >> 5) & 0x07
        return None

    @property
    def poll_final(self) -> bool:
        """Value of Poll/Final bit."""
        return bool((self.control >> 4) & 1)


def build_frame(
    dest_address: bytes,
    src_address: bytes,
    control: int,
    information: bytes | None = None,
) -> bytes:
    """Build a complete HDLC frame including format, addresses, HCS (if I-frame), and FCS."""
    is_information_frame = (control & 1) == 0
    info_length = len(information) if information is not None else 0

    if is_information_frame:
        # Header length without format word = len(dest) + len(src) + 1 + 2 (hcs)
        # Total frame length between flags = header + info_length + 2 (fcs)
        frame_length = 2 + len(dest_address) + len(src_address) + 1 + 2 + info_length + 2
        if frame_length > 0x07FF:
            raise ProtocolError(
                f"Frame length {frame_length} exceeds maximum HDLC frame length 2047"
            )
        format_word = 0xA000 | (frame_length & 0x07FF)
        format_bytes = format_word.to_bytes(2, "big")
        header_data = format_bytes + dest_address + src_address + bytes([control])
        header_check_sequence = calculate_crc16(header_data).to_bytes(2, "little")
        frame_body = (
            header_data + header_check_sequence + (information if information is not None else b"")
        )
    else:
        frame_length = 2 + len(dest_address) + len(src_address) + 1 + info_length + 2
        if frame_length > 0x07FF:
            raise ProtocolError(
                f"Frame length {frame_length} exceeds maximum HDLC frame length 2047"
            )
        format_word = 0xA000 | (frame_length & 0x07FF)
        format_bytes = format_word.to_bytes(2, "big")
        frame_body = (
            format_bytes
            + dest_address
            + src_address
            + bytes([control])
            + (information if information is not None else b"")
        )

    frame_check_sequence = calculate_crc16(frame_body).to_bytes(2, "little")
    return bytes([HDLC_FLAG]) + frame_body + frame_check_sequence + bytes([HDLC_FLAG])


def parse_hdlc_frame(frame: bytes) -> HdlcFrame:
    """Parse and validate raw HDLC frame bytes including flag check, FCS, and HCS."""
    if len(frame) < 7:
        raise ProtocolError(f"HDLC frame too short: {len(frame)} bytes")
    if frame[0] != HDLC_FLAG or frame[-1] != HDLC_FLAG:
        raise ProtocolError("HDLC frame missing opening or closing 0x7E flag")

    content = frame[1:-1]
    if not check_crc16(content):
        raise ProtocolError(f"FCS check failed on HDLC frame: {frame.hex()}")

    format_word = int.from_bytes(content[0:2], "big")
    format_type = (format_word >> 12) & 0x0F
    if format_type != 0x0A:
        raise ProtocolError(f"Unsupported HDLC frame format type: {format_type} (expected 10/0xA)")
    segmented = bool((format_word >> 11) & 0x01)
    declared_length = format_word & 0x07FF
    if declared_length != len(content):
        raise ProtocolError(
            f"Declared HDLC frame length {declared_length} "
            f"does not match actual length {len(content)}"
        )

    destination_address, offset = decode_address(content, 2)
    source_address, offset = decode_address(content, offset)
    if offset >= len(content) - 2:
        raise ProtocolError("HDLC frame truncated before control byte")

    control = content[offset]
    offset += 1
    is_information_frame = (control & 1) == 0

    header_check_sequence: bytes | None = None
    if is_information_frame:
        header_with_hcs = content[: offset + 2]
        if not check_crc16(header_with_hcs):
            raise ProtocolError(f"HCS check failed on HDLC I-frame header: {header_with_hcs.hex()}")
        header_check_sequence = content[offset : offset + 2]
        offset += 2
        information_bytes = content[offset:-2]
    else:
        information_bytes = content[offset:-2]

    frame_check_sequence = content[-2:]
    return HdlcFrame(
        format_type=format_type,
        segmented=segmented,
        length=declared_length,
        dest_address=destination_address,
        src_address=source_address,
        control=control,
        hcs=header_check_sequence,
        information=information_bytes if information_bytes else None,
        fcs=frame_check_sequence,
    )


def _align_buffer_to_flag(buffer: bytearray) -> bool:
    """Align buffer to opening HDLC flag and discard fill flags. Returns False if no flag found."""
    try:
        start_index = buffer.index(HDLC_FLAG)
    except ValueError:
        buffer.clear()
        return False

    if start_index > 0:
        del buffer[:start_index]

    while len(buffer) > 1 and buffer[1] == HDLC_FLAG:
        del buffer[0]

    return True


def _consume_frame(buffer: bytearray, total_length: int) -> bytes:
    """Extract frame bytes and slice buffer, handling shared boundary flags."""
    frame = bytes(buffer[:total_length])
    if len(buffer) > total_length and (buffer[total_length] & 0xF0) == 0xA0:
        del buffer[: total_length - 1]
    else:
        del buffer[:total_length]
    return frame


def _extract_next_frame(buffer: bytearray) -> bytes | None:
    """Extract next complete HDLC frame from buffer, or None if incomplete/invalid."""
    if (buffer[1] & 0xF0) != 0xA0:
        del buffer[:1]
        return None

    declared_length = int.from_bytes(buffer[1:3], "big") & 0x07FF
    total_length = declared_length + 2

    if len(buffer) < total_length:
        return None

    if buffer[declared_length + 1] != HDLC_FLAG:
        del buffer[:1]
        return None

    return _consume_frame(buffer, total_length)


def slice_hdlc_frames(buffer: bytearray) -> list[bytes]:
    """Scan and extract complete DLMS HDLC frames from buffer, discarding consumed bytes."""
    frames: list[bytes] = []
    while _align_buffer_to_flag(buffer):
        if len(buffer) < 3:
            break
        previous_length = len(buffer)
        frame = _extract_next_frame(buffer)
        if frame is not None:
            frames.append(frame)
        elif len(buffer) == previous_length:
            break

    return frames


def wrap_llc(apdu: bytes) -> bytes:
    """Prepend LLC request header (0xE6, 0xE6, 0x00) to an APDU."""
    return LLC_REQ_HEADER + apdu


def unwrap_llc(info: bytes) -> bytes:
    """Validate and strip LLC header from incoming HDLC information field."""
    if len(info) < 3:
        raise ProtocolError(f"HDLC information field too short for LLC header: {len(info)} bytes")
    llc_header = info[:3]
    if llc_header not in (LLC_RESP_HEADER, LLC_REQ_HEADER):
        raise ProtocolError(f"Unknown or invalid LLC header: {llc_header.hex()}")
    return info[3:]
