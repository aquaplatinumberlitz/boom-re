#!/bin/sh
# one single-player match on Village01 per room type (types that allow 1 player: 14 16 17 19 22 32 33)
cd /home/admin/boom-re
for t in "$@"; do
  pkill -f "[b]oom-server --log /home/admin/boom-re/logs/(maps|roomtypes)/"; pkill -9 -f "[c]a_fixed_patched"; pkill -9 -f "[X]vfb :77"
  WINEPREFIX=$HOME/.wine wineserver -k 2>/dev/null; sleep 3
  out=logs/roomtypes/t$t
  rm -rf "$out"; mkdir -p "$out"
  RUST=1 MAP_INDEX=0 ROOM_TYPE=$t TURN_MODE=1 PLAY_START=4 POST_PLAY_START=2 MATCH_END=6 \
    KEYS="space:0.1:4 Down:0.6:1 Left:0.6:1 Up:0.6:1 Right:0.6:1" \
    timeout 330 sh tools/match_play.sh tools/gdb/plain.gdb "$out" 300 > "$out/run.txt" 2>&1
  crash=$(grep -a -c CRASH "$out/gdb.txt" 2>/dev/null)
  stage=$(grep -o 'dne:1[0-9]' "$out/CALog.log" 2>/dev/null | tail -1)
  echo "type $t crash=$crash last=$stage" >> logs/roomtypes/summary.txt
done
