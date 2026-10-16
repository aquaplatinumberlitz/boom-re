@echo off
rem usage: snap.bat <SITE> [CONT|-] [timeout_ms] [patches...]   -> logs\snap\<SITE>\{pre.snap,post.snap,snap.log}
set D=\\host.lan\Data\boom-re\logs\snap\%1
if not exist "%D%" mkdir "%D%"
cd /d C:\boom
taskkill /f /im ca.exe >nul 2>&1
copy /Y \\host.lan\Data\boom-re\thirdparty\swd3d\*.dll C:\boom\ >nul
set GALLIUM_DRIVER=llvmpipe
del /q C:\boom\CALog.log 2>nul
\\host.lan\Data\boom-re\tools\snap.exe "%D%" %* 8E701D:7429:EB29 69E636:0f854c010000:e94d01000090 > "%D%\snap.log" 2>&1
copy /Y C:\boom\CALog.log "%D%\CALog.log" >nul
echo done> "%D%\done"
