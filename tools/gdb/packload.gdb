set pagination off
python
import gdb, re
class P(gdb.Breakpoint):
    def stop(self):
        esp = int(gdb.parse_and_eval('$esp'))
        inf = gdb.selected_inferior()
        a = int.from_bytes(bytes(inf.read_memory(esp + 4, 4)), 'little')
        try:
            s = bytes(inf.read_memory(a, 96)).split(b'\0')[0]
        except Exception:
            return False
        if re.search(rb'(?i)square|map/|theme', s):
            print('LOAD ' + s.decode('latin1'))
        return False
P('*0xA37880')
end
continue
