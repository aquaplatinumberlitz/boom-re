"""Resolve the original IAT of ca.exe (0xC0F000..0xC0F800) and rebuild imports so the Windows loader fills it.

Inputs (from tools/live_dump.ps1 + tools/dump_exports.ps1, captured in the SAME Windows boot):
  logs/exports.tsv            module \t export \t hexaddr | FWD:DLL.Name
  logs/live/iat.bin           IAT bytes of the live (Themida) process
  logs/live/modules.tsv       name \t base \t size
  logs/live/reg_XXXXXXXX.bin  executable private regions (Themida wrappers)

usage:
  python3 tools/fix_iat.py report
  python3 tools/fix_iat.py build in.exe out.exe     # add import descriptors for the original IAT
"""
import collections, pathlib, struct, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIVE = ROOT / "logs" / "live"
IAT_VA, IAT_SIZE = 0xC0F000, 0x800


def load_exports():
    addr2 = collections.defaultdict(list)
    fwd = {}  # (mod, name) -> "DLL.Func"
    by_name = {}
    for line in open(ROOT / "logs" / "exports.tsv"):
        mod, fn, a = line.rstrip("\n").split("\t")
        mod = mod.split("\\")[-1].lower()
        if a.startswith("FWD:"):
            fwd[(mod, fn)] = a[4:]
        else:
            addr2[int(a, 16)].append((mod, fn))
            by_name[(mod, fn)] = int(a, 16)
    return addr2, fwd, by_name


def load_modules():
    mods = []
    for line in open(LIVE / "modules.tsv"):
        n, b, s = line.strip().split("\t")
        mods.append((n.lower(), int(b, 16), int(s, 16)))
    return mods


def module_of(mods, a):
    for n, b, s in mods:
        if b <= a < b + s:
            return n
    return None


def emulate(start, mods, regions, limit=200000):
    """Run a Themida wrapper until execution enters a loaded module; return that address (or None)."""
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UcError
    from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EIP
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    for base, data in regions:
        size = (len(data) + 0xFFF) & ~0xFFF
        mu.mem_map(base, size)
        mu.mem_write(base, data)
    STACK = 0x0F000000
    mu.mem_map(STACK, 0x100000)
    sp = STACK + 0x80000
    mu.mem_write(sp, struct.pack("<I", 0xDEAD0000))
    mu.reg_write(UC_X86_REG_ESP, sp)
    hit = []

    def on_code(uc, addr, size, _):
        if module_of(mods, addr):
            hit.append(addr)
            uc.emu_stop()

    # entering a module means fetching unmapped memory: catch it via the unmapped-fetch error too
    from unicorn import UC_HOOK_MEM_FETCH_UNMAPPED
    def on_unmapped(uc, access, addr, size, value, _):
        hit.append(addr)
        return False

    mu.hook_add(UC_HOOK_MEM_FETCH_UNMAPPED, on_unmapped)
    try:
        mu.emu_start(start, 0xFFFFFFFF, count=limit)
    except UcError:
        pass
    return hit[0] if hit else None


def resolve():
    addr2, fwd, by_name = load_exports()
    mods = load_modules()
    iat = (LIVE / "iat.bin").read_bytes()
    regions = []
    for p in sorted(LIVE.glob("reg_*.bin")):
        regions.append((int(p.stem[4:], 16), p.read_bytes()))
    slots = []
    for i in range(0, IAT_SIZE, 4):
        v = struct.unpack_from("<I", iat, i)[0]
        va = IAT_VA + i
        if v == 0:
            slots.append((va, 0, None, "zero"))
            continue
        if module_of(mods, v):
            a, how = v, "direct"
        else:
            a, how = emulate(v, mods, regions), "wrapper"
        names = addr2.get(a, []) if a else []
        slots.append((va, a or 0, names, how if names else how + "-unresolved"))
    return slots, fwd, by_name, mods


def groups(slots):
    gs, cur = [], []
    for s in slots:
        if s[3] == "zero":
            if cur:
                gs.append(cur)
            cur = []
        else:
            cur.append(s)
    if cur:
        gs.append(cur)
    return gs


def pick_names(slots, fwd):
    """Choose (dll, func) per slot; for kernel32 groups map ntdll targets back to kernel32 forwarders."""
    rev_fwd = collections.defaultdict(list)  # "NTDLL.RtlX" -> [(mod, name)]
    for (mod, fn), target in fwd.items():
        rev_fwd[target.lower()].append((mod, fn))
    out = []
    for g in groups(slots):
        cnt = collections.Counter(n[0][0] for _, _, n, _ in g if n)
        gdll = cnt.most_common(1)[0][0] if cnt else None
        if gdll in ("kernelbase.dll", "ntdll.dll"):
            gdll = "kernel32.dll"
        res = []
        for va, a, names, how in g:
            choice = None
            if names:
                same = [n for n in names if n[0] == gdll]
                if same:
                    choice = same[0]
                else:
                    for mod, fn in names:  # e.g. ntdll!RtlAllocateHeap reached through kernel32!HeapAlloc
                        cands = rev_fwd.get(f"{mod.split('.')[0]}.{fn}".lower(), [])
                        cands = [c for c in cands if c[0] == gdll] or cands
                        if cands:
                            choice = cands[0]
                            break
                    if choice is None:
                        choice = names[0]
            res.append((va, choice, how))
        out.append((gdll, res))
    return out


