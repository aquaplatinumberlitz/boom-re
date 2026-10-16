"""Patch unpacked_ca.exe so it runs without anti-cheat / patch server and talks to our own server.

usage: python3 tools/patch_client.py unpacked_ca.exe ca_patched.exe [server_ip]

Patches (VA, see README "Địa chỉ quan trọng"):
  0x8E701D  jz -> jmp        skip HackShield + BlackCipher init in CFxApp__vf4
  0x8E56ED  10 x nop         skip PatchServer_CheckVersion (treat as success)
  0x69E636  jnz -> jmp       skip the HackShield heartbeat in CStage::vf47 (anti-cheat object is null without HackShield)
  IP strings                 every hardcoded server IP -> server_ip
"""
import sys
import pefile

PATCHES = [
    # (va, original bytes, new bytes, note)
    (0x8E701D, bytes.fromhex("7429"), bytes.fromhex("EB29"), "skip HackShield/BlackCipher init"),
    (0x8E56ED, bytes.fromhex("57E87BEBFFFF85C07421"), b"\x90" * 10, "skip PatchServer_CheckVersion"),
    (0x69E636, bytes.fromhex("0F854C010000"), bytes.fromhex("E94D01000090"), "skip HackShield heartbeat (CStage::vf47)"),
]

IP_STRINGS = {  # va -> original (from strings xrefs; all used for server addresses)
    0xC88930: "222.255.122.204",  # CMultiServer default (gethostbyname)
    0xC88920: "120.138.77.22",
    0xC88910: "120.138.77.23",
    0xC88900: "120.138.77.24",
    0xC888F0: "120.138.77.25",
    0xC888E0: "120.138.77.83",
    0xC888D0: "120.138.77.84",
    0xC888C0: "120.138.77.85",
    0xC7C638: "118.102.5.126",    # used next to HackShield version string (sub_900C39)
    0xC83534: "175.207.3.35",     # sub_96A44A
}


def main(src, dst, ip="172.18.0.1"):
    pe = pefile.PE(src)
    data = bytearray(open(src, "rb").read())
    base = pe.OPTIONAL_HEADER.ImageBase

    def off(va):
        return pe.get_offset_from_rva(va - base)

    for va, old, new, note in PATCHES:
        o = off(va)
        cur = bytes(data[o:o + len(old)])
        if cur == new:
            print(f"{va:#x} already patched ({note})")
            continue
        if cur != old:
            sys.exit(f"{va:#x}: unexpected bytes {cur.hex()} (want {old.hex()}) -- wrong binary?")
        data[o:o + len(new)] = new
        print(f"{va:#x} {old.hex()} -> {new.hex()}  {note}")

    for va, orig in IP_STRINGS.items():
        o = off(va)
        cur = bytes(data[o:o + len(orig) + 1])
        if cur != orig.encode() + b"\0":
            sys.exit(f"{va:#x}: expected {orig!r}, found {cur!r}")
        if len(ip) > len(orig):
            sys.exit(f"server ip {ip!r} longer than slot {orig!r}")
        data[o:o + len(orig)] = ip.encode().ljust(len(orig), b"\0")
        print(f"{va:#x} {orig} -> {ip}")

    open(dst, "wb").write(data)
    print("wrote", dst)


if __name__ == "__main__":
    main(*sys.argv[1:])
