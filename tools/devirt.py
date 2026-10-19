"""Replace Themida-virtualized blocks of the dump with hand-written equivalents.

usage: python3 tools/devirt.py ca_fixed.exe ca_devirt.exe
(called by tools/rebuild_wine.sh between fix_iat.py build and patch_client.py)

Each block in BLOCKS: the VM site's `jmp 0x13xxxxx` is redirected to new code in a `.devirt` section;
the new code does what the VM block did and jumps to the continuation. Static results (tables, constants)
are written straight into the image. Evidence for every block: tools/vmtrace.py on the original client,
see /home/admin/boom-rs/docs/research/findings/VN_DEVIRT_STATUS.md.
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
        site=0x9682E5, cont=0x968385, func="sub_9682DE (Init(index) of the 2-instance CGameStage member object)",
        # Evidence: tools/vmemu.py on logs/snap/8F5F40/pre.snap, ctor sub_9683B4 and a direct call Init(1) on a zero object: the VM only
        # calls these natives (12 calls, same sequence for index 0 and 1; the first argument is the index): box setters/resets of every
        # member. Object layout: +0 u8 box (sub_414059), +0xC/+0x18 u32 boxes (sub_413F32 = -1), +0x24/+0x30 (sub_41411C = 0),
        # +0x60/+0x3C sub-readers (sub_A62630), +0x84/+0x90/+0x9C/+0xA8 u32 boxes (sub_413F32 = -1), +0xB4 object (sub_50BA05).
        # Context at the site: esi = this, [ebp+8] = index; ebx is not used.
        asm=f"""
            push dword ptr [ebp + 8]
            mov ecx, esi
            call {0x414059:#x}
            push -1
            lea ecx, [esi + 0xC]
            call {0x413F32:#x}
            push -1
            lea ecx, [esi + 0x18]
            call {0x413F32:#x}
            push 0
            lea ecx, [esi + 0x24]
            call {0x41411C:#x}
            push 0
            lea ecx, [esi + 0x30]
            call {0x41411C:#x}
            lea ecx, [esi + 0x60]
            call {0xA62630:#x}
            lea ecx, [esi + 0x3C]
            call {0xA62630:#x}
            push -1
            lea ecx, [esi + 0x84]
            call {0x413F32:#x}
            push -1
            lea ecx, [esi + 0x90]
            call {0x413F32:#x}
            push -1
            lea ecx, [esi + 0x9C]
            call {0x413F32:#x}
            push -1
            lea ecx, [esi + 0xA8]
            call {0x413F32:#x}
            lea ecx, [esi + 0xB4]
            call {0x50BA05:#x}
            jmp {0x968385:#x}
        """,
    ),
    dict(
        site=0x736C27, cont=0x736D6C, func="CGamePlayMap__Load success tail (skip, emulated: no effect for room 19 / Village01)",
        # Themida chunk spans 0x736C27..0x736D5A (marker EB 10 57 4C 20 at 0x736D5A, 16 bytes mutated);
        # native visible ONLY from marker end 0x736D6C: mov ecx,[0xE60884]; call sub_8EC54D; mov bl,1;
        # jmp loc_736B2C (cleanup path) -> mov al,bl -> epilog. cont reads NO incoming registers (ecx/bl
        # clobbered right away; cleanup uses only ebp-locals alreadly initialized) -> a plain jmp is a valid
        # no-op substitute for the chunk. Chunk's own work (registering the fresh 0x90 ctor object for room
        # kinds 20/33, unknown for others) dropped on purpose; room type 19 needs none of it.
        # 2026-10-18: emulated (tools/vmemu.py on logs/snap/8F5F40/pre.snap + live dump of the CGamePlayMap object
        # logs/mapdump/map.bin (11 MB at ebx) + the Load frame logs/mapdump/stack.bin, tools/gdb/dump_map.gdb): the chunk only
        # calls the box getter sub_414543(ebx + 0x8F480C) and sets the loop counter [ebp-0x308] = 0 (not read after cont), i.e. a
        # loop with 0 iterations for this map/room. The loop body for other maps/room kinds is still unknown.
        asm=f"""
            jmp {0x736D6C:#x}
        """,
    ),
    dict(
        site=0x6EFD4A, cont=0x6EFEDC, func="sub_6EFD24 (CGameMsgCache ring-table setter used by bomb placement)",
        # Evidence: tools/vmemu.py on a pre-snapshot of the original client (logs/snap/8F5F40/pre.snap) with a hand-built
        # frame (12 args, this = CGameMsgCache, vectors this+0x34 / this+0x44, this+0xF4): the VM calls sub_421AB9(this+0x44,
        # slot) [count vector operator[]], sub_6EEED9(this+0x34, ...) [record vector operator[]], sub_6EFBCA() [session key = stage this[4887]], writes a
        # 0x44-byte record, ++count[slot], and calls sub_6EFC07(slot) unless (arg_2C & 4). Field mapping verified with distinct
        # arg values (/home/admin/boom-rs/docs/archive/re/VM_6EFD4A_INPUTS.md section 8). Same record/ring as the native 16-arg sibling sub_6EFEE3 (flush
        # vf8 -> C->S 111), minus its four fields +0x20..+0x2C. Return value = leftover eax (6EFC07's pointer, or arg_2C).
        # Context at the site: this at [ebp-0x24], arg_k at [ebp+8+k]; ebx/esi/edi are saved by the prolog.
        asm=f"""
            mov ebx, dword ptr [ebp - 0x24]
            mov esi, dword ptr [ebp + 0xC]
            mov eax, dword ptr [ebx + 0x44]
            lea edi, [eax + esi*4]
            mov esi, dword ptr [ebx + 0x10]
            imul esi, dword ptr [ebp + 0xC]
            add esi, dword ptr [edi]
            imul esi, esi, 0x44
            add esi, dword ptr [ebx + 0x34]
            call {0x6EFBCA:#x}
            mov dword ptr [esi + 8], eax
            mov dword ptr [esi + 4], 1
            mov eax, dword ptr [ebp + 8]
            mov dword ptr [esi], eax
            mov eax, dword ptr [ebp + 0x10]
            mov dword ptr [esi + 0xC], eax
            mov eax, dword ptr [ebp + 0x18]
            mov dword ptr [esi + 0x10], eax
            mov eax, dword ptr [ebp + 0x1C]
            mov dword ptr [esi + 0x14], eax
            mov eax, dword ptr [ebp + 0x20]
            mov dword ptr [esi + 0x18], eax
            mov eax, dword ptr [ebp + 0x24]
            mov dword ptr [esi + 0x1C], eax
            mov al, byte ptr [ebp + 0x14]
            mov byte ptr [esi + 0x30], al
            mov eax, dword ptr [ebp + 0x28]
            mov dword ptr [esi + 0x34], eax
            mov eax, dword ptr [ebp + 0x2C]
            mov dword ptr [esi + 0x38], eax
            mov eax, dword ptr [ebp + 0x30]
            mov dword ptr [esi + 0x3C], eax
            mov al, byte ptr [ebp + 0x34]
            mov byte ptr [esi + 0x40], al
            inc dword ptr [edi]
            movzx eax, byte ptr [ebp + 0x34]
            test al, 4
            jnz d24_done
            push dword ptr [ebp + 0xC]
            mov ecx, ebx
            call {0x6EFC07:#x}
        d24_done:
            jmp {0x6EFEDC:#x}
        """,
    ),
    dict(
        site=0x5a6e89, cont=0x5a6f64, func="CGOBomber__vf21 random check (skip)",
        # guard: [esi+0x2718] counter, rand()%1001 < ebx -> VM (anti-cheat style sampling).
        # The native code in front takes `jge cont` for ~99% of the calls (rand() % N >= threshold), so the original game runs
        # without this VM chunk almost always; a plain jmp is the common path. (/home/admin/boom-rs/docs/archive/re/VM_TRIAGE_HISTORY.md, class S.)
        asm=f"""
            jmp {0x5a6f64:#x}
        """,
    ),
    dict(
        site=0x6f287e, cont=0x6f2923, func="sub_6F27EE random tail (skip)",
        # guard: rand()%999 >= 10 -> cont; the struct setter work before the site is native.
        # The native code in front takes `jge cont` for ~99% of the calls (rand() % N >= threshold), so the original game runs
        # without this VM chunk almost always; a plain jmp is the common path. (/home/admin/boom-rs/docs/archive/re/VM_TRIAGE_HISTORY.md, class S.)
        asm=f"""
            jmp {0x6f2923:#x}
        """,
    ),
    dict(
        site=0x754c82, cont=0x754d20, func="CMapScriptStageClear__vf7 random check in NPC loop (skip)",
        # guard: rand()%995 >= 10 -> cont (loop over NPC objects).
        # The native code in front takes `jge cont` for ~99% of the calls (rand() % N >= threshold), so the original game runs
        # without this VM chunk almost always; a plain jmp is the common path. (/home/admin/boom-rs/docs/archive/re/VM_TRIAGE_HISTORY.md, class S.)
        asm=f"""
            jmp {0x754d20:#x}
        """,
    ),
    dict(
        site=0x71581A, cont=0x7158E4, func="sub_71580C (CGameStage__OnPacket case 552 handler)",
        # Evidence: tools/vmemu.py on logs/snap/8F5F40/pre.snap + a gdb dump of the live CGameStage (tools/gdb/dump_stage.gdb ->
        # logs/stagedump/stage.bin, --overlay), fake packet (+0x10 buf, +0x20 limit, +0x24 cursor, +0x28 mode). The VM only makes these
        # native calls, in this order, unconditionally (same sequence for different packet values; no direct writes):
        #   CGameMsgCache__vf3(this + 0x4AC0, 1); RecvPkt__Decode4(packet) [result unused]; sub_711E7F(this); sub_708192(this);
        #   sub_414543(this + 0x4AB4) [Themida check hub]; sub_705F63(this). The three CGameStage methods are mutated (not VM) code.
        # Context at the site: esi = this (CGameStage), [ebp+8] = packet (RecvPkt*). Return value is junk (ignored by the dispatcher).
        asm=f"""
            lea ecx, [esi + 0x4AC0]
            push 1
            call {0x6F292B:#x}
            mov ecx, dword ptr [ebp + 8]
            call {0xA65750:#x}
            mov ecx, esi
            call {0x711E7F:#x}
            mov ecx, esi
            call {0x708192:#x}
            lea ecx, [esi + 0x4AB4]
            call {0x414543:#x}
            mov ecx, esi
            call {0x705F63:#x}
            jmp {0x7158E4:#x}
        """,
    ),
    dict(
        site=0x8E5519, cont=0x8E5547, func="CFxApp__vf6 shutdown tail (skip)",
        # CFxApp__vf6 (0x8E50D1) is the app SHUTDOWN: it walks every global singleton and calls its deleting destructor (vf0(1)),
        # guarded by Feature_IsDisabled(0xB8/0x3C). The chunk at 0x8E5519 (0x2E bytes) is at the very end of it; it only runs on exit,
        # so a plain jmp to the continuation (0x8E5547) is enough to avoid a crash while closing the game.
        asm=f"""
            jmp {0x8E5547:#x}
        """,
    ),
    dict(
        site=0x5788C9, cont=0x414543, func="CBombOwner__vf33 tail (EXPERIMENT: plain skip)",
        # Chunk = 0x5788C9..0x5788DB (site jmp e9 -> 0x26574543, a Themida heap-mutated module, then junk);
        # native resumes at 0x5788DC = `jmp 0x414543` (Themida check hub, returns al=0) and the next function
        # prologue starts at 0x5788E5. Mutate class: the mutated copy of the tail runs the same chain that ends
        # at jmp 0x414543, so a plain jmp preserves behavior without the heap module (not runnable inside the
        # dump -> SIGSEGV at 0x26574543 as seen in the OnEnter vf161 path).
        asm=f"""
            jmp {0x414543:#x}
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
