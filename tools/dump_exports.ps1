# Run with 32-bit PowerShell (C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe).
# Writes "module<TAB>export<TAB>hexaddr" for every export of the listed DLLs, as loaded in this boot.
param([string]$Out, [string]$GameDir)
$src = @"
using System; using System.Runtime.InteropServices; using System.Collections.Generic;
public static class Exp {
  [DllImport("kernel32", SetLastError=true, CharSet=CharSet.Ansi)] public static extern IntPtr LoadLibraryA(string n);
  public static List<string> Dump(string name) {
    var r = new List<string>(); IntPtr b = LoadLibraryA(name); if (b == IntPtr.Zero) { r.Add(name + "\t!LOADFAIL\t0"); return r; }
    int pe = Marshal.ReadInt32(b, 0x3C); int ed = Marshal.ReadInt32(b, pe + 0x78); int edSz = Marshal.ReadInt32(b, pe + 0x7C); if (ed == 0) return r;
    int nNames = Marshal.ReadInt32(b, ed + 0x18), nFuncs = Marshal.ReadInt32(b, ed + 0x14), ordBase = Marshal.ReadInt32(b, ed + 0x10);
    int aF = Marshal.ReadInt32(b, ed + 0x1C), aN = Marshal.ReadInt32(b, ed + 0x20), aO = Marshal.ReadInt32(b, ed + 0x24);
    var named = new HashSet<int>();
    for (int i = 0; i < nNames; i++) {
      string fn = Marshal.PtrToStringAnsi(new IntPtr(b.ToInt32() + Marshal.ReadInt32(b, aN + 4 * i)));
      int ord = Marshal.ReadInt16(b, aO + 2 * i) & 0xFFFF; named.Add(ord);
      int rva = Marshal.ReadInt32(b, aF + 4 * ord);
      if (rva >= ed && rva < ed + edSz) r.Add(name + "\t" + fn + "\tFWD:" + Marshal.PtrToStringAnsi(new IntPtr(b.ToInt32() + rva)));
      else r.Add(name + "\t" + fn + "\t" + (b.ToInt32() + rva).ToString("x"));
    }
    for (int o = 0; o < nFuncs; o++) if (!named.Contains(o)) {
      int rva = Marshal.ReadInt32(b, aF + 4 * o); if (rva != 0) r.Add(name + "\t#" + (o + ordBase) + "\t" + (b.ToInt32() + rva).ToString("x"));
    }
    return r;
  }
}
"@
Add-Type -TypeDefinition $src
Set-Location $GameDir
$dlls = @('kernel32.dll','KernelBase.dll','ntdll.dll','user32.dll','gdi32.dll','gdi32full.dll','advapi32.dll','shell32.dll','ole32.dll','oleaut32.dll',
  'combase.dll','ws2_32.dll','wininet.dll','winmm.dll','comctl32.dll','imagehlp.dll','IPHLPAPI.DLL','version.dll','msvcrt.dll','ucrtbase.dll',
  'shlwapi.dll','sechost.dll','rpcrt4.dll','win32u.dll','imm32.dll','dbghelp.dll','psapi.dll','crypt32.dll','wsock32.dll','dsound.dll','d3d9.dll','ddraw.dll',
  "$GameDir\d3dx9_30.dll","$GameDir\binkw32.dll","$GameDir\mss32.dll","$GameDir\nmco3.dll","$GameDir\dwk.dll","$GameDir\ijl15.dll",
  "$GameDir\npa.dll","$GameDir\nda.dll","$GameDir\dtm.dll")
$lines = foreach ($d in $dlls) { [Exp]::Dump($d) }
$lines | Set-Content -Encoding ASCII $Out
"[$([IntPtr]::Size*8)-bit] wrote $($lines.Count) exports" | Add-Content -Encoding ASCII "$Out.log"
