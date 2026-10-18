//! Packet codec, ported from tools/boomproto.py (addresses refer to unpacked_ca.exe).

use std::sync::OnceLock;

// --- CRC (Crc32InitTable 0xA26290 / Crc8InitTable 0xA26420) ---------------
fn crc32_table() -> &'static [u32; 256] {
    static T: OnceLock<[u32; 256]> = OnceLock::new();
    T.get_or_init(|| {
        let mut t = [0u32; 256];
        for (i, e) in t.iter_mut().enumerate() {
            let mut c = (i as u32) << 24;
            for _ in 0..8 {
                c = if c & 0x8000_0000 != 0 { (c << 1) ^ 0x04C1_1DB7 } else { c << 1 };
            }
            *e = c;
        }
        t
    })
}

fn crc8_table() -> &'static [u8; 256] {
    static T: OnceLock<[u8; 256]> = OnceLock::new();
    T.get_or_init(|| {
        let mut t = [0u8; 256];
        for (i, e) in t.iter_mut().enumerate() {
            let mut c = i as u32;
            for _ in 0..8 {
                c = if c & 0x80 != 0 { (c << 1) ^ 0x107 } else { c << 1 };
            }
            *e = c as u8;
        }
        t
    })
}

/// Crc32Update 0xA26330
pub fn crc32(init: u32, data: &[u8]) -> u32 {
    let t = crc32_table();
    data.iter().fold(init, |c, &b| t[((b as u32 ^ (c >> 24)) & 0xFF) as usize] ^ (c << 8))
}

/// Crc8Update 0xA264C0
pub fn crc8(init: u32, data: &[u8]) -> u8 {
    let t = crc8_table();
    data.iter().fold(init as u8, |c, &b| t[(c ^ b) as usize])
}

// --- payload XOR (PacketEncryptXor 0xA64240 / PacketDecryptXor 0xA642E0) ---
const K0: u32 = 0x5335_1D9C;
const KSTEP: u32 = 0x63CA_ACE3;

fn xor_cipher(data: &[u8], key: u32, encrypt: bool) -> Vec<u8> {
    let n = data.len() / 4;
    let mut out = Vec::with_capacity(data.len());
    let mut k = key ^ K0;
    let mut prev_plain = 0u32;
    for i in 0..n {
        if i > 0 {
            k = k.wrapping_sub(KSTEP);
        }
        let src = u32::from_le_bytes(data[4 * i..4 * i + 4].try_into().unwrap());
        let chain = if i > 0 { prev_plain } else { 0 };
        let (word, plain) = if encrypt {
            (k ^ src ^ chain, src)
        } else {
            let p = k ^ src ^ chain;
            (p, p)
        };
        out.extend_from_slice(&word.to_le_bytes());
        prev_plain = plain;
    }
    if n > 0 {
        k = prev_plain; // tail key = last plaintext dword
    }
    for (j, &b) in data[4 * n..].iter().enumerate() {
        out.push(b ^ (k >> (8 * j)) as u8);
    }
    out
}

pub fn encrypt(data: &[u8], key: u32) -> Vec<u8> {
    xor_cipher(data, key, true)
}

pub fn decrypt(data: &[u8], key: u32) -> Vec<u8> {
    xor_cipher(data, key, false)
}

// --- opcode substitution (g_OpcodeSubstEncTable 0xE5CEE8, Dec 0xE5DEE8) ---
static OP_ENC: &[u8] = include_bytes!("../../decomp/net/opcode_enc_table.bin");
static OP_DEC: &[u8] = include_bytes!("../../decomp/net/opcode_dec_table.bin");

/// Header/format layout (switches in 0xA63EE0, 0xA643F0, 0xA64B70) -> (hdr_size, len_size, extra_size, type_size)
pub fn layout(hdr_mode: u8) -> (usize, usize, usize, usize) {
    let a = if matches!(hdr_mode, 0 | 1 | 4 | 5) { 1 } else { 2 };
    let b = if matches!(hdr_mode, 1 | 3 | 5) { 4 } else { 2 };
    let c = match hdr_mode {
        4 => 1,
        5 => 4,
        _ => 0,
    };
    (a, b, c, a)
}

/// XOR keys of the obfuscated big-endian ints (0xA26920..); u64: RecvPkt__Decode8 0xA26980 (only the low dword).
pub fn xor_key(size: usize) -> u64 {
    match size {
        1 => 0x5A,
        2 => 0xA569,
        4 => 0x96CA_5395,
        8 => 0x71B1_8589,
        _ => panic!("bad int size {size}"),
    }
}

