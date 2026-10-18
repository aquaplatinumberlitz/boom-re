@echo off
rem usage: snap.bat <SITE> [CONT|-] [timeout_ms] [patches...]   -> logs\snap\<SITE>\{pre.snap,post.snap,snap.log}
set D=\\host.lan\Data\boom-re\logs\snap\%1
if not exist "%D%" mkdir "%D%"
cd /d C:\boom
taskkill /f /im ca.exe >nul 2>&1
copy /Y \\host.lan\Data\boom-re\thirdparty\swd3d\*.dll C:\boom\ >nul
set GALLIUM_DRIVER=llvmpipe
del /q C:\boom\CALog.log 2>nul
\\host.lan\Data\boom-re\tools\snap.exe "%D%" %* 8E701D:7429:EB29 69E636:0f854c010000:e94d01000090 595372:e8f5c3e6ff:B001909090 59E869:e8fe2ee6ff:B001909090 59E98A:e8dd2de6ff:B001909090 68BB28:e83f5cd7ff:B001909090 690AEC:e87b0cd7ff:B001909090 69E62E:e83931d6ff:B001909090 6AA235:e83275d5ff:B001909090 6B0070:e8f716d5ff:B001909090 6B0278:e8ef14d5ff:B001909090 84E4ED:e87a32bbff:B001909090 852E4F:e818e9baff:B001909090 855828:e83fbfbaff:B001909090 8E29A3:e8c4edb1ff:B001909090 8E31D8:e88fe5b1ff:B001909090 8E3899:e8cedeb1ff:B001909090 8E4E57:e810c9b1ff:B001909090 8F3108:e85fe6b0ff:B001909090 8F3207:e860e5b0ff:B001909090 900D53:e8140ab0ff:B001909090 900D62:e8050ab0ff:B001909090 900D71:e8f609b0ff:B001909090 900D81:e8e609b0ff:B001909090 > "%D%\snap.log" 2>&1
copy /Y C:\boom\CALog.log "%D%\CALog.log" >nul
echo done> "%D%\done"
