"""Tests for HDLC framing, CRC-16 calculations, address coding, and LLC encapsulation."""

from __future__ import annotations

import pytest

from microdlms.exceptions import ProtocolError
from microdlms.hdlc import (
    HDLC_FLAG,
    LLC_REQ_HEADER,
    LLC_RESP_HEADER,
    build_frame,
    calculate_crc16,
    check_crc16,
    decode_address,
    encode_address,
    make_i_control,
    parse_hdlc_frame,
    slice_hdlc_frames,
    unwrap_llc,
    wrap_llc,
)


def test_crc16_calculation() -> None:
    """Verify standard HDLC / X.25 CRC-16 calculation and residue verification."""
    # Empty bytes: crc of empty with initial 0xFFFF and final XOR is 0x0000
    assert calculate_crc16(b"") == 0x0000

    # Test standard check sequence: data + FCS-16 in little-endian satisfies check_crc16
    data = b"Hello DLMS"
    crc = calculate_crc16(data)
    with_crc = data + crc.to_bytes(2, "little")
    assert check_crc16(with_crc) is True

    # Corrupted byte should fail check
    corrupted = bytearray(with_crc)
    corrupted[0] ^= 0x01
    assert check_crc16(bytes(corrupted)) is False


def test_address_encoding_and_decoding() -> None:
    """Test 1-byte and 2-byte HDLC address serialization and parsing."""
    # 1-byte client address: logical 32 -> (32 << 1) | 1 = 0x41
    client_bytes = encode_address(32)
    assert client_bytes == b"\x41"
    decoded, offset = decode_address(client_bytes)
    assert decoded == b"\x41"
    assert offset == 1

    # 2-byte server address: logical 1, physical 42 -> 0x02, 0x55
    server_bytes = encode_address(1, 42)
    assert server_bytes == b"\x02\x55"
    decoded_srv, offset_srv = decode_address(server_bytes)
    assert decoded_srv == b"\x02\x55"
    assert offset_srv == 2

    # Incomplete address without extension bit 1 raises ProtocolError
    with pytest.raises(ProtocolError, match="Incomplete HDLC address"):
        decode_address(b"\x02\x04\x06")


def test_i_control_packing_and_properties() -> None:
    """Test HDLC Information frame control byte packing and sequence decoding."""
    # ns=0, nr=0, poll=True -> 0x10
    control_0_0 = make_i_control(send_seq=0, recv_seq=0, poll=True)
    assert control_0_0 == 0x10

    # ns=1, nr=1, poll=True -> 0x32
    control_1_1 = make_i_control(send_seq=1, recv_seq=1, poll=True)
    assert control_1_1 == 0x32

    # Sequence wrap modulo 8: ns=7, nr=7, poll=True -> 0xFE
    control_7_7 = make_i_control(send_seq=7, recv_seq=7, poll=True)
    assert control_7_7 == 0xFE

    # Poll=False
    control_no_poll = make_i_control(send_seq=2, recv_seq=3, poll=False)
    assert (control_no_poll >> 4) & 1 == 0


def test_build_and_parse_unnumbered_frame() -> None:
    """Test building and parsing unnumbered control frames (SNRM and DISC)."""
    destination_address = encode_address(1, 42)
    source_address = encode_address(32)

    # SNRM frame
    snrm_frame = build_frame(
        dest_address=destination_address, src_address=source_address, control=0x93
    )
    assert snrm_frame.startswith(b"\x7e")
    assert snrm_frame.endswith(b"\x7e")

    parsed = parse_hdlc_frame(snrm_frame)
    assert parsed.dest_address == destination_address
    assert parsed.src_address == source_address
    assert parsed.control == 0x93
    assert parsed.is_iframe is False
    assert parsed.hcs is None
    assert parsed.send_seq is None
    assert parsed.poll_final is True

    # DISC frame
    disc_frame = build_frame(
        dest_address=destination_address, src_address=source_address, control=0x53
    )
    parsed_disc = parse_hdlc_frame(disc_frame)
    assert parsed_disc.control == 0x53
    assert parsed_disc.is_iframe is False


def test_build_and_parse_iframe() -> None:
    """Test building and parsing I-frames with HCS and LLC information payload."""
    destination_address = encode_address(1, 42)
    source_address = encode_address(32)
    info_payload = wrap_llc(b"\x01\x02\x03\x04")

    control_byte = make_i_control(send_seq=2, recv_seq=3, poll=True)
    frame_bytes = build_frame(
        dest_address=destination_address,
        src_address=source_address,
        control=control_byte,
        information=info_payload,
    )

    parsed = parse_hdlc_frame(frame_bytes)
    assert parsed.is_iframe is True
    assert parsed.send_seq == 2
    assert parsed.recv_seq == 3
    assert parsed.hcs is not None
    assert parsed.information == info_payload


