@echo off
set D=\\host.lan\Data\boom-re\logs\snap\TESTEXIT
if not exist "%D%" mkdir "%D%"
taskkill /f /im powershell.exe >nul 2>&1
del /q "%D%\drive.txt" "%D%\drv_*.png" 2>nul
start "" powershell -NoProfile -ExecutionPolicy Bypass -File \\host.lan\Data\boom-re\tools\battle_drive.ps1 -Out "%D%"
call \\host.lan\Data\boom-re\win\snap.bat 71581A - 600000
