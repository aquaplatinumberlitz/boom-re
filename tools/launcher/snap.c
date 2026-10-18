/* snap: run the ORIGINAL ca.exe and take a FULL memory snapshot when execution reaches a VM site
 * (so the Themida VM block can be emulated off-line with its real runtime state: tools/vmemu.py --snap).
 *
 *   snap.exe <outdir> <site_hex> [cont_hex] [timeout_ms] [extra patches va:old:new ...]
 *
 * - waits for Themida to decrypt .text, applies extra patches (e.g. 8E701D:7429:EB29 = skip HackShield),
 * - site must start with `jmp rel32` (E9, the VM entry jmp): replaced by `jmp cave_pre`,
 *   cave_pre: pushfd/pushad, save regs + TEB, flag=1, spin until flag==2, restore, jmp <original target>
 * - when flag==1: suspend every thread, dump all committed readable memory -> <outdir>\pre.snap, resume (flag=2)
 * - if cont is given (an address after the block whose first instruction is >=5 bytes long or a known
 *   instruction run — we copy 'contlen' bytes, see below), it is hooked the same way -> <outdir>\post.snap
 *   (cont hook: `jmp cave_post`, cave_post saves regs, flag=3, spin until 4, restore, executes the
 *    relocated original bytes passed as patch "cont" and jumps back). For simplicity the post hook only
 *    records registers (post.regs), no full dump.
 * Snapshot file: "BSNP" u32 version=1, u32 nregions, then per region {u32 base, u32 size, u32 protect, u32 type}
 *   followed by data; regs block (pre.regs): edi esi ebp esp ebx edx ecx eax eflags teb (10 dwords).
 * Build: i686-w64-mingw32-gcc -O2 -o snap.exe snap.c
 */
#include <windows.h>
#include <tlhelp32.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CAVE 0x30000000u
#define OFF_FLAG 0xFF0
#define OFF_REGS 0x800   /* pre: 10 dwords */
#define OFF_PREGS 0x840  /* post: 10 dwords */

typedef struct { DWORD va; BYTE old[32], nw[32]; int len, done; } Patch;
static int hexbytes(const char *s, BYTE *out) { int n = 0; while (s[0] && s[1] && s[0] != '\n' && s[0] != '\r') { sscanf(s, "%2hhx", &out[n++]); s += 2; } return n; }

static BYTE cave[0x1000]; static int cl;
static void emit(const void *b, int n) { memcpy(cave + cl, b, n); cl += n; }
static void emit1(BYTE b) { emit(&b, 1); }
static void emit4(DWORD d) { emit(&d, 4); }
static void jmp_to(DWORD target) { emit1(0xE9); emit4(target - (CAVE + cl + 4)); }

/* pushfd; pushad; mov eax,fs:[18h]; mov [regs+36],eax; esi=esp; edi=regs; ecx=9; rep movsd;
   mov dword [flag], set; spin: pause; cmp dword [flag], wait; jne spin; popad; popfd */
static void snap_stub(DWORD regs, DWORD set, DWORD wait) {
    emit1(0x9C); emit1(0x60);
    emit("\x64\xA1\x18\x00\x00\x00", 6);                 /* mov eax, fs:[18h] */
    emit1(0xA3); emit4(regs + 36);                        /* mov [regs+36], eax */
    emit("\x89\xE6", 2); emit1(0xBF); emit4(regs);        /* mov esi, esp; mov edi, regs */
    emit1(0xB9); emit4(9); emit("\xFC\xF3\xA5", 3);       /* mov ecx, 9; cld; rep movsd */
    emit("\xC7\x05", 2); emit4(CAVE + OFF_FLAG); emit4(set);
    int spin = cl;
    emit("\xF3\x90", 2);                                  /* pause */
    emit("\x81\x3D", 2); emit4(CAVE + OFF_FLAG); emit4(wait);
    emit("\x75", 1); emit1((BYTE)(spin - (cl + 1)));      /* jne spin */
    emit1(0x61); emit1(0x9D);
}

static void suspend_all(DWORD pid, int resume) {
    HANDLE s = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0); THREADENTRY32 te = {sizeof te};
    for (BOOL ok = Thread32First(s, &te); ok; ok = Thread32Next(s, &te)) {
        if (te.th32OwnerProcessID != pid) continue;
        HANDLE t = OpenThread(THREAD_SUSPEND_RESUME, FALSE, te.th32ThreadID);
        if (t) { if (resume) ResumeThread(t); else SuspendThread(t); CloseHandle(t); }
    }
    CloseHandle(s);
}

