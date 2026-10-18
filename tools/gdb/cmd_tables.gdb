set pagination off
break *0x6EFEDC
commands
silent
python
import gdb, struct
inf = gdb.selected_inferior()
out = open('/home/admin/boom-re/logs/cmd_tables.txt', 'w')
for name, base in (('EA78E8', 0xEA78E8), ('E64B20', 0xE64B20)):
    data = bytes(inf.read_memory(base, 0x1000 * 4))
    for op in range(0x1000):
        p = struct.unpack_from('<I', data, op * 4)[0]
        if p:
            try:
                vt = struct.unpack('<I', bytes(inf.read_memory(p, 4)))[0]
            except Exception:
                vt = 0
            out.write(f'{name} {op} obj={p:#x} vt={vt:#x}\n')
out.close()
print('TABLES dumped')
end
kill
quit
end
continue
printf "END\n"
quit
