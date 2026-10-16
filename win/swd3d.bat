@echo off
rem Original client + software D3D9 (Wine wined3d + Mesa llvmpipe, thirdparty\swd3d) -> renders without a GPU.
set LOG=\\host.lan\Data\boom-re\logs
copy /Y \\host.lan\Data\boom-re\thirdparty\swd3d\*.dll C:\boom\ >nul
set GALLIUM_DRIVER=llvmpipe
del /q C:\boom\CALog.log "%LOG%\watch.txt" "%LOG%\w_*.png" 2>nul
call \\host.lan\Data\boom-re\win\watch2.bat
