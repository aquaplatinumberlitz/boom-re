#!/bin/sh
# Run ca_fixed_patched.exe under winedbg --gdb (gdb proxy, stable), feed a gdb command file, and do the
# login clicks via xdotool in parallel. The gdb proxy lets gdb read inferior memory reliably (unlike
# interactive winedbg). usage: tools/wine_gdb.sh <gdb_cmd_file> [user] [pass] [secs]  -> logs/xvfb/gdb.txt
cd "$(dirname "$0")/.."
CMDS=$(realpath "$1"); U=${2:-tester}; P=${3:-1234}; SECS=${4:-80}; OUT=logs/xvfb; mkdir -p $OUT
pkill -9 -f "[c]a_fixed_patched" 2>/dev/null; pkill -9 -f "[X]vfb :77" 2>/dev/null; sleep 1
Xvfb :77 -screen 0 1024x768x24 -nolisten tcp >/dev/null 2>&1 & XP=$!
sleep 1; export DISPLAY=:77
# login clicks in the background. Under winedbg --gdb start-up is ~3x slower than plain wine, so keep retrying
# (up to ~3 min) until CALog shows the channel stage (dne:10) instead of a fixed short window.
( for a in $(seq 1 18); do
    grep -q 'dne:10' wine/Boom/CALog.log 2>/dev/null && break
    xdotool mousemove 575 602 click 1; sleep 0.4; xdotool type --delay 50 "$U"; sleep 0.2
    xdotool mousemove 575 634 click 1; sleep 0.4; xdotool type --delay 50 "$P"; sleep 0.2
    xdotool mousemove 581 733 click 1; sleep 10
  done ) &
CLK=$!
( cd wine/Boom && rm -f CALog.log && cat "$CMDS" \
  | env -u WAYLAND_DISPLAY WINEDEBUG=-all timeout "$SECS" winedbg --gdb 'Z:\home\admin\boom-re\wine\Boom\ca_fixed_patched.exe' > ../../$OUT/gdb.txt 2>&1 ) &
GP=$!
# screenshots near the end (channel screen should be up by then)
( sleep $((SECS-20)); for t in 0 6 12; do sleep $t; import -window root "$OUT/gdbshot_$t.png" 2>/dev/null; done ) &
wait $GP
kill $CLK $XP 2>/dev/null
grep -vE '^Wine-gdb> *$|warning: remote' "$OUT/gdb.txt" | grep -v '^$'
