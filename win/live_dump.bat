@echo off
set OUT=\\host.lan\Data\boom-re\logs
set PS32=C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe
%PS32% -NoProfile -ExecutionPolicy Bypass -File \\host.lan\Data\boom-re\tools\dump_exports.ps1 -Out C:\boom\exports.tsv -GameDir C:\boom > "%OUT%\dump_exports.out" 2>&1
copy /Y C:\boom\exports.tsv "%OUT%\exports.tsv" >nul
rmdir /s /q C:\boom\live 2>nul
%PS32% -NoProfile -ExecutionPolicy Bypass -File \\host.lan\Data\boom-re\tools\live_dump.ps1 -Exe C:\boom\ca.exe -OutDir C:\boom\live > "%OUT%\live_dump.out" 2>&1
robocopy C:\boom\live "%OUT%\live" /E /NFL /NDL /NJH /NJS
echo done> "%OUT%\live.done"