pub fn put_int(out: &mut Vec<u8>, v: u64, size: usize, obf: bool) {
    let v = if obf { v ^ xor_key(size) } else { v };
    out.extend_from_slice(&v.to_be_bytes()[8 - size..]);
}

pub fn get_int(buf: &[u8], size: usize, obf: bool) -> u64 {
    let v = buf[..size].iter().fold(0u64, |a, &b| (a << 8) | b as u64);
    if obf {
        v ^ xor_key(size)
    } else {
        v
    }
}

/// Byte run obfuscation (0xA26A10, strings/blobs): 4/2/1-byte chunks, little-endian int ^ key, big-endian out.
pub fn obf_bytes(out: &mut Vec<u8>, raw: &[u8]) {
    let mut i = 0;
    while i < raw.len() {
        let k = chunk(raw.len() - i);
        let v = raw[i..i + k].iter().rev().fold(0u64, |a, &b| (a << 8) | b as u64);
        put_int(out, v, k, true);
        i += k;
    }
}

fn chunk(left: usize) -> usize {
    if left >= 4 {
        4
    } else if left >= 2 {
        2
    } else {
        1
    }
}

/// Windows-1258 (Vietnamese) text, the client's string encoding.
pub fn cp1258(text: &str) -> Vec<u8> {
    encoding_rs::WINDOWS_1258.encode(text).0.into_owned()
}

pub fn from_cp1258(raw: &[u8]) -> String {
    encoding_rs::WINDOWS_1258.decode(raw).0.into_owned()
}

/// RecvPkt__DecodeStr 0xA65E70: [u16 len][bytes], bytes run-obfuscated when `obf`.
pub fn put_str(out: &mut Vec<u8>, raw: &[u8], obf: bool) {
    put_int(out, raw.len() as u64, 2, obf);
    if obf {
        obf_bytes(out, raw)
    } else {
        out.extend_from_slice(raw)
    }
}

/// -> (bytes, consumed)
pub fn get_str(buf: &[u8], obf: bool) -> (Vec<u8>, usize) {
    let n = get_int(buf, 2, obf) as usize;
    if !obf {
        return (buf[2..2 + n].to_vec(), 2 + n);
    }
    let mut out = Vec::with_capacity(n);
    let mut i = 0;
    while i < n {
        let k = chunk(n - i);
        let v = get_int(&buf[2 + i..], k, true);
        out.extend_from_slice(&v.to_le_bytes()[..k]);
        i += k;
    }
    (out, 2 + n)
}

/// RecvPkt__DecodeBlob 0xA658A0: [u32 N][N bytes] = serialized sub-reader (0xA62890):
/// [0x18][u32 LE len][len bytes of plain little-endian fields, read by 0xA62F40/0xA62F70/0xA63A40].
pub fn put_blob(out: &mut Vec<u8>, inner: &[u8], obf: bool) {
    let mut raw = Vec::with_capacity(inner.len() + 5);
    raw.push(0x18);
    raw.extend_from_slice(&(inner.len() as u32).to_le_bytes());
    raw.extend_from_slice(inner);
    put_int(out, raw.len() as u64, 4, obf);
    if obf {
        obf_bytes(out, &raw)
    } else {
        out.extend_from_slice(&raw)
    }
}

/// CClientSocket fields this[16..24] (see CClientSocket__ReceivePacket debug string).
#[derive(Clone, Debug)]
pub struct SeqState {
    pub header_type: u32,
    pub base_r: u32,
    pub base_s: u32,
    pub modif: u32,
    pub seq_r: u32,
    pub seq_s: u32,
    pub dseq_r: u32,
    pub dseq_s: u32,
}

impl Default for SeqState {
    fn default() -> Self {
        SeqState { header_type: 0, base_r: 102, base_s: 192, modif: 231, seq_r: 40, seq_s: 40, dseq_r: 3, dseq_s: 3 }
    }
}

impl SeqState {
    /// Seq byte the client expects on a frame it receives (CClientSocket__CheckSeqByte 0xA66030).
    pub fn recv_seq_byte(&self) -> u8 {
        if self.dseq_r != 0 {
            ((self.header_type + self.modif) ^ (self.base_r + self.seq_r)) as u8
        } else {
            self.base_r as u8
        }
    }

