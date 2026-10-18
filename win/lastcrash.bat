@echo off
set LOG=\\host.lan\Data\boom-re\logs
powershell -NoProfile -Command "Get-WinEvent -FilterHashtable @{LogName='Application';Id=1000,1001} -MaxEvents 6 -ErrorAction SilentlyContinue | Where-Object {$_.Message -match 'ca.exe'} | Select-Object -First 2 | ForEach-Object { $_.TimeCreated.ToString() + ' ' + $_.Message } | Out-File -Encoding ASCII '%LOG%\lastcrash.txt'"
echo done> "%LOG%\lastcrash.done"
