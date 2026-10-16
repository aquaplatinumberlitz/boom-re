"""Logging fake server for Boom Online. Stage 0: accept, log everything, optionally send a canned reply.

usage: python3 tools/fakeserver.py [--ports 3838,4848,5858,6868] [--log logs/fakeserver.log]
"""
import argparse, asyncio, datetime, pathlib, struct, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import boomproto as bp

CLIENT_VERSION = 116  # sub_8E2494
HEADER_TYPE = 0       # row of the opcode substitution table, 0..15


def hello_packet(header_type=HEADER_TYPE, version=CLIENT_VERSION):
    """First packet from server on every connection (PatchServer_CheckVersion 0x8E426E / Net_OnHandshake 0x999C02).
    Format (0,0): [seq][len u16][type u8 (substituted)][u16 ?][u16 version][u32 header_type][str][u8 flag]."""
    st = bp.SeqState()
    st.header_type = header_type
    seq_byte = ((header_type + st.modif) ^ (st.base_r + st.seq_r)) & 0xFF  # decoded by CheckSeqByte 0xA66030
    body = bytes([0]) + struct.pack(">HHI", 0, version, header_type) + struct.pack(">H", 0) + bytes([0])
    return bp.build(body, hdr_mode=0, cks_mode=0, seq_byte=seq_byte, seq=st.seq_r, header_type=header_type)

SIZES = {"u8": 1, "u16": 2, "u32": 4, "u64": 8}


def obf_body(opcode, *fields):
    """Body for formats with checksum mode 1/2: [opcode u16][fields], every int XOR-obfuscated (put_int obf=True).
    fields: ('u8'|'u16'|'u32'|'u64', value) or ('str', text)"""
    out = bp.put_int(opcode, 2, True)
    for kind, v in fields:
        if kind == "str":
            out += bp.put_str(v, True)
        elif kind == "blob":
            out += bp.put_blob(v, True)
        else:
            out += bp.put_int(v, SIZES[kind], True)
    return out


def login_net_info(host="127.0.0.1", ports=(0, 0, 0)):
    """CLoginStage__On_15 0x84FE35: blob {str host, u16 x3 (-> sub_8E289C), u8 mode (0 none / 1: 2 str / 2: u16), u16}.
    Moves CWaitForLoginDlg from state 2 (set by login_ok) to 1; 10 ticks later the dialog ends with 3 ->
    sub_84FABC -> stage 10 (SelectServer)."""
    h = host.encode()
    inner = struct.pack("<I", len(h)) + h + struct.pack("<HHH", *ports) + bytes([0]) + struct.pack("<H", 0)
    return obf_body(15, ("blob", inner))


def channel_list(names=("Kenh 1", "Kenh 2", "Kenh 3", "Kenh 4")):
    """CStage__On_14 -> sub_99489D: u8 1 = new data (cached by the client), blob {u16 n, n records (sub_994663):
    str name, u32, u8 x7, u16 x2, u8 x4, u32 x2}. Field meanings: unknown yet (zeros except a running id)."""
    inner = struct.pack("<H", len(names))
    for i, n in enumerate(names):
        inner += _lstr(n) + struct.pack("<I", i + 1) + bytes(7) + struct.pack("<HH", 0, 0) + bytes(4) + struct.pack("<II", 0, 0)
    return obf_body(14, ("u8", 1), ("blob", inner))


def channel_status(users=(10, 20, 30, 40)):
    """CSelectServerStage__On_16 / CLoginStage__On_16: blob {u16 n, n x (u16, u32)} -> CChannelInfo (sub_9949C6)."""
    inner = struct.pack("<H", len(users))
    for i, u in enumerate(users):
        inner += struct.pack("<HI", i, u)
    return obf_body(16, ("blob", inner))


