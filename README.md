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
| Gỡ HackShield/BlackCipher, patch IP server | ✅ Patch **trong bộ nhớ** client gốc (Themida) | `tools/launch.ps1`, `tools/launcher/boomlaunch.c` |
| Chạy client thật nối vào server giả | 🟡 **Đăng nhập qua được**; kẹt ở Direct3D (VM không GPU) | [Chạy client](#chạy-client-với-server-giả) |
| Server giả lập | 🟡 Prototype Python: hello + chuỗi login 6 packet | `tools/fakeserver.py` |
| Sửa IAT bản dump để chạy `unpacked_ca.exe` | ⬜ Dở (226 ô giải được, wrapper Themida chưa) | `tools/fix_iat.py` |

### Câu hỏi còn mở
- Byte thứ 2 của header khi header dài 2 byte (client gửi `0xF4`, client không kiểm tra khi nhận).
- Render: `init renderer falied. hr=0x887600aa` trong WinBoat; Wine (WoW64 mới) chết ở anti-VM của Themida (`EXCEPTION_PRIV_INSTRUCTION` @ 0x11E5F62).

### Đã kiểm chứng trên client thật (2026-10-16)
- Định dạng trước handshake đọc từ bộ nhớ process: `dword_EA6FE0/E4` = `dword_EEC1BC/C0` = **(0,0)**; sau handshake (2,3); gửi (2,2).
- Codec `boomproto.py` giải mã đúng packet thật của client (CRC8 khớp).
- "type" trong payload **chính là opcode** (u16 ở mode 2/3): dispatcher `Rewind` rồi `Decode2`.
- Luồng: kết nối patch (server gửi hello, version=116) → client đóng → kết nối chính: hello → client gửi opcode 0 (6×u32) → server gửi 13, 2, 12, 21, 1, 43 (mỗi cái `u8 0` = dùng cache) → `Login_DoLoginSequence` (0x8E2DEC) thành công, cửa sổ "Boom" mở.

---

## Việc tiếp theo

Theo thứ tự ưu tiên:

1. **Cho client render được** (đang chặn): thử Windows có GPU thật / VM có GPU passthrough, hoặc Wine bản có WoW64 kiểu cũ (32-bit prefix), hoặc d3d9 software trong WinBoat.
2. **Server thật bằng Rust** (prototype Python ở `tools/fakeserver.py` là đặc tả sống): sau login → nhận gì tiếp, lobby, phòng, ván chơi.
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
Đang dùng Windows của **WinBoat** (docker `dockur/windows`, user/pass trong `~/.winboat/docker-compose.yml`, ổ host `$HOME` = `\\host.lan\Data`).

```sh
docker port WinBoat        # lấy port 3389 (đổi sau mỗi lần restart container)
xfreerdp3 /u:<USER> /p:<PASS> /v:127.0.0.1 /port:<PORT> /cert:ignore \
  '/app:program:C:\Windows\System32\cmd.exe,cmd:/c \\host.lan\Data\boom-re\unpack.bat'
```
`win/unpack.bat` copy client vào `C:\boom` (bỏ `*.idd`, `hackshield`, `blackcipher`), chạy `unlicense ca.exe`, chép `unpacked_ca.exe` + log về đây.
Kết quả lần trước: **OEP = 0x9E5EFE**, base 0x400000, 433 import, IAT giả ở 0x1900000.

Nếu RDP bị reset ngay / guest API không trả lời: Windows trong WinBoat bị treo → `docker restart WinBoat` (đã gặp 1 lần).

### 2. IDA

- Mở `unpacked_ca.exe` lần đầu: auto-analysis **~70 phút** (binary 18MB). Trong lúc đó mọi lệnh IDA MCP bị treo — chờ đến khi xong.
- Nạp lại toàn bộ tên/comment đã đặt: chạy `tools/ida_apply_names.py` trong IDA (File → Script file).
- Đã có sẵn `.i64` thì mở thẳng, không cần làm lại.

---

## Chạy client với server giả

Đang dùng **client gốc (Themida)**, patch trong bộ nhớ (không sửa file):
- Bỏ HackShield/BlackCipher: `0x8E701D` `74 29` → `EB 29`.
- Đổi IP server (hoặc chuyển hướng bằng iptables DNAT trong container WinBoat).

WinBoat (render chưa được, nhưng mạng + login chạy):
```sh
docker run -d --rm --name boomsrv --network winboat_default --ip 172.18.0.50 \
  --user "$(id -u):$(id -g)" -v "$HOME/boom-re:/work" -w /work python:3.12-slim python -u tools/fakeserver.py --log /work/logs/fakeserver.log
docker exec WinBoat sh -c 'for d in 222.255.122.204 120.138.77.0/24 118.102.5.126 175.207.3.35; do
  iptables -t nat -I PREROUTING -s 172.30.0.0/24 -d $d -p tcp -j DNAT --to-destination 172.18.0.50; done'
xfreerdp3 ... '/app:program:C:\Windows\System32\cmd.exe,cmd:/c \\host.lan\Data\boom-re\watch2.bat'
```
(host bật `ufw` nên Windows không gọi thẳng host được → server chạy trong container cùng mạng.)

Wine (render có GPU, nhưng Themida chết trong Wine WoW64):
```sh
cd wine/Boom && wine boomlaunch.exe 127.0.0.1     # wine/Boom = bản copy reflink của client
```

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
| `win/*.bat` | Script chạy trong Windows (unpack, chạy client, chụp màn hình, dump bộ nhớ) |

## Lưu ý / bẫy đã gặp

- Hằng số trong pseudocode Hex-Rays là **thập phân** — đổi hex cẩn thận (đã từng sai `1674226915` → phải là `0x63CAACE3`, phát hiện nhờ `verify_emu.py`).
- Các biến toàn cục mang giá trị `0xFFFFFFFF` trong dump là chưa được khởi tạo lúc OEP → giá trị thật phải đọc lúc runtime.
- `Map/*` có dword thứ 2 = 2 nên dễ bị nhận nhầm là sprite; nhận dạng bằng dword đầu = 1000/1001.
- Python chạy với `-I` thì không tự thêm thư mục script vào `sys.path` (tools đã tự xử lý).
