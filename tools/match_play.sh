#!/bin/sh
# gdb run of a full match + walking test (KEYS=): login -> room -> 501 -> 189 (TURN_MODE) -> 190 -> 189 mode 0 (PLAY_START) -> arrow keys + Space.
# RUST=1: use the Rust server (server/target/release/boom-server) instead of tools/fakeserver.py
# usage: tools/match_gdb.sh <gdb_cmds> <outdir> [secs]   (gdb files: tools/gdb/*.gdb; GREP= pattern to summarise gdb.txt)
S=$(dirname "$(realpath "$0")"); CMDS=$(realpath "$1"); OUT=$(realpath -m "$2"); SECS=${3:-420}
mkdir -p "$OUT"
cd /home/admin/boom-re
pkill -9 -f "[c]a_fixed_patched" 2>/dev/null; pkill -9 -f "[X]vfb :77" 2>/dev/null; sleep 1
AUTO_START=5 TURN_START=10 TURN_MODE=${TURN_MODE:-4} GO_START=3 PLAY_START=${PLAY_START:-0} POST_PLAY_START=${POST_PLAY_START:-0} BOMB_ECHO=${BOMB_ECHO:-0} BOMB_PLACE=${BOMB_PLACE:-0} DEATH_END=${DEATH_END:-0} BEGIN_START=${BEGIN_START:-0} BEGIN_OP=${BEGIN_OP:-191} \
  $( [ -n "$RUST" ] && echo server/target/release/boom-server || echo python3 tools/fakeserver.py ) --log "$OUT/fakeserver.log" > "$OUT/fakeserver.out" 2>&1 & FS=$!
Xvfb :77 -screen 0 1024x768x24 -nolisten tcp >/dev/null 2>&1 & XP=$!
sleep 1; export DISPLAY=:77
( for a in $(seq 1 18); do
    grep -q 'dne:10' wine/Boom/CALog.log 2>/dev/null && break
    xdotool mousemove 575 602 click 1; sleep 0.4; xdotool type --delay 50 tester; sleep 0.2
    xdotool mousemove 575 634 click 1; sleep 0.4; xdotool type --delay 50 1234; sleep 0.2
    xdotool mousemove 581 733 click 1; sleep 10
  done
  for a in $(seq 1 30); do grep -q 'dne:10' wine/Boom/CALog.log 2>/dev/null && break; sleep 5; done
  sleep 20; xdotool mousemove 650 393 click 1
  for a in $(seq 1 40); do grep -q 'dne:11' wine/Boom/CALog.log 2>/dev/null && break; sleep 5; done
  sleep 25; i=0
  for c in 975,38,3 385,50,4 437,612,10 512,384,8; do
    i=$((i+1)); x=${c%%,*}; r=${c#*,}; y=${r%%,*}; w=${r#*,}
    xdotool mousemove "$x" "$y" click 1; sleep "$w"; import -window root "$OUT/click_$i.png" 2>/dev/null
  done
  for a in $(seq 1 40); do grep -q 'dne:13' wine/Boom/CALog.log 2>/dev/null && break; sleep 5; done
  echo "dne13 at $(date +%T)" > "$OUT/driver.txt"
  sleep 60; import -window root "$OUT/match_before.png" 2>/dev/null
  xdotool mousemove 512 400 click 1; sleep 1
  # KEYS="key:hold_s:wait_s ..." (default: bomb, wait for the blast, then try to walk); one screenshot after each step
  i=0
  for k in ${KEYS:-space:0.1:5 Down:1:1 Left:1:1 Down:1:1 Left:1:1 Up:1:1 Right:1:1}; do
    i=$((i+1)); key=${k%%:*}; r=${k#*:}; hold=${r%%:*}; w=${r#*:}
    echo "key $key $(date +%T)" >> "$OUT/driver.txt"
    xdotool keydown "$key"; sleep "$hold"; xdotool keyup "$key"; sleep "$w"
    import -window root "$OUT/step_$i.png" 2>/dev/null
  done
  import -window root "$OUT/match_after.png" 2>/dev/null
  echo "keys done $(date +%T)" >> "$OUT/driver.txt" ) &
CLK=$!
( cd wine/Boom && rm -f CALog.log && cat "$CMDS" \
  | env -u WAYLAND_DISPLAY WINEDEBUG=-all timeout "$SECS" winedbg --gdb 'Z:\home\admin\boom-re\wine\Boom\ca_fixed_patched.exe' > "$OUT/gdb.txt" 2>&1 ) &
GP=$!
wait $GP
kill $CLK $XP $FS 2>/dev/null
cp wine/Boom/CALog.log "$OUT/CALog.log" 2>/dev/null
grep -E -A60 "${GREP:-CRASH|PHASE|PLAY189|ON189|TICK|CC8|CTX32|STRAT|VF15|DA84|KEYMAP|SETEN}" "$OUT/gdb.txt" | grep -v "^Wine-gdb> *$" | head -80
cat "$OUT/driver.txt"
