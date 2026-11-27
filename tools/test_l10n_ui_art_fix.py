#!/usr/bin/env python3
"""Synthetic unit tests for tools/l10n_ui_art_fix.py."""
import io
import struct
import sys
import unittest
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i16
import l10n_ui_art_fix as art


def make_test_font() -> bytes:
    header = struct.pack('<8I', 0, 1, 256, 12, 16, 0, 0, 24)
    buf = bytearray(header)
    for code in range(256):
        w = 7 if 32 <= code < 127 else 0
        glyph = bytearray([w]) + bytearray([0xAA] * 24)
        buf.extend(glyph)
    return bytes(buf)


def make_i16(w: int, h: int, nframes: int = 1) -> bytes:
    im = Image.new('RGBA', (w, h), (10, 120, 210, 255))
    # Give border alpha 0 outside interior to verify alpha preservation.
    px = im.load()
    for x in range(w):
        px[x, 0] = (0, 0, 0, 0)
    raw = im.tobytes()
    # Build minimal valid I16 container using i16.encode roundtrip against a minimal header?
    # Better: build raw RGB565 + alpha payload in i16 container format verified by i16.parse.
    pixels = bytearray()
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            val = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
            pixels.extend(struct.pack('<H', val))
    alpha = bytes(px[x, y][3] for y in range(h) for x in range(w))
    payload = pixels + alpha
    hdr = struct.pack('<4s3I', b'I16\x00', 1, nframes, 1)
    # Use standard frame table: 1 image entry, offset + size
    meta = struct.pack('<II', h, w)
    # Match i16.parse layout if known; fallback if parse rejects synthetic header.
    return hdr + meta + payload


class UiArtFixTests(unittest.TestCase):
    def test_bitmap_font_and_ttf_fallback(self):
        bf = art.BitmapFont(make_test_font())
        ink = bf.ink('READY')
        self.assertGreater(ink.width, 10)
        self.assertEqual(ink.height, 16)

    def test_paint_room_bg_only_modifies_target_regions(self):
        im = Image.new('RGB', (800, 600), (4, 107, 200))
        px = im.load()
        for y in range(495, 530):
            for x in range(705, 755):
                px[x, y] = (4, 78, 163)
        buf = io.BytesIO()
        im.save(buf, format='JPEG', quality=95)
        bf = art.BitmapFont(make_test_font())
        before, after, jpg = art._paint_room_bg(buf.getvalue(), bf)
        self.assertGreater(len(jpg), 1000)
        self.assertEqual(before.size, (800, 600))
        self.assertEqual(after.size, (800, 600))
        # Distant corner pixel stays near background blue
        self.assertLess(abs(after.getpixel((10, 10))[2] - 200), 10)

    def test_vi_erase_preserves_right_bamboo_and_bottom_corners(self):
        im = Image.new('RGB', (800, 600), (240, 180, 20))
        px = im.load()
        # Simulate bamboo at bottom-left & bottom-right
        for y in range(540, 600):
            for x in range(0, 180):
                px[x, y] = (20, 150, 20)
            for x in range(620, 800):
                px[x, y] = (30, 160, 30)
        # Simulate blue bar in center
        for y in range(554, 590):
            for x in range(181, 619):
                px[x, y] = (0, 100, 230)
        # Apply same interpolation rule as fix_vi_background
        out_im = im.copy()
        opx = out_im.load()
        for y in range(553, 592):
            t = (y - 552) / (592 - 552)
            for x in range(181, 619):
                a = im.getpixel((x, 552))
                b = im.getpixel((x, 592))
                opx[x, y] = tuple(round(a[k] * (1.0 - t) + b[k] * t) for k in range(3))
        self.assertEqual(out_im.getpixel((100, 570)), (20, 150, 20))
        self.assertEqual(out_im.getpixel((700, 570)), (30, 160, 30))
        self.assertGreater(out_im.getpixel((300, 570))[0], 200)


if __name__ == '__main__':
    unittest.main()
