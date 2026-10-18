@echo off
rem Chuẩn bị bản chạy KR tối thiểu trong guest để dump bộ nhớ (không cần asset).
rem Dùng: \\host.lan\Data\boom-re\win\kr_setup.bat
set SRC=\\host.lan\Data\boomkr-run
set DST=C:\boomkr
if not exist "%DST%" mkdir "%DST%"
for %%f in (CA.exe CAWH.sys GameGuard.des nmco3.dll nmcogame.dll NGMDll.dll NGMResource.dll NGClient.aes CAKR.ini binkw32.dll CrashReporter.dll d3dx9_30.dll D3DX9_43.dll dbghelp.dll gdiplus.dll ijl15.dll mss32.dll) do (
  if exist "%SRC%\%%f" copy /Y "%SRC%\%%f" "%DST%\%%f" >nul
)
echo [boom] kr_setup xong: %DST%
dir /b "%DST%"