static void dump_all(HANDLE h, const char *path, DWORD *regs) {
    FILE *f = fopen(path, "wb"); DWORD hdr[3] = {0x504E5342, 1, 0}; fwrite(hdr, 4, 3, f);
    fwrite(regs, 4, 10, f);
    MEMORY_BASIC_INFORMATION mbi; DWORD a = 0x10000, n = 0; unsigned long long total = 0;
    BYTE *buf = malloc(0x100000);
    while (a < 0x7FFF0000 && VirtualQueryEx(h, (LPCVOID)(size_t)a, &mbi, sizeof mbi)) {
        DWORD base = (DWORD)(size_t)mbi.BaseAddress, size = (DWORD)mbi.RegionSize;
        int readable = mbi.State == MEM_COMMIT && !(mbi.Protect & (PAGE_GUARD | PAGE_NOACCESS)) && mbi.Protect;
        if (readable && !(mbi.Type == MEM_MAPPED && size > 0x2000000)) {
            DWORD rh[4] = {base, size, mbi.Protect, mbi.Type}; fwrite(rh, 4, 4, f);
            for (DWORD o = 0; o < size; o += 0x100000) {
                DWORD c = size - o < 0x100000 ? size - o : 0x100000; SIZE_T r = 0;
                if (!ReadProcessMemory(h, (LPCVOID)(size_t)(base + o), buf, c, &r) || r != c) memset(buf + r, 0, c - r);
                fwrite(buf, 1, c, f);
            }
            n++; total += size;
        }
        a = base + size;
    }
    fseek(f, 8, SEEK_SET); fwrite(&n, 4, 1, f); fclose(f); free(buf);
    printf("dumped %lu regions, %llu MB -> %s\n", n, total >> 20, path); fflush(stdout);
}

