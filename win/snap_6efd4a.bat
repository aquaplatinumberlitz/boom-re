@echo off
set D=\\host.lan\Data\boom-re\logs\snap\6EFD4A
if not exist "%D%" mkdir "%D%"
taskkill /f /im powershell.exe >nul 2>&1
del /q "%D%\drive.txt" "%D%\drv_*.png" 2>nul
start "" powershell -NoProfile -ExecutionPolicy Bypass -File \\host.lan\Data\boom-re\tools\battle_drive.ps1 -Out "%D%"
call \\host.lan\Data\boom-re\win\snap.bat 6EFD4A 6EFEDC 600000 6EFEDC:5f5e5bc9c23000:00
