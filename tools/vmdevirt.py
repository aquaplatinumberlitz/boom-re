"""Themida VM devirtualizer — stage 1: discovery.

Method (after Shablyko's FALCON write-up, adapted to 32-bit Themida builds and to a *dump*):
the VM entry is self-contained — the context pointer, VIP and handler table are computed from
constants living in the .vlizer-like section, not from host input. A dump plus a synthetic
stack is therefore enough to recover the VM's data structures.

Two bootstrap modes:
  --snap <pre.snap>  replay a memory snapshot of the real client from one VM site (ground truth;
                     the repo's tools/snap.bat produces these). Reveals ctx + handler table +
                     dispatch sequence.
  (image only)       run from a stub inside the dumped image with a synthetic stack. Works once
                     the stub's frame requirements are known.

Stages:
  1. discovery : sections, VM sites, stub heads, ctx window, handler table, dispatch histogram.
  2. handlers  : classify every handler (vm_exit / vpush / vpop / flag-op / branch) and extract
                 its virtual-instruction field offsets.
  3. decode    : walk virtual-instruction chains from a stub and build the CFG.
  4. emit      : recompile the chain into readable C.

usage:
  python3 tools/vmdevirt.py sites    [exe]
  python3 tools/vmdevirt.py discover [exe] [--json out.json]
  python3 tools/vmdevirt.py jumps    --snap logs/snap/8F346C/pre.snap --site 8F346C [--json out.json]
"""
import argparse
import collections
import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# snapshot register order written by tools/launcher/snap.c
SNAP_ORDER = ["edi", "esi", "ebp", "esp", "ebx", "edx", "ecx", "eax", "eflags"]


# ---------------------------------------------------------------- PE image

