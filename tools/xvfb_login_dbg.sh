#!/bin/sh
# Like xvfb_login.sh but under winedbg (first-chance exceptions + backtraces) -> logs/xvfb/login_dbg.txt
cd "$(dirname "$0")/.."
U=${1:-tester}; P=${2:-1234}; OUT=logs/xvfb; mkdir -p $OUT
Xvfb :77 -screen 0 1024x768x24 -nolisten tcp >/dev/null 2>&1 & XPID=$!
sleep 1; export DISPLAY=:77
( cd wine/Boom && rm -f CALog.log && ( printf 'set $BreakOnFirstChance=1\n'; for i in 1 2 3 4 5 6 7 8 9 10 11 12; do printf 'cont\nbt\ninfo regs\n'; done; printf 'quit\n' ) \
  | env -u WAYLAND_DISPLAY WINEDEBUG=-all timeout 70 wine winedbg 'Z:\home\admin\boom-re\wine\Boom\ca_fixed_patched.exe' > ../../$OUT/login_dbg.txt 2>&1 ) & WPID=$!
sleep 22
xdotool mousemove 575 602 click 1; sleep 0.5; xdotool type --delay 80 "$U"; sleep 0.3
xdotool mousemove 575 634 click 1; sleep 0.5; xdotool type --delay 80 "$P"; sleep 0.3
xdotool mousemove 581 733 click 1
sleep 15; import -window root $OUT/login_dbg.png
wait $WPID; kill $XPID 2>/dev/null
grep -E 'Unhandled|First chance|=>|^  [0-9] ' $OUT/login_dbg.txt | head -30
