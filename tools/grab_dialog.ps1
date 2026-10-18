# Dump tiêu đề + text của mọi cửa sổ dialog đang mở, dùng API Unicode (GetWindowTextW)
# để không bị lỗi codepage (dialog tiếng Hàn hiện ??? trên màn hình).
# Chạy trong guest: powershell -ExecutionPolicy Bypass -File \\host.lan\Data\boom-re\tools\grab_dialog.ps1
$ErrorActionPreference = "SilentlyContinue"
$out = "\\host.lan\Data\boom-re\logs\kr-dialog.txt"

Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public class Win {
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc cb, IntPtr l);
  public delegate bool EnumWindowsProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowTextW(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetClassNameW(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
}
"@

$lines = New-Object System.Collections.Generic.List[string]
$cb = [Win+EnumWindowsProc]{
  param($h, $l)
  if (-not [Win]::IsWindowVisible($h)) { return $true }
  $sb = New-Object System.Text.StringBuilder 1024
  [void][Win]::GetWindowTextW($h, $sb, 1024)
  $t = $sb.ToString()
  if ($t.Length -eq 0) { return $true }
  $cn = New-Object System.Text.StringBuilder 256
  [void][Win]::GetClassNameW($h, $cn, 256)
  $pid = 0
  [void][Win]::GetWindowThreadProcessId($h, [ref]$pid)
  $pname = (Get-Process -Id $pid).ProcessName
  $lines.Add("HWND=$h PID=$pid PROC=$pname CLASS=$($cn.ToString()) TEXT=$t")
  return $true
}
[void][Win]::EnumWindows($cb, [IntPtr]::Zero)
$lines | Out-File -FilePath $out -Encoding utf8
Write-Host "wrote $($lines.Count) windows -> $out"
