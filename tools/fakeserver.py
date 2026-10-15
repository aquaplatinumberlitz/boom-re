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

def obf_body(opcode, *fields):
    """Body for formats with checksum mode 1/2: [opcode u16][fields], every int XOR-obfuscated (put_int obf=True).
    fields: ('u8'|'u16'|'u32', value)"""
    out = bp.put_int(opcode, 2, True)
    for kind, v in fields:
        out += bp.put_int(v, {"u8": 1, "u16": 2, "u32": 4}[kind], True)
    return out


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


def login_replies():
    """Login_DoLoginSequence 0x8E2DEC waits for 13, 2, 12, 21, 1, 43 in this order.
    Each starts with a u8 'have new data' flag; 0 = use local cache."""
    return [
        obf_body(13, ("u8", 0)),           # CStage__On_13: dyn image info
        obf_body(2, ("u8", 0)),            # FxClientString
        obf_body(12, ("u8", 0)),           # FxQuestString
        obf_body(21, ("u8", 0)),           # FxMessageTable
        obf_body(1, ("u8", 0), ("u8", 0)), # multisvr.ssd / multisvrn.ssd
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
                if op == 0:
                    for r in login_replies():
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
