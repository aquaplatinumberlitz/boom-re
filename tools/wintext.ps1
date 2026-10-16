# Dump texts of all top-level + child windows of a process (e.g. CrashDlg content). usage: wintext.ps1 -Name ca -Out file
param([string]$Name = "ca", [string]$Out)
Add-Type @"
using System; using System.Text; using System.Runtime.InteropServices; using System.Collections.Generic;
public static class W {
  public delegate bool EP(IntPtr h, IntPtr l);
  [DllImport("user32")] static extern bool EnumWindows(EP f, IntPtr l);
  [DllImport("user32")] static extern bool EnumChildWindows(IntPtr p, EP f, IntPtr l);
  [DllImport("user32")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32", CharSet=CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32", CharSet=CharSet.Unicode)] static extern int GetClassName(IntPtr h, StringBuilder s, int n);
  [DllImport("user32", CharSet=CharSet.Unicode)] static extern IntPtr SendMessage(IntPtr h, uint m, IntPtr w, StringBuilder l);
  static string T(IntPtr h) { var s = new StringBuilder(65536); SendMessage(h, 0x0D, new IntPtr(65536), s); var c = new StringBuilder(256); GetClassName(h, c, 256); return c + ": " + s; }
  public static string Dump(uint pid) {
    var sb = new StringBuilder();
    EnumWindows((h, l) => { uint p; GetWindowThreadProcessId(h, out p); if (p == pid) { sb.AppendLine("TOP " + T(h)); EnumChildWindows(h, (c, l2) => { sb.AppendLine("  " + T(c)); return true; }, IntPtr.Zero); } return true; }, IntPtr.Zero);
    return sb.ToString();
  }
}
"@
Get-Process $Name -ErrorAction SilentlyContinue | ForEach-Object { [W]::Dump([uint32]$_.Id) } | Out-File -Encoding UTF8 $Out
