"""Observe one Themida-virtualized block on the ORIGINAL client (where the VM runs correctly).

Builds a code cave (loaded at a fixed address in the target by tools/launcher/inject.exe) that:
  pre  (hooked at the VM site):        save regs + snapshot data/obj/stack, then continue into the VM
  post (hooked at the continuation):    save regs + snapshot again, re-run the overwritten instructions, jump back
Then `diff` compares the two snapshots -> what the block did.

usage:
  python3 tools/vmtrace.py build <site> <cont> [--obj-reg esi] -> logs/vmtrace/<site>/{cave.bin,patches.txt,cfg.json}
  python3 tools/vmtrace.py diff <site>                         -> human-readable diff of logs/vmtrace/<site>/dump.bin
Run in Windows: win\\vmtrace.bat <site>  (writes logs/vmtrace/<site>/dump.bin)
"""
import json, pathlib, struct, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = 0x30000000          # cave + buffers, VirtualAllocEx'd at this address
DATA = (0xE00000, 0xF09000)  # writable globals of ca.exe (.data part of the merged section)
OBJ_SIZE, STK_BELOW, STK_SIZE = 0x400, 0x200, 0x300

# layout
OFF_FLAG = 0x0FF0
OFF_PRE_REGS, OFF_POST_REGS = 0x1000, 0x1040
OFF_PRE_OBJ, OFF_POST_OBJ = 0x2000, 0x3000
OFF_PRE_STK, OFF_POST_STK = 0x4000, 0x5000
OFF_PRE_DATA = 0x10000
OFF_POST_DATA = OFF_PRE_DATA + ((DATA[1] - DATA[0] + 0xFFFF) & ~0xFFFF)
TOTAL = OFF_POST_DATA + (OFF_POST_DATA - OFF_PRE_DATA)
REG_ORDER = ["edi", "esi", "ebp", "esp", "ebx", "edx", "ecx", "eax", "eflags"]  # pushfd; pushad layout
OBJ_REG_INDEX = {r: i for i, r in enumerate(REG_ORDER)}


def snap_asm(regs_off, obj_off, stk_off, data_off, obj_reg, flag):
    a = BASE
    oi = OBJ_REG_INDEX[obj_reg] * 4
    return f"""
        pushfd
        pushad
        cld
        mov esi, esp
        mov edi, {a + regs_off:#x}
        mov ecx, 9
        rep movsd dword ptr es:[edi], dword ptr [esi]
        mov esi, [esp + {oi:#x}]
        mov edi, {a + obj_off:#x}
        mov ecx, {OBJ_SIZE // 4:#x}
        rep movsd dword ptr es:[edi], dword ptr [esi]
        mov esi, [esp + 8]
        sub esi, {STK_BELOW:#x}
        mov edi, {a + stk_off:#x}
        mov ecx, {STK_SIZE // 4:#x}
        rep movsd dword ptr es:[edi], dword ptr [esi]
        mov esi, {DATA[0]:#x}
        mov edi, {a + data_off:#x}
        mov ecx, {(DATA[1] - DATA[0]) // 4:#x}
        rep movsd dword ptr es:[edi], dword ptr [esi]
        mov dword ptr [{a + OFF_FLAG:#x}], {flag}
        popad
        popfd
    """


