@echo off
echo [boom] starting snapshot launcher, game window will open in a few seconds...
set D=\\host.lan\Data\boom-re\logs\snap\6EFD4A
if not exist "%D%" mkdir "%D%"
del /q "%D%\pre.snap" "%D%\post.snap" "%D%\done" "%D%\snap.log" 2>nul
call \\host.lan\Data\boom-re\win\snap.bat 6EFD4A 6EFEDC 900000 6EFEDC:5f5e5bc9c23000:00
echo [boom] finished, see %D%\snap.log
pause
