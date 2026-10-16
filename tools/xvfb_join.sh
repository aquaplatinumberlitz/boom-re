#!/bin/sh
# Login, wait for the channel screen (CALog dne:10), click the first channel slot, take screenshots.
# usage: tools/xvfb_join.sh [user] [pass] [seconds=90]   -> logs/xvfb/join_*.png, CALog printed at the end
cd "$(dirname "$0")/.."
U=${1:-tester}; P=${2:-1234}; SECS=${3:-90}; OUT=logs/xvfb; mkdir -p $OUT; rm -f $OUT/join_*.png
pkill -9 -f '[c]a_fixed_patched' 2>/dev/null; pkill -9 -f '[X]vfb :77' 2>/dev/null; sleep 1
Xvfb :77 -screen 0 1024x768x24 -nolisten tcp >/dev/null 2>&1 & XPID=$!
sleep 1
export DISPLAY=:77
( cd wine/Boom && rm -f CALog.log && env -u WAYLAND_DISPLAY WINEDEBUG=${WDBG:--all} timeout $SECS wine ca_fixed_patched.exe > ../../$OUT/wine.log 2>&1 ) & WPID=$!
sleep 12
for a in 1 2 3 4 5 6; do
  grep -q 'dne:10' wine/Boom/CALog.log 2>/dev/null && break
  xdotool mousemove 575 602 click 1; sleep 0.4; xdotool type --delay 60 "$U"; sleep 0.2
  xdotool mousemove 575 634 click 1; sleep 0.4; xdotool type --delay 60 "$P"; sleep 0.2
  xdotool mousemove 581 733 click 1
  sleep 8
done
sleep 6                                   # channel list (opcode 40 -> 14/16) + auto-rebuild
import -window root $OUT/join_0.png
xdotool mousemove 650 393 click 1        # slot 1 ("Kenh 1")
sleep 4; import -window root $OUT/join_1.png
xdotool mousemove 650 393 click --repeat 2 --delay 120 1   # double click, in case single click only selects
sleep 8; import -window root $OUT/join_2.png
sleep 8; import -window root $OUT/join_3.png
kill $WPID 2>/dev/null; pkill -9 -f '[c]a_fixed_patched' 2>/dev/null; kill $XPID 2>/dev/null
echo "--- CALog"; cat wine/Boom/CALog.log
