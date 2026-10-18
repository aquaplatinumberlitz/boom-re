#!/bin/sh
# Retry the automated WinBoat snapshot run (win/snap_bisect.bat) until pre.snap appears (the original client dies at random
# when code is patched). usage: tools/snap_retry.sh [max_tries]
cd /home/admin/boom-re
D=logs/snap/BISECT
for n in $(seq 1 ${1:-8}); do
  rm -f $D/done $D/pre.snap $D/post.snap
  P=$(docker port WinBoat 3389/tcp | head -1 | cut -d: -f2)
  timeout 480 xfreerdp3 /u:admin /p:admin /v:127.0.0.1 /port:$P /cert:ignore \
    '/app:program:C:\Windows\System32\cmd.exe,cmd:/c \\host.lan\Data\boom-re\win\snap_bisect_run.bat' > logs/rdp_bisect.log 2>&1 &
  RP=$!
  for i in $(seq 1 90); do sleep 5; [ -f $D/done ] && break; done
  kill -9 $RP 2>/dev/null
  echo "try $n: $(tail -2 $D/snap.log | tr '\n' ' ') | $(tail -1 $D/CALog.log)"
  [ -f $D/pre.snap ] && { echo GOT pre.snap; exit 0; }
done
echo "no snapshot"; exit 1
