#!/bin/sh
# login, reach stage 10, then click the category arrows / tab area to fire the tab-change (event 900), screenshot.
cd "$(dirname "$0")/.."
OUT=logs/xvfb; mkdir -p $OUT; rm -f $OUT/tab_*.png
pkill -9 -f '[c]a_fixed_patched' 2>/dev/null; pkill -9 -f 'Xvfb :77' 2>/dev/null; sleep 1
Xvfb :77 -screen 0 1024x768x24 -nolisten tcp >/dev/null 2>&1 & XP=$!
sleep 1; export DISPLAY=:77
( cd wine/Boom && rm -f CALog.log && env -u WAYLAND_DISPLAY WINEDEBUG=-all timeout 90 wine ca_fixed_patched.exe >/dev/null 2>&1 ) & WP=$!
sleep 12
for a in 1 2 3 4; do
  xdotool mousemove 575 602 click 1; sleep 0.4; xdotool type --delay 60 tester; sleep 0.2
  xdotool mousemove 575 634 click 1; sleep 0.4; xdotool type --delay 60 1234; sleep 0.2
  xdotool mousemove 581 733 click 1; sleep 7
done
sleep 3; import -window root $OUT/tab_before.png
# click the > arrow (next category/mode) and the < arrow and the top game-mode icons
xdotool mousemove 663 97 click 1; sleep 2; import -window root $OUT/tab_right.png
xdotool mousemove 373 97 click 1; sleep 2; import -window root $OUT/tab_left.png
xdotool mousemove 250 68 click 1; sleep 2; import -window root $OUT/tab_mode.png
wait $WP; kill $XP 2>/dev/null
