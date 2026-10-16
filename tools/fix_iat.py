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

# Slots Themida fully inlined (wrapper runs a copy of the API body), identified by how the game uses them.
# See docs/runtime.md "IAT: các ô xác định thủ công".
OVERRIDES = {
    0xC0F008: ("advapi32.dll", "RegQueryValueA"),        # sub_A232B0: (HKCR, subkey, buf, &cb)
    0xC0F1D4: ("kernel32.dll", "InterlockedExchange"),   # sub_9A6296: spinlock (p, 1) == 0
    0xC0F290: ("kernel32.dll", "CreateToolhelp32Snapshot"),  # (TH32CS_SNAPPROCESS=2, 0), cmp -1
    0xC0F294: ("kernel32.dll", "Process32First"),        # dwSize 0x128 = PROCESSENTRY32 (ANSI)
    0xC0F298: ("kernel32.dll", "Process32Next"),
    0xC0F2EC: ("kernel32.dll", "Thread32First"),         # dwSize 0x1C = THREADENTRY32
    0xC0F2F0: ("kernel32.dll", "Thread32Next"),
    0xC0F3E8: ("kernel32.dll", "InterlockedCompareExchange"),  # (p, 1|2, 0) == 0 lock; unlicense said oleaut32!VarUI4FromI8 (same bytes)
    0xC0F3EC: ("kernel32.dll", "InterlockedDecrement"),  # CRT ___removelocaleref
    0xC0F3F0: ("kernel32.dll", "InterlockedIncrement"),  # CRT ___addlocaleref
    0xC0F4D4: ("user32.dll", "GetMessageW"),             # (&msg,0,0,0) loop + DispatchMessageW
    0xC0F520: ("user32.dll", "EmptyClipboard"),          # syscall NtUserEmptyClipboard
    0xC0F528: ("user32.dll", "CloseClipboard"),          # syscall NtUserCloseClipboard
    0xC0F550: ("user32.dll", "GetWindow"),               # (hwnd, GW_CHILD=5) / (hwnd, GW_HWNDNEXT=2)
    0xC0F558: ("user32.dll", "EnumThreadWindows"),       # (tid, callback sub_A11FF0, lparam)
    0xC0F5C8: ("user32.dll", "keybd_event"),             # (VK_ESCAPE,0,0,0)+(VK_ESCAPE,0,KEYUP,0); syscall NtUserSendInput
    0xC0F5CC: ("user32.dll", "SystemParametersInfoA"),   # (SPI_SETSTICKYKEYS=59, 8, p, 0), (SPI_SETFILTERKEYS=51, 24, p, 0)
    # never referenced except by orphan thunks (sub_AC3Bxx / sub_9D7FB2) -> placeholders, must only be loadable
    0xC0F278: ("kernel32.dll", "Module32First"),         # PLACEHOLDER (unused, next to toolhelp group)
    0xC0F27C: ("kernel32.dll", "Module32Next"),          # PLACEHOLDER
    0xC0F280: ("kernel32.dll", "GetTickCount"),          # PLACEHOLDER
    0xC0F348: ("kernel32.dll", "SetHandleCount"),        # same Themida 1-arg family as Interlocked{In,De}crement; CRT __ioinit
    0xC0F40C: ("kernel32.dll", "InterlockedExchangeAdd"),  # same Themida-internal 2-arg family as InterlockedExchange; used via CALL_FIXES
    0xC0F54C: ("user32.dll", "GetDesktopWindow"),        # PLACEHOLDER
    0xC0F554: ("user32.dll", "GetDesktopWindow"),        # PLACEHOLDER
}

