@echo off
set LOG=\\host.lan\Data\boom-re\logs\crash
if not exist "%LOG%" mkdir "%LOG%"
(dir /s /b /od C:\boom\*.dmp C:\boom\*.nfo C:\boom\*.dmp.log "%TEMP%\*.dmp" "%TEMP%\*.nfo" "%TEMP%\Crash_CA*" "%USERPROFILE%\Crash_CA*" C:\Windows\Temp\Crash_CA* 2>nul) > "%LOG%\list.txt"
for /f "delims=" %%f in ('dir /s /b C:\boom\*.nfo C:\boom\*.dmp.log "%TEMP%\*.nfo" "%TEMP%\Crash_CA*.log" 2^>nul') do copy /Y "%%f" "%LOG%\" >nul
for /f "delims=" %%f in ('dir /s /b /od C:\boom\*.dmp "%TEMP%\Crash_CA.dmp" 2^>nul') do copy /Y "%%f" "%LOG%\" >nul
echo done> "%LOG%\..\getcrash.done"
