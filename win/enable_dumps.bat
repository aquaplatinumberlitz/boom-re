@echo off
set LOG=\\host.lan\Data\boom-re\logs
mkdir C:\dumps 2>nul
reg add "HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\ca.exe" /v DumpFolder /t REG_EXPAND_SZ /d C:\dumps /f > "%LOG%\enable_dumps.txt" 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\ca.exe" /v DumpType /t REG_DWORD /d 2 /f >> "%LOG%\enable_dumps.txt" 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\ca.exe" /v DumpCount /t REG_DWORD /d 3 /f >> "%LOG%\enable_dumps.txt" 2>&1
echo done> "%LOG%\enable_dumps.done"
