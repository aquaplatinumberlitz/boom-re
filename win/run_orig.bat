@echo off
setlocal
set SRC=\\host.lan\Data\Downloads\Boom
set OUT=\\host.lan\Data\boom-re
set LOG=%OUT%\logs
if not exist "%LOG%" mkdir "%LOG%"
echo [*] Sync client files (incl. .idd) to C:\boom ...
robocopy "%SRC%" C:\boom /E /XD hackshield blackcipher /NFL /NDL /NJH /NJS

cd /d C:\boom
echo [*] Start ca.exe %*
start "" C:\boom\ca.exe %*
for %%t in (10 20 40 80) do (
  powershell -NoProfile -Command "Start-Sleep -Seconds 10; Add-Type -AssemblyName System.Windows.Forms,System.Drawing; $b=[System.Windows.Forms.SystemInformation]::VirtualScreen; $bmp=New-Object System.Drawing.Bitmap $b.Width,$b.Height; $g=[System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen($b.Location,[System.Drawing.Point]::Empty,$b.Size); $bmp.Save('%LOG%\shot_%%t.png'); Get-Process | Where-Object {$_.ProcessName -like 'ca*'} | Format-Table Id,ProcessName,Responding,MainWindowTitle -AutoSize | Out-File -Append '%LOG%\proc.txt'"
)
copy /Y C:\boom\CALog.log "%LOG%\CALog.log" >nul
taskkill /f /im ca.exe >nul 2>&1
echo done> "%LOG%\run.done"
