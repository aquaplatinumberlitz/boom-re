@echo off
set LOG=\\host.lan\Data\boom-re\logs
powershell -NoProfile -Command "Get-WinEvent -FilterHashtable @{LogName='Application'; StartTime=(Get-Date).AddMinutes(-15)} -MaxEvents 30 | Where-Object {$_.Message -match 'ca.exe'} | Format-List TimeCreated,ProviderName,Id,Message | Out-File -Width 200 '%LOG%\evlog.txt'"
dir /s /b /od C:\boom\*.dmp C:\boom\*.mdmp >> "%LOG%\evlog.txt" 2>nul
echo done> "%LOG%\ev.done"
