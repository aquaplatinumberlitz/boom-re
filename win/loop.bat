@echo off
set LOG=\\host.lan\Data\boom-re\logs
del "%LOG%\loop.txt" 2>nul
cd /d C:\boom
for %%i in (1 2 3) do (
  start "" C:\boom\ca.exe
  powershell -NoProfile -Command "Start-Sleep 20; Get-Process ca -ErrorAction SilentlyContinue | ForEach-Object { '%%i ' + $_.MainWindowTitle } | Out-File -Append -Encoding ASCII '%LOG%\loop.txt'"
  copy /Y C:\boom\CALog.log "%LOG%\CALog_%%i.log" >nul
  taskkill /f /im ca.exe >nul 2>&1
  timeout /t 3 >nul
)
echo done> "%LOG%\loop.done"
