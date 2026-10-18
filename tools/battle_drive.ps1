# Drive the ORIGINAL client in the WinBoat guest: login -> channel -> square -> create room -> (server auto-starts
# the match) -> press Space repeatedly so the bomb-placement path (site 0x6EFD4A) fires while snap.exe is armed.
# Coordinates are the same as tools/match_gdb.sh (1024x768 client area). usage: battle_drive.ps1 -Out <dir>
param([string]$Out = "\\host.lan\Data\boom-re\logs\snap\6EFD4A", [int]$SpaceSecs = 150)
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
Add-Type @"
using System; using System.Runtime.InteropServices;
public static class In {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
  [StructLayout(LayoutKind.Sequential)] public struct PT { public int X, Y; }
  [DllImport("user32")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32")] public static extern void mouse_event(uint f, int dx, int dy, uint d, IntPtr e);
  [DllImport("user32")] public static extern void keybd_event(byte vk, byte sc, uint f, IntPtr e);
  [DllImport("user32")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32")] public static extern bool ClientToScreen(IntPtr h, ref PT p);
  [DllImport("user32")] public static extern bool GetClientRect(IntPtr h, out RECT r);
  [DllImport("user32")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32")] public static extern bool MoveWindow(IntPtr h, int x, int y, int w, int hh, bool r);
  [DllImport("user32")] public static extern bool IsIconic(IntPtr h);
  [DllImport("user32")] public static extern uint MapVirtualKey(uint c, uint t);
}
"@
$log = "$Out\drive.txt"
function L($m) { "$(Get-Date -Format HH:mm:ss) $m" | Out-File -Append -Encoding ASCII $log }
function Shot($n) {
  $b = [System.Windows.Forms.SystemInformation]::VirtualScreen
  $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
  $g = [System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)
  $bmp.Save("$Out\drv_$n.png"); $g.Dispose(); $bmp.Dispose()
}
function Win { $p = Get-Process ca -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1; $p }
function Origin($h) { $pt = New-Object In+PT; [In]::ClientToScreen($h, [ref]$pt) | Out-Null; $pt }
function Click($x, $y) {
  $p = Win; if (-not $p) { return }; $h = $p.MainWindowHandle; if ([In]::IsIconic($h)) { [In]::ShowWindow($h, 9) | Out-Null; Start-Sleep 1 }; [In]::SetForegroundWindow($h) | Out-Null
  $o = Origin $h; $x = [int]($x * 0.78125); $y = [int]($y * 0.78125); [In]::SetCursorPos($o.X + $x, $o.Y + $y) | Out-Null; Start-Sleep -Milliseconds 150
  [In]::mouse_event(2, 0, 0, 0, [IntPtr]::Zero); Start-Sleep -Milliseconds 80; [In]::mouse_event(4, 0, 0, 0, [IntPtr]::Zero)
}
function Key($vk, $holdMs = 60) {
  $sc = [byte][In]::MapVirtualKey($vk, 0)
  [In]::keybd_event([byte]$vk, $sc, 0, [IntPtr]::Zero); Start-Sleep -Milliseconds $holdMs
  [In]::keybd_event([byte]$vk, $sc, 2, [IntPtr]::Zero); Start-Sleep -Milliseconds 60
}
function Typ($s) { foreach ($c in $s.ToCharArray()) { Key ([int][char]::ToUpper($c)) 50 } }
function HasStage($n) { $f = "C:\boom\CALog.log"; (Test-Path $f) -and ((Get-Content $f -ErrorAction SilentlyContinue | Select-String "dne:$n\)" -Quiet)) }

L "waiting for ca window"
for ($i = 0; $i -lt 120 -and -not (Win); $i++) { Start-Sleep 1 }
Start-Sleep 5
$h0 = (Win).MainWindowHandle; [In]::ShowWindow($h0, 9) | Out-Null; Start-Sleep 2; [In]::MoveWindow($h0, 0, 0, 1040, 806, $true) | Out-Null; Start-Sleep 2; $r = New-Object In+RECT; [In]::GetWindowRect($h0, [ref]$r) | Out-Null; $c = New-Object In+RECT; [In]::GetClientRect($h0, [ref]$c) | Out-Null
L "rect $($r.L),$($r.T),$($r.R),$($r.B) client $($c.R)x$($c.B) visible=$([In]::IsWindowVisible($h0)) iconic=$([In]::IsIconic($h0)) screen=$([System.Windows.Forms.SystemInformation]::VirtualScreen)"
L "window found: $((Win).MainWindowTitle) $((Win).MainWindowHandle)"; Shot 0
# login (retry until stage 10)
for ($a = 0; $a -lt 18 -and -not (HasStage 10); $a++) {
  Click 575 602; Start-Sleep -Milliseconds 400; Typ "tester"; Start-Sleep -Milliseconds 200
  Click 575 634; Start-Sleep -Milliseconds 400; Typ "1234"; Start-Sleep -Milliseconds 200
  Click 581 733; L "login attempt $a"; Shot "login$a"; Start-Sleep 10
}
L "login loop done; stage10=$(HasStage 10)"; Shot 1
for ($a = 0; $a -lt 40 -and -not (HasStage 10); $a++) { Start-Sleep 5 }
Start-Sleep 8; Click 663 97; Start-Sleep 3; Shot 'tab'; Click 650 393
for ($a = 0; $a -lt 40 -and -not (HasStage 11); $a++) { Start-Sleep 5 }
L "stage11=$(HasStage 11)"; Shot 2
Start-Sleep 6
foreach ($c in @(@(975, 38, 2), @(385, 50, 2), @(437, 612, 4), @(512, 384, 3))) { Click $c[0] $c[1]; Start-Sleep $c[2] }
L "room clicks done; stage12=$(HasStage 12)"; Shot 3
for ($a = 0; $a -lt 60 -and -not (HasStage 13); $a++) { Start-Sleep 5 }
L "stage13=$(HasStage 13)"; Shot 4
Start-Sleep 10; Click 512 400
$t0 = Get-Date; $n = 0
while (((Get-Date) - $t0).TotalSeconds -lt $SpaceSecs) {
  Key 0x25 500; Key 0x20 120; $n++
  if ($n % 5 -eq 0) { Shot "sp$n"; L "space x$n" }
  Start-Sleep 2
  if (-not (Win)) { L "ca gone"; break }
}
Shot "end"; L "driver done"
