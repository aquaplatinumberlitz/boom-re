@echo off
set LOG=\\host.lan\Data\boom-re\logs
cd /d C:\boom
dir C:\boom\*.idd > "%LOG%\diag.txt" 2>&1
echo --- run >> "%LOG%\diag.txt"
start "" /wait C:\boom\ca_patched.exe
echo exitcode=%errorlevel% >> "%LOG%\diag.txt"
powershell -NoProfile -Command "Get-WinEvent -FilterHashtable @{LogName='Application'; StartTime=(Get-Date).AddMinutes(-30)} -MaxEvents 15 | Where-Object {$_.ProviderName -match 'Application Error|Windows Error Reporting|SideBySide|Application Hang'} | Format-List TimeCreated,ProviderName,Id,Message | Out-File -Append -Width 200 '%LOG%\diag.txt'"
dir /od C:\boom\*.log C:\boom\*.txt C:\boom\log 2>nul >> "%LOG%\diag.txt"
echo done> "%LOG%\diag.done"
