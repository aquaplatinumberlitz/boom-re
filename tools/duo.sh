#!/bin/sh
# Two clients at once (multiplayer tests): A = Xvfb :77, WINEPREFIX ~/.wine, wine/Boom; B = Xvfb :78, WINEPREFIX ~/.wine2, wine/Boom2
# (separate Wine prefixes -> separate wineserver -> the client's single-instance mutex does not collide).
# usage: tools/duo.sh <outdir> [secs]      env: RUST=1 (Rust server), CLICKS_A / CLICKS_B ("x,y,wait ..." after the lobby),
#        KEYS_A / KEYS_B (xdotool keys after stage 13, "key:hold:wait ..."), plus every server env (AUTO_START, ...)
OUT=$(realpath -m "$1"); SECS=${2:-420}
mkdir -p "$OUT"
cd /home/admin/boom-re
pkill -9 -f "[c]a_fixed_patched" 2>/dev/null; pkill -9 -f "[X]vfb :7[78]" 2>/dev/null; sleep 1
cp ca_fixed_patched.exe wine/Boom2/ 2>/dev/null
$( [ -n "$RUST" ] && echo server/target/release/boom-server || echo python3 tools/fakeserver.py ) --log "$OUT/server.log" > "$OUT/server.out" 2>&1 & FS=$!

client() {  # $1 = A|B  $2 = display  $3 = prefix  $4 = game dir  $5 = user
  tag=$1; D=$2; PFX=$3; DIR=$4; USER=$5
  Xvfb :$D -screen 0 1024x768x24 -nolisten tcp >/dev/null 2>&1 &
  sleep 1
  ( cd "$DIR" && rm -f CALog.log && DISPLAY=:$D WINEPREFIX=$PFX WINEDEBUG=-all timeout "$SECS" wine ca_fixed_patched.exe > "$OUT/wine_$tag.txt" 2>&1 ) &
  (
    export DISPLAY=:$D
    log="$DIR/CALog.log"
    for a in $(seq 1 18); do
      grep -q 'dne:10' "$log" 2>/dev/null && break
      xdotool mousemove 575 602 click 1; sleep 0.4; xdotool type --delay 50 "$USER"; sleep 0.2
      xdotool mousemove 575 634 click 1; sleep 0.4; xdotool type --delay 50 1234; sleep 0.2
      xdotool mousemove 581 733 click 1; sleep 10
    done
    for a in $(seq 1 30); do grep -q 'dne:10' "$log" 2>/dev/null && break; sleep 5; done
    sleep 20; xdotool mousemove 650 393 click 1
    for a in $(seq 1 40); do grep -q 'dne:11' "$log" 2>/dev/null && break; sleep 5; done
    sleep 20; import -window root "$OUT/${tag}_lobby.png" 2>/dev/null
    eval "clicks=\${CLICKS_$tag}"
    i=0
    for c in $clicks; do
      i=$((i+1)); x=${c%%,*}; r=${c#*,}; y=${r%%,*}; w=${r#*,}
      xdotool mousemove "$x" "$y" click 1; sleep "$w"; import -window root "$OUT/${tag}_click_$i.png" 2>/dev/null
    done
    for a in $(seq 1 60); do grep -q 'dne:13' "$log" 2>/dev/null && break; sleep 5; done
    echo "$tag dne13 $(date +%T)" >> "$OUT/driver.txt"
    sleep 40; import -window root "$OUT/${tag}_match.png" 2>/dev/null
    eval "keys=\${KEYS_$tag}"
    i=0
    for k in $keys; do
      i=$((i+1)); key=${k%%:*}; r=${k#*:}; hold=${r%%:*}; w=${r#*:}
      xdotool keydown "$key"; sleep "$hold"; xdotool keyup "$key"; sleep "$w"
      import -window root "$OUT/${tag}_step_$i.png" 2>/dev/null
    done
    echo "$tag done $(date +%T)" >> "$OUT/driver.txt"
    cp "$log" "$OUT/CALog_$tag.log"
  ) &
}
client A 77 "$HOME/.wine" wine/Boom tester
sleep 15
client B 78 "$HOME/.wine2" wine/Boom2 tester2
sleep "$SECS"
pkill -9 -f "[c]a_fixed_patched" 2>/dev/null; pkill -9 -f "[X]vfb :7[78]" 2>/dev/null
kill $FS 2>/dev/null
cat "$OUT/driver.txt" 2>/dev/null
