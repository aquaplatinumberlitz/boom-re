"""Emulate one Themida-virtualized block with Unicorn and print what it does.

Two ways to get the memory the VM needs:
  --snap logs/snap/<SITE>/pre.snap   full memory of the ORIGINAL client taken at the VM site (tools/launcher/snap.c,
                                     win/snap.bat): registers, TEB, stacks, Themida runtime data — the VM runs correctly.
  (default) the dump unpacked_ca.exe only — the VM lacks its runtime state and goes astray (see docs/devirt.md).

Native code reached from the VM:
  - control enters ca.exe .text with [esp] pointing back into the Themida section -> a native CALL made by the VM:
    logged (target name, ecx, stack args). With --run-natives the call is executed in the emulator too
    (game code runs; Windows API entries are faked, see below); otherwise faked (eax = --ret, callee cleanup = its `ret N`).
  - control enters .text otherwise -> the VM EXIT (continuation); emulation stops.
  - control enters another module (Windows/game DLL) -> API call: logged by export name, faked (eax=--api-ret).
Logged: memory writes outside the stack and outside the Themida section, unmapped accesses.

usage: python3 tools/vmemu.py <site> --snap logs/snap/<SITE>/pre.snap [--run-natives] [--max N] [--trace N]
       python3 tools/vmemu.py <site> [reg=value ...] [--obj esi]          (dump only)
"""
import argparse, json, pathlib, struct

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = 0x400000
IMAGE = (0x400000, 0x16B2000)
THEMIDA = (0x11E4000, 0x16AB000)
STACK_TOP, STACK_SIZE = 0x30000000, 0x40000
REG_ORDER = ["edi", "esi", "ebp", "esp", "ebx", "edx", "ecx", "eax", "eflags"]


def load_snap(path):
    """-> (regs dict incl. teb, [(base, size, protect, type, data)])"""
    raw = open(path, "rb").read()
    magic, ver, n = struct.unpack_from("<4sII", raw, 0)
    assert magic == b"BSNP", magic
    regs = dict(zip(REG_ORDER + ["teb"], struct.unpack_from("<10I", raw, 12)))
    off, regions = 52, []
    for _ in range(n):
        b, s, prot, typ = struct.unpack_from("<4I", raw, off); off += 16
        regions.append((b, s, prot, typ, raw[off:off + s])); off += s
    return regs, regions


class Names:
    def __init__(self):
        d = json.load(open(ROOT / "decomp" / "ida_names.json"))["names"]
        self.n = {int(k, 16): v for k, v in d.items()}
        self.mods = []  # (base, end, name, {va: export})

    def add_module(self, base, data):
        import pefile
        try:
            pe = pefile.PE(data=data, fast_load=True)
            pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXPORT"]])
        except Exception:
            return
        exp = getattr(pe, "DIRECTORY_ENTRY_EXPORT", None)
        name = exp.name.decode(errors="replace") if exp and exp.name else f"mod_{base:x}"
        ex = {base + e.address: (e.name.decode() if e.name else f"#{e.ordinal}") for e in (exp.symbols if exp else [])}
        self.mods.append((base, base + pe.OPTIONAL_HEADER.SizeOfImage, name, ex))

    def module(self, a):
        for b, e, name, ex in self.mods:
            if b <= a < e:
                return name, ex.get(a)
        return None, None

    def near(self, a):
        for b, e, name, ex in self.mods:
            if b <= a < e:
                best = max((v for v in ex if v <= a), default=None)
                return f"{name}!{ex[best]}+{a - best:#x}" if best else f"{name}!{a:#x}"
        return f"{a:#x}"

    def __call__(self, a):
        if a in self.n:
            return self.n[a]
        m, e = self.module(a)
        return f"{m}!{e or hex(a)}" if m else f"sub_{a:X}"


def ret_imm(read, target):
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    for x in Cs(CS_ARCH_X86, CS_MODE_32).disasm(read(target, 0x3000), target):
        if x.mnemonic == "ret":
            return int(x.op_str, 16) if x.op_str else 0
        if x.mnemonic == "jmp" and not x.op_str.startswith("0x"):
            break
    return 0


