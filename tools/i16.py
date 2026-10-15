"""Decoder for CDataI16Alpha sprites (CDataI16Alpha__Load 0xA3D850).

Blob layout:
  u32 nFrames, u32 version(=2), u32 nImages, u32 unk
  nImages * (u32 h, u32 w)       image size (height first, verified visually)
  nFrames * 48 bytes             frame records (not decoded yet)
  nImages * (u32 len, len bytes) RLE image data, len==0 -> empty image
RLE (CWriteRLE ctor 0xA2AC00, color iter 0xA29F90, alpha iter 0xA2C970):
  first byte & 0xC1 == 0xC0 -> 24-bit BGR pixels, no alpha stream, data at +1
  first byte & 0xC1 == 0xC1 -> 24-bit BGR, alpha stream at start + u32(LE @+1), color data at +5
  otherwise                 -> 16-bit RGB565 pixels, no alpha stream
  ctrl byte: run = ctrl & 0x3F; bit7 -> transparent run; bit6 -> one pixel repeated; else literal pixels
  alpha ctrl: same, value byte per literal / one byte per repeat; bit7 or run==0 -> 0
"""
import struct, zlib

KEY565 = 0xF81F

def _rgb565(v):
    return ((v >> 11) & 0x1F) * 255 // 31, ((v >> 5) & 0x3F) * 255 // 63, (v & 0x1F) * 255 // 31

class _Alpha:
    def __init__(self, data, pos):
        self.d, self.p, self.ctrl, self.n, self.v = data, pos, 0, 0, 0
    def next(self):
        if self.n:
            if self.ctrl & 0xC0 == 0:
                self.v = self.d[self.p]; self.p += 1
            self.n -= 1
            return self.v
        c = self.d[self.p]; self.p += 1
        self.ctrl, self.n = c, c & 0x3F
        if self.n == 0:
            self.v = 0
            return 0
        if c & 0x80:
            self.v = 0
        else:
            self.v = self.d[self.p]; self.p += 1
        self.n -= 1
        return self.v

def decode_image(data, w, h):
    """-> (rgba bytes, color bytes consumed, end-of-color-stream offset)"""
    first = data[0]
    alpha = None
    if first & 0xC1 == 0xC0:
        p, bpp, end = 1, 3, len(data)
    elif first & 0xC1 == 0xC1:
        aoff = struct.unpack_from("<I", data, 1)[0]
        p, bpp, end = 5, 3, aoff
        alpha = _Alpha(data, aoff)
    else:
        p, bpp, end = 0, 2, len(data)
    out = bytearray(w * h * 4)
    n, ctrl, col = 0, 0, None
    for i in range(w * h):
        if n == 0:
            ctrl = data[p]; p += 1
            n = ctrl & 0x3F
            if ctrl & 0x80:
                col = None
            else:
                col = data[p:p + bpp]; p += bpp
        elif ctrl & 0xC0 == 0:
            col = data[p:p + bpp]; p += bpp
        n -= 1
        a = alpha.next() if alpha else 0
        if col is None:
            continue
        if bpp == 3:
            r, g, b = col[2], col[1], col[0]
        else:
            v = col[0] | col[1] << 8
            if v == KEY565:
                continue
            r, g, b = _rgb565(v)
        out[4 * i:4 * i + 4] = bytes((r, g, b, 255 - a if alpha else 255))
    return bytes(out), p, end

def parse(blob):
    nfr, ver, nimg, unk = struct.unpack_from("<4I", blob)
    if ver != 2:
        raise ValueError("not I16 v2")
    sizes = [struct.unpack_from("<II", blob, 16 + 8 * i) for i in range(nimg)]
    off = 16 + 8 * nimg
    frames = [blob[off + 48 * i: off + 48 * (i + 1)] for i in range(nfr)]
    off += 48 * nfr
    imgs = []
    for i in range(nimg):
        ln = struct.unpack_from("<I", blob, off)[0]; off += 4
        imgs.append(blob[off:off + ln]); off += ln
    return dict(nframes=nfr, unk=unk, sizes=sizes, frames=frames, images=imgs, end=off)

def png(rgba, w, h):
    raw = b"".join(b"\x00" + rgba[y * w * 4:(y + 1) * w * 4] for y in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def to_pngs(blob):
    """-> list of (index, png bytes) for every non-empty image in an I16 blob."""
    s = parse(blob)
    res = []
    for i, ((h, w), img) in enumerate(zip(s["sizes"], s["images"])):
        if img and w and h:
            rgba, _, _ = decode_image(img, w, h)
            res.append((i, png(rgba, w, h)))
    return res
