"""Boom Online (VBNB_116) TCP packet codec, reimplemented from ca.exe.

Addresses refer to unpacked_ca.exe (IDA db unpacked_ca.exe.i64).
Unverified against live traffic -- see docs/protocol.md "Open questions".
"""
import struct
from pathlib import Path

_TABLE_DIR = Path(__file__).resolve().parent.parent / "decomp" / "net"

# --- CRC (Crc32InitTable 0xA26290 / Crc8InitTable 0xA26420) ---------------
def _crc32_table():
    t = []
    for i in range(256):
        c = i << 24
        for _ in range(8):
            c = ((c << 1) ^ 0x04C11DB7) if c & 0x80000000 else (c << 1)
        t.append(c & 0xFFFFFFFF)
    return t

def _crc8_table():
    t = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = ((c << 1) ^ 0x107) if c & 0x80 else (c << 1)
        t.append(c & 0xFF)
    return t

CRC32_T, CRC8_T = _crc32_table(), _crc8_table()

def crc32(init, data):  # Crc32Update 0xA26330
    c = init & 0xFFFFFFFF
    for b in data:
        c = (CRC32_T[(b ^ (c >> 24)) & 0xFF] ^ (c << 8)) & 0xFFFFFFFF
    return c

def crc8(init, data):  # Crc8Update 0xA264C0
    c = init & 0xFF
    for b in data:
        c = CRC8_T[c ^ b]
    return c

# --- payload XOR (PacketEncryptXor 0xA64240 / PacketDecryptXor 0xA642E0) ---
_K0, _KSTEP = 0x53351D9C, 0x63CAACE3  # 1674226915

def _xor_cipher(data, key, encrypt):
    n, tail = divmod(len(data), 4)
    src = struct.unpack_from("<%dI" % n, data) if n else ()
    out = []
    k = (key ^ _K0) & 0xFFFFFFFF
    prev_plain = 0
    for i in range(n):
        if i:
            k = (k - _KSTEP) & 0xFFFFFFFF
        if encrypt:
            plain = src[i]
            out.append(k ^ plain ^ (prev_plain if i else 0))
        else:
            plain = k ^ src[i] ^ (prev_plain if i else 0)
            out.append(plain)
        prev_plain = plain
    if n:
        k = prev_plain  # tail key = last plaintext dword
    res = bytearray(struct.pack("<%dI" % n, *out))
    for j in range(tail):
        res.append(data[4 * n + j] ^ ((k >> (8 * j)) & 0xFF))
    return bytes(res)

def encrypt(data, key):
    return _xor_cipher(data, key, True)

def decrypt(data, key):
    return _xor_cipher(data, key, False)

# --- opcode substitution (g_OpcodeSubstEncTable 0xE5CEE8, Dec 0xE5DEE8) ---
def _load(name):
    p = _TABLE_DIR / name
    return p.read_bytes() if p.exists() else None

OP_ENC, OP_DEC = _load("opcode_enc_table.bin"), _load("opcode_dec_table.bin")

# --- header/format layout (switches in 0xA63EE0, 0xA643F0, 0xA64B70) -------
def layout(hdr_mode):
    """-> (hdr_size, len_size, extra_size, type_size)"""
    a = 1 if hdr_mode in (0, 1, 4, 5) else 2
    b = 4 if hdr_mode in (1, 3, 5) else 2
    c = {4: 1, 5: 4}.get(hdr_mode, 0)
    return a, b, c, a

# Obfuscated big-endian ints used when checksum mode is 1 or 2 (0xA26920..)
XOR = {1: 0x5A, 2: 0xA569, 4: 0x96CA5395}

def put_int(v, size, obf):
    if obf:
        v ^= XOR[size]
    return (v & ((1 << (8 * size)) - 1)).to_bytes(size, "big")

def get_int(buf, size, obf):
    v = int.from_bytes(buf[:size], "big")
    return v ^ XOR[size] if obf else v


class SeqState:
    """CClientSocket fields this[16..24] (see CClientSocket__ReceivePacket debug string)."""

    def __init__(self, base_r=102, base_s=192, modif=231, seq_r=40, seq_s=40, dseq_r=3, dseq_s=3):
        self.header_type = 0  # this[16], set by handshake (SetHeaderType)
        self.have_type = False  # this[17]
        self.base_r, self.base_s, self.modif = base_r, base_s, modif
        self.seq_r, self.seq_s, self.dseq_r, self.dseq_s = seq_r, seq_s, dseq_r, dseq_s

    def set_header_type(self, t):
        self.header_type, self.have_type = t, True

    def make_seq_byte(self):  # CClientSocket__MakeSeqByte 0xA660A0 (send side)
        if self.dseq_s:
            return ((self.header_type + self.modif) ^ (self.base_s + self.seq_s)) & 0xFF
        return self.base_s & 0xFF

    def expected_seq_byte_r(self):  # CClientSocket__CheckSeqByte 0xA66030 (recv side)
        if self.dseq_r:
            return ((self.header_type + self.modif) ^ (self.base_r + self.seq_r)) & 0xFF
        return self.base_r & 0xFF


def build(body, hdr_mode, cks_mode, seq_byte, seq, header_type, substitute=True):
    """Serialize a frame (SendPkt__Serialize). body = [type][opcode u16][fields...] plaintext."""
    a, b, c, tsz = layout(hdr_mode)
    head = bytearray(a)
    head[0] = seq_byte
    if cks_mode in (1, 2):
        k = 4 if cks_mode == 1 else 1
        head += put_int(len(body) + c, b, True)
        head += bytes(c)
        enc = encrypt(body, seq)
        ck = crc32(seq, body).to_bytes(4, "big") if k == 4 else bytes([crc8(seq, body)])
        return bytes(head) + enc + ck
    head += put_int(len(body) + c, b, False)
    head += bytes(c)
    body = bytearray(body)
    if substitute and seq and OP_ENC:
        for i in range(tsz):
            body[i] = OP_ENC[256 * header_type + body[i]]
    return bytes(head) + bytes(body)


def parse(frame, hdr_mode, cks_mode, seq, header_type, substitute=True):
    """Deserialize a frame (RecvPkt__Deserialize). Returns plaintext body."""
    a, b, c, tsz = layout(hdr_mode)
    if cks_mode in (1, 2):
        k = 4 if cks_mode == 1 else 1
        n = get_int(frame[a:], b, True) - c
        enc = frame[a + b + c : a + b + c + n]
        body = decrypt(enc, seq)
        ck = frame[a + b + c + n : a + b + c + n + k]
        want = crc32(seq, body).to_bytes(4, "big") if k == 4 else bytes([crc8(seq, body)])
        if ck != want:
            raise ValueError("checksum mismatch")
        return body
    n = get_int(frame[a:], b, False) - c
    body = bytearray(frame[a + b + c : a + b + c + n])
    if substitute and seq and OP_DEC:
        for i in range(tsz):
            body[i] = OP_DEC[256 * header_type + body[i]]
    return bytes(body)


if __name__ == "__main__":
    import os
    for hdr in range(6):
        for cks in (0, 1, 2):
            for ln in range(0, 23):
                body = os.urandom(max(ln, 3))
                f = build(body, hdr, cks, 0xAB, 43, 7)
                assert parse(f, hdr, cks, 43, 7) == body, (hdr, cks, ln)
    for ln in range(0, 40):
        d = os.urandom(ln)
        assert decrypt(encrypt(d, 0x1234), 0x1234) == d
    print("roundtrip ok")