def setup_fs(mu, teb):
    """Flat segments + FS -> TEB through a GDT (unicorn 32-bit has no FS_BASE)."""
    from unicorn import UC_PROT_ALL
    from unicorn import x86_const as X
    GDT = 0x7FF00000
    mu.mem_map(GDT, 0x1000, UC_PROT_ALL)

    def desc(base, limit, access, flags=0xC):
        d = (limit & 0xFFFF) | ((base & 0xFFFFFF) << 16) | (access << 40) | (((limit >> 16) & 0xF) << 48)
        d |= (flags << 52) | (((base >> 24) & 0xFF) << 56)
        return struct.pack("<Q", d)

    mu.mem_write(GDT + 8, desc(0, 0xFFFFF, 0xFA))        # 1 code r3
    mu.mem_write(GDT + 16, desc(0, 0xFFFFF, 0xF2))       # 2 data r3
    mu.mem_write(GDT + 24, desc(teb, 0xFFF, 0xF2, 0x4))  # 3 fs r3
    mu.mem_write(GDT + 32, desc(0, 0xFFFFF, 0x92))       # 4 stack r0
    mu.reg_write(X.UC_X86_REG_GDTR, (0, GDT, 0x1000, 0))
    mu.reg_write(X.UC_X86_REG_FS, (3 << 3) | 3)
    mu.reg_write(X.UC_X86_REG_DS, (2 << 3) | 3)
    mu.reg_write(X.UC_X86_REG_ES, (2 << 3) | 3)
    mu.reg_write(X.UC_X86_REG_SS, 4 << 3)


