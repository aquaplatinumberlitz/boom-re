"""Find every place where game code enters the Themida sections of unpacked_ca.exe and classify it.

usage: python3 tools/themida_scan.py unpacked_ca.exe  -> decomp/themida_entries.json

Classification (follows straight-line code + unconditional jmps, max 400 instructions):
  vm      : reaches the VM entry 0x11EE128; 'key' = immediate pushed right before (bytecode selector)
  return  : comes back into game .text (mutated / obfuscated native x86 -> runs fine natively)
  unknown : hit a conditional branch / ret / indirect jump first (needs manual look)
"""
import collections, json, pathlib, struct, sys
import capstone, pefile

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEXT = (0x401000, 0xBC0000)          # game code (.text, code part)
THEMIDA = (0x11E4000, 0x16AB000)     # Themida sections ('        ', 'rfsnoyxf', ...)
VM_ENTRY = 0x11EE128


def main(path):
    pe = pefile.PE(path, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    img = bytearray(pe.OPTIONAL_HEADER.SizeOfImage)
    for s in pe.sections:
        d = s.get_data()
        img[s.VirtualAddress:s.VirtualAddress + len(d)] = d
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

    def insn(va):
        return next(md.disasm(bytes(img[va - base:va - base + 16]), va), None)

    # 1) sites: E8/E9 rel32 in game text whose target is inside Themida sections
    sites = []
    lo, hi = TEXT
    for off in range(lo - base, hi - base - 5):
        op = img[off]
        if op in (0xE8, 0xE9):
            tgt = (base + off + 5 + struct.unpack_from("<i", img, off + 1)[0]) & 0xFFFFFFFF
            if THEMIDA[0] <= tgt < THEMIDA[1]:
                i = insn(base + off)
                if i and i.address == base + off and i.mnemonic in ("call", "jmp"):
                    sites.append((base + off, i.mnemonic, tgt))

    def follow(start):
        va, last_push, path = start, None, []
        for _ in range(400):
            if va == VM_ENTRY:
                return "vm", last_push, path
            if TEXT[0] <= va < TEXT[1] and path:
                return "return", va, path
            i = insn(va)
            if i is None:
                return "unknown", None, path
            path.append(va)
            if i.mnemonic == "push" and i.op_str.startswith("0x"):
                last_push = int(i.op_str, 16)
            if i.mnemonic == "jmp" and i.op_str.startswith("0x"):
                va = int(i.op_str, 16)
                continue
            if i.mnemonic.startswith("j") or i.mnemonic in ("ret", "call") or i.mnemonic == "jmp":
                return "unknown", i.mnemonic + " " + i.op_str, path
            va += i.size
        return "unknown", "too long", path

    out = []
    for site, kind, tgt in sites:
        cls, info, path = follow(tgt)
        e = {"site": "%X" % site, "insn": kind, "target": "%X" % tgt, "class": cls}
        if cls == "vm":
            e["key"] = "%X" % info if info is not None else None
        elif cls == "return":
            e["back_to"] = "%X" % info
        else:
            e["stop"] = info
        e["steps"] = len(path)
        out.append(e)
    # attach IDA function names if available
    names = {}
    p = ROOT / "decomp" / "ida_names.json"
    if p.exists():
        names = {int(k, 16): v for k, v in json.loads(p.read_text())["names"].items()}
    starts = sorted(names)
    import bisect
    for e in out:
        s = int(e["site"], 16)
        i = bisect.bisect_right(starts, s) - 1
        if i >= 0 and s - starts[i] < 0x4000:
            e["near_func"] = "%s+%X" % (names[starts[i]], s - starts[i])
    dst = ROOT / "decomp" / "themida_entries.json"
    dst.write_text(json.dumps(out, indent=1))
    print(collections.Counter(e["class"] for e in out), "->", dst)
    for e in out:
        if e["class"] == "vm":
            print("VM ", e["site"], e.get("near_func"), "key", e.get("key"))


if __name__ == "__main__":
    main(sys.argv[1])
