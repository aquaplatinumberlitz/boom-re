@echo off
set LOG=\\host.lan\Data\boom-re\logs
cd /d C:\boom
start "" C:\boom\ca.exe
for %%t in (05 10 15 20 30 45 60) do (
  powershell -NoProfile -Command "Start-Sleep 5; Add-Type -AssemblyName System.Windows.Forms,System.Drawing; $b=[System.Windows.Forms.SystemInformation]::VirtualScreen; $bmp=New-Object System.Drawing.Bitmap $b.Width,$b.Height; $g=[System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen($b.Location,[System.Drawing.Point]::Empty,$b.Size); $bmp.Save('%LOG%\w_%%t.png'); Get-Process ca -ErrorAction SilentlyContinue | ForEach-Object { '%%t ' + $_.MainWindowTitle } | Out-File -Append -Encoding ASCII '%LOG%\watch.txt'"
)
copy /Y C:\boom\CALog.log "%LOG%\CALog_w.log" >nul
taskkill /f /im ca.exe >nul 2>&1
echo done> "%LOG%\watch.done"
