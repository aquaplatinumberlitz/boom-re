@echo off
set LOG=\\host.lan\Data\boom-re\logs\dumps
if not exist "%LOG%" mkdir "%LOG%"
dir /b /o-d C:\dumps > "%LOG%\list.txt" 2>&1
copy /Y C:\dumps\ca.exe.*.dmp "%LOG%\" > "%LOG%\copy.txt" 2>&1
echo done> "%LOG%\getdumps.done"
