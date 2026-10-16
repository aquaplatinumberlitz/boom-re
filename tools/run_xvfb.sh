#!/bin/sh
# Run wine/Boom/<exe> inside a private Xvfb display (does not touch the user's desktop) and take screenshots.
# usage: tools/run_xvfb.sh [exe=ca_fixed_patched.exe] [seconds=40]   -> logs/xvfb/shot_*.png, logs/xvfb/wine.log
cd "$(dirname "$0")/.."
EXE=${1:-ca_fixed_patched.exe}; SECS=${2:-40}; OUT=logs/xvfb; mkdir -p $OUT; rm -f $OUT/*.png
Xvfb :77 -screen 0 1024x768x24 -nolisten tcp >/dev/null 2>&1 & XPID=$!
sleep 1
( cd wine/Boom && rm -f CALog.log && env -u WAYLAND_DISPLAY DISPLAY=:77 WINEDEBUG=${WINEDEBUG:--all} timeout $SECS wine "$EXE" > ../../$OUT/wine.log 2>&1; echo "exit=$?" > ../../$OUT/exit.txt ) & WPID=$!
for t in 5 10 20 30 $((SECS-3)); do
  [ $t -lt $SECS ] || continue
  sleep $((t - ${prev:-0})); prev=$t
  import -display :77 -window root $OUT/shot_$t.png 2>/dev/null
done
wait $WPID
kill $XPID 2>/dev/null
echo "--- CALog"; cat wine/Boom/CALog.log 2>/dev/null
ls $OUT