class Image:
    """Flat 32-bit PE image: VA <-> file data, section table, Themida section list."""

    def __init__(self, path):
        import pefile
        self.path = pathlib.Path(path)
        self.pe = pefile.PE(str(self.path), fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.raw = bytearray(self.pe.OPTIONAL_HEADER.SizeOfImage)
        for s in self.pe.sections:
            d = s.get_data()
            self.raw[s.VirtualAddress:s.VirtualAddress + len(d)] = d
        self.sections = [(s.Name.rstrip(b"\0").decode("latin1"), s.VirtualAddress,
                          s.Misc_VirtualSize, len(s.get_data())) for s in self.pe.sections]
        self.entry = self.base + self.pe.OPTIONAL_HEADER.AddressOfEntryPoint

    def read(self, va, n):
        return bytes(self.raw[va - self.base:va - self.base + n])

    def dword(self, va):
        return struct.unpack_from("<I", self.raw, va - self.base)[0]

    def readable(self, va):
        return self.base <= va < self.base + len(self.raw)

    def section_at(self, va):
        for name, rva, vsz, rsz in self.sections:
            lo, hi = self.base + rva, self.base + rva + max(vsz, rsz)
            if lo <= va < hi:
                return name, lo, hi
        return None, None, None

    def text_range(self):
        for name, rva, vsz, rsz in self.sections:
            if name in (".text", ".code"):
                return self.base + rva, self.base + rva + max(vsz, rsz)
        raise SystemExit("no .text section")

    def themida_sections(self):
        """Sections whose name is not a normal PE name: Themida renames or blanks them."""
        known = {".text", ".code", ".data", ".rdata", ".rsrc", ".reloc", ".idata",
                 ".edata", ".tls", ".bss", ".CRT", ".SCY"}
        out = []
        for name, rva, vsz, rsz in self.sections:
            if name.startswith(".") and name in known:
                continue
            if name.startswith(".") and name not in known:
                pass
            if max(vsz, rsz) < 0x1000:
                continue
            out.append((name, self.base + rva, self.base + rva + max(vsz, rsz)))
        return out

    def vm_range(self):
        secs = self.themida_sections()
        return min(s[1] for s in secs), max(s[2] for s in secs)


def md32(detail=False):
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    m = Cs(CS_ARCH_X86, CS_MODE_32)
    m.detail = detail
    return m


# ---------------------------------------------------------------- sites / stubs

def scan_sites(img, md, limit=None):
    """Every direct call/jmp from game .text into a Themida section."""
    lo, hi = img.text_range()
    vm_lo, vm_hi = img.vm_range()
    sites = []
    for va in range(lo, hi - 5):
        op = img.raw[va - img.base]
        if op not in (0xE8, 0xE9):
            continue
        tgt = (va + 5 + struct.unpack_from("<i", img.raw, va - img.base + 1)[0]) & 0xFFFFFFFF
        if not (vm_lo <= tgt < vm_hi):
            continue
        i = next(md.disasm(img.read(va, 8), va), None)
        if i is None or i.address != va or i.mnemonic not in ("call", "jmp"):
            continue
        sites.append((va, i.mnemonic, tgt))
    return sites


def follow_stub(img, md, start, limit=800):
    """Follow straight-line code + unconditional jmps; stop at the first non-linear terminator."""
    va, seen = start, []
    for _ in range(limit):
        i = next(md.disasm(img.read(va, 16), va), None)
        if i is None:
            return None, seen
        seen.append(va)
        if i.mnemonic == "jmp" and i.op_str.startswith("0x"):
            va = int(i.op_str, 16)
            if not img.readable(va):
                return None, seen
            continue
        if i.mnemonic in ("ret", "call") or i.mnemonic.startswith("j") or i.mnemonic == "jmp":
            return va, seen
        va += i.size
    return None, seen


# ---------------------------------------------------------------- snapshot

class Snap:
    """A BSNP memory snapshot produced by tools/launcher/snap.c."""

    def __init__(self, path):
        raw = open(path, "rb").read()
        magic, ver, n = struct.unpack_from("<4sII", raw, 0)
        if magic != b"BSNP":
            raise SystemExit(f"{path}: bad magic {magic!r}")
        self.regs = dict(zip(SNAP_ORDER + ["teb"], struct.unpack_from("<10I", raw, 12)))
        off, self.regions = 52, []
        for _ in range(n):
            b, s, prot, typ = struct.unpack_from("<4I", raw, off)
            off += 16
            self.regions.append((b, s, prot, typ, raw[off:off + s]))
            off += s


def build_uc(snap=None, img=None):
    """Unicorn 32-bit sandbox: snapshot regions (or the dumped image) + GDT-backed FS."""
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_ALL
    from unicorn import x86_const as X
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mapped = []
    if snap:
        for b, s, prot, typ, data in snap.regions:
            size = (s + 0xFFF) & ~0xFFF
            try:
                mu.mem_map(b, size, UC_PROT_ALL)
                mu.mem_write(b, data)
                mapped.append((b, b + size))
            except Exception:
                pass
        teb = snap.regs["teb"]
    else:
        mu.mem_map(img.base, (len(img.raw) + 0xFFF) & ~0xFFF, UC_PROT_ALL)
        mu.mem_write(img.base, bytes(img.raw))
        mapped.append((img.base, img.base + len(img.raw)))
        stack = 0x7FF00000
        mu.mem_map(stack - 0x100000, 0x100000, UC_PROT_ALL)
        mapped.append((stack - 0x100000, stack))
        teb = 0x7FFE0000
        mu.mem_map(teb, 0x2000, UC_PROT_ALL)
    gdt = None
    for a in (0x0F000000, 0x50000000, 0x60000000, 0x1F000000, 0x2F000000):
        try:
            mu.mem_map(a, 0x2000, UC_PROT_ALL)
            gdt = a
            break
        except Exception:
            continue
    if gdt is None:
        raise SystemExit("no free page for the GDT")

    def desc(base, limit, access, flags=0xC):
        d = (limit & 0xFFFF) | ((base & 0xFFFFFF) << 16) | (access << 40) | (((limit >> 16) & 0xF) << 48)
        return struct.pack("<Q", d | (flags << 52) | (((base >> 24) & 0xFF) << 56))

    mu.mem_write(gdt + 8, desc(0, 0xFFFFF, 0xFA))
    mu.mem_write(gdt + 16, desc(0, 0xFFFFF, 0xF2))
    mu.mem_write(gdt + 24, desc(teb, 0xFFF, 0xF2, 0x4))
    mu.mem_write(gdt + 32, desc(0, 0xFFFFF, 0x92))
    mu.reg_write(X.UC_X86_REG_GDTR, (0, gdt, 0x1000, 0))
    mu.reg_write(X.UC_X86_REG_FS, (3 << 3) | 3)
    mu.reg_write(X.UC_X86_REG_DS, (2 << 3) | 3)
    mu.reg_write(X.UC_X86_REG_ES, (2 << 3) | 3)
    mu.reg_write(X.UC_X86_REG_SS, 4 << 3)
    return mu


# ---------------------------------------------------------------- run + hooks

def run(mu, entry, vm_lo, vm_hi, max_insn=4_000_000, stop_on_exit=False, log_n=20000,
        stop_leave=False):
    """Run and record: writes into the VM section, indirect transfers (dispatcher), exits."""
    from unicorn import (UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_UNMAPPED,
                         UC_HOOK_MEM_READ_UNMAPPED, UC_PROT_ALL, UcError)
    from unicorn import x86_const as X
    from capstone.x86 import X86_OP_MEM, X86_OP_REG
    md = md32(detail=True)
    ev = {"insn": 0, "writes": collections.Counter(), "vals": {}, "ind": [],
          "exit": None, "stop": None, "eip": entry, "pages": collections.Counter(),
          "seq": []}

    armed = [not stop_leave]      # stop_leave: only stop once we have entered the VM range

    def on_code(mu8, addr, size, u):
        ev["insn"] += 1
        ev["eip"] = addr
        ev["pages"][addr & ~0xFFF] += 1
        if not armed[0] and vm_lo <= addr < vm_hi:
            armed[0] = True
        if stop_leave and armed[0] and not (vm_lo <= addr < vm_hi):
            ev["stop"] = ev["stop"] or "leave_vm"
            ev["exit"] = addr
            mu8.emu_stop()
            return
        if ev["insn"] > max_insn:
            ev["stop"] = "budget"
            mu8.emu_stop()
            return
        # indirect branch: FF /4 (jmp r/m) or FF /5 (call r/m)
        b = mu8.mem_read(addr, 2)
        if b[0] == 0xFF and ((b[1] >> 3) & 7) in (4, 5):
            i = next(md.disasm(bytes(mu8.mem_read(addr, 8)), addr), None)
            if i is None or not i.operands:
                return
            op = i.operands[0]
            slot, tgt = None, None
            if op.type == X86_OP_MEM:
                # full addressing mode: [base + index*scale + disp]
                slot = op.mem.disp & 0xFFFFFFFF
                for reg, scale in ((op.mem.base, 1), (op.mem.index, op.mem.scale)):
                    if reg:
                        try:
                            rv = mu8.reg_read(getattr(X, "UC_X86_REG_" + md.reg_name(reg).upper()))
                        except Exception:
                            rv = 0
                        slot = (slot + rv * scale) & 0xFFFFFFFF
                try:
                    tgt = struct.unpack("<I", mu8.mem_read(slot, 4))[0]
                except Exception:
                    tgt = None
            elif op.type == X86_OP_REG:
                try:
                    tgt = mu8.reg_read(getattr(X, "UC_X86_REG_" + md.reg_name(op.reg).upper()))
                except Exception:
                    tgt = None
            if len(ev["ind"]) < log_n:
                ev["ind"].append((addr, slot, tgt))
            if stop_on_exit and isinstance(tgt, int) and not (vm_lo <= tgt < vm_hi):
                ev["exit"] = tgt
                mu8.emu_stop()

    def on_write(mu8, access, addr, size, val, u):
        if vm_lo <= addr < vm_hi:
            ev["writes"][(addr, size)] += 1
            ev["vals"][addr] = val

    def on_unmapped(mu8, access, addr, size, val, u):
        ev["stop"] = f"unmapped {addr:#x} from {mu8.reg_read(X.UC_X86_REG_EIP):#x}"
        mu8.emu_stop()

    h = [mu.hook_add(UC_HOOK_CODE, on_code),
         mu.hook_add(UC_HOOK_MEM_WRITE, on_write),
         mu.hook_add(UC_HOOK_MEM_UNMAPPED, on_unmapped)]
    try:
        mu.emu_start(entry, 0xFFFFFFFF)
    except UcError as e:
        ev["stop"] = ev["stop"] or f"uc {e}"
    ev["eip"] = mu.reg_read(X.UC_X86_REG_EIP)
    ev["esp"] = mu.reg_read(X.UC_X86_REG_ESP)
    for x in h:
        mu.hook_del(x)
    return ev


def setup_from_snap(mu, snap, img, site):
    """Load snapshot register state and undo the snapshot hook at `site`."""
    from unicorn import x86_const as X
    r = snap.regs
    mu.reg_write(X.UC_X86_REG_ESP, r["esp"] + 4)   # snap.c saved esp after its own pushfd
    mu.reg_write(X.UC_X86_REG_EFLAGS, r["eflags"])
    for k in ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp"):
        mu.reg_write(getattr(X, "UC_X86_REG_" + k.upper()), r[k])
    mu.mem_write(site, img.pe.get_data(site - img.base, 5))   # original bytes at the site


def analyse_jumps(ev, img, vm_lo, vm_hi):
    """Group indirect transfers by table slot -> handler table base + entry count."""
    slots = collections.Counter()
    for eip, slot, tgt in ev["ind"]:
        if slot is None or not isinstance(tgt, int):
            continue
        slots[slot] += 1
    if not slots:
        return {}
    uniq = sorted(slots)
    # the table is the largest run of slots spaced 4 bytes apart
    runs, cur = [], [uniq[0]]
    for a in uniq[1:]:
        if a - cur[-1] <= 8:
            cur.append(a)
        else:
            runs.append(cur)
            cur = [a]
    runs.append(cur)
    runs.sort(key=len, reverse=True)
    table = runs[0]
    base = table[0] & ~3
    targets = collections.Counter()
    for eip, slot, tgt in ev["ind"]:
        if slot in table and isinstance(tgt, int):
            targets[tgt] += 1
    return {"base": base, "slots": len(table), "span": table[-1] - table[0] + 4,
            "hits": sum(slots[s] for s in table),
            "targets": targets, "all_slots": slots}


# ---------------------------------------------------------------- commands

def cmd_sites(a):
    img = Image(a.exe)
    md = md32()
    heads = collections.Counter()
    for va, kind, tgt in scan_sites(img, md):
        head, _ = follow_stub(img, md, tgt)
        heads[head] += 1
        print(f"{va:#010x} {kind:<4} -> {tgt:#010x} head {head if head is None else hex(head)}")
    print("\nhead histogram:")
    for h, c in heads.most_common():
        if h:
            print(f"  {h:#010x} x{c}")


def cmd_discover(a):
    img = Image(a.exe)
    md = md32()
    rep = {"image": str(img.path), "base": hex(img.base), "entry": hex(img.entry),
           "sections": [{"name": n, "lo": hex(img.base + rva), "size": hex(max(v, r))}
                        for n, rva, v, r in img.sections],
           "themida": [{"name": n, "lo": hex(lo), "hi": hex(hi)} for n, lo, hi in img.themida_sections()]}
    print(f"image {img.path.name}: base {img.base:#x} entry {img.entry:#x}")
    for n, lo, hi in img.themida_sections():
        print(f"  vm section {n!r:<10} {lo:#010x}..{hi:#010x} ({(hi - lo) >> 10} KiB)")
    sites = scan_sites(img, md)
    heads = collections.Counter()
    for va, kind, tgt in sites:
        head, _ = follow_stub(img, md, tgt)
        heads[head] += 1
    rep["sites"] = len(sites)
    rep["heads"] = {hex(k): v for k, v in heads.items() if k}
    print(f"\nsites {len(sites)}  distinct stub heads {len([h for h in heads if h])}")
    for h, c in heads.most_common(10):
        if h:
            print(f"  head {h:#010x} x{c}")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(rep, indent=1))
        print(f"-> {a.json}")


