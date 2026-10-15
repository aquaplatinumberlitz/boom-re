@echo off
setlocal
set SRC=\\host.lan\Data\Downloads\Boom
set OUT=\\host.lan\Data\boom-re
echo [*] Copy client vao C:\boom (bo qua .idd va anti-cheat)...
robocopy "%SRC%" C:\boom /E /XF *.idd /XD hackshield blackcipher /NFL /NDL /NJH /NJS
if not exist C:\boom-tools mkdir C:\boom-tools
copy /Y "%OUT%\tools\unlicense.exe" C:\boom-tools\ >nul
cd /d C:\boom
echo [*] Unpack ca.exe ...
C:\boom-tools\unlicense.exe ca.exe --verbose --timeout 30 > C:\boom\unlicense_ca.log 2>&1
copy /Y C:\boom\unlicense_ca.log "%OUT%\" >nul
if exist C:\boom\unpacked_ca.exe copy /Y C:\boom\unpacked_ca.exe "%OUT%\" >nul
echo [*] Xong. Ket qua o %OUT%
dir "%OUT%"
echo done> "%OUT%\unpack.done"
