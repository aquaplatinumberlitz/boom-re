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



class Cycle:
    """Detect a repeating window in the dispatch-index stream.

    A "threaded" VM block often loops (poll/keep-alive), so `cont` is never reached. One
    iteration of that loop is the unit we actually want: stop when the last `p` handler
    indexes repeat the previous two windows of the same length (3 copies total).
    """

    def __init__(self, maxp=128, copies=3):
        self.hist = []
        self.maxp = maxp
        self.copies = copies
        self.period = None

    def push(self, idx):
        self.hist.append(idx)
        h = self.hist
        for p in range(1, min(self.maxp, len(h) // self.copies) + 1):
            ok = True
            for c in range(1, self.copies):
                if h[-p:] != h[-p * (c + 1):-p * c]:
                    ok = False
                    break
            if ok:
                self.period = p
                return p
        return None


# ---------------------------------------------------------------- run + hooks

def run(mu, entry, vm_lo, vm_hi, max_insn=4_000_000, stop_on_exit=False, log_n=20000,
        stop_leave=False, cycle=False):
    """Run and record: writes into the VM section, indirect transfers (dispatcher), exits."""
    from unicorn import (UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_UNMAPPED,
                         UC_HOOK_MEM_READ_UNMAPPED, UC_PROT_ALL, UcError)
    from unicorn import x86_const as X
    from capstone.x86 import X86_OP_MEM, X86_OP_REG
    md = md32(detail=True)
    ev = {"insn": 0, "writes": collections.Counter(), "vals": {}, "ind": [],
          "exit": None, "stop": None, "eip": entry, "pages": collections.Counter(),
          "seq": [], "cycle": None}
    cyc = Cycle()

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
            if cycle and op.type == X86_OP_MEM and op.mem.index and op.mem.scale == 4:
                try:
                    idx = mu8.reg_read(getattr(X, "UC_X86_REG_" + md.reg_name(op.mem.index).upper()))
                except Exception:
                    idx = None
                per = cyc.push(idx)
                if per is not None:
                    ev["cycle"] = {"period": per, "at": addr, "dispatches": len(cyc.hist)}
                    ev["stop"] = ev["stop"] or "cycle"
                    mu8.emu_stop()
                    return
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
    ev = run(mu, site, vm_lo, vm_hi, max_insn=a.max, stop_leave=True, cycle=a.cycle)
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
    vmcalls = collections.Counter()
    vmseq = []             # thứ tự các lần rời VM (để so với bản devirt tay)
    last = [None]          # địa chỉ cuối, để chỉ đếm lần ĐẦU vào một hàm image
    n = [0]
    stop = [None]
    cyc = Cycle()
    md_t = md32(detail=True) if (a.cycle or a.fake_native) else None
    stop_vip = int(a.stop_vip, 16) if a.stop_vip else None
    hub_count = a.hub_count
    disp_t = int(a.disp, 16) if a.disp else None
    hub_hits = [0]
    SCRATCH = 0x70000000
    try:
        from unicorn import UC_PROT_ALL
        mu.mem_map(SCRATCH, 0x10000, UC_PROT_ALL)
    except Exception:
        pass
    fake_ret = SCRATCH if a.fake_ret == "scratch" else int(a.fake_ret, 0)
    skips = {}
    for spec in (a.skip or []):
        k, _, v = spec.partition("=")
        skips[int(k, 16)] = int(v, 0) if v else 0
    armed = [False]

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
        prev_in_vm = last[0] is not None and vm_lo <= last[0] < vm_hi
        last[0] = addr
        if stop_vip is not None and disp_t is not None and addr == disp_t:
            if mu8.reg_read(getattr(X, "UC_X86_REG_" + (a.vip_reg or "esi").upper())) == stop_vip:
                hub_hits[0] += 1
                if hub_hits[0] >= hub_count:
                    stop[0] = "cycle"
                    print(f"hub {stop_vip:#x} reached {hub_hits[0]} times -> one iteration")
                    mu8.emu_stop()
                    return
        if a.cycle and md_t is not None:
            b = bytes(mu8.mem_read(addr, 2))
            if b[0] == 0xFF and ((b[1] >> 3) & 7) in (4, 5):
                i = next(md_t.disasm(bytes(mu8.mem_read(addr, 10)), addr), None)
                if i and i.operands:
                    op = i.operands[0]
                    if op.type == 3 and op.mem.index and op.mem.scale == 4:
                        try:
                            idx = mu8.reg_read(getattr(X, "UC_X86_REG_" + md_t.reg_name(op.mem.index).upper()))
                        except Exception:
                            idx = None
                        per = cyc.push(idx)
                        if per is not None:
                            stop[0] = "cycle"
                            print(f"cycle: period {per} handler-index, "
                                  f"{len(cyc.hist)} dispatches, at {addr:#x}")
                            mu8.emu_stop()
                            return
        if vm_lo <= addr < vm_hi:
            armed[0] = True
        elif a.fake_native and armed[0] and img.base <= addr < img.base + len(img.raw):
            if addr != site and prev_in_vm:
                vmcalls[addr] += 1
                if len(vmseq) < 200:
                    # capture thiscall ecx + up to 4 stack arguments (cdecl layout)
                    esp = mu8.reg_read(X.UC_X86_REG_ESP)
                    try:
                        args = struct.unpack("<4I", mu8.mem_read(esp + 4, 16))
                    except Exception:
                        args = (0, 0, 0, 0)
                    vmseq.append((addr, mu8.reg_read(X.UC_X86_REG_ECX), args))
            # left the VM into game code that lives in the dumped image: execute it, unless the
            # caller told us to skip it (anti-cheat / integrity checks that need a real process).
            if addr in skips:
                ra = fake_native(mu8, md_t, addr, ret_val=skips[addr],
                                 vm_lo=img.base, vm_hi=img.base + len(img.raw))
                if ra is not None:
                    calls[f"{addr:#x} (skipped)"] += 1
                    return
            return
        elif a.fake_native and armed[0] and md_t is not None:
            # left the image entirely (DLL / system): do not execute it, fake the return.
            try:
                b0 = bytes(mu8.mem_read(addr, 1))[0]
            except Exception:
                b0 = 0
            if b0 == 0xEA:                                  # WoW64 syscall transition
                ra = struct.unpack("<I", mu8.mem_read(mu8.reg_read(X.UC_X86_REG_ESP), 4))[0]
                mu8.reg_write(X.UC_X86_REG_EAX, 0)
                mu8.reg_write(X.UC_X86_REG_EIP, ra)
                mu8.reg_write(X.UC_X86_REG_ESP, mu8.reg_read(X.UC_X86_REG_ESP) + 4)
                calls["syscall"] += 1
                return
            ra = fake_native(mu8, md_t, addr, ret_val=fake_ret,
                             vm_lo=img.base, vm_hi=img.base + len(img.raw))
            if ra is None:
                stop[0] = stop[0] or f"left VM to {addr:#x} (no VM return addr)"
                mu8.emu_stop()
                return
            calls[f"{addr:#x}"] += 1
            if len(exits) < 200:
                exits.append(addr)
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
    if cont is not None and stop[0] != "cont":
        print("WARNING: chưa tới cont — số liệu dưới đây gồm cả code chạy sau khi khối kết thúc.")
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
    if vmseq:
        print("\nthứ tự rời VM (một vòng):")
        for i, (x, ecx, args) in enumerate(vmseq[:a.show]):
            astr = " ".join(f"{v:#x}" for v in args)
            print(f"   {i:2d}. {x:#010x}  ecx={ecx:#x}  args=[{astr}]")
    if vmcalls:
        print(f"\nVM -> native targets (một vòng): {len(vmcalls)} hàm, {sum(vmcalls.values())} lần")
        for k, c in vmcalls.most_common(12):
            print(f"   {k:#010x} x{c}")
    if calls:
        print("\nfaked native returns:", len(calls), "sites; top:")
        for k, c in calls.most_common(10):
            print(f"   {k} x{c}")
    if exits:
        print(f"left VM {len(exits)} times, first: {[hex(x) for x in exits[:6]]}")
    if a.json:
        out = {"site": hex(site), "cont": hex(cont) if cont else None, "insn": n[0], "stop": stop[0],
               "ctx": hex(ctx) if ctx else None,
               "writes": {g: [{"addr": hex(w[0]), "size": w[1], "n": w[2], "first": w[3], "last": w[4],
                               "eip": hex(w[5])} for w in groups[g]] for g in groups},
               "exits": [hex(x) for x in exits],
               "vmcalls": {hex(k): v for k, v in vmcalls.items()},
               "vmseq": [{"addr": hex(x), "ecx": hex(ecx), "args": [hex(v) for v in args]}
                         for x, ecx, args in vmseq],
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
        prev_in_vm = last[0] is not None and vm_lo <= last[0] < vm_hi
        last[0] = addr
        if stop_vip is not None and disp_t is not None and addr == disp_t:
            if mu8.reg_read(getattr(X, "UC_X86_REG_" + (a.vip_reg or "esi").upper())) == stop_vip:
                hub_hits[0] += 1
                if hub_hits[0] >= hub_count:
                    stop[0] = "cycle"
                    print(f"hub {stop_vip:#x} reached {hub_hits[0]} times -> one iteration")
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
    if cont is not None and stop[0] != "cont":
        print("WARNING: chưa tới cont — trace này là cả pool VM đã chạy, KHÔNG phải riêng khối; "
              "đừng dùng để kết luận ngữ nghĩa khối.")
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
    # fold in whatever the later stages already produced, so the profile is one file to read
    for key, name in (("opcodes", "vm_opcodes.json"), ("handlers", "vm_handlers.json")):
        q = ROOT / "decomp" / name
        if q.exists():
            try:
                prof[key] = json.loads(q.read_text())
            except Exception:
                pass
    out = pathlib.Path(a.json or (ROOT / "decomp" / "vm_profile.json"))
    out.write_text(json.dumps(prof, indent=1))
    print(f"-> {out}")



def _ret_imm(mu, md, addr, limit=64):
    """Bytes popped by `ret imm16` at an API stub (0 for cdecl / plain ret)."""
    try:
        raw = bytes(mu.mem_read(addr, 96))
    except Exception:
        return 0
    for i in md.disasm(raw, addr):
        if i.mnemonic == "ret":
            return int(i.op_str, 16) if i.op_str else 0
        if i.mnemonic in ("jmp", "call") and not i.op_str.startswith("0x"):
            break
    return 0


def fake_native(mu, md, callee, ret_val=0, vm_lo=0, vm_hi=0):
    """Return from an external call without executing it.

    The VM reached `callee` (a game function or a DLL API). We do not run it: we pop the
    return address that the `call` pushed, set eax, and let the VM continue. Returns the
    return address, or None when the stack does not look like a call from the VM.
    """
    from unicorn import x86_const as X
    esp = mu.reg_read(X.UC_X86_REG_ESP)
    try:
        ra = struct.unpack("<I", mu.mem_read(esp, 4))[0]
    except Exception:
        return None
    if vm_lo and not (vm_lo <= ra < vm_hi):
        return None
    n = _ret_imm(mu, md, callee)
    mu.reg_write(X.UC_X86_REG_EAX, ret_val)
    mu.reg_write(X.UC_X86_REG_ESP, esp + 4 + n)
    mu.reg_write(X.UC_X86_REG_EIP, ra)
    return ra


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


def cmd_bytecode(a):
    """Learn the virtual-instruction encoding from a trace, then decode the bytecode statically.

    At every dispatch the VM reveals (opcode, VIP). Consecutive dispatches give the size of the
    instruction: size = vip_next - vip_cur. A negative or non-adjacent delta means the current
    VI is a branch/jump. Sizes that disagree across the trace are reported as conflicts.
    """
    from unicorn import UC_HOOK_CODE, UcError
    from unicorn import x86_const as X
    site = int(a.site, 16)
    disp = int(a.disp, 16) if a.disp else None
    img = Image(a.exe)
    snap = Snap(a.snap)
    vm_lo, vm_hi = img.vm_range()
    mu = build_uc(snap=snap)
    setup_from_snap(mu, snap, img, site)
    vreg = getattr(X, "UC_X86_REG_" + (a.vip_reg or "esi").upper())
    seq, n, stop = [], [0], [None]

    def on_code(mu8, addr, size, u):
        n[0] += 1
        if n[0] > a.max:
            stop[0] = "budget"
            mu8.emu_stop()
            return
        if disp is not None and addr != disp:
            return
        if disp is None:
            b = bytes(mu8.mem_read(addr, 2))
            if not (b[0] == 0xFF and ((b[1] >> 3) & 7) == 4):
                return
        op = mu8.reg_read(X.UC_X86_REG_EAX)
        vip = mu8.reg_read(vreg)
        seq.append((vip, op))

    mu.hook_add(UC_HOOK_CODE, on_code)
    try:
        mu.emu_start(site, 0xFFFFFFFF)
    except UcError as e:
        stop[0] = stop[0] or f"uc {e}"
    print(f"insns {n[0]}  dispatches {len(seq)}  stop {stop[0]}")
    if len(seq) < 10:
        return
    sizes, conflicts, branches = {}, collections.Counter(), collections.Counter()
    for (v1, o1), (v2, o2) in zip(seq, seq[1:]):
        d = v2 - v1
        if 0 < d <= 16:
            if o1 in sizes and sizes[o1] != d:
                conflicts[o1] += 1
            else:
                sizes[o1] = d
        else:
            branches[o1] += 1
    print(f"opcodes seen {len(set(o for _, o in seq))}  sizes known {len(sizes)}  conflicts {len(conflicts)}")
    print("size histogram:", dict(collections.Counter(sizes.values())))
    if branches:
        print("opcodes with non-sequential follow-up (branch candidates):")
        for o, c in branches.most_common(10):
            print(f"   op {o:#04x} x{c}")
    if conflicts:
        print("conflicting sizes (same opcode, different length):")
        for o, c in conflicts.most_common(6):
            print(f"   op {o:#04x} x{c} (kept {sizes.get(o)})")
    lo = min(v for v, _ in seq)
    hi = max(v for v, _ in seq)
    print(f"VIP span {lo:#x}..{hi:#x}  ({hi - lo + 1} bytes)")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(
            {"sizes": {hex(k): v for k, v in sizes.items()},
             "branches": {hex(k): v for k, v in branches.items()},
             "conflicts": {hex(k): v for k, v in conflicts.items()},
             "vip_lo": hex(lo), "vip_hi": hex(hi), "dispatches": len(seq)}, indent=1))
        print(f"-> {a.json}")


def cmd_decode(a):
    """Decode the bytecode statically using the learned opcode sizes."""
    img = Image(a.exe)
    sizes = {int(k, 16): v for k, v in json.loads(pathlib.Path(a.sizes).read_text())["sizes"].items()}
    branches = {int(k, 16): v for k, v in json.loads(pathlib.Path(a.sizes).read_text())["branches"].items()}
    lo = int(a.start, 16)
    hi = int(a.end, 16) if a.end else lo + int(a.length, 16)
    pc, out, unknown = lo, [], []
    hist = collections.Counter()
    while pc < hi:
        op = img.read(pc, 1)[0]
        hist[op] += 1
        if op in sizes:
            n = sizes[op]
        elif op in branches:
            n = 5          # opcode + signed dword delta (checked below)
        else:
            unknown.append(pc)
            pc += 1
            continue
        out.append({"off": pc, "op": op, "size": n, "operands": img.read(pc + 1, max(0, n - 1)).hex()})
        pc += n
    print(f"decoded {len(out)} virtual instructions over {hi - lo} bytes")
    print(f"unknown opcode bytes: {len(unknown)}" + (f" (first: {[hex(x) for x in unknown[:6]]})" if unknown else ""))
    print("top opcodes:", [(hex(k), v) for k, v in hist.most_common(8)])
    # branch sanity: does the dword operand land inside the stream on a decoded boundary?
    starts = {v["off"] for v in out}
    inside = 0
    for v in out:
        if v["op"] in branches and len(v["operands"]) == 8:
            delta = struct.unpack("<i", bytes.fromhex(v["operands"]))[0]
            tgt = v["off"] + v["size"] + delta
            if lo <= tgt < hi and tgt in starts:
                inside += 1
    nb = sum(1 for v in out if v["op"] in branches)
    print(f"branch instructions: {nb}; target lands on a decoded boundary: {inside}")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(out[:200000], indent=0))
        print(f"-> {a.json}")


def cmd_opcodes(a):
    """Join three sources into one opcode map: handler table (static), VI sizes (trace),
    handler features (static). This is the specification the emitter needs."""
    from unicorn import UC_HOOK_CODE, UcError
    from unicorn import x86_const as X
    site = int(a.site, 16)
    img = Image(a.exe)
    md = md32()
    ctx = int(a.ctx, 16)
    table = {idx: addr for idx, addr in read_handler_table(img, ctx)}
    snap = Snap(a.snap)
    mu = build_uc(snap=snap)
    setup_from_snap(mu, snap, img, site)
    vreg = getattr(X, "UC_X86_REG_" + (a.vip_reg or "esi").upper())
    seq, n, stop = [], [0], [None]
    disp = int(a.disp, 16)

    def on_code(mu8, addr, size, u):
        n[0] += 1
        if n[0] > a.max:
            stop[0] = "budget"
            mu8.emu_stop()
            return
        if addr == disp:
            seq.append((mu8.reg_read(vreg), mu8.reg_read(X.UC_X86_REG_EAX)))

    mu.hook_add(UC_HOOK_CODE, on_code)
    try:
        mu.emu_start(site, 0xFFFFFFFF)
    except UcError as e:
        stop[0] = stop[0] or f"uc {e}"
    sizes, branches = {}, collections.Counter()
    for (v1, o1), (v2, _) in zip(seq, seq[1:]):
        d = v2 - v1
        if 0 < d <= 16:
            sizes.setdefault(o1, d)
        else:
            branches[o1] += 1
    print(f"dispatches {len(seq)}  opcodes {len(set(o for _, o in seq))}  stop {stop[0]}")
    rows = []
    for op in sorted(set(o for _, o in seq)):
        h = table.get(op)
        row = {"opcode": hex(op), "handler": hex(h) if h else None,
               "size": sizes.get(op), "branch_hits": branches.get(op, 0),
               "count": sum(1 for _, o in seq if o == op)}
        if h:
            feats, first = describe_handler(img, md, h, max_insn=24)
            row.update({"pushfd": feats["pushfd"], "lods": feats["lods"],
                        "dispatch": feats["dispatch"], "first": first})
        rows.append(row)
    with_h = sum(1 for r in rows if r["handler"])
    with_sz = sum(1 for r in rows if r["size"])
    print(f"opcodes with a handler in the table: {with_h}/{len(rows)}")
    print(f"opcodes with a measured size:        {with_sz}/{len(rows)}")
    print(f"branch opcodes: {[r['opcode'] for r in rows if r['branch_hits']]}")
    for r in rows[:a.show]:
        print(f"  op {r['opcode']:>6} size={str(r['size']):<4} n={r['count']:<5} "
              f"handler={r['handler']} pushfd={r.get('pushfd')} lods={r.get('lods')}  {r.get('first','')[:44]}")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(rows, indent=1))
        print(f"-> {a.json}")


