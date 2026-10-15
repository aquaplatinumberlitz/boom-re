@echo off
set LOG=\\host.lan\Data\boom-re\logs
taskkill /f /im ca.exe >nul 2>&1
powershell -NoProfile -Command "Get-ChildItem C:\boom -Recurse -File | Where-Object {$_.LastWriteTime -gt (Get-Date).AddMinutes(-20) -and $_.Extension -notin '.idd','.idx'} | Sort-Object LastWriteTime | Format-Table LastWriteTime,Length,FullName -AutoSize | Out-File -Width 250 '%LOG%\recent_files.txt'"
echo done> "%LOG%\crash.done"
