"""Patch unpacked_ca.exe so it runs without anti-cheat / patch server and talks to our own server.

usage: python3 tools/patch_client.py unpacked_ca.exe ca_patched.exe [server_ip]

Patches (VA, see README "Địa chỉ quan trọng"):
  Feature 212  call -> mov al,1  every `push 0xD4; call Feature_IsDisabled` (22 sites): HackShield feature off,
                             the game's own switch (InitHackShield, heartbeat CStage::vf47, login, sub_8E31C0 users...)
  0x8E703A  jne -> jmp       skip BlackCipher init (sub_4134BF) in CFxApp__vf4
  0x8E56ED  10 x nop         skip PatchServer_CheckVersion (treat as success)
  IP strings                 every hardcoded server IP -> server_ip
"""
import struct, sys
import pefile

PATCHES = [
    # (va, original bytes, new bytes, note)
    (0x8E703A, bytes.fromhex("750C"), bytes.fromhex("EB0C"), "skip BlackCipher init"),
    (0x8E56ED, bytes.fromhex("57E87BEBFFFF85C07421"), b"\x90" * 10, "skip PatchServer_CheckVersion"),
    # sub_592BFA (array ctor of 10 x CMotionBlurFloorEffect, 0xA0 each; reached when the lobby square map loads,
    # sub_4BECBE -> sub_6EBC30(0x19)): bytes 1..6 of `push offset dtor; push offset ctor` were replaced in the dump by
    # FF 15 58 06 90 01 = call [0x01900658] (unmapped Themida region) -> count/ctor garbage -> jump to a stack address.
    # Restored from the intact twin sub_592C2D / unwind funclet 0xB1F8C0 (dtor sub_4C68E8) and the class ctor sub_4C6890
    # (only other function setting vt_CMotionBlurFloorEffect); bytes 0 and 7..9 (68 .. 68 4C 00) match.
    (0x592C09, bytes.fromhex("68FF1558069001684C00"), bytes.fromhex("68E8684C006890684C00"),
     "restore push dtor/ctor in sub_592BFA (lobby square map load)"),
]

# `call Feature_IsDisabled_stub0` (0x40176C, always returns al=0) right after `push 0xD4` (feature 212 = HackShield)
FEATURE_IS_DISABLED = 0x40176C
FEATURE_D4_CALLS = [0x595372, 0x59E869, 0x59E98A, 0x68BB28, 0x690AEC, 0x69E62E, 0x6AA235, 0x6B0070, 0x6B0278,
                    0x84E4ED, 0x852E4F, 0x855828, 0x8E29A3, 0x8E31D8, 0x8E3899, 0x8E4E57, 0x8F3108, 0x8F3207,
                    0x900D53, 0x900D62, 0x900D71, 0x900D81]
for _va in FEATURE_D4_CALLS:
    PATCHES.append((_va, None, bytes.fromhex("B001909090"), "Feature_IsDisabled(212 HackShield) -> 1"))

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
        if old is None:  # call rel32 to Feature_IsDisabled
            old = b"\xE8" + struct.pack("<i", FEATURE_IS_DISABLED - (va + 5))
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
