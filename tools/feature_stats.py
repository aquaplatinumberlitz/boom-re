"""Đếm trạng thái tính năng của client VN từ dữ liệu RE (không đoán).

Nguồn:
  decomp/opcode_dispatch.json   59 dispatcher, opcode -> handler (từ IDA)
  decomp/ida_names.json         20.7k tên hàm/class (RTTI)
  server/src/*.rs, tools/fakeserver.py   opcode mà server giả đã xử lý

Dùng:
  python3 tools/feature_stats.py            # in bảng
  python3 tools/feature_stats.py --json F   # ghi JSON
"""
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# nhóm chức năng: tên nhóm -> các mảnh tên class/dispatcher khớp
GROUPS = {
    "auth/login": ("Login", "Session", "Account", "SelectServer", "Channel", "User"),
    "social": ("Chat", "Chatting", "Friend", "Exchange", "UserMarket", "Clan", "Guild", "Mail"),
    "lobby/room": ("Lobby", "Square", "Prepare", "Room", "EnterChannel"),
    "battle": ("Game", "Bomber", "Bomb", "Battle", "Monster", "Mon", "Zombie", "Snow", "HiddenCatch",
               "FighterOfLegend", "Npc", "Map", "Score", "Round"),
    "economy": ("Shop", "Item", "Cash", "Gacha", "Inventory", "Buy", "Market", "Money"),
    "progression": ("Quest", "Rank", "Level", "Exp", "Mission", "Achievement", "Event"),
    "render/ui": ("Render", "Wnd", "Dlg", "Pane", "Button", "List", "Web"),
    "asset": ("Pack", "Idx", "Sprite", "Sound", "Audio", "Font", "Resource"),
}


def load():
    disp = json.loads((ROOT / "decomp" / "opcode_dispatch.json").read_text())
    names = json.loads((ROOT / "decomp" / "ida_names.json").read_text())["names"]
    return disp, names


def client_opcodes(disp):
    out = set()
    for ops in disp.values():
        out.update(int(k) for k in ops)
    return out


def server_opcodes(known):
    """Số opcode có xuất hiện trong code server (Rust + fakeserver)."""
    found = set()
    files = list((ROOT / "server" / "src").glob("*.rs")) + [ROOT / "tools" / "fakeserver.py"]
    for f in files:
        if not f.exists():
            continue
        text = f.read_text(errors="replace")
        for m in re.finditer(r"\b(\d{2,3})\b", text):
            n = int(m.group(1))
            if n in known:
                found.add(n)
    return found


def classify(name):
    """Khớp theo biên từ: 'Pack' không được khớp bên trong 'Packet'."""
    # chỉ xét tên class (trước "__"), tránh khớp nhầm vào "OnPacket"
    cls = name.split("@")[0].split("__")[0].lower()
    for g, keys in GROUPS.items():
        if any(k.lower() in cls for k in keys):
            return g
    return "khác"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args()
    disp, names = load()
    known = client_opcodes(disp)
    srv = server_opcodes(known)

    classes = {}
    for n in names.values():
        m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)__(?:vf|On_|)", n)
        if m:
            cls = m.group(1)
            classes[cls] = classes.get(cls, 0) + 1

    per_group = {}
    for name, ops in disp.items():
        g = classify(name)
        d = per_group.setdefault(g, {"dispatchers": 0, "opcodes": 0, "handlers": 0, "named": 0})
        d["dispatchers"] += 1
        d["opcodes"] += len(ops)
        for v in ops.values():
            d["handlers"] += len(v)
            d["named"] += sum(1 for h in v if not h.startswith("sub_"))

    print(f"client opcode biết: {len(known)}   server đã xử lý: {len(srv)} "
          f"({100*len(srv)/len(known):.1f}%)")
    print(f"dispatcher: {len(disp)}   class có tên RTTI: {len(classes)}   tên hàm: {len(names)}\n")
    print(f"{'nhóm':<16} {'disp':>5} {'opcode':>7} {'handler':>8} {'có tên':>7} {'server':>7}")
    for g, d in sorted(per_group.items(), key=lambda kv: -kv[1]["opcodes"]):
        s = sum(1 for name, ops in disp.items() if classify(name) == g
                for op in ops if int(op) in srv)
        print(f"{g:<16} {d['dispatchers']:>5} {d['opcodes']:>7} {d['handlers']:>8} "
              f"{d['named']:>7} {s:>7}")

    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({
            "client_opcodes": sorted(known), "server_opcodes": sorted(srv),
            "per_group": per_group, "classes": len(classes), "names": len(names)}, indent=1))
        print(f"\n-> {a.json}")


if __name__ == "__main__":
    main()
