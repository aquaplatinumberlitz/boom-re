# 32-bit PowerShell. Start ORIGINAL ca.exe and patch code in memory as soon as Themida has decrypted it.
# Patch list "va:oldhex:newhex;..." (same patches as tools/patch_client.py)
param([string]$Exe, [string]$Patches = "8E701D:7429:EB29", [string]$Log, [int]$TimeoutMs = 30000)
$src = @"
using System; using System.Runtime.InteropServices; using System.Diagnostics;
public static class L {
  [DllImport("kernel32")] static extern IntPtr OpenProcess(int a, bool i, int pid);
  [DllImport("kernel32")] static extern bool ReadProcessMemory(IntPtr h, IntPtr a, byte[] b, int n, out int r);
  [DllImport("kernel32")] static extern bool WriteProcessMemory(IntPtr h, IntPtr a, byte[] b, int n, out int w);
  [DllImport("kernel32")] static extern bool VirtualProtectEx(IntPtr h, IntPtr a, int n, int p, out int old);
  [DllImport("kernel32")] static extern bool FlushInstructionCache(IntPtr h, IntPtr a, int n);
  static byte[] Hex(string s) { var b = new byte[s.Length / 2]; for (int i = 0; i < b.Length; i++) b[i] = Convert.ToByte(s.Substring(2 * i, 2), 16); return b; }
  public static string Run(int pid, string patches, int timeoutMs) {
    IntPtr h = OpenProcess(0x1F0FFF, false, pid);
    var items = patches.Split(';'); var done = new bool[items.Length]; var sw = Stopwatch.StartNew(); string log = "";
    while (sw.ElapsedMilliseconds < timeoutMs) {
      bool all = true;
      for (int k = 0; k < items.Length; k++) {
        if (done[k]) continue; all = false;
        var f = items[k].Split(':'); var va = new IntPtr(Convert.ToInt32(f[0], 16)); var old = Hex(f[1]); var nw = Hex(f[2]);
        var cur = new byte[old.Length]; int r;
        if (!ReadProcessMemory(h, va, cur, cur.Length, out r) || r != cur.Length) continue;
        if (BitConverter.ToString(cur) == BitConverter.ToString(nw)) { done[k] = true; log += f[0] + " already\n"; continue; }
        if (BitConverter.ToString(cur) != BitConverter.ToString(old)) continue;
        int op; VirtualProtectEx(h, va, nw.Length, 0x40, out op); int w;
        bool ok = WriteProcessMemory(h, va, nw, nw.Length, out w); int tmp; VirtualProtectEx(h, va, nw.Length, op, out tmp);
        FlushInstructionCache(h, va, nw.Length);
        done[k] = ok; log += f[0] + " patched=" + ok + " at " + sw.ElapsedMilliseconds + "ms\n";
      }
      if (all) break;
      System.Threading.Thread.Sleep(0);
    }
    return log;
  }
}
"@
Add-Type -TypeDefinition $src
$p = Start-Process -FilePath $Exe -WorkingDirectory (Split-Path $Exe) -PassThru
[L]::Run($p.Id, $Patches, $TimeoutMs) | Set-Content -Encoding ASCII $Log