def test_parse_frame_errors() -> None:
    """Verify error detection for corrupted or malformed HDLC frames."""
    # Frame too short
    with pytest.raises(ProtocolError, match="too short"):
        parse_hdlc_frame(b"\x7e\xa0\x01\x7e")

    # Missing flags
    with pytest.raises(ProtocolError, match="missing opening or closing"):
        parse_hdlc_frame(b"\x00\xa0\x08\x02\x55\x41\x93\xe9\x57\x7e")

    # Corrupted FCS
    valid_frame = build_frame(encode_address(1, 42), encode_address(32), 0x93)
    corrupted_frame_check_sequence = bytearray(valid_frame)
    corrupted_frame_check_sequence[-2] ^= 0xFF
    with pytest.raises(ProtocolError, match="FCS check failed"):
        parse_hdlc_frame(bytes(corrupted_frame_check_sequence))

    # Length mismatch in format field
    corrupted_length_frame = bytearray(valid_frame)
    corrupted_length_frame[2] = 0x50  # corrupt declared length
    # Recalculate FCS so length check triggers
    content = corrupted_length_frame[1:-3]
    frame_check_sequence = calculate_crc16(content)
    corrupted_length_frame[-3:-1] = frame_check_sequence.to_bytes(2, "little")
    with pytest.raises(ProtocolError):
        parse_hdlc_frame(bytes(corrupted_length_frame))

    # Corrupted HCS in I-frame
    destination_address = encode_address(1, 42)
    source_address = encode_address(32)
    iframe = bytearray(
        build_frame(destination_address, source_address, make_i_control(0, 0), b"test_info")
    )
    # In this iframe: flags(1) + fmt(2) + dest(2) + src(1) + ctrl(1) = 7 -> HCS at index 7, 8
    iframe[7] ^= 0xFF
    # Recompute FCS so HCS check specifically triggers
    content = iframe[1:-3]
    frame_check_sequence = calculate_crc16(content)
    iframe[-3:-1] = frame_check_sequence.to_bytes(2, "little")
    with pytest.raises(ProtocolError, match="HCS check failed"):
        parse_hdlc_frame(bytes(iframe))


def test_slice_hdlc_frames() -> None:
    """Test extracting complete frames from noisy or fragmented serial byte streams."""
    frame_1 = build_frame(encode_address(1, 42), encode_address(32), 0x93)
    frame_2 = build_frame(encode_address(1, 42), encode_address(32), 0x53)

    # 1. Single frame
    buffer = bytearray(frame_1)
    sliced = slice_hdlc_frames(buffer)
    assert len(sliced) == 1
    assert sliced[0] == frame_1
    assert len(buffer) == 0

    # 2. Inter-frame fill flags and noise
    noisy = b"\x00\xff" + bytes([HDLC_FLAG, HDLC_FLAG]) + frame_1 + bytes([HDLC_FLAG]) + frame_2
    buffer = bytearray(noisy)
    sliced = slice_hdlc_frames(buffer)
    assert len(sliced) == 2
    assert sliced[0] == frame_1
    assert sliced[1] == frame_2
    assert len(buffer) == 0

    # 3. Streamed byte-by-byte
    buffer = bytearray()
    sliced_stream = []
    for byte in frame_1:
        buffer.append(byte)
        sliced_stream.extend(slice_hdlc_frames(buffer))
    assert len(sliced_stream) == 1
    assert sliced_stream[0] == frame_1
    assert len(buffer) == 0

    # 4. Incomplete frame preserved in buffer
    incomplete = bytearray(frame_1 + frame_2[:5])
    sliced_inc = slice_hdlc_frames(incomplete)
    assert len(sliced_inc) == 1
    assert sliced_inc[0] == frame_1
    assert bytes(incomplete) == frame_2[:5]

    # 5. Buffer with only noise is cleared
    only_noise = bytearray(b"\x01\x02\x03\x04")
    assert slice_hdlc_frames(only_noise) == []
    assert len(only_noise) == 0

    # 6. Buffer with non-DLMS (non-0xA0) header is skipped
    non_dlms = bytearray(b"\x7e\x12\x34\x7e" + frame_1)
    sliced_non_dlms = slice_hdlc_frames(non_dlms)
    assert len(sliced_non_dlms) == 1
    assert sliced_non_dlms[0] == frame_1

    # 7. Buffer with declared length where closing flag is missing is skipped
    fake_frame = bytearray(b"\x7e\xa0\x08\x01\x02\x03\x04\x05\x06\xaa" + frame_1)
    sliced_missing_flag = slice_hdlc_frames(fake_frame)
    assert len(sliced_missing_flag) == 1
    assert sliced_missing_flag[0] == frame_1


