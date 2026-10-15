@echo off
set LOG=\\host.lan\Data\boom-re\logs
C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File \\host.lan\Data\boom-re\tools\peek.ps1 -Exe C:\boom\ca.exe -Ranges "EA6FE0:8,EEC1BC:8,E57944:8,E5794C:8,E47F54:16,F06128:16" -Out C:\boom\peek.txt -Wait 8 > "%LOG%\peek.out" 2>&1
copy /Y C:\boom\peek.txt "%LOG%\peek.txt" >nul
echo done> "%LOG%\peek.done"
