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

def run(mu, entry, vm_lo, vm_hi, max_insn=4_000_000, stop_on_exit=False, log_n=20000):
    """Run and record: writes into the VM section, indirect transfers (dispatcher), exits."""
    from unicorn import (UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_UNMAPPED,
                         UC_HOOK_MEM_READ_UNMAPPED, UC_PROT_ALL, UcError)
    from unicorn import x86_const as X
    md = md32(detail=True)
    ev = {"insn": 0, "writes": collections.Counter(), "vals": {}, "ind": [],
          "exit": None, "stop": None, "eip": entry, "pages": collections.Counter(),
          "seq": []}

    def on_code(mu8, addr, size, u):
        ev["insn"] += 1
        ev["eip"] = addr
        ev["pages"][addr & ~0xFFF] += 1
        if ev["insn"] > max_insn:
            ev["stop"] = "budget"
            mu8.emu_stop()
            return
        # indirect branch: FF /4 (jmp r/m) or FF /5 (call r/m) with a 1-byte opcode
        b = mu8.mem_read(addr, 2)
        if b[0] == 0xFF and ((b[1] >> 3) & 7) in (4, 5) and (b[1] & 0xC0) == 0:
            i = next(md.disasm(bytes(mu8.mem_read(addr, 8)), addr), None)
            if i is None or not i.operands:
                return
            opnd = i.operands[0]
            slot = None
            if opnd.type == 3 and opnd.mem.base == 0 and opnd.mem.disp:  # X86_OP_MEM
                slot = opnd.mem.disp & 0xFFFFFFFF
            tgt = mu8.reg_read(X.UC_X86_REG_EIP) if False else None
            if slot is not None:
                try:
                    tgt = struct.unpack("<I", mu8.mem_read(slot, 4))[0]
                except Exception:
                    tgt = None
            else:
                tgt = i.op_str
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sites", "discover", "jumps"])
    ap.add_argument("exe", nargs="?", default=str(ROOT / "unpacked_ca.exe"))
    ap.add_argument("--site", help="VM site (hex), required for jumps")
    ap.add_argument("--snap", help="pre.snap produced by win/snap.bat")
    ap.add_argument("--max", type=int, default=4_000_000)
    ap.add_argument("--json")
    a = ap.parse_args()
    {"sites": cmd_sites, "discover": cmd_discover, "jumps": cmd_jumps}[a.cmd](a)


if __name__ == "__main__":
    main()
