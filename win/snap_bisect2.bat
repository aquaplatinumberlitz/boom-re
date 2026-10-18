@echo off
rem bisect run: base patches + login-time Feature(212) sites only. Driver automates input.
set D=\\host.lan\Data\boom-re\logs\snap\BISECT2
if not exist "%D%" mkdir "%D%"
taskkill /f /im powershell.exe >nul 2>&1
del /q "%D%\drive.txt" "%D%\drv_*.png" "%D%\snap.log" "%D%\done" 2>nul
start "" powershell -NoProfile -ExecutionPolicy Bypass -File \\host.lan\Data\boom-re\tools\battle_drive.ps1 -Out "%D%"
cd /d C:\boom
taskkill /f /im ca.exe >nul 2>&1
copy /Y \\host.lan\Data\boom-re\thirdparty\swd3d\*.dll C:\boom\ >nul
set GALLIUM_DRIVER=llvmpipe
del /q C:\boom\CALog.log 2>nul
\\host.lan\Data\boom-re\tools\snap.exe "%D%" 71581A - 400000 8E701D:7429:EB29 69E636:0f854c010000:e94d01000090 84E4ED:e87a32bbff:B001909090 852E4F:e818e9baff:B001909090 855828:e83fbfbaff:B001909090 8E29A3:e8c4edb1ff:B001909090 8E31D8:e88fe5b1ff:B001909090 8E3899:e8cedeb1ff:B001909090 8E4E57:e810c9b1ff:B001909090 8F3108:e85fe6b0ff:B001909090 8F3207:e860e5b0ff:B001909090 900D53:e8140ab0ff:B001909090 900D62:e8050ab0ff:B001909090 900D71:e8f609b0ff:B001909090 900D81:e8e609b0ff:B001909090 > "%D%\snap.log" 2>&1
copy /Y C:\boom\CALog.log "%D%\CALog.log" >nul
echo done> "%D%\done"