def build(site, cont, obj_reg="esi"):
    import capstone, keystone, pefile
    pe = pefile.PE(str(ROOT / "unpacked_ca.exe"), fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    ks = keystone.Ks(keystone.KS_ARCH_X86, keystone.KS_MODE_32)

    site_bytes = pe.get_data(site - base, 5)
    if site_bytes[0] != 0xE9:
        sys.exit(f"site {site:#x} is not jmp rel32: {site_bytes.hex()}")
    vm_target = (site + 5 + struct.unpack_from("<i", site_bytes, 1)[0]) & 0xFFFFFFFF

    # instructions at the continuation that the 5-byte hook overwrites -> re-executed in the cave
    reloc, n = [], 0
    for ins in md.disasm(pe.get_data(cont - base, 32), cont):
        reloc.append(ins)
        n += ins.size
        if n >= 5:
            break
    back = cont + n
    reloc_asm = "\n".join(f"{i.mnemonic} {i.op_str}" for i in reloc)

    pre_va = BASE
    pre = snap_asm(OFF_PRE_REGS, OFF_PRE_OBJ, OFF_PRE_STK, OFF_PRE_DATA, obj_reg, 1) + f"\njmp {vm_target:#x}\n"
    pre_code, _ = ks.asm(pre, pre_va)
    post_va = BASE + 0x400
    post = snap_asm(OFF_POST_REGS, OFF_POST_OBJ, OFF_POST_STK, OFF_POST_DATA, obj_reg, 2) + f"\n{reloc_asm}\njmp {back:#x}\n"
    post_code, _ = ks.asm(post, post_va)
    assert len(pre_code) < 0x400 and len(post_code) < 0x400

    cave = bytearray(0x800)
    cave[0:len(pre_code)] = bytes(pre_code)
    cave[0x400:0x400 + len(post_code)] = bytes(post_code)

    def jmp(frm, to):
        return b"\xE9" + struct.pack("<i", to - (frm + 5))

    cont_old = pe.get_data(cont - base, 5)
    patches = [
        (site, site_bytes, jmp(site, pre_va)),
        (cont, cont_old, jmp(cont, post_va)),
    ]
    out = ROOT / "logs" / "vmtrace" / ("%X" % site)
    out.mkdir(parents=True, exist_ok=True)
    (out / "cave.bin").write_bytes(cave)
    # always also skip HackShield/BlackCipher
    lines = ["8E701D:7429:EB29"] + ["%X:%s:%s" % (va, o.hex(), n_.hex()) for va, o, n_ in patches]
    (out / "patches.txt").write_text("\n".join(lines) + "\n")
    cfg = dict(site="%X" % site, cont="%X" % cont, back="%X" % back, vm_target="%X" % vm_target, base="%X" % BASE,
               total="%X" % TOTAL, flag="%X" % (BASE + OFF_FLAG), obj_reg=obj_reg, data=["%X" % DATA[0], "%X" % DATA[1]],
               reloc=reloc_asm)
    (out / "cfg.json").write_text(json.dumps(cfg, indent=1))
    print(json.dumps(cfg, indent=1))


def regs(buf, off):
    return dict(zip(REG_ORDER, struct.unpack_from("<9I", buf, off)))


def diff(site):
    d = ROOT / "logs" / "vmtrace" / ("%X" % site)
    buf = (d / "dump.bin").read_bytes()
    flag = struct.unpack_from("<I", buf, OFF_FLAG)[0]
    print("flag", flag, "(2 = both hooks hit)")
    pre, post = regs(buf, OFF_PRE_REGS), regs(buf, OFF_POST_REGS)
    print("regs:", " ".join(f"{k}={pre[k]:08x}->{post[k]:08x}" + ("*" if pre[k] != post[k] else "") for k in REG_ORDER))

    def cmp(name, a_off, b_off, size, base_addr):
        a, b = buf[a_off:a_off + size], buf[b_off:b_off + size]
        changes = []
        for i in range(0, size, 4):
            if a[i:i + 4] != b[i:i + 4]:
                changes.append((base_addr + i, struct.unpack_from("<I", a, i)[0], struct.unpack_from("<I", b, i)[0]))
        print(f"{name}: {len(changes)} dwords changed")
        for va, x, y in changes[:200]:
            print(f"   {va:08x}: {x:08x} -> {y:08x}")

    cmp("obj[%s]" % "this", OFF_PRE_OBJ, OFF_POST_OBJ, OBJ_SIZE, pre[json.loads((d / "cfg.json").read_text())["obj_reg"]])
    cmp("stack[ebp-0x200..]", OFF_PRE_STK, OFF_POST_STK, STK_SIZE, pre["ebp"] - STK_BELOW)
    cmp("data", OFF_PRE_DATA, OFF_POST_DATA, DATA[1] - DATA[0], DATA[0])


if __name__ == "__main__":
    if sys.argv[1] == "build":
        args = sys.argv[2:]
        obj = "esi"
        if "--obj-reg" in args:
            i = args.index("--obj-reg"); obj = args[i + 1]; del args[i:i + 2]
        build(int(args[0], 16), int(args[1], 16), obj)
    else:
        diff(int(sys.argv[2], 16))