def test_hdlc_frame_property_and_truncation_branches() -> None:
    """Test S-frame recv_seq, U-frame recv_seq is None, and frame truncation before control byte."""
    # U-frame (control 0x73): recv_seq is None
    parsed_ua_frame = parse_hdlc_frame(build_frame(encode_address(32), encode_address(1, 42), 0x73))
    assert parsed_ua_frame.recv_seq is None
    assert parsed_ua_frame.poll_final is True

    # S-frame (control 0x31: RR with N(R)=1, poll=1)
    parsed_receiver_ready = parse_hdlc_frame(
        build_frame(encode_address(32), encode_address(1, 42), 0x31)
    )
    assert parsed_receiver_ready.is_iframe is False
    assert parsed_receiver_ready.recv_seq == 1

    # Frame truncated before control byte (dest + src take up all 4 bytes before FCS)
    body = b"\xa0\x06\x41\x41"  # declared len 6, 4 bytes body
    frame_check_sequence = calculate_crc16(body)
    trunc_frame = b"\x7e" + body + frame_check_sequence.to_bytes(2, "little") + b"\x7e"
    with pytest.raises(ProtocolError, match="truncated before control byte"):
        parse_hdlc_frame(trunc_frame)


def test_llc_encapsulation() -> None:
    """Test wrapping and unwrapping LLC headers."""
    apdu = b"\xc0\x01\x02"
    wrapped = wrap_llc(apdu)
    assert wrapped == LLC_REQ_HEADER + apdu

    # Unwrapping request LLC
    assert unwrap_llc(wrapped) == apdu

    # Unwrapping response LLC
    response_wrapped = LLC_RESP_HEADER + apdu
    assert unwrap_llc(response_wrapped) == apdu

    # Invalid short payload
    with pytest.raises(ProtocolError, match="too short for LLC"):
        unwrap_llc(b"\xe6\xe6")

    # Invalid LLC header
    with pytest.raises(ProtocolError, match="Unknown or invalid LLC header"):
        unwrap_llc(b"\x00\x00\x00" + apdu)


def test_shared_flag_slicing() -> None:
    """Verify that back-to-back frames sharing a single 0x7E delimiter are both extracted."""
    frame_1 = build_frame(encode_address(32), encode_address(1, 42), 0x73)
    frame_2 = build_frame(encode_address(32), encode_address(1, 42), 0x53)
    # Concatenate with a shared flag (frame_1's closing 0x7e serves as frame_2's opening 0x7e)
    shared_flag_frames = frame_1 + frame_2[1:]
    buffer = bytearray(shared_flag_frames)
    frames = slice_hdlc_frames(buffer)
    assert len(frames) == 2
    assert frames[0] == frame_1
    assert frames[1] == frame_2


def test_multibyte_address_encoding_and_frame_overflow() -> None:
    """Test encoding multi-byte addresses (e.g. physical address > 127) and frame length limits."""
    # Physical address 942 (> 127)
    addr_multi = encode_address(1, 942)
    decoded, offset = decode_address(addr_multi, 1)  # skip logical byte
    assert len(decoded) == 2
    assert offset == len(addr_multi)

    # Logical address > 127
    addr_multi_logical = encode_address(200)
    decoded_logical, offset_logical = decode_address(addr_multi_logical)
    assert len(decoded_logical) == 2
    assert offset_logical == 2

    # Frame length overflow in U-frame (> 2047 bytes)
    huge_info = b"\x00" * 2050
    with pytest.raises(ProtocolError, match="exceeds maximum HDLC frame length"):
        build_frame(encode_address(32), encode_address(1, 42), 0x93, information=huge_info)

    # Frame length overflow in I-frame
    with pytest.raises(ProtocolError, match="exceeds maximum HDLC frame length"):
        build_frame(
            encode_address(32),
            encode_address(1, 42),
            make_i_control(0, 0),
            information=huge_info,
        )

    # Corrupt format type in parse_hdlc_frame (not type 3 / 0xA)
    frame_bytes = bytearray(build_frame(encode_address(32), encode_address(1, 42), 0x73))
    frame_bytes[1] = 0x90  # upper nibble 9 instead of A
    content = frame_bytes[1:-3]
    frame_check_sequence = calculate_crc16(content)
    frame_bytes[-3:-1] = frame_check_sequence.to_bytes(2, "little")
    with pytest.raises(ProtocolError, match="Unsupported HDLC frame format type"):
        parse_hdlc_frame(bytes(frame_bytes))
