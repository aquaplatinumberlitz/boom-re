@echo off
set OUT=\\host.lan\Data\boom-re\logs
C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File \\host.lan\Data\boom-re\tools\dump_exports.ps1 -Out C:\boom\exports.tsv -GameDir C:\boom > "%OUT%\dump_exports.out" 2>&1
copy /Y C:\boom\exports.tsv "%OUT%\exports.tsv" >nul
copy /Y C:\boom\exports.tsv.log "%OUT%\exports.log" >nul
echo done> "%OUT%\exports.done"
