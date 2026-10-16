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

Mode client dùng — ✅ (đọc từ bộ nhớ client đang chạy, `tools/peek.ps1`):

| Chiều | (cks, hdr) | Nguồn |
|---|---|---|
| Client → server | (2, 2) | `0xE5794C/50`, `0xE47F54/58` |
| Server → client, packet đầu (hello) | (0, 0) | `dword_EEC1BC/C0` (kết nối chính), `dword_EA6FE0/E4` (kết nối patch) — đều = 0 lúc runtime |
| Server → client, sau hello | (2, 3) | `0xE57944/48` |

## Seq byte (byte đầu header) — ✅ (khớp traffic thật)

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

## Obfuscate số nguyên (mode 1/2) — ✅ (khớp traffic thật)

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

## Payload — ✅

```
[opcode: 1|2 byte = "type size" của mode][fields...]
```
"Type" **chính là opcode**: dispatcher gọi `RecvPkt__Rewind` rồi `RecvPkt__Decode2` → đọc lại đúng trường đầu tiên.
Ở mode 2/3 opcode là u16 (XOR `0xA569`), ở mode 0 là u8 và được tráo qua bảng opcode.
Đọc bằng `RecvPkt__Decode1/2/4/8/Str/Buf` (0xA65670…), ghi bằng `SendPkt__Encode*` (0xA65220…).

## Hello (packet đầu từ server, mọi kết nối) — ✅ chạy được với client thật

Server gửi ngay khi client kết nối; client không gửi gì trước.
Cùng một định dạng cho kết nối patch (`PatchServer_CheckVersion` 0x8E426E) và kết nối chính (`Net_OnHandshake` 0x999C02):
```
format (0,0): [seq u8][len u16 BE][opcode u8 = 0 (tráo bảng)]
  u16 ?            (0)
  u16 version      phải = 116 (sub_8E2494); khác 116 → client chạy autoupdate.exe rồi thoát
  u32 header_type  hàng bảng tráo opcode (0..15) → SetHeaderType
  str ?            (u16 len + byte)
  u8  flag         1 → thêm: u8, str, u32, u8 (sub_8E3AA0)
```
Seq byte cho header_type `t`: `((t + 231) ^ (102 + 40)) & 0xFF` (t=0 → `0x69`).
Sau hello, phía nhận của client chuyển sang (2,3) và `seq_r = 43`.

Kết nối patch: nhận hello hợp lệ → client tự đóng socket (~0,1s) rồi mở kết nối chính tới server khác trong danh sách.

## Đăng nhập — ✅ chạy được với client thật

`Login_DoLoginSequence` 0x8E2DEC (gọi sau hello trên kết nối chính):

1. Client gửi **opcode 0** + 6×u32: `sub_65419B(E61024)`, `sub_98D908(..)`, `*(E60FBC+92)`, `sub_8EE552(E60A0C)`, `sub_9967C4(CMultiServer)`, `sub_98131D(E64B10)`.
   Chạy không qua launcher của VNG thì cả 6 đều = 0. Ví dụ packet thật:
   `0f f4 a5 73 | 11 74 a3 99 … 00 00 | 96` → hdr `0f f4`, len 26, payload, CRC8 0x96.
2. Server phải trả **đúng thứ tự**, mỗi packet tối đa 10 giây:

| Opcode | Handler | Nội dung | Tối thiểu |
|---|---|---|---|
| 13 | `CStage__On_13` 0x654ADE | u8 có dữ liệu?, blob → `fxdynimginfo.ssd` | `u8 0` |
| 2 | 0x98DFAB | u8, blob FxClientString | `u8 0` (dùng cache) |
| 12 | 0x9D3F17 | u8, blob FxQuestString | `u8 0` |
| 21 | 0x8F13E6 | u8, blob FxMessageTable | `u8 0` |
| 1 | 0x99933B | u8, blob `multisvr.ssd`; u8, blob `multisvrn.ssd` | `u8 0, u8 0` |
| 43 | 0x982A90 | u8, blob | `u8 0` |

Nhận đủ → hàm trả 2, cửa sổ game "Boom" mở. Tiếp theo client làm gì: **chưa biết** (bị chặn bởi lỗi render).
Cài đặt mẫu: `tools/fakeserver.py` (`hello_packet`, `login_replies`, `Session`).

## Dispatch

`CMainWnd::OnPacket` lần lượt thử:
1. `sub_8F97CB` → factory `dword_EA78E8[opcode]` (packet template `enGameServerPacket`, đăng ký lúc runtime)
2. `sub_8F9796` → factory `dword_E64B20[opcode]` (`enGeneralServerPacket`)
3. `sub_694646`
4. `stage->OnPacket` (vf51) của stage hiện tại; stage con gọi tiếp `CStage::OnPacket` (0x6A978B, 191 opcode)
5. `sub_8F939A`

Bảng opcode → handler (520 opcode, 59 dispatcher): `decomp/opcode_dispatch.json`.
Handler được đặt tên dạng `<Stage>__On_<opcode>` trong IDA. Pseudocode của các stage: `decomp/handlers/`.

## Kiểm chứng

- Mã hoá/giải mã/CRC: emulate hàm thật của binary (`tools/verify_emu.py`) — 88/88 khớp.
- Phía client → server: giải mã packet thật của client, CRC8 khớp.
- Phía server → client: client thật chấp nhận hello + 6 packet login do `fakeserver.py` tạo.

## Câu hỏi còn mở

- Byte thứ 2 của header khi A = 2: client gửi `0xF4`; khi nhận client không kiểm tra (server gửi 0 vẫn được).
- Ý nghĩa 6×u32 trong opcode 0 (có lẽ session/account từ launcher VNG).
- Packet sau đăng nhập (lobby, phòng, ván chơi).