def cmd_semantics(a):
    """First-pass semantics for every observed opcode: walk its handler and keep the
    instructions that actually do work (touch ctx/stack/memory or a register), skipping the
    junk that only shuffles pushes and pops."""
    img = Image(a.exe)
    md = md32()
    rows = json.loads(pathlib.Path(a.opcodes).read_text())
    vm_lo, vm_hi = img.vm_range()
    ctx = int(a.ctx, 16)
    out = []
    for r in rows:
        h = r.get("handler")
        if not h:
            continue
        va = int(h, 16)
        seen, body = set(), []
        for _ in range(28):
            if va in seen or not (vm_lo <= va < vm_hi):
                break
            seen.add(va)
            i = next(md.disasm(img.read(va, 16), va), None)
            if i is None:
                break
            m, o = i.mnemonic, i.op_str
            # keep the instruction if it is not pure stack shuffling
            keep = any(k in o for k in ("[edi", "[esi", "[esp +", "[esp -", "pushfd", "lods", "eax,", "ecx,", "edx,", "ebx,"))
            if m in ("xor", "add", "sub", "and", "or", "shl", "shr", "sar", "not", "neg", "imul", "mul", "div",
                     "cmp", "test", "movzx", "movsx", "inc", "dec", "xchg", "lodsb", "lodsw", "lodsd", "pushfd"):
                keep = True
            if keep and len(body) < 10:
                tag = ""
                if "[edi" in o:
                    try:
                        import re
                        m2 = re.search(r"\[edi \+ (0x[0-9a-f]+)\]", o)
                        if m2:
                            tag = f"ctx+{int(m2.group(1), 16):#x}"
                    except Exception:
                        pass
                body.append({"addr": hex(va), "insn": f"{m} {o}", "ctx": tag})
            if m == "jmp" and o.startswith("0x"):
                va = int(o, 16)
                continue
            if m.startswith("j") or m in ("ret", "jmp") or (m == "call" and not o.startswith("0x")):
                break
            va += i.size
        out.append({"opcode": r["opcode"], "handler": h, "size": r.get("size"),
                    "branch": bool(r.get("branch_hits")), "body": body})
    with_body = sum(1 for r in out if r["body"])
    print(f"semantics sketched for {with_body}/{len(out)} opcodes")
    for r in out[:a.show]:
        print(f"\n  op {r['opcode']} size={r['size']} handler={r['handler']}"
              + (" [BRANCH]" if r["branch"] else ""))
        for b in r["body"][:6]:
            print(f"      {b['insn']:<44} {b['ctx']}")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(out, indent=1))
        print(f"\n-> {a.json}")


