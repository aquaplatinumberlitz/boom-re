#!/bin/sh
# Run the dump in a private Xvfb, type a login on the login screen, take screenshots.
# usage: tools/xvfb_login.sh [user] [pass] [seconds=60]   -> logs/xvfb/login_*.png
cd "$(dirname "$0")/.."
U=${1:-tester}; P=${2:-1234}; SECS=${3:-60}; OUT=logs/xvfb; mkdir -p $OUT; rm -f $OUT/login_*.png
Xvfb :77 -screen 0 1024x768x24 -nolisten tcp >/dev/null 2>&1 & XPID=$!
sleep 1
export DISPLAY=:77
( cd wine/Boom && rm -f CALog.log && env -u WAYLAND_DISPLAY WINEDEBUG=-all timeout $SECS wine ca_fixed_patched.exe > ../../$OUT/wine.log 2>&1; echo "exit=$?" > ../../$OUT/exit.txt ) & WPID=$!
sleep 18; import -window root $OUT/login_0.png
xdotool mousemove 575 602 click 1; sleep 0.5; xdotool type --delay 80 "$U"; sleep 0.3
xdotool mousemove 575 634 click 1; sleep 0.5; xdotool type --delay 80 "$P"; sleep 0.3
import -window root $OUT/login_1.png
xdotool mousemove 581 733 click 1
for t in 2 3 4 5; do sleep 4; import -window root $OUT/login_$t.png; done
wait $WPID; kill $XPID 2>/dev/null
echo "--- CALog"; cat wine/Boom/CALog.log
