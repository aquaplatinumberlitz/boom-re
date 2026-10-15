# Boom Online client — reverse engineering

Dịch ngược client **Boom Online** (VNG, bản Việt của Nexon *Crazy Arcade / BnB*, nhánh source `VBNB_116`).
Server đã chết, mất source; chỉ còn client. Mục tiêu dài hạn: hiểu đủ để viết **server giả lập** và chơi lại được.

> **Vào làm tiếp?** Đọc mục [Trạng thái](#trạng-thái) → [Việc tiếp theo](#việc-tiếp-theo) → [Bắt đầu phiên làm việc](#bắt-đầu-phiên-làm-việc).

---

## Trạng thái

| Phần | Trạng thái | Ở đâu |
|---|---|---|
| Unpack Themida `ca.exe` | ✅ Xong | [Unpack](#1-unpack-themida) |
| IDA: phân tích + đặt tên từ RTTI | ✅ 3699 vtable, 13.800 hàm ảo, ~20k tên | `decomp/ida_names.json` |
| Lớp mạng TCP: frame, seq byte, mã hoá, CRC, bảng tráo opcode | ✅ Xong; crypto **đã kiểm chứng** bằng emulate binary | `docs/protocol.md`, `tools/boomproto.py` |
| Đường đi packet → handler | ✅ 520 opcode / 59 dispatcher | `decomp/opcode_dispatch.json`, `decomp/handlers/` |
| Cấu trúc field của từng packet | ⬜ Chưa (mới có handshake) | |
| Pack `.idx/.idd` (mục lục, mã hoá entry, zlib) | ✅ Xong, kiểm CRC 100% | `docs/assets.md`, `tools/idf.py` |
| Sprite `CDataI16Alpha` → PNG | ✅ Xong (108.726 ảnh) | `tools/i16.py` |
| Frame animation của sprite (record 48 byte) | ⬜ Chưa | |
| Định dạng `.map` (965 map) và `Attr/*` | ⬜ Chưa | `decomp/CGamePlayMap__Load.c` |
| Gỡ HackShield/BlackCipher, patch IP server | ⬜ Chưa | |
| Server giả lập | ⬜ Chưa | |

### Câu hỏi còn mở
- Định dạng packet server gửi **trước** handshake (`dword_EEC1BC/C0`, giá trị đặt lúc runtime).
- Byte thứ 2 của header khi header dài 2 byte.
- Ý nghĩa byte `type` so với `opcode` u16 trong payload.
- Chưa có traffic thật để so toàn bộ frame (mới kiểm chứng phần crypto).

---

## Việc tiếp theo

Theo thứ tự ưu tiên:

1. **Cho client chạy được không cần server thật.**
   - Patch IP server hardcode (`120.138.77.22-25`, `.83-85`, `118.102.5.126`, `222.255.122.204`, `175.207.3.35`) → `127.0.0.1` hoặc IP host.
   - Gỡ khởi tạo HackShield / BlackCipher / GameGuard (tìm theo chuỗi `CBlackCipher2Client::*`, `hackshield`, `ehsvc.dll`).
   - Chạy trong WinBoat, đọc bộ nhớ để trả lời các câu hỏi mở ở trên.
2. **Server giả tối thiểu** (Python, dùng `tools/boomproto.py`): accept TCP → gửi handshake (`Net_OnHandshake` 0x999C02) → xem client gửi gì → login → lobby.
3. **Cấu trúc field từng packet**: đọc handler trong `decomp/handlers/` theo luồng Login (`CLoginStage`) → Lobby → Room (`CPrepareStage`) → Game (`CGameStage`). Ghi vào `docs/protocol.md`.
4. **`.map` / `Attr/*`**: server cần để chạy ván chơi. Loader map: `CGamePlayMap__Load` 0x7354FD.
5. (Phụ) Frame animation sprite.

---

## Bắt đầu phiên làm việc

Những thứ **không có trong git** (nặng hoặc có bản quyền) và phải có sẵn trên máy:

| Thứ | Ở máy hiện tại | Cách tạo lại |
|---|---|---|
| Client gốc | `~/Downloads/Boom/` | Bản cài game |
| `unpacked_ca.exe` (18MB) | `~/boom-re/` | [Unpack](#1-unpack-themida) |
| Database IDA `unpacked_ca.exe.i64` (283MB) | `~/boom-re/` | [IDA](#2-ida) |
| `assets/` (665MB) | `~/boom-re/assets/` | `python3 tools/idf.py extract ~/Downloads/Boom assets` (~5 phút) |
| `tools/unlicense.exe` | `~/boom-re/tools/` | [unlicense 0.4.0](https://github.com/ergrelet/unlicense/releases/tag/0.4.0) bản `py3.11-x86` |

Kiểm tra nhanh mọi thứ còn chạy:
```sh
python3 tools/boomproto.py                       # -> roundtrip ok
python3 tools/idf.py ~/Downloads/Boom             # liệt kê 4 pack
uv run --with unicorn --with pefile python tools/verify_emu.py unpacked_ca.exe   # -> fails: 0
```

### 1. Unpack Themida

`ca.exe` bị pack bằng Themida/WinLicense 2.x. Phải **chạy** nó trong Windows để dump, không chạy trên host.
Đang dùng Windows của **WinBoat** (docker `dockur/windows`, user/pass `admin/admin`, ổ host `$HOME` = `\\host.lan\Data`).

```sh
docker port WinBoat        # lấy port 3389 (đổi sau mỗi lần restart container)
xfreerdp3 /u:admin /p:admin /v:127.0.0.1 /port:<PORT> /cert:ignore \
  '/app:program:C:\Windows\System32\cmd.exe,cmd:/c \\host.lan\Data\boom-re\unpack.bat'
```
`unpack.bat` copy client vào `C:\boom` (bỏ `*.idd`, `hackshield`, `blackcipher`), chạy `unlicense ca.exe`, chép `unpacked_ca.exe` + log về đây.
Kết quả lần trước: **OEP = 0x9E5EFE**, base 0x400000, 433 import, IAT giả ở 0x1900000.

Nếu RDP bị reset ngay / guest API không trả lời: Windows trong WinBoat bị treo → `docker restart WinBoat` (đã gặp 1 lần).

### 2. IDA

- Mở `unpacked_ca.exe` lần đầu: auto-analysis **~70 phút** (binary 18MB). Trong lúc đó mọi lệnh IDA MCP bị treo — chờ đến khi xong.
- Nạp lại toàn bộ tên/comment đã đặt: chạy `tools/ida_apply_names.py` trong IDA (File → Script file).
- Đã có sẵn `.i64` thì mở thẳng, không cần làm lại.

---

## Đã tìm được gì

### Client
- `ca.exe`: game chính, PE32 i386, build 2015-03-27. `v2.49/ca.exe` là bản cũ hơn (2015-03-11), cũng bị pack Themida.
- PDB gốc: `M:\Source\VBNB_116\Binary\intl\Vietnam\client\CA.pdb`.
- MSVC C++, boost, lua_tinker, TinyXML, zlib 1.1.4. Còn nguyên RTTI: **2558 class** (`rtti.txt`).
- Anti-cheat: `hackshield/`, `blackcipher/`, `gameguard.des`, driver `cawh.sys`, `procobsrv.sys`.
- Login qua Nexon Messenger (`nmco3.dll`, `CNMLoginPassportFunc`…), stage `CLoginStage`.
- Launcher/updater (`autoupdate.exe`, `paio.exe`, `vui game.exe`) không phải game.

### Mạng — tóm tắt (chi tiết: `docs/protocol.md`)
- Frame: `[seq byte][len][payload][checksum]`, big-endian.
- Client gửi: payload mã hoá XOR nối chuỗi (khoá `seq ^ 0x53351D9C`, mỗi dword `-= 0x63CAACE3`) + CRC8.
- Seq: base 102/192, modif 231, bộ đếm bắt đầu 40, mỗi packet +3.
- Handshake (packet đầu từ server) mang "header type" → chọn 1 trong 16 hàng bảng tráo opcode.
- Payload: `[type][opcode u16][fields]`. Packet đi qua `CMainWnd::OnPacket` 0x8F995D → handler của stage hiện tại (`<Stage>__OnPacket`, đặt tên handler dạng `<Stage>__On_<opcode>`).

### Tài nguyên — tóm tắt (chi tiết: `docs/assets.md`)
- 4 pack `fx`, `charte`, `emote`, `fxasset`; `.idx` mã hoá XOR nối chuỗi.
- Entry `Map/*`, `Attr/*` mã hoá thêm (có CRC32); tên chứa `_mm` thì nén zlib.
- Sprite: RLE, pixel 24-bit BGR hoặc RGB565, có alpha riêng.
- `Attr/BomberAttr` = chỉ số nhân vật, `Attr/ItemAttr` = vật phẩm, `Attr/MapGroup` = nhóm map.

### Địa chỉ quan trọng (`unpacked_ca.exe`)

| Địa chỉ | Tên | Ghi chú |
|---|---|---|
| 0x9E5EFE | OEP | |
| 0x8842DD | `CClientSocket__ctor` | đặt seq params |
| 0xA662E0 / 0xA663E0 | `ProcessRecvPacket` / `SendPacket` | |
| 0xA64B70 / 0xA643F0 | `RecvPkt__Deserialize` / `SendPkt__Serialize` | |
| 0xA642E0 / 0xA64240 | `PacketDecryptXor` / `PacketEncryptXor` | |
| 0xE5CEE8 / 0xE5DEE8 | bảng tráo opcode enc / dec | |
| 0x999C02 | `Net_OnHandshake` | |
| 0x8F4094 | `Net_DispatchMainSocket` | |
| 0x8F995D | `CMainWnd__OnPacket` | |
| 0x6A978B | `CStage__OnPacket` | 191 opcode chung |
| 0x8E426E | `PatchServer_CheckVersion` | kết nối kiểm tra bản vá |
| 0xA388C0 | `PackFS__AttachIdf` | mở pack |
| 0xA37880 | `CData__LoadFromPack` | giải mã/giải nén entry |
| 0xA3D850 | `CDataI16Alpha__Load` | sprite |
| 0x7354FD | `CGamePlayMap__Load` | map |
| 0xE60838 | `g_pMainWnd` | |

---

## Cấu trúc repo

| Đường dẫn | Nội dung |
|---|---|
| `docs/protocol.md` | Protocol TCP (frame, mã hoá, seq, handshake, dispatch) |
| `docs/assets.md` | Định dạng pack + sprite |
| `tools/boomproto.py` | Codec packet (tự test khi chạy trực tiếp) |
| `tools/verify_emu.py` | Chạy hàm crypto thật của binary bằng Unicorn, so với `boomproto.py` |
| `tools/idf.py` | Đọc/giải nén pack (`extract`) |
| `tools/i16.py` | Sprite → PNG |
| `tools/ida_apply_names.py` | Nạp `decomp/ida_names.json` vào IDA |
| `decomp/ida_names.json` | Toàn bộ tên + comment đã đặt trong IDA |
| `decomp/opcode_dispatch.json` | dispatcher → opcode → handler |
| `decomp/handlers/` | Pseudocode `OnPacket` của từng Stage |
| `decomp/net/` | Pseudocode hàm mạng + bảng tráo opcode `.bin` |
| `decomp/CGamePlayMap__Load.c` | Pseudocode loader map |
| `rtti.txt`, `ca_strings.txt` | Tên class RTTI, strings của binary |
| `unpack.bat` | Script unpack chạy trong Windows |

## Lưu ý / bẫy đã gặp

- Hằng số trong pseudocode Hex-Rays là **thập phân** — đổi hex cẩn thận (đã từng sai `1674226915` → phải là `0x63CAACE3`, phát hiện nhờ `verify_emu.py`).
- Các biến toàn cục mang giá trị `0xFFFFFFFF` trong dump là chưa được khởi tạo lúc OEP → giá trị thật phải đọc lúc runtime.
- `Map/*` có dword thứ 2 = 2 nên dễ bị nhận nhầm là sprite; nhận dạng bằng dword đầu = 1000/1001.
- Python chạy với `-I` thì không tự thêm thư mục script vào `sys.path` (tools đã tự xử lý).
