#!/bin/sh
# Build the runnable dump and run it under winedbg in wine/Boom:
#   unpacked_ca.exe --fix_iat--> ca_fixed.exe --devirt--> ca_devirt.exe --patch_client--> ca_fixed_patched.exe
# usage: tools/rebuild_wine.sh [server_ip]     (TIMEOUT=seconds env, default 120)
set -e
cd "$(dirname "$0")/.."
uv run --quiet --with unicorn --with pefile python -I tools/fix_iat.py build unpacked_ca.exe ca_fixed.exe
uv run --quiet --with pefile --with keystone-engine python -I tools/devirt.py ca_fixed.exe ca_devirt.exe
uv run --quiet --with pefile python -I tools/patch_client.py ca_devirt.exe ca_fixed_patched.exe "${1:-127.0.0.1}" | tail -1
cp ca_fixed_patched.exe wine/Boom/
cd wine/Boom && rm -f CALog.log
printf 'cont\ncont\nbt\ninfo regs\nquit\n' | WINEDEBUG=-all timeout "${TIMEOUT:-120}" wine winedbg 'Z:\home\admin\boom-re\wine\Boom\ca_fixed_patched.exe' > ../../logs/winedbg.log 2>&1 || true
grep -v '^Wine-dbg>$' ../../logs/winedbg.log | grep -E 'Unhandled|=>|^  [0-9]|EIP|EAX' | head -12
tail -5 CALog.log 2>/dev/null || true
