/* boomlaunch: start the ORIGINAL Themida-protected ca.exe and patch it in memory once Themida
 * has decrypted the image (same patches as tools/patch_client.py, but the file on disk is untouched).
 *   boomlaunch.exe [server_ip] [ca.exe args...]      default server_ip = 127.0.0.1
 * Build: i686-w64-mingw32-gcc -O2 -o boomlaunch.exe boomlaunch.c
 */
#include <windows.h>
#include <stdio.h>
#include <string.h>

typedef struct { DWORD va; const char *old; const char *new_; int len; int done; } Patch;

static const char *IPS[][2] = {   /* va, original string (see tools/patch_client.py IP_STRINGS) */
    {(const char *)0xC88930, "222.255.122.204"}, {(const char *)0xC88920, "120.138.77.22"},
    {(const char *)0xC88910, "120.138.77.23"},   {(const char *)0xC88900, "120.138.77.24"},
    {(const char *)0xC888F0, "120.138.77.25"},   {(const char *)0xC888E0, "120.138.77.83"},
    {(const char *)0xC888D0, "120.138.77.84"},   {(const char *)0xC888C0, "120.138.77.85"},
    {(const char *)0xC7C638, "118.102.5.126"},   {(const char *)0xC83534, "175.207.3.35"},
};

int main(int argc, char **argv) {
    const char *ip = argc > 1 ? argv[1] : "127.0.0.1";
    char cmd[2048] = "ca.exe";
    for (int i = 2; i < argc; i++) { strcat(cmd, " "); strcat(cmd, argv[i]); }

    Patch p[16]; int np = 0;
    static char ipbuf[16][32];
    p[np++] = (Patch){0x8E701D, "\x74\x29", "\xEB\x29", 2, 0};          /* skip HackShield/BlackCipher */
    for (int i = 0; i < 10; i++) {
        int n = (int)strlen(IPS[i][1]);
        memset(ipbuf[i], 0, sizeof ipbuf[i]);
        strncpy(ipbuf[i], ip, n);
        p[np++] = (Patch){(DWORD)(size_t)IPS[i][0], IPS[i][1], ipbuf[i], n + 1, 0};
    }

    STARTUPINFOA si = {sizeof si}; PROCESS_INFORMATION pi;
    if (!CreateProcessA(NULL, cmd, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi)) {
        printf("CreateProcess failed: %lu\n", GetLastError()); return 1;
    }
    DWORD t0 = GetTickCount(); int left = np;
    while (left && GetTickCount() - t0 < 30000) {
        for (int k = 0; k < np; k++) {
            if (p[k].done) continue;
            char cur[64]; SIZE_T r = 0;
            if (!ReadProcessMemory(pi.hProcess, (LPCVOID)(size_t)p[k].va, cur, p[k].len, &r) || r != (SIZE_T)p[k].len) continue;
            if (memcmp(cur, p[k].new_, p[k].len) == 0) { p[k].done = 1; left--; continue; }
            if (memcmp(cur, p[k].old, p[k].len) != 0) continue;
            DWORD op, tmp; SIZE_T w = 0;
            VirtualProtectEx(pi.hProcess, (LPVOID)(size_t)p[k].va, p[k].len, PAGE_EXECUTE_READWRITE, &op);
            BOOL ok = WriteProcessMemory(pi.hProcess, (LPVOID)(size_t)p[k].va, p[k].new_, p[k].len, &w);
            VirtualProtectEx(pi.hProcess, (LPVOID)(size_t)p[k].va, p[k].len, op, &tmp);
            FlushInstructionCache(pi.hProcess, (LPCVOID)(size_t)p[k].va, p[k].len);
            printf("patch %08lX %s at %lums\n", p[k].va, ok ? "ok" : "FAILED", GetTickCount() - t0);
            fflush(stdout);
            p[k].done = 1; left--;
        }
        Sleep(0);
    }
    if (left) printf("%d patches not applied (timeout)\n", left);
    WaitForSingleObject(pi.hProcess, INFINITE);
    DWORD code; GetExitCodeProcess(pi.hProcess, &code);
    printf("ca.exe exited with %lu\n", code);
    return 0;
}