# Slots pointing into anti-cheat modules we do not want to load: replaced by tiny stubs (xor eax,eax; ret N).
STUBS = {
    0xC0F418: 0,   # ngclient.aes (BlackCipher), called with 0 args (sub_412B42)
    0xC0F41C: 12,  # ngclient.aes, BlackCipher init (sub_4134BF, skipped by our patch) - 3 args
}
# unlicense's fake IAT got three Themida-internal "multi API" emulators wrong (named after unrelated exports with
# identical bytes). Each call site through them is redirected to the right ORIGINAL IAT slot (filled by the loader).
# Classified by CRT source / how the result is used (see docs/runtime.md).
_INC, _DEC, _XCHG, _XADD, _CAS = 0xC0F3F0, 0xC0F3EC, 0xC0F1D4, 0xC0F40C, 0xC0F3E8
FAKE_BAD = {0x16AD3C8: "D3DXGetVertexShaderProfile", 0x16AD2CC: "D3DXGetShaderConstantTable", 0x16AD4CC: "VarUI4FromI8"}
CALL_FIXES = {
    # 1-arg (fake D3DXGetVertexShaderProfile): Increment if result ignored / ==0 on ctor, Decrement if ==0 -> free / <0
    0x9D8720: _INC, 0x9D874C: _DEC, 0x9D8775: _INC, 0x9D879E: _DEC,      # std::_Init_locks ctor/dtor
    0x9E62B5: _DEC, 0x9E637B: _INC,                                      # ___init_ctype
    0x9E6561: _DEC, 0x9E6680: _INC, 0x9E6EF9: _DEC,                      # __free_locale, __get_current_locale, __setlocale_set_cat
    0x9E8C64: _INC, 0x9E8DF7: _DEC,                                      # __initptd, __freefls
    0x9EB50E: _DEC, 0x9EB539: _INC, 0x9EB872: _DEC, 0x9EB929: _DEC,      # ___updatetmbcinfo, __setmbcp
    0x9F6B81: 0xC0F348, 0x9FB17F: _INC, 0x9FB857: _INC, 0x9FB868: _DEC,      # __ioinit = SetHandleCount(_nhandle), ___init_time, ___init_monetary
    0xA24D60: _INC, 0xA5DE04: _INC, 0xA5F7C8: _INC, 0xA87B8A: _DEC,      # game code: counter / AddRef / Release
    # 2-arg (fake D3DXGetShaderConstantTable)
    0x401792: _XADD, 0x4017B3: _XADD,                                    # atomic add / sub(-x)
    0x8125E4: _XCHG, 0x812606: _XCHG, 0x9A632B: _XCHG, 0x9D93F0: _XCHG,
    0x9D95BD: _XCHG, 0x9F7B36: _XCHG, 0xA03BF3: _XCHG, 0xABB906: _XCHG,
    # 3-arg (fake VarUI4FromI8)
    0x9D93AD: _CAS, 0xA24019: _CAS, 0xA24BD4: _CAS, 0xA24DDD: _CAS,
}
LOW_PRIORITY_DLLS = {"kernelbase.dll", "ntdll.dll", "win32u.dll", "gdi32full.dll", "combase.dll", "ucrtbase.dll"}


def parse_image_exports(name, base, img):
    """Exports of a module from its in-memory image (RVA == offset). -> (addr->[(mod,fn)], {(mod,fn): 'FWD:x'})"""
    addr2, fwd = collections.defaultdict(list), {}
    try:
        pe = struct.unpack_from("<I", img, 0x3C)[0]
        ed, edsz = struct.unpack_from("<II", img, pe + 0x78)
        if not ed:
            return addr2, fwd
        ordbase, nfuncs, nnames, af, an, ao = struct.unpack_from("<IIIIII", img, ed + 0x10)
        named = set()
        for i in range(nnames):
            nrva = struct.unpack_from("<I", img, an + 4 * i)[0]
            fn = img[nrva:img.index(b"\0", nrva)].decode("latin1")
            o = struct.unpack_from("<H", img, ao + 2 * i)[0]
            named.add(o)
            rva = struct.unpack_from("<I", img, af + 4 * o)[0]
            if ed <= rva < ed + edsz:
                fwd[(name, fn)] = img[rva:img.index(b"\0", rva)].decode("latin1")
            else:
                addr2[base + rva].append((name, fn))
        for o in range(nfuncs):
            if o not in named:
                rva = struct.unpack_from("<I", img, af + 4 * o)[0]
                if rva and not (ed <= rva < ed + edsz):
                    addr2[base + rva].append((name, "#%d" % (o + ordbase)))
    except (struct.error, ValueError):
        pass
    return addr2, fwd


def load_exports():
    """Exports of every module of the live process (from logs/live/image_*.bin)."""
    addr2, fwd, by_name = collections.defaultdict(list), {}, {}
    for n, base, size in load_modules():
        p = LIVE / ("image_%08x.bin" % base)
        if not p.exists():
            continue
        a2, f = parse_image_exports(n, base, p.read_bytes())
        for k, v in a2.items():
            addr2[k].extend(v)
            for mf in v:
                by_name[mf] = k
        fwd.update(f)
    return addr2, fwd, by_name


def nearest_export(addr2, mods, a, maxdist=0x40):
    """Themida 'stolen bytes': wrapper runs the API prologue itself, then jumps a few bytes into the API."""
    m = module_of(mods, a)
    best = None
    for k in range(a, a - maxdist, -1):
        if k in addr2 and addr2[k][0][0] == m:
            best = k
            break
    return best


