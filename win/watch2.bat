@echo off
set LOG=\\host.lan\Data\boom-re\logs
cd /d C:\boom
start "" C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File \\host.lan\Data\boom-re\tools\launch.ps1 -Exe C:\boom\ca.exe -Log "%LOG%\launch.txt" -WaitExitMs 70000
for %%t in (05 10 15 20 30 45 60) do (
  powershell -NoProfile -Command "Start-Sleep 5; Add-Type -AssemblyName System.Windows.Forms,System.Drawing; $b=[System.Windows.Forms.SystemInformation]::VirtualScreen; $bmp=New-Object System.Drawing.Bitmap $b.Width,$b.Height; $g=[System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen($b.Location,[System.Drawing.Point]::Empty,$b.Size); $bmp.Save('%LOG%\w_%%t.png'); Get-Process ca -ErrorAction SilentlyContinue | ForEach-Object { '%%t ' + $_.MainWindowTitle } | Out-File -Append -Encoding ASCII '%LOG%\watch.txt'"
)
powershell -NoProfile -ExecutionPolicy Bypass -File \\host.lan\Data\boom-re\tools\wintext.ps1 -Name ca -Out "%LOG%\wintext.txt"
copy /Y C:\boom\CALog.log "%LOG%\CALog_w.log" >nul
taskkill /f /im ca.exe >nul 2>&1
echo done> "%LOG%\watch.done"