def cmd_jumps(a):
    site = int(a.site, 16)
    img = Image(a.exe)
    snap = Snap(a.snap)
    vm_lo, vm_hi = img.vm_range()
    print(f"snapshot: {len(snap.regions)} regions, teb {snap.regs['teb']:#x}, esp {snap.regs['esp']:#x}")
    print(f"vm range {vm_lo:#x}..{vm_hi:#x}   site {site:#x}")
    mu = build_uc(snap=snap)
    setup_from_snap(mu, snap, img, site)
    ev = run(mu, site, vm_lo, vm_hi, max_insn=a.max)
    print(f"insns {ev['insn']} stop {ev['stop']} eip {ev['eip']:#x} esp {ev['esp']:#x}")
    print(f"vm-section writes {len(ev['writes'])} distinct addrs, indirect transfers {len(ev['ind'])}")
    info = analyse_jumps(ev, img, vm_lo, vm_hi)
    if not info:
        print("no indirect transfers seen")
        return
    base = info["base"]
    print(f"\nhandler table candidate: base {base:#x}  slots {info['slots']}  "
          f"span {info['span']:#x}  dispatches {info['hits']}")
    print(f"distinct handler targets: {len(info['targets'])}")
    for t, c in info["targets"].most_common(15):
        sec, lo, hi = img.section_at(t)
        print(f"  {t:#010x} x{c:<6} {sec}")
    if a.json:
        out = {"site": hex(site), "insn": ev["insn"], "stop": ev["stop"],
               "table_base": hex(base), "slots": info["slots"],
               "targets": {hex(k): v for k, v in info["targets"].items()},
               "ctx_writes": {hex(k[0]): {"size": k[1], "n": v} for k, v in ev["writes"].items()},
               "ctx_vals": {hex(k): v for k, v in ev["vals"].items()}}
        pathlib.Path(a.json).write_text(json.dumps(out, indent=1))
        print(f"-> {a.json}")


