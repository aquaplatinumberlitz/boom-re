#!/bin/sh
# Login in a private Xvfb under winedbg with breakpoints; winedbg commands from $BP_CMDS (file).
# usage: tools/xvfb_login_bp.sh cmds.txt [user] [pass]   -> logs/xvfb/login_bp.txt
cd "$(dirname "$0")/.."
CMDS=$(realpath "$1"); U=${2:-tester}; P=${3:-1234}; OUT=logs/xvfb; mkdir -p $OUT
Xvfb :77 -screen 0 1024x768x24 -nolisten tcp >/dev/null 2>&1 & XPID=$!
sleep 1; export DISPLAY=:77
( cd wine/Boom && rm -f CALog.log && cat "$CMDS" \
  | env -u WAYLAND_DISPLAY WINEDEBUG=-all timeout 90 wine winedbg 'Z:\home\admin\boom-re\wine\Boom\ca_fixed_patched.exe' > ../../$OUT/login_bp.txt 2>&1 ) & WPID=$!
sleep 22
xdotool mousemove 575 602 click 1; sleep 0.5; xdotool type --delay 80 "$U"; sleep 0.3
xdotool mousemove 575 634 click 1; sleep 0.5; xdotool type --delay 80 "$P"; sleep 0.3
xdotool mousemove 581 733 click 1
wait $WPID; kill $XPID 2>/dev/null
