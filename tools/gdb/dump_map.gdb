set pagination off
break *0x736C27
commands
silent
printf "SITE ebx=%x ebp=%x esp=%x esi=%x edi=%x eax=%x ecx=%x edx=%x\n", $ebx, $ebp, $esp, $esi, $edi, $eax, $ecx, $edx
python
import gdb
inf = gdb.selected_inferior()
r = {k: int(gdb.parse_and_eval('$' + k)) & 0xffffffff for k in ('ebx','ebp','esp','esi','edi','eax','ecx','edx','eflags')}
out = '/home/admin/boom-re/logs/mapdump/'
open(out + 'regs.txt', 'w').write(' '.join(f'{k}={v:#x}' for k, v in r.items()) + '\n')
def dump(name, lo, size, chunk=0x10000):
    ok = 0
    with open(out + name, 'wb') as f, open(out + name + '.map', 'w') as m:
        for a in range(lo, lo + size, chunk):
            try:
                f.seek(a - lo); f.write(bytes(inf.read_memory(a, chunk))); m.write(f'{a:#x} ok\n'); ok += 1
            except Exception as e:
                m.write(f'{a:#x} fail\n')
    print(f'DUMP {name} {lo:#x} +{size:#x} chunks_ok={ok}')
dump('stack.bin', r['esp'] - 0x1000, 0x3000, 0x1000)
dump('map.bin', r['ebx'], 0xB00000)
end
kill
quit
end
continue
printf "NOSITE\n"
quit
