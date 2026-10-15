"""Boom Online .idx/.idd pack reader (PackFS__AttachIdf 0xA388C0, PackFS__DecryptIdx 0xA355B0)."""
import struct, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from pathlib import Path

KEYS = {"fx": 1906092848, "charte": 95551996, "emote": 95551996, "fxasset": 95551996}

def decrypt_idx(data, key):
    n, tail = divmod(len(data), 4)
    c = struct.unpack_from("<%dI" % n, data)
    p, prev = [], key
    for i, x in enumerate(c):
        prev = (x ^ key) if i == 0 else (prev ^ x)
        p.append(prev)
    last = p[-1] if n else key
    out = bytearray(struct.pack("<%dI" % n, *p))
    for j in range(tail):
        out.append(data[4 * n + j] ^ ((last >> (8 * j)) & 0xFF))
    return bytes(out)

def parse_idx(buf):
    off = 0
    first = struct.unpack_from("<I", buf, 0)[0]
    if first == 0:
        ver, count = struct.unpack_from("<II", buf, 4)
        off, extra = 12, True
    else:
        ver, count, off, extra = None, first, 4, False
    ents = []
    for _ in range(count):
        nl = struct.unpack_from("<i", buf, off)[0]; off += 4
        name = buf[off:off + nl].decode("cp949", "replace"); off += nl
        a, b, c = struct.unpack_from("<III", buf, off); off += 12
        d = 0
        if extra:
            d = struct.unpack_from("<I", buf, off)[0]; off += 4
        ents.append((name, a, b, c, d))
    return ver, ents, off

def _main():
    root = Path(sys.argv[1])
    for stem, key in KEYS.items():
        p = root / (stem + ".idx")
        if not p.exists():
            continue
        buf = decrypt_idx(p.read_bytes(), key)
        ver, ents, end = parse_idx(buf)
        print(f"{stem}: ver={ver} entries={len(ents)} parsed={end}/{len(buf)} idd={(root / (stem + '.idd')).stat().st_size}")
        for e in ents[:6]:
            print("   ", e)


def decrypt_entry(data, key):
    """PackFS__DecryptEntry 0xA35640"""
    n, tail = divmod(len(data), 4)
    c = struct.unpack_from("<%dI" % n, data)
    p = []
    for i, x in enumerate(c):
        if i == 0:
            v = x ^ key ^ 0x9C6C95CE
        else:
            v = p[-1] ^ x ^ ((i * i * (i + 966) * (i + 2020)) & 0xFFFFFFFF) ^ 0x9C6C95CE
        p.append(v)
    last = p[-1] if n else key
    out = bytearray(struct.pack("<%dI" % n, *p))
    for j in range(tail):
        out.append(data[4 * n + j] ^ ((last >> (8 * j)) & 0xFF))
    return bytes(out)


def _crc32(init, data):
    import boomproto
    return boomproto.crc32(init, data)


def unpack_entry(name, blob, c, d):
    """CData__LoadFromPack 0xA37880: decrypt (c=key, d=crc32) or zlib for names containing '_mm'."""
    if c:
        blob = decrypt_entry(blob, c)
        if d not in (0, 1) and _crc32(c, blob) != d:
            raise ValueError("crc mismatch: " + name)
    elif "_mm" in name:
        import zlib
        clen, rlen = struct.unpack_from("<II", blob)
        blob = zlib.decompress(blob[8:8 + clen])
    return blob


def iter_pack(root, stem):
    root = Path(root)
    ver, ents, _ = parse_idx(decrypt_idx((root / (stem + ".idx")).read_bytes(), KEYS[stem]))
    with open(root / (stem + ".idd"), "rb") as f:
        for name, off, size, c, d in ents:
            f.seek(off)
            yield name, unpack_entry(name, f.read(size), c, d), (c, d)


def _kind(blob):
    if blob[:4] in (b"\xe8\x03\x00\x00", b"\xe9\x03\x00\x00"):
        return "map"  # CGamePlayMap version 1000/1001
    if len(blob) >= 8 and blob[4:8] == b"\x02\x00\x00\x00":
        return "i16"
    if blob[:3] == b"ID3" or blob[:2] in (b"\xff\xfb", b"\xff\xf3"):
        return "mp3"
    if blob[:4] == b"OggS":
        return "ogg"
    if blob[:4] == b"RIFF":
        return "wav"
    return "bin"


def extract(root, out, stems=None, png=True):
    import i16
    out = Path(out)
    for stem in stems or KEYS:
        if not (Path(root) / (stem + ".idx")).exists():
            continue
        stats = {}
        for name, blob, _ in iter_pack(root, stem):
            base = out / stem / name.replace("\\", "/")
            base.parent.mkdir(parents=True, exist_ok=True)
            kind = _kind(blob)
            if kind == "i16" and png:
                try:
                    imgs = i16.to_pngs(blob)
                except Exception:
                    kind = "i16-bad"
                else:
                    base.mkdir(parents=True, exist_ok=True)
                    for i, data in imgs:
                        (base / ("%03d.png" % i)).write_bytes(data)
            if kind != "i16" or not png:
                base.with_name(base.name + "." + kind).write_bytes(blob)
            stats[kind] = stats.get(kind, 0) + 1
        print(f"{stem}: {stats} -> {out / stem}", flush=True)


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "extract":
        extract(sys.argv[2], sys.argv[3], sys.argv[4:] or None)
    else:
        _main()
