"""Compare pre.snap / post.snap of one VM block (tools/launcher/snap.c): registers, the caller's frame, .data globals.
usage: python3 tools/snapdiff.py logs/snap/<SITE> [--heap]"""
import pathlib, struct, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from vmemu import load_snap, REG_ORDER

d = pathlib.Path(sys.argv[1])
r0, g0 = load_snap(d / "pre.snap")
r1, g1 = load_snap(d / "post.snap")
print("regs:", " ".join(f"{k}={r0[k]:#x}->{r1[k]:#x}" + ("*" if r0[k] != r1[k] else "") for k in REG_ORDER))
m0 = {b: data for b, s, p, t, data in g0}
m1 = {b: data for b, s, p, t, data in g1}


def rd(m, lo, n):
    for b, data in m.items():
        if b <= lo and lo + n <= b + len(data):
            return data[lo - b:lo - b + n]
    return None


def diff(name, lo, hi, rel=None):
    a, b = rd(m0, lo, hi - lo), rd(m1, lo, hi - lo)
    if a is None or b is None:
        print(name, "not in both snapshots"); return
    for i in range(0, hi - lo, 4):
        if a[i:i + 4] != b[i:i + 4]:
            tag = f"ebp{lo + i - rel:+#x}" if rel is not None else f"{lo + i:#x}"
            print(f"  {name} {tag}: {struct.unpack_from('<I', a, i)[0]:#010x} -> {struct.unpack_from('<I', b, i)[0]:#010x}")


ebp, esp = r0["ebp"], r0["esp"] + 4
diff("frame", esp, ebp + 0x40, ebp)
diff("data", 0xE00000, 0xF09000)
for spec in sys.argv[2:]:
    if spec.startswith("--obj="):  # --obj=<ptr-global or address>:size   e.g. --obj=*E6092C:0x200
        what, size = spec[6:].split(":")
        addr = int(what.lstrip("*"), 16)
        if what.startswith("*"):
            addr = struct.unpack("<I", rd(m0, addr, 4))[0]
        print(f"object {addr:#x}:")
        diff("obj", addr, addr + int(size, 0), addr)
