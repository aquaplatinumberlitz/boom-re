set pagination off
python
import gdb, struct
def box(addr):
    inf = gdb.selected_inferior()
    p = struct.unpack('<I', bytes(inf.read_memory(addr + 8, 4)))[0]
    raw = bytes(inf.read_memory(p, 5))
    k = raw[4]; out = bytearray(4)
    for i in range(4):
        if k == 0: k = 42
        out[i] = k ^ raw[i]; k = (k + raw[i] + 42) & 0xFF
    return struct.unpack('<I', bytes(out))[0]
class BP(gdb.Breakpoint):
    def stop(self):
        b = int(gdb.parse_and_eval('$ecx')) & 0xffffffff
        try:
            print(f"BOMB obj={b:#x} id168={box(b+168):#x} id280={box(b+280):#x} b192={box(b+192):#x} vt={struct.unpack('<I', bytes(gdb.selected_inferior().read_memory(b,4)))[0]:#x}")
        except Exception as e:
            print('BOMB err', e)
        return False
BP('*0x5910BF')
end
continue
printf "END\n"
quit
