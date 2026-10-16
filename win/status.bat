@echo off
set LOG=\\host.lan\Data\boom-re\logs
(tasklist /fi "imagename eq ca.exe" & tasklist /fi "imagename eq powershell.exe" & dir C:\boom\live | find /c "image_" & dir C:\boom\live | find "bytes") > "%LOG%\status.txt" 2>&1
echo done> "%LOG%\status.done"