def cmd_vfx(a):
    """Per-virtual-instruction effects: diff the VM context between two dispatches and group
    the resulting change-sets by opcode. Repeated identical effect sets are the opcode's
    empirical semantics."""
    from unicorn import UC_HOOK_CODE, UcError
    from unicorn import x86_const as X
    site = int(a.site, 16)
    disp = int(a.disp, 16)
    ctx = int(a.ctx, 16)
    img = Image(a.exe)
    md = md32(detail=True)
    snap = Snap(a.snap)
    mu = build_uc(snap=snap)
    setup_from_snap(mu, snap, img, site)
    vreg = getattr(X, "UC_X86_REG_" + (a.vip_reg or "esi").upper())
    FE = int(a.fields, 16)          # how much of the context to diff
    REGS = {k: getattr(X, "UC_X86_REG_" + k.upper()) for k in ("eax", "ebx", "ecx", "edx", "edi", "ebp", "esp")}
    prev = [None]                   # (op, vip, ctx_bytes, regs)
    sigs = collections.defaultdict(collections.Counter)
    counts = collections.Counter()
    n, stop, armed, calls = [0], [None], [False], [0]
    md_t = md
    vm_lo, vm_hi = img.vm_range()

    def fake_at(mu8, addr):
        """Fake a native call and return True when handled."""
        esp = mu8.reg_read(X.UC_X86_REG_ESP)
        try:
            ra = struct.unpack("<I", mu8.mem_read(esp, 4))[0]
        except Exception:
            return False
        if not (vm_lo <= ra < vm_hi):
            return False
        mu8.reg_write(X.UC_X86_REG_EAX, 0)
        mu8.reg_write(X.UC_X86_REG_ESP, esp + 4)
        mu8.reg_write(X.UC_X86_REG_EIP, ra)
        return True

    def on_code(mu8, addr, size, u):
        n[0] += 1
        if n[0] > a.max:
            stop[0] = "budget"
            mu8.emu_stop()
            return
        if vm_lo <= addr < vm_hi:
            armed[0] = True
        elif armed[0]:
            if fake_at(mu8, addr):
                calls[0] += 1
            else:
                stop[0] = f"left VM to {addr:#x}"
                mu8.emu_stop()
            return
        if addr != disp:
            return
        op = mu8.reg_read(X.UC_X86_REG_EAX)
        vip = mu8.reg_read(vreg)
        cur = bytes(mu8.mem_read(ctx, FE))
        rv = {k: mu8.reg_read(v) for k, v in REGS.items()}
        if prev[0] is not None:
            pop, pvip, pctx, prg = prev[0]
            rmask = tuple(sorted(k for k in REGS if rv[k] != prg[k]))
            changes = []
            for i in range(0, FE, 4):
                old = struct.unpack_from("<I", pctx, i)[0]
                new = struct.unpack_from("<I", cur, i)[0]
                if old != new:
                    changes.append((i, old, new))
            kind = (rmask, tuple(sorted((i, o, nv) for i, o, nv in changes)))
            sigs[pop][kind] += 1
        counts[op] += 1
        prev[0] = (op, vip, cur, rv)

    mu.hook_add(UC_HOOK_CODE, on_code)
    try:
        mu.emu_start(site, 0xFFFFFFFF)
    except UcError as e:
        stop[0] = stop[0] or f"uc {e}"
    print(f"insns {n[0]}  dispatches {sum(counts.values())}  faked natives {calls[0]}  stop {stop[0]}")
    print(f"opcodes observed: {len(counts)}")
    out = []
    for op, c in counts.most_common():
        sig = sigs.get(op, collections.Counter())
        top = sig.most_common(1)
        row = {"opcode": hex(op), "count": c, "distinct_effects": len(sig)}
        if top:
            k, cnt = top[0]
            row["dominant"] = {"share": f"{cnt}/{sum(sig.values())}",
                               "regs": list(k[0]),
                               "changes": [[hex(i), hex(o), hex(nv)] for i, o, nv in k[1]]}
        out.append(row)
    # determinism: how many opcodes have one dominant effect?
    det = sum(1 for r in out if r.get("dominant") and
              r["dominant"]["share"].split("/")[0] == r["dominant"]["share"].split("/")[1])
    print(f"opcodes whose every occurrence produced the same ctx effect-set: {det}/{len(out)}")
    for r in out[:a.show]:
        print(f"  op {r['opcode']:>6} n={r['count']:<6} effects={r['distinct_effects']:<3} "
              f"dominant={r.get('dominant', {}).get('share', '-')} "
              f"regs={','.join(r.get('dominant', {}).get('regs') or [])}")
        for ch in (r.get("dominant", {}).get("changes") or [])[:4]:
            print(f"        ctx+{int(ch[0],16):#05x}: {ch[1]} -> {ch[2]}")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(out, indent=1))
        print(f"-> {a.json}")