def main():
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_UNMAPPED, UC_PROT_ALL
    from unicorn import x86_const as X
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    md = Cs(CS_ARCH_X86, CS_MODE_32)

    ap = argparse.ArgumentParser()
    ap.add_argument("site")
    ap.add_argument("regs", nargs="*")
    ap.add_argument("--snap")
    ap.add_argument("--exe", default=str(ROOT / "unpacked_ca.exe"))
    ap.add_argument("--obj", action="append", default=[])
    ap.add_argument("--run-natives", action="store_true", help="execute game functions called by the VM")
    ap.add_argument("--ret", type=lambda s: int(s, 0), default=1)
    ap.add_argument("--api-ret", type=lambda s: int(s, 0), default=1)
    ap.add_argument("--max", type=int, default=100_000_000)
    ap.add_argument("--trace", type=int, default=0)
    ap.add_argument("--trace-from", type=int, default=0)
    ap.add_argument("--pre-asm", help="x86 run before the site (assembled at a scratch page, falls through to the site)")
    ap.add_argument("--set-reg", action="append", default=[], help="reg=value applied after loading the snapshot")
    ap.add_argument("--skip", action="append", default=[], help="addr[=eax]: do not execute this native, fake its return")
    ap.add_argument("--fake-api", action="store_true", help="fake Windows API entries instead of executing them")
    ap.add_argument("--quiet-api", action="store_true", help="do not log API entries")
    ap.add_argument("--writes", action="store_true", help="also log writes made inside executed native calls")
    a = ap.parse_args()

    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    names = Names()
    regs = {"eax": 0, "ebx": 0, "ecx": 0, "edx": 0, "esi": 0, "edi": 0, "ebp": STACK_TOP - 0x800, "esp": STACK_TOP - 0x1000}
    if a.snap:
        sregs, regions = load_snap(a.snap)
        for b, s, prot, typ, data in regions:
            mu.mem_map(b, (s + 0xFFF) & ~0xFFF, UC_PROT_ALL)
            mu.mem_write(b, data)
        for b, s, prot, typ, data in regions:
            if typ == 0x1000000 and data[:2] == b"MZ" and b != BASE:
                try:
                    size = struct.unpack_from("<I", data, struct.unpack_from("<I", data, 0x3C)[0] + 0x50)[0]
                    names.add_module(b, bytes(mu.mem_read(b, size)))
                except Exception:
                    pass
        regs.update({k: sregs[k] for k in regs})
        regs["esp"] += 4  # snap.c saved esp after its pushfd
        import pefile
        pe = pefile.PE(a.exe, fast_load=True)
        site_ = int(a.site, 16)
        mu.mem_write(site_, pe.get_data(site_ - BASE, 5))  # undo the snapshot hook (jmp cave)
        mu.reg_write(X.UC_X86_REG_EFLAGS, sregs["eflags"])
        stack_lo = sregs["esp"] - 0x100000
        setup_fs(mu, sregs["teb"])
        print(f"snapshot: {len(regions)} regions, teb {sregs['teb']:#x}, {len(names.mods)} modules")
    else:
        import pefile
        img = pefile.PE(a.exe).get_memory_mapped_image()
        mu.mem_map(BASE, (len(img) + 0xFFF) & ~0xFFF, UC_PROT_ALL)
        mu.mem_write(BASE, img)
        mu.mem_map(STACK_TOP - STACK_SIZE, STACK_SIZE + 0x1000, UC_PROT_ALL)
        stack_lo = STACK_TOP - STACK_SIZE
        for kv in a.regs:
            k, v = kv.split("=")
            regs[k] = int(v, 0)
        for r in a.obj:
            mu.mem_map(regs[r] & ~0xFFF, 0x10000, UC_PROT_ALL)
    for kv in a.set_reg:
        k, v = kv.split("=")
        regs[k] = int(v, 0)
    stack_hi = regs["esp"] + 0x2000
    for k, v in regs.items():
        mu.reg_write(getattr(X, "UC_X86_REG_" + k.upper()), v)
    site = int(a.site, 16)
    start = site
    if a.pre_asm:
        import keystone
        SCR = 0x7FF01000
        mu.mem_map(SCR, 0x1000, UC_PROT_ALL)
        enc, _ = keystone.Ks(keystone.KS_ARCH_X86, keystone.KS_MODE_32).asm(a.pre_asm + f"\njmp {site:#x}", SCR)
        mu.mem_write(SCR, bytes(enc))
        start = SCR
    mu.reg_write(X.UC_X86_REG_EIP, start)
    esp0 = regs["esp"]
    read = lambda addr, n: bytes(mu.mem_read(addr, n))
    rd32 = lambda addr: struct.unpack("<I", read(addr, 4))[0]

    skips = {}
    for sk in a.skip:
        k, _, v = sk.partition("=")
        skips[int(k, 16)] = int(v, 0) if v else 0
    st = {"n": 0, "in_vm": False, "done": None, "native_ret": []}

    def log(msg):
        print(f"#{st['n']:>9} " + "  " * len(st["native_ret"]) + msg, flush=True)

    def on_write(uc, access, addr, sz, value, _):
        if stack_lo <= addr < stack_hi or THEMIDA[0] <= addr < THEMIDA[1]:
            return
        if st["native_ret"] and not a.writes:
            return
        log(f"W [{addr:#x}] = {value & ((1 << (8 * sz)) - 1):#x} ({sz})")

    def on_unmapped(uc, access, addr, sz, value, _):
        log(f"UNMAPPED {addr:#x} eip={uc.reg_read(X.UC_X86_REG_EIP):#x} -> zero page")
        uc.mem_map(addr & ~0xFFF, 0x1000, UC_PROT_ALL)
        return True

    clock = {"t": 0}

    def syscall(uc, num, nm, args):
        """Minimal WoW64 syscall layer: enough for timers/heap growth/sleep. Default STATUS_SUCCESS."""
        short = nm.split("!")[-1]
        if short in ("NtQueryPerformanceCounter", "ZwQueryPerformanceCounter"):
            clock["t"] += 10000
            if args[0]:
                uc.mem_write(args[0], struct.pack("<Q", 0x100000000 + clock["t"]))
            if args[1]:
                uc.mem_write(args[1], struct.pack("<Q", 10_000_000))
            return 0
        if short in ("NtAllocateVirtualMemory", "ZwAllocateVirtualMemory"):
            pbase, psize = args[1], args[3]
            base_, size_ = rd32(pbase), rd32(psize)
            size_ = (size_ + 0xFFF) & ~0xFFF
            if base_ == 0:
                base_ = alloc["next"]; alloc["next"] += (size_ + 0xFFFF) & ~0xFFFF
            try:
                uc.mem_map(base_ & ~0xFFF, size_, UC_PROT_ALL)
            except Exception:
                pass
            uc.mem_write(pbase, struct.pack("<I", base_)); uc.mem_write(psize, struct.pack("<I", size_))
            return 0
        return 0

    alloc = {"next": 0x60000000}

    def fake_return(uc, esp, n, eax):
        uc.reg_write(X.UC_X86_REG_EAX, eax)
        uc.reg_write(X.UC_X86_REG_EIP, rd32(esp))
        uc.reg_write(X.UC_X86_REG_ESP, esp + 4 + n)

    def on_code(uc, addr, sz, _):
        st["n"] += 1
        if a.trace and a.trace_from <= st["n"] < a.trace_from + a.trace:
            x = next(md.disasm(read(addr, 16), addr), None)
            r = " ".join(f"{n}={uc.reg_read(getattr(X, 'UC_X86_REG_' + n.upper())):x}" for n in ("eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi"))
            print(f"{addr:08x} {x.mnemonic if x else '?':6s} {x.op_str if x else '':40s} {r}")
        if st["native_ret"] and addr == st["native_ret"][-1][0]:
            ra, tgt = st["native_ret"].pop()
            log(f"<- {names(tgt)} eax={uc.reg_read(X.UC_X86_REG_EAX):#x}")
            return
        if THEMIDA[0] <= addr < THEMIDA[1]:
            st["in_vm"] = True
            return
        if not st["in_vm"]:
            return
        esp = uc.reg_read(X.UC_X86_REG_ESP)
        if IMAGE[0] <= addr < IMAGE[1]:
            if st["native_ret"]:
                return
            ra = rd32(esp)
            if THEMIDA[0] <= ra < THEMIDA[1]:
                args = struct.unpack("<6I", read(esp + 4, 24))
                log(f"CALL {names(addr)} ({addr:#x}) ecx={uc.reg_read(X.UC_X86_REG_ECX):#x} args={' '.join(hex(v) for v in args)}")
                if addr in skips:
                    fake_return(uc, esp, ret_imm(read, addr) if not addr == 0 else 0, skips[addr])
                    log(f"  (skipped, eax={skips[addr]:#x})")
                elif a.run_natives:
                    st["native_ret"].append((ra, addr))
                else:
                    fake_return(uc, esp, ret_imm(read, addr), a.ret)
            else:
                st["done"] = addr
                uc.emu_stop()
            return
        b0 = read(addr, 1)[0]
        if b0 == 0xEA:  # WoW64 transition: jmp far 0x33:... -> emulate the syscall
            num = uc.reg_read(X.UC_X86_REG_EAX)
            stub = rd32(esp)
            nm = names.near(stub)
            args = struct.unpack("<6I", read(esp + 8, 24))
            res = syscall(uc, num, nm, args)
            log(f"SYSCALL {num:#x} {nm} args={' '.join(hex(v) for v in args)} -> {res:#x}")
            uc.reg_write(X.UC_X86_REG_EAX, res)
            uc.reg_write(X.UC_X86_REG_EIP, stub)
            uc.reg_write(X.UC_X86_REG_ESP, esp + 4)
            return
        m, e = names.module(addr)
        if m is not None and e is not None:
            args = struct.unpack("<5I", read(esp + 4, 20))
            if a.fake_api:
                n = ret_imm(read, addr)
                log(f"API {m}!{e} args={' '.join(hex(v) for v in args[:max(1, n // 4)])} -> {a.api_ret:#x}")
                fake_return(uc, esp, n, a.api_ret)
            elif not a.quiet_api and len(st["native_ret"]) <= 1:
                log(f"api {m}!{e} args={' '.join(hex(v) for v in args[:4])}")

    frame = (esp0, regs["ebp"] + 0x40) if regs["ebp"] > esp0 else (esp0, esp0 + 0x400)
    frame0 = read(frame[0], frame[1] - frame[0])
    DATA = (0xE00000, 0xF09000)
    data0 = read(DATA[0], DATA[1] - DATA[0]) if a.snap else None
    mu.hook_add(UC_HOOK_CODE, on_code)
    mu.hook_add(UC_HOOK_MEM_WRITE, on_write)
    mu.hook_add(UC_HOOK_MEM_UNMAPPED, on_unmapped)
    try:
        mu.emu_start(start, 0xFFFFFFFF, count=a.max)
    except Exception as e:
        print("emu error:", e, "eip", hex(mu.reg_read(X.UC_X86_REG_EIP)))
    def diff(name, lo, before, rel=None):
        after = read(lo, len(before))
        for i in range(0, len(before), 4):
            if before[i:i + 4] != after[i:i + 4]:
                tag = f"ebp{lo + i - rel:+#x}" if rel is not None else f"{lo + i:#x}"
                print(f"  {name} {tag}: {struct.unpack_from('<I', before, i)[0]:#010x} -> {struct.unpack_from('<I', after, i)[0]:#010x}")
    print(f"frame diff ({frame[0]:#x}..{frame[1]:#x}):")
    diff("frame", frame[0], frame0, regs["ebp"])
    if data0 is not None:
        print("global diff (.data 0xE00000-0xF09000):")
        diff("data", DATA[0], data0)
    out = {k: mu.reg_read(getattr(X, "UC_X86_REG_" + k.upper())) for k in regs}
    print(f"steps {st['n']}, exit -> {st['done'] and hex(st['done'])}")
    print("regs:", " ".join(f"{k}={v:#x}" + ("*" if v != regs[k] else "") for k, v in out.items()), f"(esp delta {out['esp'] - esp0:+#x})")


if __name__ == "__main__":
    main()
