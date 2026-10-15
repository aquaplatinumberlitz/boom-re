# Boom Online TCP protocol (VBNB_116 client)

Tìm từ `unpacked_ca.exe` (IDA: `unpacked_ca.exe.i64`). Code tham chiếu: `tools/boomproto.py`.

Độ tin cậy:
- ✅ **đã kiểm chứng**: chạy code thật của binary trong Unicorn và so với Python (`tools/verify_emu.py`).
- 🟢 **đọc từ decompile**: logic rõ ràng nhưng chưa chạy thử.
- ❓ **chưa chắc**.

## Lớp socket

| Class / hàm | Địa chỉ | Vai trò |
|---|---|---|
| `CClientSocket::Connect` | 0xA68850 | connect TCP |
| `CClientSocket::Read/Write` | 0xA69010 / 0xA69150 | `recv` / `send` |
| `CPacketSocket::RecvToBuffer` | 0xA66260 | đọc vào buffer |
| `CClientSocket::ProcessRecvPacket` | 0xA662E0 | kiểm seq byte → cắt frame → giải mã |
| `CPacketSocket::SendPacket` | 0xA663E0 | mã hoá → ghi seq byte → gửi |
| `CClientSocket::ReceivePacket` (vf20) | 0x884383 | wrapper, có chuỗi debug liệt kê tên trường |
| `Net_DispatchMainSocket` | 0x8F4094 | vòng nhận packet chính |
| `CMainWnd::OnPacket` | 0x8F995D | định tuyến packet |
| `Net_OnHandshake` | 0x999C02 | packet đầu tiên từ server |

Constructor `CClientSocket` (0x8842DD) đặt các trường:

| Trường | Tên (theo chuỗi debug) | Giá trị đầu |
|---|---|---|
| this[16] | header type | 0, server cấp qua handshake |
| this[18] / this[19] | base (r) / (s) | 102 / 192 |
| this[20] | modif | 231 |
| this[21] / this[22] | seq (r) / (s) | 40 / 40 |
| this[23] / this[24] | deltaseq (r) / (s) | 3 / 3 |

## Frame

```
[hdr: A byte][len: B byte][extra: C byte][payload ...][checksum: K byte]
```
Kích thước theo **header mode** (switch trong 0xA63EE0 / 0xA643F0 / 0xA64B70) — 🟢

| mode | A (hdr) | B (len) | C (extra) | type size |
|---|---|---|---|---|
| 0 | 1 | 2 | 0 | 1 |
| 1 | 1 | 4 | 0 | 1 |
| 2 | 2 | 2 | 0 | 2 |
| 3 | 2 | 4 | 0 | 2 |
| 4 | 1 | 2 | 1 | 1 |
| 5 | 1 | 4 | 4 | 1 |

`len` = độ dài payload + C. Mọi số nguyên đều **big-endian**.

**Checksum mode**:
- 0 → không mã hoá, không checksum; byte type đầu payload được tráo bằng bảng opcode (dưới).
- 1 → payload mã hoá XOR, checksum CRC32 (4 byte), `len` bị XOR-obfuscate.
- 2 → như 1 nhưng checksum CRC8 (1 byte).

Mode client dùng — 🟢:
- Gửi: `CSendPacketBase(type, cks=2, hdr=2)` (globals `0xE5794C/0xE57950`, `0xE47F54/58`).
- Nhận sau handshake: `SetRecvFormat(cks=2, hdr=3)` (`0xE57944/48`).
- Nhận trước handshake: lấy từ `dword_EEC1BC/C0`, giá trị đặt lúc runtime → ❓

## Seq byte (byte đầu header) — 🟢

Gửi (`MakeSeqByte` 0xA660A0):
```
b = deltaseq_s ? ((type + modif) ^ (base_s + seq_s)) & 0xFF : base_s
seq_s += deltaseq_s       // sau mỗi packet
```
Nhận (`CheckSeqByte` 0xA66030):
```
if chưa có header type:  type = ((b ^ (base_r + seq_r)) - modif) & 0xFF
else kiểm b == deltaseq_r ? ((type + modif) ^ (base_r + seq_r)) : base_r
seq_r += deltaseq_r
```
Với header mode 2/3 (A = 2) chỉ byte đầu được ghi → ❓ byte thứ 2.

## Mã hoá payload — ✅

`PacketEncryptXor` 0xA64240 / `PacketDecryptXor` 0xA642E0, key = seq hiện tại (seq_s khi gửi, seq_r khi nhận):
```
k = key ^ 0x53351D9C
c[0] = k ^ p[0]
for i >= 1:  k -= 0x63CAACE3;  c[i] = k ^ p[i] ^ p[i-1]     (dword little-endian)
byte lẻ cuối: c = p ^ (p[last_dword] >> 8*j)   (nếu không có dword nào: dùng k ban đầu)
```
Checksum tính trên **plaintext**, giá trị khởi đầu = key:
- CRC32: poly 0x04C11DB7, MSB-first, `crc = T[b ^ (crc>>24)] ^ (crc<<8)`, ghi big-endian.
- CRC8: poly 0x07, `crc = T[crc ^ b]`.

## Obfuscate số nguyên (mode 1/2) — 🟢

Khi checksum mode là 1/2, `len` và **mọi field** ghi bằng `Encode1/2/4` đều bị XOR:
- u8 `^ 0x5A`
- u16 `^ 0xA569`
- u32 `^ 0x96CA5395`

Chuỗi = u16 độ dài + byte, trong đó phần byte được XOR theo từng khối 4/2/1 (0xA26A10).

## Bảng tráo opcode (mode 0) — ✅ nghịch đảo nhau

16 hàng × 256 byte, hàng chọn theo header type:
- encode `g_OpcodeSubstEncTable` 0xE5CEE8
- decode `g_OpcodeSubstDecTable` 0xE5DEE8
- Dump: `decomp/net/opcode_{enc,dec}_table.bin`

## Payload

```
[type: 1|2 byte][opcode: u16][fields...]
```
Đọc bằng `RecvPkt__Decode1/2/4/8/Str/Buf` (0xA65670…), ghi bằng `SendPkt__Encode*` (0xA65220…).

## Handshake (packet đầu từ server) — 🟢

`Net_OnHandshake` 0x999C02. Khi `type == 0`:
```
u16 ?, u16 ?, u32 header_type, str ?, u8 flag
if flag == 1: u8 ?, str ?, u32 ?, u8 ?
```
→ `SetRecvFormat(2,3)` rồi `SetHeaderType(header_type)`.

## Dispatch

`CMainWnd::OnPacket` lần lượt thử:
1. `sub_8F97CB` → factory `dword_EA78E8[opcode]` (packet template `enGameServerPacket`, đăng ký lúc runtime)
2. `sub_8F9796` → factory `dword_E64B20[opcode]` (`enGeneralServerPacket`)
3. `sub_694646`
4. `stage->OnPacket` (vf51) của stage hiện tại; stage con gọi tiếp `CStage::OnPacket` (0x6A978B, 191 opcode)
5. `sub_8F939A`

Bảng opcode → handler (520 opcode, 59 dispatcher): `decomp/opcode_dispatch.json`.
Handler được đặt tên dạng `<Stage>__On_<opcode>` trong IDA. Pseudocode của các stage: `decomp/handlers/`.

## Câu hỏi còn mở

- Định dạng nhận trước handshake (`dword_EEC1BC/C0`) → đọc lúc runtime.
- Byte thứ 2 của header khi A = 2.
- Ý nghĩa byte `type` so với `opcode` u16.
- Chưa có traffic thật để so: cần chạy client nối vào server giả rồi đối chiếu.
