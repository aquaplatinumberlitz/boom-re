set pagination off
python
import gdb, re
seen = set()
def rd(addr, n=64):
    try:
        b = bytes(gdb.selected_inferior().read_memory(addr, n))
        return b.split(b'\0')[0]
    except Exception:
        return b''
class K(gdb.Breakpoint):
    def stop(self):
        esp = int(gdb.parse_and_eval('$esp'))
        a = int.from_bytes(bytes(gdb.selected_inferior().read_memory(esp + 4, 4)), 'little')
        cands = [rd(a)]
        try:
            p = int.from_bytes(bytes(gdb.selected_inferior().read_memory(a, 4)), 'little')
            cands.append(rd(p))
        except Exception:
            pass
        for c in cands:
            if re.fullmatch(rb'[A-Za-z_][A-Za-z0-9_%]{1,60}', c) and c not in seen:
                seen.add(c)
                print('KEY ' + c.decode())
        return False
K('*0x98DB56')
end
continue