def report():
    slots, fwd, _, _ = resolve()
    st = collections.Counter(s[3] for s in slots)
    print(st)
    for gdll, res in pick_names(slots, fwd):
        bad = [hex(va) for va, c, _ in res if c is None]
        mixed = sorted({c[0] for _, c, _ in res if c and c[0] != gdll})
        print(f"{res[0][0]:#x} {gdll} n={len(res)} unresolved={bad} other_dlls={mixed}")


def build(src, dst):
    import pefile
    slots, fwd, _, _ = resolve()
    plan = pick_names(slots, fwd)
    for gdll, res in plan:
        if any(c is None for _, c, _ in res):
            sys.exit(f"unresolved slots in group {res[0][0]:#x}; run 'report'")
    pe = pefile.PE(src)
    base = pe.OPTIONAL_HEADER.ImageBase
    old_dir = pe.OPTIONAL_HEADER.DATA_DIRECTORY[1]
    old_desc = pe.get_data(old_dir.VirtualAddress, old_dir.Size)
    old_desc = old_desc[: (len(old_desc) // 20 - 1) * 20]  # drop terminator
    # new section layout: [descriptors][INT arrays][hint/name + dll names]
    last = pe.sections[-1]
    sec_rva = (last.VirtualAddress + max(last.Misc_VirtualSize, last.SizeOfRawData) + 0xFFF) & ~0xFFF
    ndesc = len(old_desc) // 20 + len(plan) + 1
    desc_size = ndesc * 20
    blob = bytearray()
    ints, names = bytearray(), bytearray()
    int_off = desc_size
    total_ints = sum(len(r) + 1 for _, r in plan) * 4
    names_off = int_off + total_ints
    new_desc = bytearray(old_desc)
    for gdll, res in plan:
        dll_name_rva = sec_rva + names_off + len(names)
        dll = res[0][1][0]
        # every slot in a group must come from the same DLL for one descriptor; split if needed
        names += dll.encode() + b"\0"
        if len(names) % 2:
            names += b"\0"
        oft = sec_rva + int_off + len(ints)
        for va, (mod, fn), _ in res:
            if fn.startswith("#"):
                ints += struct.pack("<I", 0x80000000 | int(fn[1:]))
            else:
                ints += struct.pack("<I", sec_rva + names_off + len(names))
                names += b"\0\0" + fn.encode() + b"\0"
                if len(names) % 2:
                    names += b"\0"
        ints += b"\0\0\0\0"
        new_desc += struct.pack("<IIIII", oft, 0, 0, dll_name_rva, res[0][0] - base)
    new_desc += b"\0" * 20
    blob = new_desc + ints + names
    raw_align = pe.OPTIONAL_HEADER.FileAlignment
    raw_size = (len(blob) + raw_align - 1) // raw_align * raw_align
    data = bytearray(open(src, "rb").read())
    raw_ptr = (len(data) + raw_align - 1) // raw_align * raw_align
    data += b"\0" * (raw_ptr - len(data)) + blob + b"\0" * (raw_size - len(blob))
    # section header
    hdr_off = pe.sections[-1].get_file_offset() + 40
    if hdr_off + 40 > pe.sections[0].PointerToRawData:
        sys.exit("no room for a new section header")
    sh = struct.pack("<8sIIIIIIHHI", b".imp2\0\0\0", len(blob), sec_rva, raw_size, raw_ptr, 0, 0, 0, 0, 0xC0000040)
    data[hdr_off:hdr_off + 40] = sh
    out = pefile.PE(data=bytes(data))
    out.FILE_HEADER.NumberOfSections += 1
    out.OPTIONAL_HEADER.SizeOfImage = (sec_rva + len(blob) + 0xFFF) & ~0xFFF
    out.OPTIONAL_HEADER.DATA_DIRECTORY[1].VirtualAddress = sec_rva
    out.OPTIONAL_HEADER.DATA_DIRECTORY[1].Size = len(new_desc)
    out.OPTIONAL_HEADER.DATA_DIRECTORY[12].VirtualAddress = 0  # IAT dir: let loader handle
    out.OPTIONAL_HEADER.DATA_DIRECTORY[12].Size = 0
    # original IAT lives in a section that must be writable for the loader to patch it
    for s in out.sections:
        if s.VirtualAddress <= IAT_VA - base < s.VirtualAddress + s.Misc_VirtualSize:
            s.Characteristics |= 0x80000000
    out.write(dst)
    print(f"wrote {dst}: +{len(plan)} import descriptors, section .imp2 @ {sec_rva + base:#x}")


if __name__ == "__main__":
    if sys.argv[1] == "report":
        report()
    else:
        build(sys.argv[2], sys.argv[3])
