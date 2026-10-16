"""Read memory of the running ca_fixed_patched (Wine, new-wow64) via /proc/PID/mem, and decode the game's
obfuscated "value boxes". Far more reliable than winedbg scripting for inspecting live state.

A value box (set sub_413F32 / get sub_414625, 0x413F32/0x414625): the box OBJECT is 12 bytes; obj+8 points to a
6-byte buffer on the heap. For a u8 field: val = buf[0] ^ (buf[1] or 42). For wider fields the get rolls a key
across buf[0..] starting from buf[4]; implemented below (u8/u16/u32).

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


def vbox(mem, obj, kind="u8"):
    """Decode a value box object at `obj` (obj+8 -> buffer)."""
    buf = mem.u32(obj + 8)
    b = mem.read(buf, 8)
    # replicate the getter's rolling decode
    out = []
    key = b[1]
    n = {"u8": 1, "u16": 2, "u32": 4}[kind]
    k = key if key else 42
    for i in range(n):
        out.append(b[i] ^ k)
        k = (k + b[i] + 42) & 0xFF
        if k == 0:
            k = 42
    return int.from_bytes(bytes(out), "little")


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
            rec = info + 0x18 + 0xE8 * i
            typ = vbox(mem, rec + 0x40, "u8")
            kind = vbox(mem, rec + 0x4C, "u8")
            mx = vbox(mem, rec + 0x34, "u8")
            # current users live in a separate 12-byte array at info + 0x3A018 + 12*i
            cur = vbox(mem, info + 0x3A018 + 0xC * i, "u32")
            print(f"  ch[{i}] type(+0x40)={typ} kind(+0x4C)={kind} max(+0x34)={mx} cur={cur}")
    else:
        va = int(a[0], 16)
        n = int(a[1]) if len(a) > 1 else 16
        data = mem.read(va, n)
        print(f"{va:#x}: {data.hex(' ')}")


if __name__ == "__main__":
    main()
