#!/bin/sh
# one single-player match per map index: crash? stage 13? screenshot
cd /home/admin/boom-re
for m in "$@"; do
  pkill -f "[b]oom-server --log /home/admin/boom-re/logs/(maps|roomtypes)/"; pkill -9 -f "[c]a_fixed_patched"; pkill -9 -f "[X]vfb :77"
  WINEPREFIX=$HOME/.wine wineserver -k 2>/dev/null; sleep 3
  idx=${m%%:*}; name=${m#*:}
  out=logs/maps/$name
  rm -rf "$out"; mkdir -p "$out"
  RUST=1 ALL_MAPS=1 BOOM_DIR=wine/Boom MAP_INDEX=$idx ROOM_TYPE=19 TURN_MODE=1 PLAY_START=4 POST_PLAY_START=2 MATCH_END=6 \
    KEYS="space:0.1:4 Down:0.6:1 Left:0.6:1 Up:0.6:1 Right:0.6:1" \
    timeout 330 sh tools/match_play.sh tools/gdb/plain.gdb "$out" 300 > "$out/run.txt" 2>&1
  crash=$(grep -a -c CRASH "$out/gdb.txt" 2>/dev/null)
  stage=$(grep -o 'dne:1[0-9]' "$out/CALog.log" 2>/dev/null | tail -1)
  echo "$idx $name crash=$crash last=$stage" >> logs/maps/summary.txt
done
