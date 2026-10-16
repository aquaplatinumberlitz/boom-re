/* Minimal D3D9 check: create window + device, clear/present a few frames, print HRESULTs.
 * Build: i686-w64-mingw32-gcc -O2 -o d3dtest.exe d3dtest.c -ld3d9 -lgdi32 */
#include <windows.h>
#include <d3d9.h>
#include <stdio.h>
static FILE *g;
static LONG CALLBACK veh(EXCEPTION_POINTERS *e) {
    fprintf(g, "EXC %08lx at %p\n", e->ExceptionRecord->ExceptionCode, e->ExceptionRecord->ExceptionAddress); fflush(g);
    return EXCEPTION_CONTINUE_SEARCH;
}
int main(void) {
    FILE *f = fopen("d3dtest.log", "w"); g = f; AddVectoredExceptionHandler(1, veh);
    fprintf(f, "start\n"); fflush(f);
    WNDCLASSA wc = {0}; wc.lpfnWndProc = DefWindowProcA; wc.hInstance = GetModuleHandleA(0); wc.lpszClassName = "t";
    RegisterClassA(&wc);
    HWND w = CreateWindowA("t", "d3dtest", WS_OVERLAPPEDWINDOW | WS_VISIBLE, 0, 0, 800, 600, 0, 0, wc.hInstance, 0);
    HMODULE m = LoadLibraryA("d3d9.dll"); fprintf(f, "d3d9 %p\n", m); fflush(f);
    IDirect3D9 *(WINAPI *create)(UINT) = (void *)GetProcAddress(m, "Direct3DCreate9");
    IDirect3D9 *d = create(D3D_SDK_VERSION);
    fprintf(f, "Direct3DCreate9 %p\n", d); fflush(f);
    if (!d) return 1;
    D3DADAPTER_IDENTIFIER9 id; IDirect3D9_GetAdapterIdentifier(d, 0, 0, &id);
    fprintf(f, "adapter: %s / %s\n", id.Description, id.Driver); fflush(f);
    D3DPRESENT_PARAMETERS pp = {0}; pp.Windowed = TRUE; pp.SwapEffect = D3DSWAPEFFECT_DISCARD; pp.BackBufferFormat = D3DFMT_UNKNOWN; pp.hDeviceWindow = w;
    IDirect3DDevice9 *dev = 0;
    HRESULT hr = IDirect3D9_CreateDevice(d, 0, D3DDEVTYPE_HAL, w, D3DCREATE_SOFTWARE_VERTEXPROCESSING, &pp, &dev);
    fprintf(f, "CreateDevice HAL/SWVP hr=%08lx\n", hr); fflush(f);
    for (int i = 0; dev && i < 60; i++) {
        IDirect3DDevice9_Clear(dev, 0, 0, D3DCLEAR_TARGET, D3DCOLOR_XRGB(0, 128, 255), 1, 0);
        hr = IDirect3DDevice9_Present(dev, 0, 0, 0, 0);
        Sleep(16);
    }
    fprintf(f, "Present hr=%08lx\n", hr); fclose(f);
    return 0;
}