int main(int argc, char **argv) {
    if (argc < 3) { printf("usage: snap outdir site [cont|-] [timeout_ms] [va:old:new ...]\n"); return 1; }
    const char *dir = argv[1]; DWORD site = strtoul(argv[2], 0, 16);
    DWORD cont = (argc > 3 && argv[3][0] != '-') ? strtoul(argv[3], 0, 16) : 0;
    DWORD timeout = argc > 4 ? strtoul(argv[4], 0, 10) : 120000;
    Patch p[48]; int np = 0;
    for (int i = 5; i < argc && np < 47; i++) {
        char tmp[200]; strncpy(tmp, argv[i], sizeof tmp - 1); tmp[sizeof tmp - 1] = 0;
        char *a = strtok(tmp, ":"), *o = strtok(0, ":"), *n = strtok(0, ":");
        if (!a || !o || !n) continue;
        p[np].va = strtoul(a, 0, 16); p[np].len = hexbytes(o, p[np].old); hexbytes(n, p[np].nw); p[np].done = 0; np++;
    }

    STARTUPINFOA si = {sizeof si}; PROCESS_INFORMATION pi;
    if (!CreateProcessA(NULL, "ca.exe", NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi)) { printf("CreateProcess %lu\n", GetLastError()); return 1; }
    VirtualAllocEx(pi.hProcess, (LPVOID)CAVE, 0x1000, MEM_RESERVE | MEM_COMMIT, PAGE_EXECUTE_READWRITE);

    /* site must be E9 rel32 once decrypted; wait for it, then build cave with the real target */
    DWORD t0 = GetTickCount(); BYTE sb[5]; SIZE_T r;
    for (;;) {
        if (ReadProcessMemory(pi.hProcess, (LPCVOID)(size_t)site, sb, 5, &r) && sb[0] == 0xE9) {
            DWORD tgt = site + 5 + *(int *)(sb + 1);
            if (tgt >= 0x11E4000 && tgt < 0x16AB000) break;
        }
        if (GetTickCount() - t0 > 30000) { printf("site never decrypted (%02x)\n", sb[0]); TerminateProcess(pi.hProcess, 0); return 1; }
        Sleep(0);
    }
    DWORD target = site + 5 + *(int *)(sb + 1);
    cl = 0x10;
    DWORD pre = CAVE + cl; snap_stub(CAVE + OFF_REGS, 1, 2); jmp_to(target);
    DWORD post = 0;
    if (cont) {
        /* cont hook: patch "cont" with jmp cave_post; cave_post re-executes the overwritten bytes, which the
           caller must pass as patch  <cont>:<oldbytes>:-  (old bytes are relocated: only position-independent
           instructions allowed, checked by tools/vmtrace.py build). Here: record regs only. */
        for (int k = 0; k < np; k++) if (p[k].va == cont) {
            post = CAVE + cl; snap_stub(CAVE + OFF_PREGS, 3, 4); /* never resumes (nobody writes 4) */
            p[k].len = p[k].len; /* old bytes */
            BYTE j[5] = {0xE9}; *(DWORD *)(j + 1) = post - (cont + 5);
            memset(p[k].nw, 0x90, p[k].len); memcpy(p[k].nw, j, 5);
        }
    }
    SIZE_T w; WriteProcessMemory(pi.hProcess, (LPVOID)CAVE, cave, sizeof cave, &w);
    BYTE j[5] = {0xE9}; *(DWORD *)(j + 1) = pre - (site + 5);
    p[np].va = site; memcpy(p[np].old, sb, 5); memcpy(p[np].nw, j, 5); p[np].len = 5; p[np].done = 0; np++;

    int left = np;
    while (left && GetTickCount() - t0 < 30000) {
        for (int k = 0; k < np; k++) {
            if (p[k].done) continue;
            BYTE cur[32];
            if (!ReadProcessMemory(pi.hProcess, (LPCVOID)(size_t)p[k].va, cur, p[k].len, &r) || memcmp(cur, p[k].old, p[k].len)) continue;
            DWORD op, tmp;
            VirtualProtectEx(pi.hProcess, (LPVOID)(size_t)p[k].va, p[k].len, PAGE_EXECUTE_READWRITE, &op);
            BOOL ok = WriteProcessMemory(pi.hProcess, (LPVOID)(size_t)p[k].va, p[k].nw, p[k].len, &w);
            VirtualProtectEx(pi.hProcess, (LPVOID)(size_t)p[k].va, p[k].len, op, &tmp);
            FlushInstructionCache(pi.hProcess, (LPCVOID)(size_t)p[k].va, p[k].len);
            printf("patch %08lX %s at %lums\n", p[k].va, ok ? "ok" : "FAIL", GetTickCount() - t0); fflush(stdout);
            p[k].done = 1; left--;
        }
        Sleep(0);
    }

    char path[MAX_PATH]; DWORD fl = 0, regs[10]; int got_pre = 0;
    while (GetTickCount() - t0 < timeout) {
        ReadProcessMemory(pi.hProcess, (LPCVOID)(CAVE + OFF_FLAG), &fl, 4, &r);
        DWORD code; if (GetExitCodeProcess(pi.hProcess, &code) && code != STILL_ACTIVE) { printf("process exited %08lx\n", code); break; }
        if (fl == 1 && !got_pre) {
            suspend_all(pi.dwProcessId, 0);
            ReadProcessMemory(pi.hProcess, (LPCVOID)(CAVE + OFF_REGS), regs, 40, &r);
            printf("pre at %lums: edi=%08lx esi=%08lx ebp=%08lx esp=%08lx ebx=%08lx edx=%08lx ecx=%08lx eax=%08lx fl=%08lx teb=%08lx\n",
                   GetTickCount() - t0, regs[0], regs[1], regs[2], regs[3], regs[4], regs[5], regs[6], regs[7], regs[8], regs[9]); fflush(stdout);
            snprintf(path, sizeof path, "%s\\pre.snap", dir); dump_all(pi.hProcess, path, regs);
            got_pre = 1;
            if (!cont) break;
            DWORD two = 2; WriteProcessMemory(pi.hProcess, (LPVOID)(CAVE + OFF_FLAG), &two, 4, &w);
            suspend_all(pi.dwProcessId, 1);
        }
        if (fl == 3) {
            ReadProcessMemory(pi.hProcess, (LPCVOID)(CAVE + OFF_PREGS), regs, 40, &r);
            printf("post: edi=%08lx esi=%08lx ebp=%08lx esp=%08lx ebx=%08lx edx=%08lx ecx=%08lx eax=%08lx\n",
                   regs[0], regs[1], regs[2], regs[3], regs[4], regs[5], regs[6], regs[7]); fflush(stdout);
            suspend_all(pi.dwProcessId, 0);
            snprintf(path, sizeof path, "%s\\post.snap", dir); dump_all(pi.hProcess, path, regs);
            break;
        }
        Sleep(5);
    }
    printf("flag=%lu after %lums\n", fl, GetTickCount() - t0);
    TerminateProcess(pi.hProcess, 0);
    return 0;
}
