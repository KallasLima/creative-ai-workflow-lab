from __future__ import annotations

import struct
import zlib


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def generate_placeholder_png(width: int = 1024, height: int = 1024) -> bytes:
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            band = ((x // 64) + (y // 64)) % 2
            r = 42 + (x * 70 // width)
            g = 130 + (y * 80 // height)
            b = 210 if band else 170
            if 420 < x < 604 and 420 < y < 604:
                r, g, b = 255, 240, 120
            rows.extend((r, g, b))

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return signature + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", zlib.compress(bytes(rows), 6)) + _chunk(b"IEND", b"")
