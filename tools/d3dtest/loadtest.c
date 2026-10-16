#include <windows.h>
#include <stdio.h>
int main(void) {
    FILE *f = fopen("d3dtest.log", "w");
    const char *n[] = {"ucrtbase.dll", "libgallium_wgl.dll", "opengl32.dll", "wined3d.dll", "d3d9.dll"};
    for (int i = 0; i < 5; i++) { fprintf(f, "load %s ...", n[i]); fflush(f); HMODULE h = LoadLibraryA(n[i]); fprintf(f, " %p err=%lu\n", h, GetLastError()); fflush(f); }
    fclose(f); return 0;
}
