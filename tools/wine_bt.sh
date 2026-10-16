#!/bin/sh
# Start the dump in Xvfb, wait N seconds, attach winedbg and dump backtraces of all threads, then kill.
# usage: tools/wine_bt.sh [seconds=20] [exe=ca_fixed_patched.exe]   -> logs/xvfb/bt.txt, logs/xvfb/shot_bt.png
cd "$(dirname "$0")/.."
SECS=${1:-20}; EXE=${2:-ca_fixed_patched.exe}; OUT=logs/xvfb; mkdir -p $OUT
Xvfb :77 -screen 0 1024x768x24 -nolisten tcp >/dev/null 2>&1 & XPID=$!
sleep 1
( cd wine/Boom && rm -f CALog.log && env -u WAYLAND_DISPLAY DISPLAY=:77 WINEDEBUG=-all timeout $((SECS+60)) wine "$EXE" >/dev/null 2>&1 ) & WPID=$!
sleep $SECS
import -display :77 -window root $OUT/shot_bt.png 2>/dev/null
PID=$(WINEDEBUG=-all wine winedbg --command "info proc" 2>/dev/null | grep -i "$EXE" | awk '{print $1}' | sed 's/^=//' | head -1)
echo "winpid=$PID"
if [ -n "$PID" ]; then
  printf 'attach 0x%s\ninfo thread\nbt all\ndetach\nquit\n' "$PID" | WINEDEBUG=-all timeout 60 wine winedbg > $OUT/bt.txt 2>&1
fi
for p in $(pgrep -f "Boom.$EXE"); do kill $p 2>/dev/null; done
kill $XPID 2>/dev/null; wait $WPID 2>/dev/null
echo "--- CALog"; cat wine/Boom/CALog.log 2>/dev/null
