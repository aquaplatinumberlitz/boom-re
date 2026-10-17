"""Replace Themida-virtualized blocks of the dump with hand-written equivalents.

usage: python3 tools/devirt.py ca_fixed.exe ca_devirt.exe
(called by tools/rebuild_wine.sh between fix_iat.py build and patch_client.py)

Each block in BLOCKS: the VM site's `jmp 0x13xxxxx` is redirected to new code in a `.devirt` section;
the new code does what the VM block did and jumps to the continuation. Static results (tables, constants)
are written straight into the image. Evidence for every block: tools/vmtrace.py on the original client,
see docs/devirt.md.
"""
import struct, sys

GETTICKCOUNT_SLOT = 0xC0F1FC  # original IAT, kernel32!GetTickCount (decomp/iat_resolved.json)


def crc32_table_reflected(poly):
    t = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = (c >> 1) ^ poly if c & 1 else c >> 1
        t.append(c)
    return t


def dwords(*vals):
    return b"".join(struct.pack("<I", v) for v in vals)


BLOCKS = [
    dict(
        site=0x8F452B, cont=0x8F45A7, func="sub_8F4421 (CFxApp__InitMain init step)",
        # vmtrace 8F452B: no register effects needed (edi/esi/ebp/ebx preserved; eax/ecx dead), writes:
        #   0xEED860[256] = reflected CRC32 table, poly 0xDD10EC81   (read only by Themida code @0x1330A69)
        #   0xEEE07C = 0x4A65000A, 0xEEE088 = 1, 0xEEE08C = tick count (Themida-internal, no game xrefs)
        #   0xEEE650..65C = callbacks 8F2C5D, 8F30F7, 8F2C4F, 8F31F6 (used by many game funcs, e.g. sub_413F32)
        asm=f"""
            call dword ptr [{GETTICKCOUNT_SLOT:#x}]
            mov dword ptr [0xEEE08C], eax
            jmp {0x8F45A7:#x}
        """,
        data={
            0xEED860: dwords(*crc32_table_reflected(0xDD10EC81)),
            0xEEE07C: dwords(0x4A65000A),
            0xEEE088: dwords(1),
            0xEEE650: dwords(0x8F2C5D, 0x8F30F7, 0x8F2C4F, 0x8F31F6),
        },
    ),
    dict(
        site=0x8F8F69, cont=0x8F8FCA, func="CStageMgr__ChangeStage (0x8F8EEC), start of the new-stage part",
        # Themida only overwrote 0x8F8F69..0x8F8FC9; the original x86 from 0x8F8FCA on is intact:
        # switch(id) -> malloc(size) + stage ctor -> [esi+D4], stage->vf44 (OnEnter), CALog "Sg - INT", [esi+E8]=0.
        # vmtrace 8F8F69: [esi+D8] 0x17 -> id (nothing native writes it except the ctor sub_8F9800),
        # [esi+DC] = previous id (read by GetPrevStage 0x8F889A, e.g. CHiddenCatchSinglePrepareStage__vf124 == 13).
        # Context at the site: esi = CMainWnd, ebx = new id ([ebp+8]), edi = 0 (used as arg at 0x8F8FD0).
        asm=f"""
            mov eax, dword ptr [esi + 0xD8]
            mov dword ptr [esi + 0xDC], eax
            mov dword ptr [esi + 0xD8], ebx
            jmp {0x8F8FCA:#x}
        """,
    ),
    # Main loop sub_8F4D01 (CMainSystem::Run, ecx = dword_E6092C, [ebp-0x280] = this). Evidence for these blocks:
    # full-memory snapshots of the original client at the site/continuation (tools/launcher/snap.c, win/snap.bat)
    # + emulation of the VM on the snapshot (tools/vmemu.py --snap ... --run-natives); emulated frame/global diff
    # matches the real post snapshot (tools/snapdiff.py). Anti-cheat / integrity parts are dropped:
    #   sub_A12E50 (anti-cheat init: drops %TEMP%\drc*.tmp DLL and loads it), sub_A14800 (hash of a table of all
    #   VM entry stubs, kept in locals ebp-0xCC..-0x68), sub_A13A10 (checksum of .text 0x401324+0x1266FA).
    dict(
        site=0x8F4D46, cont=0x8F5468, func="sub_8F4D01 main loop: init before the loop",
        # only native-visible effect: [ebp-0xA8] = malloc(0x2B4) zeroed (freed at function exit 0x8F6CE2)
        asm=f"""
            push 0x2B4
            call {0x9E30F2:#x}
            add esp, 4
            mov dword ptr [ebp - 0xA8], eax
            push 0x2B4
            push 0
            push eax
            call {0x9DF690:#x}
            add esp, 0xC
            jmp {0x8F5468:#x}
        """,
    ),
    dict(
        site=0x8F54E4, cont=0x8F5DFA, func="sub_8F4D01 main loop: pending stage change (CMainSystem::vf5 true)",
        # vmemu on snapshot 8F5F40 with a stage request injected (--pre-asm sub_8F391D(10)):
        # sub_A13A10 (.text checksum, dropped) then CStageMgr__ChangeStage(g_pMainWnd, sub_8F3903(this)).
        asm=f"""
            mov ecx, dword ptr [ebp - 0x280]
            call {0x8F3903:#x}
            push eax
            mov ecx, dword ptr [{0xE60838:#x}]
            call {0x8F8EEC:#x}
            jmp {0x8F5DFA:#x}
        """,
    ),
    dict(
        site=0x8F5F40, cont=0x8F6908, func="sub_8F4D01 main loop: periodic (elapsed > 0x3681) part",
        # p = new(0xC); sub_67C820(p, &[ebp-0x140]) (copy of current time); delete old CMainSystem+0xF8 (sub_8F2C6B(1));
        # CMainSystem+0xF8 = p; then same as the native else-branch 0x8F6919:
        # [ebp-0x184] = sub_9995B1(sub_412B76()); sub_441A4C(&[ebp-0x134], 1)
        asm=f"""
            push 0xC
            call {0x9DBE57:#x}
            add esp, 4
            test eax, eax
            je c_new_done
            lea edx, [ebp - 0x140]
            push edx
            mov ecx, eax
            call {0x67C820:#x}
        c_new_done:
            mov edx, dword ptr [ebp - 0x280]
            mov ecx, dword ptr [edx + 0xF8]
            mov dword ptr [edx + 0xF8], eax
            test ecx, ecx
            je c_old_done
            push 1
            call {0x8F2C6B:#x}
        c_old_done:
            call {0x412B76:#x}
            mov ecx, eax
            call {0x9995B1:#x}
            mov dword ptr [ebp - 0x184], eax
            push 1
            lea ecx, [ebp - 0x134]
            call {0x441A4C:#x}
            jmp {0x8F6908:#x}
        """,
    ),
    dict(
        site=0x8F346C, cont=0x8F38F3, func="sub_8F3409 (CMainSystem::vf10, every 5 s): keep-alive",
        # vmemu on snapshot 8F346C (frame diff == real post): CSendPacket at [ebp-0x50] (0x2C bytes),
        # SendPkt__Begin(0xF); Encode4([ebp-0x1C] time, [ebp-0x18], [ebp-0x24]) (the 3 values computed right before
        # the site: time, [EA6FF0+0x1C], [EA6FF0+0x20]); Send; dtor; sub_8F2803(sub_8E1C72()) ([EA6FF0+0x24]=1);
        # CMainSystem+0x48 = time. Dropped: rand()-driven HackShield checks (sub_8E31C0 object, sub_4AEAB0/sub_900D7C x6).
        asm=f"""
            lea ecx, [ebp - 0x50]
            push 0xF
            call {0x888462:#x}
            push dword ptr [ebp - 0x1C]
            lea ecx, [ebp - 0x50]
            call {0xA65280:#x}
            push dword ptr [ebp - 0x18]
            lea ecx, [ebp - 0x50]
            call {0xA65280:#x}
            push dword ptr [ebp - 0x24]
            lea ecx, [ebp - 0x50]
            call {0xA65280:#x}
            lea ecx, [ebp - 0x50]
            call {0x888609:#x}
            lea ecx, [ebp - 0x50]
            call {0x8884DC:#x}
            call {0x8E1C72:#x}
            mov ecx, eax
            call {0x8F2803:#x}
            mov ecx, dword ptr [ebp - 0xCC]
            mov eax, dword ptr [ebp - 0x1C]
            mov dword ptr [ecx + 0x48], eax
            jmp {0x8F38F3:#x}
        """,
    ),
    dict(
        site=0x9682E5, cont=0x968385, func="sub_9682DE (Init(index) of a 2-instance CGameStage member object)",
        # Reached when entering a match: CStageMgr__ChangeStage -> CGameStage ctor sub_70CBAF -> sub_9683B4 (member ctor)
        # -> sub_9682DE(this, 0); also sub_71A9EC (game reset) calls it for both instances with index 0 and 1.
        # The whole body (0x9682E5..0x968372) is virtualized; native code resumes at the epilog 0x968385
        # (pop edi/esi/ebp; ret 4). Layout from the ctor sub_9683B4 / dtor sub_968236: u8 box +0, u32 boxes +12/+24,
        # boxes +36/+48, sub-readers +60/+96, two sub_965B1F containers, object +0xB4 — the ctor already builds every
        # box with 0. NOT recovered from a trace (no snapshot yet): minimal equivalent = store the index in the u8 box
        # (setter sub_414059, __thiscall, ret 4). Context at the site: esi = this, [ebp+8] = index.
        asm=f"""
            movzx eax, byte ptr [ebp + 8]
            push eax
            mov ecx, esi
            call {0x414059:#x}
            jmp {0x968385:#x}
        """,
    ),
]