def cmd_emit(a):
    """Emit C from a trace JSON: the writes the block made, grouped by region, plus the native
    calls it performed. This is effect-based emission (what devirt.py writes by hand), not a
    faithful per-instruction translation."""
    t = json.loads(pathlib.Path(a.trace).read_text())
    ctx = int(t["ctx"], 16) if t.get("ctx") else None
    lines = []
    partial = t.get("stop") != "cont"
    lines.append(f"// block {t['site']} -> {t.get('cont')}   stop={t.get('stop')}   "
                 f"insns={t.get('insn')}")
    if partial:
        lines.append("// PARTIAL: khối không chạy tới cont — các hiệu ứng dưới đây KHÔNG đầy đủ.")
    lines.append("")
    lines.append(f"void vm_block_{int(t['site'], 16):X}(void *self)")
    lines.append("{")
    w = t.get("writes", {})
    # the VM's own section + context are internal state: not effects the game observes
    vm_lo = vm_hi = None
    try:
        prof = json.loads((ROOT / "decomp" / "vm_profile.json").read_text())
        vm_lo = min(int(x["lo"], 16) for x in prof["themida_sections"])
        vm_hi = max(int(x["hi"], 16) for x in prof["themida_sections"])
    except Exception:
        pass

    def internal(addr):
        return vm_lo is not None and vm_lo <= addr < vm_hi

    if w.get("image"):
        keep = [e for e in w["image"] if not internal(int(e["addr"], 16))]
        lines.append(f"    // {len(keep)} lần ghi vào .data/.text ngoài section VM (thường là scratch của VM)")
    if w.get("heap"):
        rs = t.get("regs_start") or {}
        try:
            ebp0 = int(rs.get("ebp", "0x0"), 16)
            esp0 = int(rs.get("esp", "0x0"), 16)
        except Exception:
            ebp0 = esp0 = 0
        stack_n = other = 0
        objs = []
        for e in w["heap"]:
            ad = int(e["addr"], 16)
            if (ebp0 and abs(ad - ebp0) < 0x800) or (esp0 and abs(ad - esp0) < 0x800):
                stack_n += 1
            else:
                other += 1
                objs.append(e)
        if stack_n:
            lines.append(f"    // {stack_n} địa chỉ là stack của VM (bỏ qua)")
        if other:
            lines.append(f"    // {other} địa chỉ ngoài stack — kiểm tra tay:")
            for e in sorted(objs, key=lambda x: -x["n"])[:20]:
                lines.append(f"    //   {e['addr']} n={e['n']} last={e['last']:#x}")
        else:
            lines.append("    // 0 write ra object/biến game ngoài stack")
    if ctx and w.get("ctx") and a.verbose:
        lines.append("")
        lines.append("    // state nội bộ VM (chỉ khi --verbose)")
        for e in w["ctx"]:
            off = int(e["addr"], 16) - ctx
            lines.append(f"    ctx[{off:#05x}] = {e['last']};   // {e['n']} lần ghi")
    seq = t.get("vmseq") or []
    if seq:
        lines.append("    // chuỗi gọi native, đúng thứ tự quan sát được (ecx = con trỏ this)")
        for i, e in enumerate(seq):
            tgt = int(e["addr"], 16)
            ecx = int(e["ecx"], 16)
            args = [int(x, 16) for x in e["args"]]
            shown = args[:2]
            lines.append(f"    call_{tgt:X}((void *){ecx:#x}, {', '.join(hex(x) for x in shown)});"
                         f"   // #{i}")
        lines.append("")
    calls = t.get("calls") or {}
    if calls:
        lines.append("    // lời gọi native (đã fake khi chạy)")
        for k, c in sorted(calls.items(), key=lambda kv: -kv[1])[:10]:
            lines.append(f"    //   {k} x{c}")
    lines.append("}")
    src = "\n".join(lines) + "\n"
    print(src)
    if a.json:
        pathlib.Path(a.json).write_text(src)
        print(f"-> {a.json}")


