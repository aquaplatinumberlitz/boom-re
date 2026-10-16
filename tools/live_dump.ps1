# Run with 32-bit PowerShell. Starts the ORIGINAL (Themida) ca.exe, waits, then dumps from the live process:
#   iat.bin       bytes of the original IAT region (0xC0F000..0xC0F800)
#   modules.tsv   name, base, size of loaded modules
#   regions.tsv + reg_<base>.bin   every committed private/mapped executable region outside modules
# Then kills the process. Used by tools/fix_iat.py to resolve Themida import wrappers.
param([string]$Exe, [string]$OutDir, [int]$Wait = 25)
$src = @"
using System; using System.Runtime.InteropServices; using System.IO; using System.Diagnostics; using System.Text;
public static class Live {
  [DllImport("kernel32")] static extern IntPtr OpenProcess(int a, bool i, int pid);
  [DllImport("kernel32")] static extern bool ReadProcessMemory(IntPtr h, IntPtr a, byte[] b, int n, out int r);
  [DllImport("kernel32")] static extern int VirtualQueryEx(IntPtr h, IntPtr a, out MBI m, int l);
  [StructLayout(LayoutKind.Sequential)] public struct MBI { public IntPtr Base, AllocBase; public int AllocProt; public IntPtr Size; public int State, Protect, Type; }
  public static byte[] Read(IntPtr h, long a, int n) { var b = new byte[n]; int r; ReadProcessMemory(h, new IntPtr(a), b, n, out r); return b; }
  public static void Dump(int pid, string dir) {
    IntPtr h = OpenProcess(0x0410, false, pid);
    File.WriteAllBytes(Path.Combine(dir, "iat.bin"), Read(h, 0xC0F000, 0x800));
    var p = Process.GetProcessById(pid); var sb = new StringBuilder();
    foreach (ProcessModule m in p.Modules) sb.AppendLine(m.ModuleName + "\t" + m.BaseAddress.ToInt32().ToString("x") + "\t" + m.ModuleMemorySize.ToString("x"));
    File.WriteAllText(Path.Combine(dir, "modules.tsv"), sb.ToString());
    var rs = new StringBuilder(); long a = 0x10000; MBI mbi;
    while (a < 0x7FFF0000 && VirtualQueryEx(h, new IntPtr(a), out mbi, Marshal.SizeOf(typeof(MBI))) != 0) {
      long sz = mbi.Size.ToInt64(); long b = mbi.Base.ToInt64();
      bool exec = (mbi.Protect & 0xF0) != 0; bool commit = mbi.State == 0x1000; bool image = mbi.Type == 0x1000000;
      if (commit && exec && !image && sz <= 0x4000000) {
        File.WriteAllBytes(Path.Combine(dir, "reg_" + b.ToString("x8") + ".bin"), Read(h, b, (int)sz));
        rs.AppendLine(b.ToString("x") + "\t" + sz.ToString("x") + "\t" + mbi.Protect.ToString("x"));
      }
      a = b + sz;
    }
    File.WriteAllText(Path.Combine(dir, "regions.tsv"), rs.ToString());
    // every module image: ca.exe (Themida sections hold wrapper logic) and DLLs (wrappers end in jmp [dll IAT])
    foreach (ProcessModule mm in p.Modules) {
      long ib = mm.BaseAddress.ToInt64(); int isz = mm.ModuleMemorySize;
      var img = new byte[isz]; for (int off = 0; off < isz; off += 0x1000) { var pg = Read(h, ib + off, Math.Min(0x1000, isz - off)); Buffer.BlockCopy(pg, 0, img, off, pg.Length); }
      File.WriteAllBytes(Path.Combine(dir, "image_" + ib.ToString("x8") + ".bin"), img);
    }
  }
}
"@
Add-Type -TypeDefinition $src
New-Item -ItemType Directory -Force $OutDir | Out-Null
$p = Start-Process -FilePath $Exe -WorkingDirectory (Split-Path $Exe) -PassThru
Start-Sleep -Seconds $Wait
if ($p.HasExited) { "exited early code=$($p.ExitCode)" | Set-Content "$OutDir\status.txt"; exit }
[Live]::Dump($p.Id, $OutDir)
"ok pid=$($p.Id)" | Set-Content "$OutDir\status.txt"
Stop-Process -Id $p.Id -Force
