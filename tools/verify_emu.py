"""Emulate crypto functions from unpacked_ca.exe and compare with boomproto.py."""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX
import boomproto as bp

pe = pefile.PE(sys.argv[1])
base = pe.OPTIONAL_HEADER.ImageBase
mu = Uc(UC_ARCH_X86, UC_MODE_32)
size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xFFF) & ~0xFFF
mu.mem_map(base, size)
for s in pe.sections:
    d = s.get_data()
    mu.mem_write(base + s.VirtualAddress, d[: s.Misc_VirtualSize or len(d)])
STACK, BUF, RET = 0x10000000, 0x20000000, 0x30000000
mu.mem_map(STACK, 0x100000); mu.mem_map(BUF, 0x100000); mu.mem_map(RET, 0x1000)

def call(fn, *args):
    sp = STACK + 0x80000
    data = struct.pack("<I", RET) + b"".join(struct.pack("<I", a & 0xFFFFFFFF) for a in args)
    mu.mem_write(sp, data); mu.reg_write(UC_X86_REG_ESP, sp)
    mu.emu_start(fn, RET, count=5_000_000)
    return mu.reg_read(UC_X86_REG_EAX)

# force CRC tables to be (re)built by the binary itself
mu.mem_write(0xEEEBB8, b"\x00\x00")
fails = 0
for ln in list(range(0, 20)) + [64, 101]:
    for key in (0, 40, 43, 0xDEADBEEF):
        pt = os.urandom(ln)
        mu.mem_write(BUF, pt)
        call(0xA64240, BUF, BUF + 0x1000, ln, key)
        ct = bytes(mu.mem_read(BUF + 0x1000, ln))
        call(0xA642E0, BUF + 0x1000, BUF + 0x2000, ln, key)
        back = bytes(mu.mem_read(BUF + 0x2000, ln))
        c32 = call(0xA26330, key, BUF, ln)
        c8 = call(0xA264C0, key & 0xFF, BUF, ln) & 0xFF
        ok = (ct == bp.encrypt(pt, key) and back == pt and c32 == bp.crc32(key, pt) and c8 == bp.crc8(key, pt))
        if not ok:
            fails += 1
            print("MISMATCH", ln, hex(key), ct == bp.encrypt(pt, key), back == pt, c32 == bp.crc32(key, pt), c8 == bp.crc8(key, pt))
print("fails:", fails)