def cmd_cfg(a):
    """Build the CFG of the executed virtual-instruction stream.

    Blocks are split at every branch opcode and at every branch target. Edges are the observed
    transitions; the not-taken edge of a branch is only known when that path also executed, so
    unobserved edges stay explicitly unknown.
    """
    from unicorn import UC_HOOK_CODE, UcError
    from unicorn import x86_const as X
    site = int(a.site, 16)
    disp = int(a.disp, 16)
    img = Image(a.exe)
    snap = Snap(a.snap)
    mu = build_uc(snap=snap)
    setup_from_snap(mu, snap, img, site)
    vreg = getattr(X, "UC_X86_REG_" + (a.vip_reg or "esi").upper())
    seq, n, stop = [], [0], [None]

    def on_code(mu8, addr, size, u):
        n[0] += 1
        if n[0] > a.max:
            stop[0] = "budget"
            mu8.emu_stop()
            return
        if addr == disp:
            seq.append((mu8.reg_read(vreg), mu8.reg_read(X.UC_X86_REG_EAX)))

    mu.hook_add(UC_HOOK_CODE, on_code)
    try:
        mu.emu_start(site, 0xFFFFFFFF)
    except UcError as e:
        stop[0] = stop[0] or f"uc {e}"
    print(f"insns {n[0]}  dispatches {len(seq)}  stop {stop[0]}")
    # two passes: an opcode's size is its most common VIP delta; anything else is a branch
    deltas = collections.defaultdict(collections.Counter)
    for (v1, o1), (v2, _) in zip(seq, seq[1:]):
        d = v2 - v1
        if 0 < d <= 16:
            deltas[o1][d] += 1
    sizes = {o: c.most_common(1)[0][0] for o, c in deltas.items()}
    branches = set()
    for (v1, o1), (v2, _) in zip(seq, seq[1:]):
        d = v2 - v1
        if o1 in sizes and d != sizes[o1]:
            branches.add(o1)
        elif o1 not in sizes:
            branches.add(o1)
    blocks, edges = [], collections.Counter()
    cur = []
    starts = set()
    targets = {}
    for (v1, o1), (v2, o2) in zip(seq, seq[1:]):
        cur.append((v1, o1))
        d = v2 - v1
        if o1 in branches:
            targets.setdefault(v2, set()).add((v1, o1))
            edges[(v1, v2)] += 1
            blocks.append(cur)
            cur = []
            starts.add(v2)
    if cur:
        blocks.append(cur)
    loops = [(v1, v2) for (v1, v2) in edges if v2 <= v1]
    print(f"basic blocks {len(blocks)}  edges {len(edges)}  back edges {len(loops)}")
    print(f"block sizes: min {min(len(b) for b in blocks)}  max {max(len(b) for b in blocks)}  "
          f"mean {sum(len(b) for b in blocks)/len(blocks):.1f}")
    print(f"branch targets reached: {len(targets)}")
    print("largest blocks:")
    for b in sorted(blocks, key=len, reverse=True)[:5]:
        ops = " ".join(f"{o:02x}" for _, o in b[:10])
        print(f"   {b[0][0]:#x} len={len(b):<5} ops: {ops}")
    print("top edges (from -> to, count):")
    for (v1, v2), c in edges.most_common(8):
        kind = "back" if v2 <= v1 else "fwd"
        print(f"   {v1:#x} -> {v2:#x}  x{c}  ({kind})")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(
            {"blocks": [{"start": hex(b[0][0]), "ops": [hex(o) for _, o in b],
                         "vips": [hex(v) for v, _ in b]} for b in blocks[:5000]],
             "edges": [{"from": hex(a_), "to": hex(b_), "n": c, "back": b_ <= a_}
                       for (a_, b_), c in edges.most_common()],
             "dispatch": len(seq), "stop": stop[0]}, indent=1))
        print(f"-> {a.json}")