def login_ok(name="tester", players=1):
    """CLoginStage__On_4 0x8534F3: u8 result 0 = success -> sub_852BCA 0x852BCA (field order from the decompile;
    meaning of most fields still unknown, zeros are accepted). `players` must equal the 1P/2P count
    (CLobbyStage__On_218(dword_E60880))."""
    f = [("u8", 0),                                   # result: 0 ok, 1 not registered, ...
         ("u8", 0), ("u16", 0), ("u8", players), ("u64", 0)]
    for i in range(players):
        f += [("u32", 1000 + i), ("u32", 0), ("u16", 0), ("u16", 0),   # sub_9B698F, sub_9B69AB
              ("u32", 0), ("str", name), ("u8", 0),                    # sub_99A71D, sub_99A746 (name), sub_99AC50
              ("str", name), ("str", ""),                              # sub_99A817, sub_99A783
              ("u8", 0), ("u32", 0), ("u8", 0), ("u8", 0), ("u16", 0), ("u8", 0), ("u8", 0),
              ("u32", 0), ("u32", 0), ("u8", 0), ("u8", 0), ("u8", 0),
              ("u16", 0), ("u16", 0),                                  # only if !Feature_IsDisabled(6): stub -> always
              ("u32", 0),                                              # sub_99AC6C
              ("u8", 0), ("u8", 0), ("u32", 0), ("u8", 0), ("u8", 0),
              ("u32", 0),                                              # count of (u32, u32) pairs
              ("u8", 0)]
    f += [("u8", 0), ("u8", 0), ("u8", 0), ("u16", 0), ("u8", 0),
          ("u8", 0)]                                  # 1 = "need to change password" dialog
    return obf_body(4, *f)


class Session:
    """Per-connection crypto state as seen from the server (mirror of CClientSocket fields)."""

    def __init__(self):
        self.st = bp.SeqState()
        self.st.header_type = HEADER_TYPE
        self.recv_buf = b""

    def send(self, body, hdr_mode=3, cks_mode=2):
        """Server->client after handshake: client recv format (2,3), key = client's seq_r."""
        st = self.st
        seq_byte = ((st.header_type + st.modif) ^ (st.base_r + st.seq_r)) & 0xFF
        frame = bp.build(body, hdr_mode, cks_mode, seq_byte, st.seq_r, st.header_type)
        st.seq_r += st.dseq_r
        return frame

    def feed(self, data, hdr_mode=2, cks_mode=2):
        """Client->server frames (format (2,2), key = client's seq_s). Yields plaintext bodies."""
        self.recv_buf += data
        a, b, c, _ = bp.layout(hdr_mode)
        while len(self.recv_buf) >= a + b:
            n = bp.get_int(self.recv_buf[a:], b, cks_mode in (1, 2)) - c
            total = a + b + c + n + (4 if cks_mode == 1 else 1 if cks_mode == 2 else 0)
            if len(self.recv_buf) < total:
                break
            frame, self.recv_buf = self.recv_buf[:total], self.recv_buf[total:]
            body = bp.parse(frame, hdr_mode, cks_mode, self.st.seq_s, self.st.header_type)
            self.st.seq_s += self.st.dseq_s
            yield body


def _lstr(text):
    """string inside a blob sub-reader (0xA63A40): u32 LE length + bytes"""
    b = text.encode("cp1258", errors="replace")
    return struct.pack("<I", len(b)) + b


DEFAULT_ENDPOINTS = tuple(("127.0.0.1", p, 1) for p in (3838, 4848, 5858, 6868))


def multisvr_blob(servers=(("Boom", "Fake server", 0),), endpoints=DEFAULT_ENDPOINTS, flag=0):
    """sub_998CCF 0x998CCF (cached as multisvr.ssd): u8 n {str, str, u32} (sub_9986F3), u16 m {u32 in_addr, u16 port, u8}
    (sub_998760), u8 flag (CMultiServer+0x3C). Built-in defaults (CMultiServer__ctor / CMultiServer__AddDefaultServers):
    one group {"Default Server List", "This is built in ...", 0}, endpoints {ip, 3838/4848/5858/6868, 1}."""
    out = bytes([len(servers)])
    for a, b, v in servers:
        out += _lstr(a) + _lstr(b) + struct.pack("<I", v)
    out += struct.pack("<H", len(endpoints))
    for ip, port, g in endpoints:
        out += bytes(int(x) for x in ip.split(".")) + struct.pack("<HB", port, g)
    return out + bytes([flag])


