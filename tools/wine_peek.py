"""Read memory of the running ca_fixed_patched via /proc/PID/mem, and decode the game's obfuscated "value boxes".

NOTE: under new-wow64 Wine (this setup) the 32-bit game memory is NOT readable this way: the process found by
find_pid() returns EIO for game VAs (e.g. 0xE60838). Use tools/wine_gdb.sh (winedbg --gdb) for live reads; the
decoders here (vbox/u8/u32) remain valid for bytes read through gdb.

A value box (set sub_413F32 / get sub_414625, 0x413F32/0x414625): the box OBJECT is 12 bytes; obj+8 points to a
buffer on the heap. u8 (getter sub_414625): val = buf[0] ^ (buf[1] or 42). u32 (getter sub_414543): key k = buf[4];
for i in 0..3: k = k or 42; out[i] = buf[i] ^ k; k = (k + buf[i] + 42) & 0xFF. (u16 getter not checked yet.)

usage:
  python3 tools/wine_peek.py <hexVA> [n]            raw hex dump of n bytes (default 16) at 32-bit VA
  python3 tools/wine_peek.py vbox <hexVA> [u8|u16|u32]   decode a value box object at VA
  python3 tools/wine_peek.py chan [count]           decode CChannelInfo channels (name/type/kind/max/cur)
"""
import struct, sys, glob, os


def find_pid():
    for d in glob.glob("/proc/[0-9]*"):
        try:
            cl = open(d + "/cmdline", "rb").read()
        except OSError:
            continue
        if b"ca_fixed_patched" in cl and b"winedbg" not in cl and b"wine_peek" not in cl:
            return int(d.split("/")[2])
    raise SystemExit("ca_fixed_patched not running")


class Mem:
    def __init__(self, pid):
        self.f = os.open(f"/proc/{pid}/mem", os.O_RDONLY)

    def read(self, va, n):
        return os.pread(self.f, n, va)

    def u8(self, va):
        return self.read(va, 1)[0]

    def u32(self, va):
        return struct.unpack("<I", self.read(va, 4))[0]


def decode_box(b, kind="u8"):
    """Decode a value-box buffer `b` (bytes at *(obj+8))."""
    if kind == "u8":
        return b[0] ^ (b[1] or 42)
    if kind == "u32":
        k, out = b[4], []
        for i in range(4):
            k = k or 42
            out.append(b[i] ^ k)
            k = (k + b[i] + 42) & 0xFF
        return int.from_bytes(bytes(out), "little")
    raise ValueError(f"{kind}: getter not verified")


def vbox(mem, obj, kind="u8"):
    """Decode a value box object at `obj` (obj+8 -> buffer)."""
    return decode_box(mem.read(mem.u32(obj + 8), 8), kind)


def main():
    a = sys.argv[1:]
    mem = Mem(find_pid())
    if a and a[0] == "vbox":
        va = int(a[1], 16)
        kind = a[2] if len(a) > 2 else "u8"
        print(f"vbox @ {va:#x} ({kind}) = {vbox(mem, va, kind)}")
    elif a and a[0] == "chan":
        info = mem.u32(0xE60FD8)  # CChannelInfo
        cnt = vbox(mem, info + 0xC, "u8")
        print(f"CChannelInfo @ {info:#x}, count(+0xC) = {cnt}")
        n = int(a[1]) if len(a) > 1 else min(cnt if cnt < 64 else 8, 8)
        for i in range(n):
            g = info + 0xE8 * i  # getter base: sub_994xxx read info + 232*i + G (stored record = g + 0x18)
            mx = vbox(mem, g + 0x34, "u32")    # sub_994D38 max users
            typ = vbox(mem, g + 0x40)          # sub_994D51 type
            kind = vbox(mem, g + 0x4C)         # sub_994A5A kind (18 -> 10)
            cat = vbox(mem, g + 0xE8)          # sub_994A9F category
            cur = vbox(mem, info + 0x3A018 + 0xC * i, "u32")  # sub_994D7E current users (opcode 16)
            print(f"  ch[{i}] max={mx} type={typ} kind={kind} category={cat} cur={cur}")
    else:
        va = int(a[0], 16)
        n = int(a[1]) if len(a) > 1 else 16
        data = mem.read(va, n)
        print(f"{va:#x}: {data.hex(' ')}")


if __name__ == "__main__":
    main()