def _snap_regions(path):
    raw = open(path, "rb").read()
    magic, ver, n = struct.unpack_from("<4sII", raw, 0)
    if magic != b"BSNP":
        raise SystemExit(f"{path}: not a BSNP snapshot")
    off, out = 52, []
    for _ in range(n):
        b, sz, pr, t = struct.unpack_from("<4I", raw, off)
        off += 16
        out.append((b, sz, t, raw[off:off + sz]))
        off += sz
    return out


def cmd_verify(a):
    """Check an emitted effect against the real pre/post snapshots of the same block.

    For a dword value captured by the trace, find where it lives before and after the block.
    An address present only in `post` is a place the block wrote -- independent ground truth
    for the emitted C.
    """
    val = int(a.value, 16)
    pack = struct.pack("<I", val)
    def hits(path):
        out = []
        for b, sz, t, d in _snap_regions(path):
            i = 0
            while True:
                i = d.find(pack, i)
                if i < 0:
                    break
                out.append((b + i, t))
                i += 1
                if len(out) > 4000:
                    return out
        return out
    pre = hits(a.pre)
    post = hits(a.post)
    pres = {x for x, _ in pre}
    print(f"value {val:#x}: pre {len(pre)} hit(s), post {len(post)} hit(s)")
    new = [(x, t) for x, t in post if x not in pres]
    gone = [(x, t) for x, t in pre if x not in {y for y, _ in post}]
    print(f"  chỉ có trong post (block đã ghi ở đây): {len(new)}")
    for x, t in new[:a.show]:
        print(f"     {x:#010x}  type {t:#x}")
    print(f"  chỉ có trong pre (bị ghi đè/mất): {len(gone)}")
    for x, t in gone[:a.show]:
        print(f"     {x:#010x}  type {t:#x}")
    if a.at:
        at = int(a.at, 16)
        print(f"  tại địa chỉ chỉ định {at:#x}: pre={'có' if at in pres else 'không'}, "
              f"post={'có' if at in {y for y, _ in post} else 'không'}")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(
            {"value": hex(val), "pre": [hex(x) for x, _ in pre],
             "post": [hex(x) for x, _ in post],
             "post_only": [hex(x) for x, _ in new]}, indent=1))
        print(f"-> {a.json}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sites", "discover", "jumps", "ctx", "trace", "lift",
                                    "profile", "handlers", "bytecode", "decode", "opcodes", "semantics", "vfx", "emit", "cfg", "verify"])
    ap.add_argument("exe", nargs="?", default=str(ROOT / "unpacked_ca.exe"))
    ap.add_argument("--site", help="VM site (hex)")
    ap.add_argument("--cont", help="continuation address (hex), stop when reached")
    ap.add_argument("--ctx", help="VM context base (hex) for field offsets")
    ap.add_argument("--lock-off", default="0x7C", help="ctx offset of the spinlock field")
    ap.add_argument("--snap", help="pre.snap produced by win/snap.bat")
    ap.add_argument("--max", type=int, default=4_000_000)
    ap.add_argument("--max-writes", type=int, default=200_000)
    ap.add_argument("--fake-native", action="store_true",
                    help="không chạy code ngoài VM: giả lập return khi VM gọi hàm native/API")
    ap.add_argument("--fields", default="0x94", help="số byte ctx đem diff")
    ap.add_argument("--trace", help="trace JSON (từ lệnh trace --json)")
    ap.add_argument("--opcodes", default=str(ROOT / "decomp" / "vm_opcodes.json"))
    ap.add_argument("--sizes", default=str(ROOT / "decomp" / "vm_bytecode.json"))
    ap.add_argument("--start", help="bytecode start (hex)")
    ap.add_argument("--end", help="bytecode end (hex, exclusive)")
    ap.add_argument("--length", default="0x1000", help="bytes to decode when --end is absent")
    ap.add_argument("--disp", help="địa chỉ lệnh dispatch (hex); bỏ trống thì tự dò jmp [reg]")
    ap.add_argument("--vip-reg", default="esi", help="thanh ghi giữ VIP (mặc định esi)")
    ap.add_argument("--verbose", action="store_true", help="emit cả state nội bộ VM (ctx)")
    ap.add_argument("--fake-ret", default="scratch",
                    help="giá trị trả về khi fake API: 'scratch' (con trỏ tới vùng 64KB) hoặc số")
    ap.add_argument("--hub-count", type=int, default=2, help="dừng khi hub đạt N lần (mặc định 2)")
    ap.add_argument("--stop-vip", help="dừng khi VIP quay lại địa chỉ này lần thứ 2 (một vòng)")
    ap.add_argument("--pre", help="pre.snap (trước khối)")
    ap.add_argument("--post", help="post.snap (sau khối)")
    ap.add_argument("--value", help="giá trị dword cần kiểm (hex)")
    ap.add_argument("--at", help="địa chỉ kỳ vọng (hex)")
    ap.add_argument("--skip", action="append", default=[],
                    help="addr[=eax]: bỏ qua hàm native trong image (vd anti-cheat), giả lập return")
    ap.add_argument("--cycle", action="store_true",
                    help="dừng khi (handler idx, VIP) lặp lại: lấy đúng một vòng của khối loop")
    ap.add_argument("--show", type=int, default=60)
    ap.add_argument("--json")
    a = ap.parse_args()
    {"sites": cmd_sites, "discover": cmd_discover, "jumps": cmd_jumps, "ctx": cmd_ctx,
     "trace": cmd_trace, "lift": cmd_lift, "profile": cmd_profile,
     "handlers": cmd_handlers, "bytecode": cmd_bytecode, "decode": cmd_decode,
     "opcodes": cmd_opcodes, "semantics": cmd_semantics, "vfx": cmd_vfx, "emit": cmd_emit, "cfg": cmd_cfg, "verify": cmd_verify}[a.cmd](a)


if __name__ == "__main__":
    main()
