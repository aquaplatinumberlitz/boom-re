#!/bin/sh
# Run the dump under winedbg inside Xvfb, break on every first-chance exception, print bt + regs each time.
# usage: tools/wine_dbg.sh [n_conts=12] [exe=ca_fixed_patched.exe]  -> logs/xvfb/winedbg.txt
cd "$(dirname "$0")/.."
N=${1:-12}; EXE=${2:-ca_fixed_patched.exe}; OUT=logs/xvfb; mkdir -p $OUT
Xvfb :77 -screen 0 1024x768x24 -nolisten tcp >/dev/null 2>&1 & XPID=$!
sleep 1
cd wine/Boom && rm -f CALog.log
( printf 'set $BreakOnFirstChance=1\n'; i=0; while [ $i -lt $N ]; do printf 'cont\nbt\ninfo regs\n'; i=$((i+1)); done; printf 'quit\n' ) \
  | env -u WAYLAND_DISPLAY DISPLAY=:77 WINEDEBUG=-all timeout 180 wine winedbg "Z:\\home\\admin\\boom-re\\wine\\Boom\\$EXE" > ../../$OUT/winedbg.txt 2>&1
cd ../..; kill $XPID 2>/dev/null
grep -E 'First chance|Unhandled|=>|^  [1-4] ' $OUT/winedbg.txt | head -80