# Trampoline hooks: overwrite `olen` original bytes at `site` (whose original bytes must equal `orig`) with a
# `jmp cave` (+nop padding). The cave (in .devirt) runs `asm` then continues; `asm` must replicate whatever the
# overwritten instruction(s) did and end by jumping back to site+olen. Unlike BLOCKS these do not require a VM jmp.
HOOKS = [
    dict(
        site=0x854B5B, olen=5, orig="e8d0d92000",
        name="CSelectServerStage__On_16: auto-rebuild channel slots after channel status arrives",
        # On_16 (0x854ADC) is the stage's opcode-16 (channel-status) handler. It stores the per-channel user
        # counts but never repopulates the slot list, so channels that arrive (opcode 14) only after the stage's
        # OnEnter built the (empty) slot list stay hidden until the player clicks a category tab (fires event 900 ->
        # sub_85718D). We replicate the overwritten `call sub_A62530(&v6)` (blob dtor, ecx already = &v6), then call
        # sub_85718D(stage, 0) to rebuild the slot array (stage+0x4C6C) for tab 0 -> channels show with no click.
        # stage = *(g_pMainWnd+0xD4), g_pMainWnd = dword_E60838. sub_85718D is __thiscall(this=stage, tab) (ret 4).
        asm=f"""
            call {0xA62530:#x}
            pushad
            pushfd
            mov eax, dword ptr [{0xE60838:#x}]
            test eax, eax
            jz hk16_done
            mov eax, dword ptr [eax + 0xD4]
            test eax, eax
            jz hk16_done
            push 0
            mov ecx, eax
            call {0x85718D:#x}
        hk16_done:
            popfd
            popad
            jmp {0x854B60:#x}
        """,
    ),
]