def cmd_ctx(a):
    """Run one VM block to its exit and dump the context structure it maintained."""
    site = int(a.site, 16)
    img = Image(a.exe)
    snap = Snap(a.snap)
    vm_lo, vm_hi = img.vm_range()
    mu = build_uc(snap=snap)
    setup_from_snap(mu, snap, img, site)
    ev = run(mu, site, vm_lo, vm_hi, max_insn=a.max, stop_leave=True)
    print(f"insns {ev['insn']} stop {ev['stop']} exit {ev['exit'] if ev['exit'] is None else hex(ev['exit'])}")
    addrs = sorted({k[0] for k in ev["writes"]})
    if not addrs:
        print("no VM-section writes")
        return
    # cluster: the context is the densest run of written addresses
    clusters, cur = [], [addrs[0]]
    for x in addrs[1:]:
        if x - cur[-1] <= 0x40:
            cur.append(x)
        else:
            clusters.append(cur)
            cur = [x]
    clusters.append(cur)
    clusters.sort(key=len, reverse=True)
    lo, hi = clusters[0][0] & ~0xF, clusters[0][-1] | 0xF
    print(f"ctx cluster {lo:#x}..{hi:#x} ({len(clusters[0])} fields written)")
    print(f"\n{'off':>6} {'value':>10}  kind")
    for off in range(lo, hi + 1, 4):
        try:
            v = struct.unpack("<I", mu.mem_read(off, 4))[0]
        except Exception:
            continue
        if v == 0:
            kind = "-"
        elif vm_lo <= v < vm_hi:
            sec, _, _ = img.section_at(v)
            kind = f"ptr VM ({sec!r})"
        elif img.base <= v < img.base + len(img.raw):
            sec, _, _ = img.section_at(v)
            kind = f"ptr image ({sec!r})"
        else:
            kind = ""
        mark = "*" if (off, 4) in ev["writes"] or (off, 1) in ev["writes"] or (off, 2) in ev["writes"] else " "
        print(f"{off - lo:#06x} {v:#010x}  {mark} {kind}")


