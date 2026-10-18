"""Điều khiển guest WinBoat qua QMP (chỉ dùng khi không còn đường khác).

    python3 .tmp/qmp.py shot out.png
    python3 .tmp/qmp.py key ret
    python3 .tmp/qmp.py type "admin"
    python3 .tmp/qmp.py type-hex 61646d696e     # dán chuỗi dài không cần map phím
    python3 .tmp/qmp.py combo ctrl-alt-delete

QMP của container WinBoat: 127.0.0.1:47292 -> 7149 trong container.
Ảnh chụp ghi vào /shared (bind = /home/admin trên host) rồi convert sang PNG.
"""
import json
import socket
import subprocess
import sys
import time

HOST, PORT = "127.0.0.1", 47292
HOST_SHOT = "/home/admin/_qmp_shot.ppm"      # /shared trên container = /home/admin trên host
CONT_SHOT = "/shared/_qmp_shot.ppm"

# ký tự ASCII -> tên phím QEMU
PLAIN = {c: c for c in "abcdefghijklmnopqrstuvwxyz0123456789"}
PLAIN.update({
    " ": "spc", "-": "minus", "=": "equal", ",": "comma", ".": "dot",
    "/": "slash", "\\": "backslash", ";": "semicolon", "'": "apostrophe",
    "[": "bracket_left", "]": "bracket_right", "`": "grave_accent",
})
SHIFTED = {
    ":": "semicolon", "_": "minus", "+": "equal", "?": "slash", "|": "backslash",
    "\"": "apostrophe", "<": "comma", ">": "dot", "{": "bracket_left",
    "}": "bracket_right", "~": "grave_accent", "!": "1", "@": "2", "#": "3",
    "$": "4", "%": "5", "^": "6", "&": "7", "*": "8", "(": "9", ")": "0",
}


def qmp(commands):
    s = socket.create_connection((HOST, PORT), timeout=10)
    f = s.makefile("rwb", buffering=0)
    f.readline()                      # greeting

    def cmd(o):
        f.write((json.dumps(o) + "\n").encode())
        while True:
            line = f.readline()
            if not line:
                return None
            try:
                j = json.loads(line)
            except Exception:
                continue
            if "return" in j or "error" in j:
                return j

    cmd({"execute": "qmp_capabilities"})
    out = [cmd(c) for c in commands]
    s.close()
    return out


def hmp(line):
    return {"execute": "human-monitor-command", "arguments": {"command-line": line}}


def key(name, hold_ms=60):
    qmp([hmp(f"sendkey {name} {hold_ms}")])


def combo(spec):
    parts = spec.split("-")
    qmp([hmp(f"sendkey {'-'.join(parts)} 80")])


def send_text(text):
    """Một kết nối, nghỉ giữa các phím (nhiều kết nối thì QEMU nuốt phím)."""
    s = socket.create_connection((HOST, PORT), timeout=10)
    f = s.makefile("rwb", buffering=0)
    f.readline()
    f.write((json.dumps({"execute": "qmp_capabilities"}) + "\n").encode())
    time.sleep(0.05)

    def hmp1(line):
        f.write((json.dumps({"execute": "human-monitor-command",
                             "arguments": {"command-line": line}}) + "\n").encode())
        while True:
            l = f.readline()
            if not l:
                return
            try:
                j = json.loads(l)
            except Exception:
                continue
            if "return" in j or "error" in j:
                return

    for ch in text:
        if ch in PLAIN:
            hmp1(f"sendkey {PLAIN[ch]} 60")
        elif ch in SHIFTED:
            hmp1(f"sendkey shift-{SHIFTED[ch]} 60")
        elif ch.isalpha() and ch.isupper():
            hmp1(f"sendkey shift-{ch.lower()} 60")
        time.sleep(0.10)
    s.close()


def send_text_old(text):
    cmds = []
    for ch in text:
        if ch in PLAIN:
            cmds.append(hmp(f"sendkey {PLAIN[ch]} 40"))
        elif ch in SHIFTED:
            cmds.append(hmp(f"sendkey shift-{SHIFTED[ch]} 40"))
        elif ch.isalpha() and ch.isupper():
            cmds.append(hmp(f"sendkey shift-{ch.lower()} 40"))
        else:
            print(f"  (bỏ qua ký tự không map được: {ch!r})", file=sys.stderr)
    for c in cmds:
        qmp([c])                    # mỗi phím một kết nối: guest không kịp nuốt
        time.sleep(0.12)


def ppm_size():
    with open(HOST_SHOT, "rb") as f:
        head = f.read(64).split()
    return int(head[1]), int(head[2])


def click(x, y):
    """Click tuyệt đối; toạ độ theo pixel của frame hiện tại (usb-tablet có sẵn)."""
    w, h = ppm_size()
    cmds = [
        {"execute": "input-send-event", "arguments": {"events": [
            {"type": "abs", "data": {"axis": "x", "value": int(x * 0x7FFF / w)}},
            {"type": "abs", "data": {"axis": "y", "value": int(y * 0x7FFF / h)}}]}},
        {"execute": "input-send-event", "arguments": {"events": [
            {"type": "btn", "data": {"down": True, "button": "left"}}]}},
        {"execute": "input-send-event", "arguments": {"events": [
            {"type": "btn", "data": {"down": False, "button": "left"}}]}},
    ]
    qmp(cmds)
    print(f"click ({x},{y}) trên frame {w}x{h}")


def shot(path):
    qmp([hmp(f"screendump {CONT_SHOT}")])
    subprocess.run(["docker", "exec", "WinBoat", "chmod", "644", CONT_SHOT], check=False)
    subprocess.run(["magick", HOST_SHOT, "-resize", "1280x", path], check=True)
    print(f"-> {path}")


def main():
    cmd = sys.argv[1]
    if cmd == "click":
        click(int(sys.argv[2]), int(sys.argv[3]))
    elif cmd == "shot":
        shot(sys.argv[2])
    elif cmd == "key":
        key(sys.argv[2])
    elif cmd == "combo":
        combo(sys.argv[2])
    elif cmd == "type":
        send_text(sys.argv[2])
    elif cmd == "type-hex":
        send_text(bytes.fromhex(sys.argv[2]).decode())
    else:
        raise SystemExit(f"unknown command {cmd}")


if __name__ == "__main__":
    main()
