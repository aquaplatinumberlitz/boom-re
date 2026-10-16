/* inject: start the ORIGINAL ca.exe, wait for Themida to decrypt, load a code cave at a fixed address,
 * apply patches, wait for a flag in the cave, then dump the cave region to a file.
 *   inject.exe <dir>       dir contains cave.bin, patches.txt (va:oldhex:newhex per line), cfg.json values below
 *   inject.exe <dir> <base_hex> <total_hex> <flag_hex> <want_flag> <timeout_ms>
 * Build: i686-w64-mingw32-gcc -O2 -o inject.exe inject.c
 */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { DWORD va; BYTE old[32], nw[32]; int len, done; } Patch;

static int hexbytes(const char *s, BYTE *out) { int n = 0; while (s[0] && s[1] && s[0] != '\n' && s[0] != '\r') { sscanf(s, "%2hhx", &out[n++]); s += 2; } return n; }

int main(int argc, char **argv) {
    if (argc < 7) { printf("usage: inject dir base total flag want timeout_ms\n"); return 1; }
    char path[MAX_PATH]; const char *dir = argv[1];
    DWORD base = strtoul(argv[2], 0, 16), total = strtoul(argv[3], 0, 16), flag = strtoul(argv[4], 0, 16);
    DWORD want = strtoul(argv[5], 0, 10), timeout = strtoul(argv[6], 0, 10);

    snprintf(path, sizeof path, "%s\\cave.bin", dir);
    FILE *f = fopen(path, "rb"); if (!f) { printf("no cave.bin\n"); return 1; }
    BYTE cave[0x800]; size_t cl = fread(cave, 1, sizeof cave, f); fclose(f);

    Patch p[16]; int np = 0;
    snprintf(path, sizeof path, "%s\\patches.txt", dir);
    f = fopen(path, "r"); char line[256];
    while (f && fgets(line, sizeof line, f) && np < 16) {
        char *a = strtok(line, ":"), *o = strtok(0, ":"), *n = strtok(0, ":\r\n");
        if (!a || !o || !n) continue;
        p[np].va = strtoul(a, 0, 16); p[np].len = hexbytes(o, p[np].old); hexbytes(n, p[np].nw); p[np].done = 0; np++;
    }
    if (f) fclose(f);

    STARTUPINFOA si = {sizeof si}; PROCESS_INFORMATION pi;
    if (!CreateProcessA(NULL, "ca.exe", NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi)) { printf("CreateProcess %lu\n", GetLastError()); return 1; }
    LPVOID mem = VirtualAllocEx(pi.hProcess, (LPVOID)(size_t)base, total, MEM_RESERVE | MEM_COMMIT, PAGE_EXECUTE_READWRITE);
    printf("cave alloc %p (want %08lX)\n", mem, base);
    SIZE_T w; WriteProcessMemory(pi.hProcess, (LPVOID)(size_t)base, cave, cl, &w);

    DWORD t0 = GetTickCount(); int left = np;
    while (left && GetTickCount() - t0 < 30000) {
        for (int k = 0; k < np; k++) {
            if (p[k].done) continue;
            BYTE cur[32]; SIZE_T r = 0;
            if (!ReadProcessMemory(pi.hProcess, (LPCVOID)(size_t)p[k].va, cur, p[k].len, &r) || r != (SIZE_T)p[k].len) continue;
            if (memcmp(cur, p[k].old, p[k].len) != 0) continue;
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
    DWORD fl = 0; SIZE_T r;
    while (GetTickCount() - t0 < timeout) {
        ReadProcessMemory(pi.hProcess, (LPCVOID)(size_t)flag, &fl, 4, &r);
        if (fl >= want) break;
        DWORD code; if (GetExitCodeProcess(pi.hProcess, &code) && code != STILL_ACTIVE) { printf("process exited %lu\n", code); break; }
        Sleep(20);
    }
    printf("flag=%lu after %lums\n", fl, GetTickCount() - t0);
    BYTE *buf = malloc(total); SIZE_T got = 0, chunk = 0x10000;
    for (DWORD off = 0; off < total; off += chunk) { SIZE_T rr = 0; ReadProcessMemory(pi.hProcess, (LPCVOID)(size_t)(base + off), buf + off, chunk, &rr); got += rr; }
    snprintf(path, sizeof path, "%s\\dump.bin", dir);
    f = fopen(path, "wb"); fwrite(buf, 1, total, f); fclose(f);
    printf("dumped %lu bytes\n", (unsigned long)got);
    TerminateProcess(pi.hProcess, 0);
    return 0;
}
