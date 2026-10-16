"""Replace Themida-virtualized blocks of the dump with hand-written equivalents.

usage: python3 tools/devirt.py ca_fixed.exe ca_devirt.exe
(called by tools/rebuild_wine.sh between fix_iat.py build and patch_client.py)

Each block in BLOCKS: the VM site's `jmp 0x13xxxxx` is redirected to new code in a `.devirt` section;
the new code does what the VM block did and jumps to the continuation. Static results (tables, constants)
are written straight into the image. Evidence for every block: tools/vmtrace.py on the original client,
see docs/devirt.md.
"""
import struct, sys

GETTICKCOUNT_SLOT = 0xC0F1FC  # original IAT, kernel32!GetTickCount (decomp/iat_resolved.json)


def crc32_table_reflected(poly):
    t = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = (c >> 1) ^ poly if c & 1 else c >> 1
        t.append(c)
    return t


def dwords(*vals):
    return b"".join(struct.pack("<I", v) for v in vals)


BLOCKS = [
    dict(
        site=0x8F452B, cont=0x8F45A7, func="sub_8F4421 (CFxApp__InitMain init step)",
        # vmtrace 8F452B: no register effects needed (edi/esi/ebp/ebx preserved; eax/ecx dead), writes:
        #   0xEED860[256] = reflected CRC32 table, poly 0xDD10EC81   (read only by Themida code @0x1330A69)
        #   0xEEE07C = 0x4A65000A, 0xEEE088 = 1, 0xEEE08C = tick count (Themida-internal, no game xrefs)
        #   0xEEE650..65C = callbacks 8F2C5D, 8F30F7, 8F2C4F, 8F31F6 (used by many game funcs, e.g. sub_413F32)
        asm=f"""
            call dword ptr [{GETTICKCOUNT_SLOT:#x}]
            mov dword ptr [0xEEE08C], eax
            jmp {0x8F45A7:#x}
        """,
        data={
            0xEED860: dwords(*crc32_table_reflected(0xDD10EC81)),
            0xEEE07C: dwords(0x4A65000A),
            0xEEE088: dwords(1),
            0xEEE650: dwords(0x8F2C5D, 0x8F30F7, 0x8F2C4F, 0x8F31F6),
        },
    ),
]


def main(src, dst):
    import keystone, pefile
    pe = pefile.PE(src)
    base = pe.OPTIONAL_HEADER.ImageBase
    data = bytearray(open(src, "rb").read())
    ks = keystone.Ks(keystone.KS_ARCH_X86, keystone.KS_MODE_32)

    last = pe.sections[-1]
    sec_rva = (last.VirtualAddress + max(last.Misc_VirtualSize, last.SizeOfRawData) + 0xFFF) & ~0xFFF
    code = bytearray()
    for b in BLOCKS:
        va = base + sec_rva + len(code)
        enc, _ = ks.asm(b["asm"], va)
        code += bytes(enc)
        while len(code) % 16:
            code += b"\xCC"
        o = pe.get_offset_from_rva(b["site"] - base)
        if data[o] != 0xE9:
            sys.exit(f"site {b['site']:#x}: not a jmp ({data[o:o+5].hex()})")
        data[o:o + 5] = b"\xE9" + struct.pack("<i", va - (b["site"] + 5))
        for addr, blob in b.get("data", {}).items():
            off = pe.get_offset_from_rva(addr - base)
            data[off:off + len(blob)] = blob
        print(f"devirt {b['site']:#x} -> {va:#x} ({b['func']})")

    fa = pe.OPTIONAL_HEADER.FileAlignment
    raw_size = (len(code) + fa - 1) // fa * fa
    raw_ptr = (len(data) + fa - 1) // fa * fa
    data += b"\0" * (raw_ptr - len(data)) + bytes(code) + b"\0" * (raw_size - len(code))
    hdr = pe.sections[-1].get_file_offset() + 40
    if hdr + 40 > pe.sections[0].PointerToRawData:
        sys.exit("no room for section header")
    data[hdr:hdr + 40] = struct.pack("<8sIIIIIIHHI", b".devirt\0", len(code), sec_rva, raw_size, raw_ptr, 0, 0, 0, 0, 0x60000020)
    out = pefile.PE(data=bytes(data))
    out.FILE_HEADER.NumberOfSections += 1
    out.OPTIONAL_HEADER.SizeOfImage = (sec_rva + len(code) + 0xFFF) & ~0xFFF
    out.write(dst)
    print(f"wrote {dst}: {len(BLOCKS)} block(s), .devirt @ {base + sec_rva:#x}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
