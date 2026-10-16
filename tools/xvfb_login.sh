#!/bin/sh
# Run the dump in a private Xvfb, type a login on the login screen, take screenshots.
# usage: tools/xvfb_login.sh [user] [pass] [seconds=60]   -> logs/xvfb/login_*.png
cd "$(dirname "$0")/.."
U=${1:-tester}; P=${2:-1234}; SECS=${3:-60}; OUT=logs/xvfb; mkdir -p $OUT; rm -f $OUT/login_*.png
pkill -9 -f '[c]a_fixed_patched' 2>/dev/null; pkill -9 -f '[X]vfb :77' 2>/dev/null; sleep 1  # drop leftovers (mutex)
Xvfb :77 -screen 0 1024x768x24 -nolisten tcp >/dev/null 2>&1 & XPID=$!
sleep 1
export DISPLAY=:77
( cd wine/Boom && rm -f CALog.log && env -u WAYLAND_DISPLAY WINEDEBUG=${WDBG:--all} timeout $SECS wine ca_fixed_patched.exe > ../../$OUT/wine.log 2>&1; echo "exit=$?" > ../../$OUT/exit.txt ) & WPID=$!
# The login screen appears at a variable time (intro + patch-server connect). Retry the type-and-click
# sequence a few times so at least one attempt lands once the fields are visible.
sleep 12
for a in 1 2 3 4; do
  import -window root $OUT/login_$a.png
  xdotool mousemove 575 602 click 1; sleep 0.4; xdotool type --delay 60 "$U"; sleep 0.2
  xdotool mousemove 575 634 click 1; sleep 0.4; xdotool type --delay 60 "$P"; sleep 0.2
  xdotool mousemove 581 733 click 1
  sleep 8
done
import -window root $OUT/login_9.png
wait $WPID; kill $XPID 2>/dev/null
echo "--- CALog"; cat wine/Boom/CALog.log
