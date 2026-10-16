@echo off
set LOG=\\host.lan\Data\boom-re\logs
mkdir C:\d3dtest 2>nul
copy /Y \\host.lan\Data\boom-re\thirdparty\swd3d\*.dll C:\d3dtest\ >nul
copy /Y \\host.lan\Data\boom-re\tools\d3dtest\d3dtest.exe C:\d3dtest\ >nul
cd /d C:\d3dtest
set GALLIUM_DRIVER=llvmpipe
d3dtest.exe
echo exit %errorlevel% >> d3dtest.log
copy /Y d3dtest.log "%LOG%\d3dtest.log" >nul