def unlicense_map():
    """slot va -> API address, from unlicense's own resolution (same boot as the live dump)."""
    import re
    log = (ROOT / "unlicense_ca.log").read_text()
    m = {int(a, 16): int(b, 16) for a, b in re.findall(r"(?:Resolved API|Already resolved wrapper): (0x[0-9a-f]+) -> (0x[0-9a-f]+)", log)}
    import pefile
    pe = pefile.PE(str(ROOT / "unpacked_ca.exe"), fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    out = {}
    for va in range(IAT_VA, IAT_VA + IAT_SIZE, 4):
        v = struct.unpack("<I", pe.get_data(va - base, 4))[0]
        if v in m:
            out[va] = m[v]
    return out


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


_EMU = {}


def emulate(start, mods, regions, limit=2_000_000):
    """Run a Themida wrapper until it tail-jumps into a loaded DLL.

    Success = EIP inside a module other than ca.exe while ESP is back at its initial value
    (the caller's return address on top) -> that EIP is the API the wrapper stands for.
    Wrappers end in e.g. `jmp [kernel32 IAT slot]`, so all module images must be mapped."""
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UcError
    from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX
    STACK, sp = 0x0F000000, 0x0F080000
    if "mu" not in _EMU:
        mu = Uc(UC_ARCH_X86, UC_MODE_32)
        for base, data in sorted(regions):
            size = (len(data) + 0xFFF) & ~0xFFF
            try:
                mu.mem_map(base, size)
            except UcError:
                continue  # overlapping region
            mu.mem_write(base, data)
        mu.mem_map(STACK, 0x100000)
        dll_ranges = [(b, b + s) for n, b, s in mods if not n.startswith("ca.exe")]
        state = {"hit": None}

        def on_code(uc, addr, size, _):
            for lo, hi in dll_ranges:
                if lo <= addr < hi:
                    if uc.reg_read(UC_X86_REG_ESP) == sp:
                        state["hit"] = addr
                        uc.emu_stop()
                    return

        mu.hook_add(UC_HOOK_CODE, on_code)
        _EMU.update(mu=mu, state=state)
    mu, state = _EMU["mu"], _EMU["state"]
    state["hit"] = None
    mu.mem_write(sp, struct.pack("<I", 0xDEAD0000))
    mu.reg_write(UC_X86_REG_ESP, sp)
    try:
        mu.emu_start(start, 0xFFFFFFFF, count=limit)
    except UcError:
        pass
    return state["hit"]


def resolve():
    addr2, fwd, by_name = load_exports()
    mods = load_modules()
    iat = (LIVE / "iat.bin").read_bytes()
    regions = [(int(p.stem[4:], 16), p.read_bytes()) for p in sorted(LIVE.glob("reg_*.bin"))]
    regions += [(int(p.stem[6:], 16), p.read_bytes()) for p in LIVE.glob("image_*.bin")]
    ul = unlicense_map()
    slots = []
    for i in range(0, IAT_SIZE, 4):
        v = struct.unpack_from("<I", iat, i)[0]
        va = IAT_VA + i
        if v == 0:
            slots.append((va, 0, None, "zero"))
            continue
        m = module_of(mods, v)
        if m and not m.startswith("ca.exe"):
            a, how = v, "direct"
        else:
            a, how = emulate(v, mods, regions), "emulated"
        if a and a not in addr2:
            k = nearest_export(addr2, mods, a)
            if k:
                a, how = k, how + "+stolen"
        if (not a or a not in addr2) and va in ul and ul[va] in addr2:
            a, how = ul[va], "unlicense"
        names = addr2.get(a, []) if a else []
        if va in STUBS:
            slots.append((va, 0, [("<stub>", str(STUBS[va]))], "stub"))
            continue
        if va in OVERRIDES:
            slots.append((va, 0, [OVERRIDES[va]], "override"))
            continue
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


def pick_names(slots, fwd, by_name):
    """Choose (dll, func) per slot; for kernel32 groups map ntdll targets back to kernel32 forwarders."""
    rev_fwd = collections.defaultdict(list)  # "NTDLL.RtlX" -> [(mod, name)]
    for (mod, fn), target in fwd.items():
        rev_fwd[target.lower()].append((mod, fn))
    exports_of = collections.defaultdict(set)
    for (mod, fn) in list(fwd) + list(by_name):
        exports_of[mod].add(fn)

    def aliases(fn):
        yield fn
        for pre in ("NtUser", "NtGdi", "Nt", "Rtl", "Zw"):
            if fn.startswith(pre):
                yield fn[len(pre):]

    out = []
    for g in groups(slots):
        if all(n and n[0][0] == "<stub>" for _, _, n, _ in g):
            out.append(("<stub>", [(va, n[0], how) for va, _, n, how in g]))
            continue
        cands = collections.Counter()
        for _, _, n, _ in g:
            for d in exports_of:
                if n and any(al in exports_of[d] for _, fn in n for al in aliases(fn)):
                    cands[d] += 1
        origin = collections.Counter(n[0][0] for _, _, n, _ in g if n)  # module the address really lives in
        gdll = max(cands, key=lambda d: (cands[d], d not in LOW_PRIORITY_DLLS, origin[d])) if cands else None
        res = []
        for va, a, names, how in g:
            choice = None
            if names:
                same = [n for n in names if n[0] == gdll]
                exported = exports_of[gdll]
                alias = [(gdll, fn) for _, fn in names if fn in exported]
                if not alias:  # win32u!NtUserFoo -> user32!Foo, NtGdiFoo -> gdi32!Foo
                    for _, fn in names:
                        for pre in ("NtUser", "NtGdi", "Nt", "Rtl", "Zw"):
                            if fn.startswith(pre) and fn[len(pre):] in exported:
                                alias.append((gdll, fn[len(pre):]))
                if same:
                    choice = same[0]
                elif alias:
                    choice = alias[0]
                else:
                    for mod, fn in names:  # e.g. ntdll!RtlAllocateHeap reached through kernel32!HeapAlloc
                        cands = rev_fwd.get(f"{mod.split('.')[0]}.{fn}".lower(), [])
                        cands = [c for c in cands if c[0] == gdll] or [(gdll, c[1]) for c in cands if c[1] in exported] or cands
                        if cands:
                            choice = cands[0]
                            break
                    if choice is None:
                        choice = names[0]
            res.append((va, choice, how))
        out.append((gdll, res))
    return out


def report():
    slots, fwd, by_name, _ = resolve()
    st = collections.Counter(s[3] for s in slots)
    print(st)
    for gdll, res in pick_names(slots, fwd, by_name):
        for va, c, how in res:
            if c and c[0] != gdll and gdll != "<stub>":
                print(f"  MISMATCH {va:#x} group={gdll} name={c} via={how}")
    for gdll, res in pick_names(slots, fwd, by_name):
        bad = [hex(va) for va, c, _ in res if c is None]
        mixed = sorted({c[0] for _, c, _ in res if c and c[0] != gdll})
        print(f"{res[0][0]:#x} {gdll} n={len(res)} unresolved={bad} other_dlls={mixed}")


def build(src, dst):
    import pefile
    slots, fwd, by_name, _ = resolve()
    plan = pick_names(slots, fwd, by_name)
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
        if gdll == "<stub>":
            continue
        dll = gdll
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
    new_desc_padded = new_desc.ljust(desc_size, b"\0")  # stub groups reserve space but emit nothing
    ints = ints.ljust(total_ints, b"\0")
    blob = new_desc_padded + ints + names
    # stubs: xor eax,eax ; ret N   (written straight into their IAT slots below)
    stub_slots = {}
    while len(blob) % 16:
        blob += b"\xcc"
    for va, n in STUBS.items():
        stub_slots[va] = base + sec_rva + len(blob)
        blob += b"\x31\xc0" + (b"\xc2" + struct.pack("<H", n) if n else b"\xc3")
        while len(blob) % 16:
            blob += b"\xcc"
    raw_align = pe.OPTIONAL_HEADER.FileAlignment
    raw_size = (len(blob) + raw_align - 1) // raw_align * raw_align
    data = bytearray(open(src, "rb").read())
    raw_ptr = (len(data) + raw_align - 1) // raw_align * raw_align
    data += b"\0" * (raw_ptr - len(data)) + blob + b"\0" * (raw_size - len(blob))
    # section header
    hdr_off = pe.sections[-1].get_file_offset() + 40
    if hdr_off + 40 > pe.sections[0].PointerToRawData:
        sys.exit("no room for a new section header")
    sh = struct.pack("<8sIIIIIIHHI", b".imp2\0\0\0", len(blob), sec_rva, raw_size, raw_ptr, 0, 0, 0, 0, 0xE0000060)
    data[hdr_off:hdr_off + 40] = sh
    for site, slot in CALL_FIXES.items():
        o = pe.get_offset_from_rva(site - base)
        op, tgt = bytes(data[o:o + 2]), struct.unpack_from("<I", data, o + 2)[0]
        if op != b"\xff\x15" or tgt not in FAKE_BAD:
            sys.exit(f"call site {site:#x}: unexpected {bytes(data[o:o+6]).hex()}")
        struct.pack_into("<I", data, o + 2, slot)
    for va, target in stub_slots.items():
        o = pe.get_offset_from_rva(va - base)
        data[o:o + 4] = struct.pack("<I", target)
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
