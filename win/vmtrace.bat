@echo off
rem usage: vmtrace.bat <SITE> <BASE> <TOTAL> <FLAG>   (values from logs\vmtrace\<SITE>\cfg.json)
set D=\\host.lan\Data\boom-re\logs\vmtrace\%1
cd /d C:\boom
taskkill /f /im ca.exe >nul 2>&1
\\host.lan\Data\boom-re\tools\inject.exe "%D%" %2 %3 %4 2 60000 > "%D%\inject.log" 2>&1
copy /Y C:\boom\CALog.log "%D%\CALog.log" >nul
echo done> "%D%\done"