def main(src, dst):
    import keystone, pefile
    pe = pefile.PE(src)
    base = pe.OPTIONAL_HEADER.ImageBase
    data = bytearray(open(src, "rb").read())
    ks = keystone.Ks(keystone.KS_ARCH_X86, keystone.KS_MODE_32)

    last = pe.sections[-1]
    sec_rva = (last.VirtualAddress + max(last.Misc_VirtualSize, last.SizeOfRawData) + 0xFFF) & ~0xFFF
    code = bytearray()
    for b in BLOCKS:
        va = base + sec_rva + len(code)
        enc, _ = ks.asm(b["asm"], va)
        code += bytes(enc)
        while len(code) % 16:
            code += b"\xCC"
        o = pe.get_offset_from_rva(b["site"] - base)
        if data[o] != 0xE9:
            sys.exit(f"site {b['site']:#x}: not a jmp ({data[o:o+5].hex()})")
        data[o:o + 5] = b"\xE9" + struct.pack("<i", va - (b["site"] + 5))
        for addr, blob in b.get("data", {}).items():
            off = pe.get_offset_from_rva(addr - base)
            data[off:off + len(blob)] = blob
        print(f"devirt {b['site']:#x} -> {va:#x} ({b['func']})")

    for h in HOOKS:
        va = base + sec_rva + len(code)
        enc, _ = ks.asm(h["asm"], va)
        code += bytes(enc)
        while len(code) % 16:
            code += b"\xCC"
        o = pe.get_offset_from_rva(h["site"] - base)
        cur = bytes(data[o:o + h["olen"]]).hex()
        if cur != h["orig"]:
            sys.exit(f"hook {h['site']:#x}: unexpected bytes {cur} (want {h['orig']}) -- wrong binary?")
        if h["olen"] < 5:
            sys.exit(f"hook {h['site']:#x}: olen {h['olen']} < 5, no room for jmp")
        data[o:o + 5] = b"\xE9" + struct.pack("<i", va - (h["site"] + 5))
        data[o + 5:o + h["olen"]] = b"\x90" * (h["olen"] - 5)
        print(f"hook  {h['site']:#x} -> {va:#x} ({h['name']})")

    fa = pe.OPTIONAL_HEADER.FileAlignment
    raw_size = (len(code) + fa - 1) // fa * fa
    raw_ptr = (len(data) + fa - 1) // fa * fa
    data += b"\0" * (raw_ptr - len(data)) + bytes(code) + b"\0" * (raw_size - len(code))
    hdr = pe.sections[-1].get_file_offset() + 40
    if hdr + 40 > pe.sections[0].PointerToRawData:
        sys.exit("no room for section header")
    data[hdr:hdr + 40] = struct.pack("<8sIIIIIIHHI", b".devirt\0", len(code), sec_rva, raw_size, raw_ptr, 0, 0, 0, 0, 0x60000020)
    out = pefile.PE(data=bytes(data))
    out.FILE_HEADER.NumberOfSections += 1
    out.OPTIONAL_HEADER.SizeOfImage = (sec_rva + len(code) + 0xFFF) & ~0xFFF
    out.write(dst)
    print(f"wrote {dst}: {len(BLOCKS)} block(s), .devirt @ {base + sec_rva:#x}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