    /// Seq byte the client puts on a frame it sends (CClientSocket__MakeSeqByte 0xA660A0).
    pub fn send_seq_byte(&self) -> u8 {
        if self.dseq_s != 0 {
            ((self.header_type + self.modif) ^ (self.base_s + self.seq_s)) as u8
        } else {
            self.base_s as u8
        }
    }
}

/// Serialize a frame (SendPkt__Serialize). body = plaintext [type/opcode][fields...].
pub fn build(body: &[u8], hdr_mode: u8, cks_mode: u8, seq_byte: u8, seq: u32, header_type: u32) -> Vec<u8> {
    let (a, b, c, tsz) = layout(hdr_mode);
    let mut out = vec![0u8; a];
    out[0] = seq_byte;
    if matches!(cks_mode, 1 | 2) {
        put_int(&mut out, (body.len() + c) as u64, b, true);
        out.extend(std::iter::repeat(0).take(c));
        out.extend_from_slice(&encrypt(body, seq));
        if cks_mode == 1 {
            out.extend_from_slice(&crc32(seq, body).to_be_bytes());
        } else {
            out.push(crc8(seq, body));
        }
        return out;
    }
    put_int(&mut out, (body.len() + c) as u64, b, false);
    out.extend(std::iter::repeat(0).take(c));
    let start = out.len();
    out.extend_from_slice(body);
    if seq != 0 {
        for i in 0..tsz.min(body.len()) {
            out[start + i] = OP_ENC[256 * header_type as usize + body[i] as usize];
        }
    }
    out
}

/// Total frame length if `buf` starts with a complete frame, else None.
pub fn frame_len(buf: &[u8], hdr_mode: u8, cks_mode: u8) -> Option<usize> {
    let (a, b, c, _) = layout(hdr_mode);
    if buf.len() < a + b {
        return None;
    }
    let n = (get_int(&buf[a..], b, matches!(cks_mode, 1 | 2)) as usize).checked_sub(c)?;
    let total = a + b + c + n + match cks_mode {
        1 => 4,
        2 => 1,
        _ => 0,
    };
    (buf.len() >= total).then_some(total)
}

#[derive(Debug, PartialEq, Eq)]
pub struct ChecksumMismatch;

/// Deserialize a frame (RecvPkt__Deserialize). Returns the plaintext body.
pub fn parse(frame: &[u8], hdr_mode: u8, cks_mode: u8, seq: u32, header_type: u32) -> Result<Vec<u8>, ChecksumMismatch> {
    let (a, b, c, tsz) = layout(hdr_mode);
    if matches!(cks_mode, 1 | 2) {
        let n = get_int(&frame[a..], b, true) as usize - c;
        let enc = &frame[a + b + c..a + b + c + n];
        let body = decrypt(enc, seq);
        let ck = &frame[a + b + c + n..];
        let ok = if cks_mode == 1 {
            ck[..4] == crc32(seq, &body).to_be_bytes()
        } else {
            ck[0] == crc8(seq, &body)
        };
        return if ok { Ok(body) } else { Err(ChecksumMismatch) };
    }
    let n = get_int(&frame[a..], b, false) as usize - c;
    let mut body = frame[a + b + c..a + b + c + n].to_vec();
    if seq != 0 {
        for i in 0..tsz.min(body.len()) {
            body[i] = OP_DEC[256 * header_type as usize + body[i] as usize];
        }
    }
    Ok(body)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip_all_formats() {
        let mut x: u32 = 12345;
        for hdr in 0..6 {
            for cks in [0, 1, 2] {
                for len in 0..23usize {
                    let body: Vec<u8> = (0..len.max(3))
                        .map(|_| {
                            x = x.wrapping_mul(1_103_515_245).wrapping_add(12345);
                            (x >> 16) as u8
                        })
                        .collect();
                    let f = build(&body, hdr, cks, 0xAB, 43, 7);
                    assert_eq!(frame_len(&f, hdr, cks), Some(f.len()));
                    assert_eq!(parse(&f, hdr, cks, 43, 7).unwrap(), body, "hdr {hdr} cks {cks} len {len}");
                }
            }
        }
    }

    #[test]
    fn cipher_roundtrip() {
        for len in 0..40usize {
            let d: Vec<u8> = (0..len as u8).collect();
            assert_eq!(decrypt(&encrypt(&d, 0x1234), 0x1234), d);
        }
    }
}