def cmd_trace(a):
    """Record one VM block from `site` to `cont` and summarise its effects on the process."""
    from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_UNMAPPED, UcError
    from unicorn import x86_const as X
    site = int(a.site, 16)
    cont = int(a.cont, 16) if a.cont else None
    img = Image(a.exe)
    snap = Snap(a.snap)
    vm_lo, vm_hi = img.vm_range()
    ctx = int(a.ctx, 16) if a.ctx else None
    mu = build_uc(snap=snap)
    setup_from_snap(mu, snap, img, site)
    start_regs = {k: mu.reg_read(getattr(X, "UC_X86_REG_" + k.upper()))
                  for k in ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp")}
    writes, calls, exits = {}, collections.Counter(), []
    n = [0]
    stop = [None]

    def on_code(mu8, addr, size, u):
        n[0] += 1
        if n[0] > a.max:
            stop[0] = "budget"
            mu8.emu_stop()
            return
        if cont is not None and addr == cont:
            stop[0] = "cont"
            mu8.emu_stop()
            return
        if not (vm_lo <= addr < vm_hi):
            # execution left the VM: a native call or a vm-exit. Record the landing address.
            if len(exits) < 200:
                exits.append(addr)

    def on_write(mu8, access, addr, size, val, u):
        k = (addr, size)
        if k in writes:
            writes[k][0] += 1
            writes[k][2] = val
        elif len(writes) < a.max_writes:
            writes[k] = [1, val, val, mu8.reg_read(X.UC_X86_REG_EIP)]

    def on_unmapped(mu8, access, addr, size, val, u):
        stop[0] = f"unmapped {addr:#x} from {mu8.reg_read(X.UC_X86_REG_EIP):#x}"
        mu8.emu_stop()

    mu.hook_add(UC_HOOK_CODE, on_code)
    mu.hook_add(UC_HOOK_MEM_WRITE, on_write)
    mu.hook_add(UC_HOOK_MEM_UNMAPPED, on_unmapped)
    try:
        mu.emu_start(site, 0xFFFFFFFF)
    except UcError as e:
        stop[0] = stop[0] or f"uc {e}"
    end_regs = {k: mu.reg_read(getattr(X, "UC_X86_REG_" + k.upper()))
                for k in ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp")}
    print(f"insns {n[0]}  stop {stop[0]}  exits {len(exits)}")
    for lbl, lo, hi in (("ctx", ctx, ctx + 0x400) if ctx else ("ctx", 0, 0),
                        ("image", img.base, img.base + len(img.raw))):
        pass
    groups = {"ctx": [], "image": [], "heap": [], "stack": []}
    for (addr, size), (cnt, first, last, eip) in writes.items():
        if ctx and ctx <= addr < ctx + 0x400:
            groups["ctx"].append((addr, size, cnt, first, last, eip))
        elif img.base <= addr < img.base + len(img.raw):
            groups["image"].append((addr, size, cnt, first, last, eip))
        elif addr > 0x10000000:
            groups["stack"].append((addr, size, cnt, first, last, eip))
        else:
            groups["heap"].append((addr, size, cnt, first, last, eip))
    for g in ("ctx", "image", "heap"):
        print(f"\n{g} writes: {len(groups[g])}")
        for addr, size, cnt, first, last, eip in sorted(groups[g])[:a.show]:
            off = f"{addr - ctx:+#05x}" if (ctx and g == "ctx") else ""
            print(f"  [{addr:#010x}] {off:<8} {size}B x{cnt:<4} {first:#010x} -> {last:#010x}  (first at {eip:#x})")
    print(f"\nregister delta:")
    for k in start_regs:
        if start_regs[k] != end_regs[k]:
            print(f"  {k}: {start_regs[k]:#010x} -> {end_regs[k]:#010x}")
    if exits:
        print(f"\nleft VM {len(exits)} times, first: {[hex(x) for x in exits[:6]]}")
    if a.json:
        out = {"site": hex(site), "cont": hex(cont) if cont else None, "insn": n[0], "stop": stop[0],
               "ctx": hex(ctx) if ctx else None,
               "writes": {g: [{"addr": hex(w[0]), "size": w[1], "n": w[2], "first": w[3], "last": w[4],
                               "eip": hex(w[5])} for w in groups[g]] for g in groups},
               "exits": [hex(x) for x in exits],
               "regs_start": {k: hex(v) for k, v in start_regs.items()},
               "regs_end": {k: hex(v) for k, v in end_regs.items()}}
        pathlib.Path(a.json).write_text(json.dumps(out, indent=1))
        print(f"-> {a.json}")


def cmd_lift(a):
    """Replay a block and print its semantic spine: every unique instruction that touches
    the VM context, image data or heap, with ctx offsets resolved."""
    from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED, UcError
    from unicorn import x86_const as X
    from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM
    site = int(a.site, 16)
    cont = int(a.cont, 16) if a.cont else None
    img = Image(a.exe)
    snap = Snap(a.snap)
    vm_lo, vm_hi = img.vm_range()
    ctx = int(a.ctx, 16) if a.ctx else None
    mu = build_uc(snap=snap)
    setup_from_snap(mu, snap, img, site)
    md = md32(detail=True)
    REGS = {getattr(X, "UC_X86_REG_" + k.upper()): k for k in
            ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp")}
    seen = {}
    order = []
    n = [0]
    stop = [None]

    def operand_addr(mu8, op):
        if op.type != X86_OP_MEM:
            return None
        a_ = op.mem.disp & 0xFFFFFFFF
        for reg, scale in ((op.mem.base, 1), (op.mem.index, op.mem.scale)):
            if reg:
                try:
                    a_ = (a_ + mu8.reg_read(reg) * scale) & 0xFFFFFFFF
                except Exception:
                    return None
        return a_

    def on_code(mu8, addr, size, u):
        n[0] += 1
        if n[0] > a.max:
            stop[0] = "budget"
            mu8.emu_stop()
            return
        if cont is not None and addr == cont:
            stop[0] = "cont"
            mu8.emu_stop()
            return
        if addr in seen:
            return
        i = next(md.disasm(bytes(mu8.mem_read(addr, 15)), addr), None)
        if i is None:
            return
        touches = []
        for op in i.operands:
            maddr = operand_addr(mu8, op)
            if maddr is None:
                continue
            if ctx and ctx <= maddr < ctx + 0x400:
                touches.append(("ctx", maddr - ctx, maddr))
            elif img.base <= maddr < img.base + len(img.raw):
                touches.append(("img", maddr, maddr))
            elif not (0x00100000 <= maddr < 0x10000000):
                touches.append(("heap", maddr, maddr))
        vals = []
        for op in i.operands:
            if op.type == X86_OP_REG and op.reg in REGS:
                try:
                    vals.append(f"{REGS[op.reg]}={mu8.reg_read(op.reg):#x}")
                except Exception:
                    pass
        seen[addr] = (i.mnemonic, i.op_str, tuple(touches), vals)
        order.append(addr)

    def on_unmapped(mu8, access, addr, size, val, u):
        stop[0] = f"unmapped {addr:#x}"
        mu8.emu_stop()

    mu.hook_add(UC_HOOK_CODE, on_code)
    mu.hook_add(UC_HOOK_MEM_UNMAPPED, on_unmapped)
    try:
        mu.emu_start(site, 0xFFFFFFFF)
    except UcError as e:
        stop[0] = stop[0] or f"uc {e}"
    print(f"insns {n[0]}  unique {len(order)}  stop {stop[0]}")
    sem = [x for x in order if seen[x][2]]
    print(f"semantic instructions (touch ctx/image/heap): {len(sem)} / {len(order)}\n")
    for addr in sem[:a.show]:
        mn, ops, touches, vals = seen[addr]
        t = " ".join(f"{k}{off if k != 'ctx' else f'+{off:#x}'}" for k, off, _ in touches)
        print(f"  {addr:#010x}  {mn:<8} {ops:<34}  ; {t}")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(
            [{"addr": hex(x), "insn": seen[x][0], "ops": seen[x][1],
              "touch": [[k, hex(o)] for k, o, _ in seen[x][2]]} for x in sem], indent=1))
        print(f"-> {a.json}")


def cmd_profile(a):
    """Emit decomp/vm_profile.json: everything the emitter needs, discovered not hardcoded."""
    from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_UNMAPPED, UcError
    from unicorn import x86_const as X
    from capstone.x86 import X86_OP_MEM, X86_OP_REG
    site = int(a.site, 16)
    img = Image(a.exe)
    md = md32()
    secs = img.themida_sections()
    sites = scan_sites(img, md)
    heads = collections.Counter()
    for va, kind, tgt in sites:
        head, _ = follow_stub(img, md, tgt)
        heads[head] += 1
    prof = {"image": str(img.path.name), "base": hex(img.base), "entry": hex(img.entry),
            "themida_sections": [{"name": n, "lo": hex(lo), "hi": hex(hi)} for n, lo, hi in secs],
            "sites": len(sites), "stub_heads": {hex(k): v for k, v in heads.most_common(4) if k}}
    print(f"[discover] {len(sites)} sites, {len([h for h in heads if h])} stub heads")

    snap = Snap(a.snap)
    vm_lo, vm_hi = img.vm_range()
    mu = build_uc(snap=snap)
    setup_from_snap(mu, snap, img, site)
    lock = [None]
    forms = collections.Counter()
    ctxw = collections.Counter()
    md_d = md32(detail=True)
    n = [0]

    def on_code(mu8, addr, size, u):
        n[0] += 1
        if n[0] > a.max:
            u and None
            mu8.emu_stop()
            return
        b = bytes(mu8.mem_read(addr, 2))
        if b[0] == 0xF0 and b[1] == 0x0F:            # lock cmpxchg ...
            i = next(md_d.disasm(bytes(mu8.mem_read(addr, 12)), addr), None)
            if i and i.operands:
                op = i.operands[0]
                if op.type == X86_OP_MEM:
                    ad = op.mem.disp
                    for reg, sc in ((op.mem.base, 1), (op.mem.index, op.mem.scale)):
                        if reg:
                            ad = (ad + mu8.reg_read(reg) * sc) & 0xFFFFFFFF
                    if lock[0] is None:
                        lock[0] = ad
        if b[0] == 0xFF and ((b[1] >> 3) & 7) in (4, 5):
            i = next(md_d.disasm(bytes(mu8.mem_read(addr, 10)), addr), None)
            if i and i.operands:
                op = i.operands[0]
                if op.type == X86_OP_REG:
                    forms["jmp/call reg"] += 1
                elif op.type == X86_OP_MEM:
                    if op.mem.index and op.mem.scale == 4:
                        forms[f"jmp/call [base+idx*4+{op.mem.disp:#x}]"] += 1
                    elif op.mem.base and not op.mem.index:
                        forms[f"jmp/call [base{op.mem.disp:+#x}]"] += 1
                    else:
                        forms["jmp/call [mem] other"] += 1

    def on_write(mu8, access, addr, size, val, u):
        if vm_lo <= addr < vm_hi:
            ctxw[addr] += 1

    def on_unmapped(mu8, access, addr, size, val, u):
        mu8.emu_stop()

    mu.hook_add(UC_HOOK_CODE, on_code)
    mu.hook_add(UC_HOOK_MEM_WRITE, on_write)
    mu.hook_add(UC_HOOK_MEM_UNMAPPED, on_unmapped)
    try:
        mu.emu_start(site, 0xFFFFFFFF)
    except UcError:
        pass
    anchor = lock[0]
    lock_off = int(a.lock_off, 16)
    base = int(a.ctx, 16) if a.ctx else (anchor - lock_off if anchor else None)
    print(f"[run] {n[0]} insns, spinlock field {anchor if anchor is None else hex(anchor)}, "
          f"ctx base {base if base is None else hex(base)}")
    prof["ctx"] = {"anchor": hex(anchor) if anchor else None, "base": hex(base) if base else None,
                   "lock_offset": hex(lock_off)}
    prof["dispatch_forms"] = dict(forms.most_common(10))
    prof["ctx_fields_written"] = ({hex(k - base): v for k, v in sorted(ctxw.items())}
                                  if base else {hex(k): v for k, v in sorted(ctxw.items())})
    print("[dispatch]")
    for k, v in forms.most_common(6):
        print(f"   {v:6d}  {k}")
    if base:
        print("[ctx fields written]")
        for k, v in sorted(ctxw.items())[:20]:
            print(f"   ctx+{k - base:#05x}  x{v}")
    out = pathlib.Path(a.json or (ROOT / "decomp" / "vm_profile.json"))
    out.write_text(json.dumps(prof, indent=1))
    print(f"-> {out}")


def read_handler_table(img, ctx, span=0x1000):
    """The VM keeps its handler table inside the context, indexed by a pre-scaled opcode:
    `jmp [ctx + idx*4]`. Entries are absolute code pointers into the VM section."""
    vm_lo, vm_hi = img.vm_range()
    out = []
    for off in range(0, span, 4):
        if not img.readable(ctx + off):
            break
        v = img.dword(ctx + off)
        if vm_lo <= v < vm_hi:
            out.append((off >> 2, v))
    return out


def describe_handler(img, md, addr, max_insn=40):
    """Walk a handler (following direct jmp inside the VM) and collect its features."""
    vm_lo, vm_hi = img.vm_range()
    feats = {"pushfd": 0, "lods": 0, "dispatch": 0, "pops": 0, "ret": 0, "call": 0, "n": 0}
    first = []
    va, seen = addr, set()
    for _ in range(max_insn):
        if va in seen or not (vm_lo <= va < vm_hi):
            break
        seen.add(va)
        i = next(md.disasm(img.read(va, 16), va), None)
        if i is None:
            break
        feats["n"] += 1
        m, o = i.mnemonic, i.op_str
        if m == "pushfd":
            feats["pushfd"] += 1
        elif m.startswith("lods"):
            feats["lods"] += 1
        elif m == "pop":
            feats["pops"] += 1
        elif m == "ret":
            feats["ret"] += 1
            break
        elif m in ("jmp", "call") and "[" in o:
            if "* 4]" in o or "*4]" in o:
                feats["dispatch"] += 1
            if m == "call":
                feats["call"] += 1
            break
        if not first:
            first.append(f"{m} {o}")
        if m == "jmp" and o.startswith("0x"):
            va = int(o, 16)
            continue
        if m.startswith("j") or m == "jmp":
            break
        va += i.size
    return feats, " ".join(first)


def cmd_handlers(a):
    """Enumerate the in-context handler table and classify every handler."""
    img = Image(a.exe)
    md = md32()
    ctx = int(a.ctx, 16)
    table = read_handler_table(img, ctx)
    print(f"handler table at ctx {ctx:#x}: {len(table)} entries")
    if not table:
        return
    rows = []
    classes = collections.Counter()
    for idx, addr in table:
        f, text = describe_handler(img, md, addr)
        if f["ret"] and f["pops"] >= 5:
            cls = "vm_exit"
        elif f["pushfd"]:
            cls = "flagop"
        elif f["dispatch"]:
            cls = "block_dispatch"
        elif f["lods"]:
            cls = "bytecode_read"
        else:
            cls = "block"
        classes[cls] += 1
        rows.append({"opcode": hex(idx), "addr": hex(addr), "class": cls, **f, "first": text})
    print("classes:", dict(classes))
    for r in rows[:a.show]:
        print(f"  op {r['opcode']:>6}  {r['addr']:>10}  {r['class']:<15} "
              f"n={r['n']:<3} pushfd={r['pushfd']} lods={r['lods']} disp={r['dispatch']} pops={r['pops']}  {r['first']}")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(rows, indent=1))
        print(f"-> {a.json}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sites", "discover", "jumps", "ctx", "trace", "lift",
                                    "profile", "handlers"])
    ap.add_argument("exe", nargs="?", default=str(ROOT / "unpacked_ca.exe"))
    ap.add_argument("--site", help="VM site (hex)")
    ap.add_argument("--cont", help="continuation address (hex), stop when reached")
    ap.add_argument("--ctx", help="VM context base (hex) for field offsets")
    ap.add_argument("--lock-off", default="0x7C", help="ctx offset of the spinlock field")
    ap.add_argument("--snap", help="pre.snap produced by win/snap.bat")
    ap.add_argument("--max", type=int, default=4_000_000)
    ap.add_argument("--max-writes", type=int, default=200_000)
    ap.add_argument("--show", type=int, default=60)
    ap.add_argument("--json")
    a = ap.parse_args()
    {"sites": cmd_sites, "discover": cmd_discover, "jumps": cmd_jumps, "ctx": cmd_ctx,
     "trace": cmd_trace, "lift": cmd_lift, "profile": cmd_profile,
     "handlers": cmd_handlers}[a.cmd](a)


if __name__ == "__main__":
    main()