def multisvrn_blob(entries=((1, "Kenh 1", ""),)):
    """sub_998EA0 0x998EA0 (cached as multisvrn.ssd): u8 n {u8, str, str} (sub_998690)."""
    out = bytes([len(entries)])
    for i, a, b in entries:
        out += bytes([i]) + _lstr(a) + _lstr(b)
    return out


def login_replies():
    """Login_DoLoginSequence 0x8E2DEC waits for 13, 2, 12, 21, 1, 43 in this order.
    Each starts with a u8 'have new data' flag; 0 = use local cache."""
    return [
        obf_body(13, ("u8", 0)),           # CStage__On_13: dyn image info
        obf_body(2, ("u8", 0)),            # FxClientString
        obf_body(12, ("u8", 0)),           # FxQuestString
        obf_body(21, ("u8", 0)),           # FxMessageTable
        obf_body(1, ("u8", 0), ("u8", 0)),  # sub_99933B: 0 = keep built-in list; 1 + multisvr_blob() breaks the
                                            # main connection (ErrCannotLogin) - endpoint fields not fully known yet
        obf_body(43, ("u8", 0)),           # sub_982A90
    ]


def hexdump(b, width=16):
    out = []
    for i in range(0, len(b), width):
        chunk = b[i:i + width]
        out.append(f"  {i:04x}  {chunk.hex(' '):<{width * 3}} {''.join(chr(c) if 32 <= c < 127 else '.' for c in chunk)}")
    return "\n".join(out)


class Logger:
    def __init__(self, path):
        self.path = pathlib.Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, msg):
        line = f"{datetime.datetime.now():%H:%M:%S.%f} {msg}"
        print(line, flush=True)
        with self.path.open("a") as f:
            f.write(line + "\n")


async def handle(reader, writer, port, log):
    peer = writer.get_extra_info("peername")
    log(f"[{port}] connect from {peer}")
    pkt = hello_packet()
    writer.write(pkt)
    await writer.drain()
    log(f"[{port}] S->C hello {len(pkt)} bytes\n{hexdump(pkt)}")
    sess = Session()
    sess.st.seq_r += sess.st.dseq_r  # hello consumed one recv sequence step on the client
    try:
        while True:
            data = await asyncio.wait_for(reader.read(65536), timeout=120)
            if not data:
                break
            log(f"[{port}] C->S {len(data)} bytes\n{hexdump(data)}")
            try:
                bodies = list(sess.feed(data))
            except Exception as e:
                log(f"[{port}] decode error: {e!r}")
                continue
            for body in bodies:
                op = bp.get_int(body, 2, True)
                log(f"[{port}] C->S opcode {op} body {body.hex()}")
                replies = []
                if op == 1:  # login request (u8 players, str id, str password: both encrypted, accepted as is)
                    replies = [login_ok(), login_net_info()]
                if op == 40:  # sent on entering the channel screen; the channel cache file name
                    # (channel2_%03d%s.ssd, sub_993EF4) only exists from now on -> channel list must come after it
                    replies = [channel_list(), channel_status()]
                if op == 0:
                    replies = login_replies()
                if replies:
                    for r in replies:
                        frame = sess.send(r)
                        writer.write(frame)
                        log(f"[{port}] S->C opcode {bp.get_int(r, 2, True)} {frame.hex()}")
                    await writer.drain()
    except asyncio.TimeoutError:
        log(f"[{port}] idle timeout")
    except ConnectionError as e:
        log(f"[{port}] {e!r}")
    finally:
        log(f"[{port}] close {peer}")
        writer.close()


async def main(ports, logpath):
    log = Logger(logpath)
    servers = []
    for p in ports:
        srv = await asyncio.start_server(lambda r, w, p=p: handle(r, w, p, log), "0.0.0.0", p)
        servers.append(srv)
        log(f"listening on {p}")
    await asyncio.gather(*(s.serve_forever() for s in servers))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ports", default="3838,4848,5858,6868")
    ap.add_argument("--log", default=str(pathlib.Path(__file__).resolve().parent.parent / "logs" / "fakeserver.log"))
    a = ap.parse_args()
    asyncio.run(main([int(x) for x in a.ports.split(",")], a.log))
