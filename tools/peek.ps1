# 32-bit PowerShell: start ca.exe, wait, read memory ranges "va:len,va:len" from the live process, write hex lines.
param([string]$Exe, [string]$Ranges, [string]$Out, [int]$Wait = 8)
$src = @"
using System; using System.Runtime.InteropServices;
public static class Peek {
  [DllImport("kernel32")] static extern IntPtr OpenProcess(int a, bool i, int pid);
  [DllImport("kernel32")] static extern bool ReadProcessMemory(IntPtr h, IntPtr a, byte[] b, int n, out int r);
  public static string Read(int pid, long a, int n) { IntPtr h = OpenProcess(0x0410, false, pid); var b = new byte[n]; int r; ReadProcessMemory(h, new IntPtr(a), b, n, out r); return BitConverter.ToString(b, 0, r).Replace("-", " "); }
}
"@
Add-Type -TypeDefinition $src
$p = Start-Process -FilePath $Exe -WorkingDirectory (Split-Path $Exe) -PassThru
Start-Sleep -Seconds $Wait
$lines = foreach ($r in $Ranges.Split(',')) { $va, $len = $r.Split(':'); "{0} {1}" -f $va, [Peek]::Read($p.Id, [Convert]::ToInt64($va, 16), [int]$len) }
$lines | Set-Content -Encoding ASCII $Out
Stop-Process -Id $p.Id -Force
