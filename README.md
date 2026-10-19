# Boom Online client — reverse engineering

Dịch ngược client **Boom Online** (VNG, bản Việt của Nexon *Crazy Arcade / BnB*, nhánh source `VBNB_116`).
Server đã chết, mất source; chỉ còn client. Mục tiêu dài hạn: hiểu đủ để viết **server giả lập** (bằng **Rust**, `server/`) và chơi lại được.

> **Vào làm tiếp?** Đọc theo thứ tự:
> 1. **[Trạng thái](#trạng-thái)** và **[Việc tiếp theo](#việc-tiếp-theo)** ngay dưới đây — luôn là thông tin mới nhất
> 2. [docs/features.md](docs/features.md) — checklist từng tính năng (✅/🟡/⬜, cột server Rust), thứ tự ưu tiên
> 3. [docs/progress.md](docs/progress.md) — cách build, chạy server/client, biến môi trường, debug, lịch sử các bước đầu
> 4. Nhật ký chi tiết từng gói tin: [docs/lobby.md](docs/lobby.md) (sảnh/phòng/shop), [docs/oc_e-game.md](docs/oc_e-game.md) (trận)

Tài liệu:

| File | Nội dung |
|---|---|
| [docs/features.md](docs/features.md) | **Checklist tính năng** + số liệu nền (`tools/feature_stats.py`) + thứ tự ưu tiên |
| [docs/progress.md](docs/progress.md) | **Chạy thử + handoff**: build, server (env), client tự động (Xvfb/gdb/2 client), bẫy, lịch sử |
| [docs/protocol.md](docs/protocol.md) | Protocol TCP: frame, mã hoá, seq, hello, đăng nhập, dispatch — phần lớn **đã kiểm chứng với client thật** |
| [docs/lobby.md](docs/lobby.md) | Kênh → sảnh → phòng chờ → trận → shop: nhật ký từng bước ("Cập nhật N"), định dạng gói, địa chỉ hàm |
| [docs/oc_e-game.md](docs/oc_e-game.md) | Màn trận: 117/189/190/191, bom 111/152/151, chết 120, 146, kết quả 168, hết giờ, vật phẩm 553/158 |
| [docs/oc_a-room.md](docs/oc_a-room.md), [docs/oc_c-square.md](docs/oc_c-square.md), [docs/oc_d-login.md](docs/oc_d-login.md) | Phòng chờ / sảnh / đăng nhập (agent OpenCode viết, audit dần — `progress.md` mục 7) |
| [docs/items.md](docs/items.md) | 269 vật phẩm trong trận (kind → tên/sprite/trọng số) |
| [docs/assets.md](docs/assets.md) | Pack `.idx/.idd`, mã hoá entry, sprite → PNG |
| [docs/map.md](docs/map.md) | Định dạng map |
| [docs/runtime.md](docs/runtime.md) | Chạy client: thứ tự khởi động, mã lỗi, patch bộ nhớ, mạng WinBoat, Wine, **sửa IAT bản dump** |
| [docs/devirt.md](docs/devirt.md) | **Bảng trạng thái 15 khối VM đã xử lý** + 3 đường viết lại (skip / emulate trên snapshot cũ / snapshot tại site) |
| [docs/vmtriage.md](docs/vmtriage.md) | Triage tĩnh 56 site VM (lịch sử; trạng thái hiện tại ở devirt.md) |
| [docs/vm_6EFD4A_inputs.md](docs/vm_6EFD4A_inputs.md) | Khối đặt bom `0x6EFD4A`: khung hàm, tham số, **kết quả viết lại (§8)** |
| [docs/vmdevirt.md](docs/vmdevirt.md), [docs/devirt-themida-huong-dan.md](docs/devirt-themida-huong-dan.md) | Công cụ devirt tổng quát `tools/vmdevirt.py` (đang dở) + hướng dẫn cho người mới |
| [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md), [docs/kr-re-plan.md](docs/kr-re-plan.md) | Kế hoạch dài hạn (port/remaster), kế hoạch RE client KR |

---

## Trạng thái

Cập nhật **2026-10-19**. Nguồn chi tiết: [docs/features.md](docs/features.md). Server chạy thử là **server Rust** (`server/`);
`tools/fakeserver.py` là đặc tả (golden test `server/tests/golden.txt` so từng byte).

**Chơi được (kiểm chứng với client thật, có ảnh trong `docs/`):** đăng nhập → chọn kênh → sảnh (danh sách phòng, danh sách người chơi,
chữ tiếng Việt) → tạo / vào phòng → phòng chờ 2 người (chọn map, đội, nhân vật, sẵn sàng, đóng ô, đuổi, đổi chủ phòng) → trận 2 người
(xuất phát riêng, đi đồng bộ qua UDP P2P, bom nổ, bị nhốt/chết, vật phẩm, chat) → kết quả (168) hoặc hết giờ → về phòng chờ → ván mới;
**siêu thị**: xem hàng, mua bằng VÀNG/XU.

| Phần | Trạng thái | Ở đâu |
|---|---|---|
| Unpack Themida, IAT, chạy bản dump trong Wine | ✅ `unpacked_ca.exe` (OEP 0x9E5EFE) → `ca_fixed_patched.exe` | [Unpack](#1-unpack-themida), `docs/runtime.md` |
| IDA: tên từ RTTI | ✅ 3699 vtable, ~20.7k tên | `decomp/ida_names.json` |
| Lớp mạng TCP + UDP P2P | ✅ frame, mã hoá, seq, opcode; UDP: C→S 92 → S→C 146 bảng peer | `docs/protocol.md`, `features.md` B |
| Packet → handler | ✅ 520 opcode / 59 dispatcher; server xử lý **117 (22,5%)** | `decomp/opcode_dispatch.json`, `features.md` |
| Đăng nhập, kênh (stage 10) | ✅ | `docs/protocol.md`, `docs/lobby.md` |
| Sảnh (stage 11) | ✅ bản đồ quảng trường + nhân vật mình (466/467), phòng (88/78), người chơi (64 → 69), chat (18 → 28), chữ UI tiếng Việt (S→C 2); 🟡 ô thông tin của mình, thẻ Hội, người khác trên bản đồ (469/471) | `docs/lobby.md` Cập nhật 13, 17, 21 |
| Phòng chờ (stage 12) | ✅ 2 người: map (88 → 113), sẵn sàng/đội/nhân vật (87/89/90 → 106), BẮT ĐẦU (97), đóng ô (94), đuổi (95 → 104), đổi chủ; ⬜ sửa tên/mật khẩu (85) | `docs/lobby.md` Cập nhật 15–18 |
| Trận (stage 13) | ✅ 2 người: 117 → 189/190/189/191, bom 111 → 152 → 151, chết 120 → 146, kết quả 168 → 173, hết giờ 120 s, vật phẩm 553/158; ⬜ cứu đồng đội, vật phẩm 2 người, các mode khác | `docs/oc_e-game.md` |
| Siêu thị (stage 14) | ✅ vào (325 → 289 → 38 → **20**), hàng (51/64/225/65), mua 261 → 223, XU (259/260 → 221); 🟡 danh mục thử 2 món, chưa túi đồ / lưu ví | `docs/lobby.md` Cập nhật 19–20 |
| Khối VM Themida | 🟡 15 khối trong `tools/devirt.py`; còn `0x966FEC`, 49 site anti-cheat A1xxxx (chưa chạm) | `docs/devirt.md` |
| Devirt tổng quát | 🟡 bảng handler/ctx/opcode có; chưa emit C | `docs/vmdevirt.md` |
| Pack `.idx/.idd` + sprite → PNG | ✅ 108.726 PNG, 965 map, 645 ogg | `docs/assets.md` |
| Client gốc (Themida) trong WinBoat | ✅ có hình (D3D9 phần mềm), dùng để chụp snapshot VM | `docs/runtime.md` |
| Server Rust | ✅ toàn bộ luồng trên, nhiều kết nối (`hub.rs`); 🟡 dữ liệu thử (tên `testerN`, ví/túi đồ không lưu) | `server/`, `docs/progress.md` mục 12 |

### Câu hỏi còn mở
- 6×u32 trong opcode 0 (có lẽ session từ launcher VNG; chạy trần thì toàn 0); byte thứ 2 header (`0xF4`, client không kiểm).
- Thời gian nổ bom gốc, vài trường 152/146/168 (exp/vàng), nguồn 2 ô thông tin của mình ở sảnh.
- Bản dịch gốc của chữ giao diện VN (server cũ gửi; ta tự dịch trong `server/src/strings.rs`).

---

## Việc tiếp theo

Thứ tự đầy đủ: [docs/features.md](docs/features.md#ưu-tiên-cho-mục-tiêu-chơi-lại-được). Tóm tắt:

1. Trận: cứu đồng đội bị nhốt (F6b), vật phẩm khi 2 người (F10), map/loại phòng khác (F11).
2. Sảnh/phòng: 2 ô thông tin của mình + thẻ Hội (67) + người khác xuất hiện/di chuyển trên quảng trường (469/471); sửa tên/mật khẩu phòng (85); thì thầm (D2).
3. Siêu thị → túi đồ (G2/G3), level/exp (G7), lưu tài khoản trên server.
4. Các mode khác (F13–F20), quest/event (G6/G9).
5. Khối VM còn lại khi chạm (`0x966FEC`, anti-cheat A1xxxx); audit `docs/oc_*.md`.

---

## Bắt đầu phiên làm việc

### Kiểm tra nhanh
```sh
cd ~/boom-re
python3 tools/boomproto.py                                   # -> roundtrip ok
python3 tools/idf.py ~/Downloads/Boom                         # liệt kê 4 pack
uv run --with unicorn --with pefile python tools/verify_emu.py unpacked_ca.exe   # -> fails: 0
tools/rebuild_wine.sh                                         # build dump đã sửa + chạy trong Wine (backtrace + CALog)
```

### File không có trong git (nặng / bản quyền) — đang nằm trên máy

| Thứ | Ở đâu | Cách tạo lại |
|---|---|---|
| Client gốc | `~/Downloads/Boom/` | bản cài game |
| `unpacked_ca.exe` (18MB) | `~/boom-re/` | [Unpack](#1-unpack-themida) |
| IDA database `unpacked_ca.exe.i64` (283MB) | `~/boom-re/` | [IDA](#2-ida) |
| `assets/` (665MB) | `~/boom-re/assets/` | `python3 tools/idf.py extract ~/Downloads/Boom assets` (~5 phút) |
| `tools/unlicense.exe` | `~/boom-re/tools/` | [unlicense 0.4.0](https://github.com/ergrelet/unlicense/releases/tag/0.4.0) `py3.11-x86` |
| `ca_fixed.exe`, `ca_fixed_patched.exe` | `~/boom-re/` | `tools/rebuild_wine.sh` (cần `unpacked_ca.exe` + `decomp/iat_resolved.json`) |
| `wine/Boom/` | bản copy reflink của client để chạy Wine | `cp -a --reflink=auto ~/Downloads/Boom wine/` |
| `logs/live/` (77MB), `logs/exports.tsv` | dump bộ nhớ client gốc + export DLL | `win/live_dump.bat` trong WinBoat. **Chỉ cần nếu giải lại IAT**; kết quả đã lưu ở `decomp/iat_resolved.json` |
| `unlicense_ca.log` | log unpack (fix_iat dùng khi giải lại) | sinh ra khi unpack |

### Trạng thái môi trường (không bền — kiểm tra lại mỗi phiên)

- **WinBoat** (Windows trong docker `dockur/windows`): `docker ps`; port RDP **đổi sau mỗi lần restart container** → `docker port WinBoat`.
  User/pass trong `~/.winboat/docker-compose.yml`. Thư mục home của host = `\\host.lan\Data` trong Windows.
  Bị treo (RDP reset ngay) → `docker restart WinBoat`.
- **Server**: trên host chạy `server/target/release/boom-server --log logs/server.log` (nghe 3838/4848/5858/6868); cho client gốc trong WinBoat: container `boomsrv` (`172.18.0.50` trên mạng `winboat_default`) với `SERVER_IP=172.18.0.50`.
- **Luật iptables DNAT** trong container WinBoat (chuyển IP server cũ → `boomsrv`) **mất khi restart container**; lệnh ở [Chạy client](#chạy-client-với-server-giả).
- Host bật **ufw** → Windows guest không gọi được host; dùng container cùng mạng.
- **Wine**: CachyOS Wine 10 (chỉ WoW64 mới), prefix `~/.wine`, đã đặt `ShowCrashDialog=0`.
- **IDA MCP**: database mở bằng idalib; lần đầu mở mất ~70 phút auto-analysis, trong lúc đó mọi lệnh bị treo.

### 1. Unpack Themida

`ca.exe` bị pack Themida/WinLicense 2.x. Phải **chạy** nó trong Windows để dump.
```sh
docker port WinBoat        # lấy port 3389
xfreerdp3 /u:<USER> /p:<PASS> /v:127.0.0.1 /port:<PORT> /cert:ignore \
  '/app:program:C:\Windows\System32\cmd.exe,cmd:/c \\host.lan\Data\boom-re\win\unpack.bat'
```
`win/unpack.bat` copy client vào `C:\boom` (bỏ `*.idd`, `hackshield`, `blackcipher`), chạy `unlicense ca.exe`, chép `unpacked_ca.exe` + log về.
Mọi script `win/*.bat` chạy cùng cách (RemoteApp), ghi kết quả về `logs/`.

### 2. IDA

- Đã có `.i64` thì mở thẳng.
- Làm lại từ đầu: mở `unpacked_ca.exe` (~70 phút) rồi chạy `tools/ida_apply_names.py` (nạp `decomp/ida_names.json`).
- Sau khi đặt thêm tên: chạy `tools/ida_export_names.py` trong IDA → cập nhật `decomp/ida_names.json`, rồi commit.

---

## Chạy client với server giả

**Client gốc (Themida)** — mạng/đăng nhập chạy, không render (WinBoat không GPU):
```sh
docker run -d --rm --name boomsrv --network winboat_default --ip 172.18.0.50 \
  --user "$(id -u):$(id -g)" -v "$HOME/boom-re:/work" -w /work python:3.12-slim python -u tools/fakeserver.py --log /work/logs/fakeserver.log
docker exec WinBoat sh -c 'for d in 222.255.122.204 120.138.77.0/24 118.102.5.126 175.207.3.35; do
  iptables -t nat -I PREROUTING -s 172.30.0.0/24 -d $d -p tcp -j DNAT --to-destination 172.18.0.50; done'
xfreerdp3 ... '/app:program:C:\Windows\System32\cmd.exe,cmd:/c \\host.lan\Data\boom-re\win\watch2.bat'   # launch.ps1 patch bộ nhớ + chụp màn hình
```

**Bản dump đã sửa IAT** trong Wine (đường chính; chi tiết, biến môi trường và click tự động ở `docs/progress.md` mục 3):
```sh
tools/rebuild_wine.sh                                          # build ca_fixed_patched.exe (IP đã patch thành 127.0.0.1)
(cd server && cargo build --release)
server/target/release/boom-server --log logs/server.log &      # server Rust
JOIN=1 CLICKS="975,38,6" tools/wine_gdb.sh tools/gdb/plain.gdb tester 1234 200   # đăng nhập → kênh → sảnh, ảnh ở logs/xvfb/
RUST=1 CLICKS_A="975,38,6" CLICKS_B="975,38,6" tools/duo.sh logs/duo/x 120          # 2 client
```

---

## Đã tìm được gì (tóm tắt)

### Client
- `ca.exe`: PE32 i386, build 2015-03-27; `v2.49/ca.exe` bản cũ hơn. PDB `M:\Source\VBNB_116\Binary\intl\Vietnam\client\CA.pdb`.
- MSVC C++ (CRT VS2008), boost, lua_tinker, TinyXML, zlib 1.1.4. RTTI: **2558 class** (`rtti.txt`).
- Phiên bản client = **116** (`App__GetVersion_116` 0x8E2494).
- Anti-cheat: HackShield (`hackshield/`), BlackCipher (`ngclient.aes`, `blackcipher/`), anti-cheat tự viết (quét process theo `cavn.ini`, `AntiCheat_ScanProcesses` ~0xA12C00), `cawh.sys` (thật ra là DLL hook cửa sổ của game).
- Log client: `CALog.log` trong thư mục game.

### Mạng (chi tiết `docs/protocol.md`)
- Frame `[seq][len][payload][checksum]`, big-endian; client gửi XOR nối chuỗi (`seq ^ 0x53351D9C`, mỗi dword `-= 0x63CAACE3`) + CRC8.
- Seq: base 102/192, modif 231, đếm từ 40, +3 mỗi packet. Opcode = trường đầu payload.
- Server: `server/` (Rust, chạy thử) và `tools/fakeserver.py` (đặc tả: `hello_packet`, `login_replies`, `Session`).

### Tài nguyên (chi tiết `docs/assets.md`)
- Pack `fx`, `charte`, `emote`, `fxasset`; entry `Map/*`, `Attr/*` mã hoá (CRC32), `_mm` = zlib; sprite RLE + alpha.

### Địa chỉ quan trọng (`unpacked_ca.exe`)

| Địa chỉ | Tên | Ghi chú |
|---|---|---|
| 0x9E5EFE | OEP | |
| 0x8F2146 | `WinMain` | `CrashDlg` khi có C++ exception không bắt |
| 0x8E6FEE | `CFxApp__vf4_Init` | thứ tự khởi động, `docs/runtime.md` |
| 0x8E701D | jz HackShield/BlackCipher | patch `74 29` → `EB 29` |
| 0x8E426E | `PatchServer_CheckVersion` | kết nối patch, chờ hello |
| 0x8F280B / 0x8E4778 | `App__SetExitError` / `App__ShowExitError` | mã lỗi khởi động |
| 0x998FD5 | `CMultiServer__ctor` | danh sách IP/port |
| 0x8842DD | `CClientSocket__ctor` | seq params |
| 0xA662E0 / 0xA663E0 | `ProcessRecvPacket` / `SendPacket` | |
| 0xA64B70 / 0xA643F0 | `RecvPkt__Deserialize` / `SendPkt__Serialize` | |
| 0xA642E0 / 0xA64240 | `PacketDecryptXor` / `PacketEncryptXor` | |
| 0xE5CEE8 / 0xE5DEE8 | bảng tráo opcode enc / dec | |
| 0x999C02 | `Net_OnHandshake` | hello trên kết nối chính |
| 0x8E2DEC | `Login_DoLoginSequence` | opcode 0 → chờ 13,2,12,21,1,43 |
| 0x8F995D | `CMainWnd__OnPacket` | định tuyến packet |
| 0x6A978B | `CStage__OnPacket` | 191 opcode chung |
| 0xA388C0 / 0xA37880 | `PackFS__AttachIdf` / `CData__LoadFromPack` | pack |
| 0x7354FD | `CGamePlayMap__Load` | map (có khối bị ảo hoá) |
| 0x8F8EEC | `CStageMgr__ChangeStage` | bảng id → stage trong `docs/devirt.md` |
| 0x8F4D01 | vòng lặp chính (`CFxApp__vf5` gọi) | 3 khối VM lớn — đã viết lại (`docs/devirt.md`) |
| 0x11EE128 | VM entry Themida | `docs/devirt.md`; khối kết thúc ở marker `EB 10 57 4C 20` |
| 0xC0F000–0xC0F7FF | IAT gốc | `decomp/iat_resolved.json` |
| 0x1900000 / 0x16AD000 | IAT giả của unlicense | 3 mục sai, xem `docs/runtime.md` |

---

## Cấu trúc repo

| Đường dẫn | Nội dung |
|---|---|
| `docs/` | tài liệu (xem bảng đầu file); ảnh minh hoạ `docs/*.png` |
| `tools/boomproto.py` | codec packet (tự test khi chạy trực tiếp) |
| `tools/fakeserver.py` | server giả bằng Python = **đặc tả** cho server Rust (golden test); không còn dùng để chạy thử |
| `tools/verify_emu.py` | chạy hàm crypto thật của binary bằng Unicorn, so với `boomproto.py` |
| `tools/idf.py`, `tools/i16.py` | đọc/giải nén pack, sprite → PNG |
| `tools/patch_client.py` | patch file: bỏ HackShield, bỏ patch-check, đổi IP |
| `tools/fix_iat.py` | giải IAT gốc (`report`/`export`) và build `ca_fixed.exe` (`build`) |
| `tools/rebuild_wine.sh` | fix_iat → devirt → patch → chạy bản dump trong winedbg |
| `tools/devirt.py` | khối VM viết lại / skip (`BLOCKS`, 15 khối) + `HOOKS` → `ca_devirt.exe` |
| `tools/vmdevirt.py` | devirt tổng quát (discover/profile/handlers/opcodes/trace) — `docs/vmdevirt.md` |
| `tools/match_gdb.sh`, `tools/gdb/*.gdb` | chạy cả trận (đăng nhập → phòng → 501… → phím + Space×3) dưới gdb; các script gdb theo chủ đề |
| `tools/battle_drive.ps1`, `tools/snap_retry.sh`, `win/snap_bisect*.bat` | tự động hoá client gốc trong WinBoat để chụp snapshot (`docs/runtime.md`) |
| `server/` | **server Rust** (`cargo run --release -- --log …`; env ở `docs/progress.md` 3.3): `proto.rs` codec, `packets.rs` builder S→C, `session.rs` luồng phiên, `hub.rs` phòng/sảnh chung, `strings.rs` chữ UI tiếng Việt, `maps.rs` |
| `tools/duo.sh` | 2 client (2 Wine prefix) cùng lúc: `RUST=1 CLICKS_A=… CLICKS_B=… tools/duo.sh <outdir> <giây>` |
| `tools/feature_stats.py` | số liệu nền cho `docs/features.md` |
| `tools/vmtrace.py`, `tools/launcher/inject.c`, `win/vmtrace.bat` | quan sát một khối VM trên client gốc (cave + snapshot + diff) |
| `tools/launcher/snap.c`, `win/snap.bat` | snapshot toàn bộ bộ nhớ client gốc tại một site VM (pre/post) |
| `tools/vmemu.py`, `tools/snapdiff.py` | emulate khối VM trên snapshot (Unicorn), so với diff thật — quy trình trong `docs/devirt.md` |
| `tools/xvfb_join.sh` | đăng nhập → vào kênh → sảnh; `CLICKS=` click tiếp (tạo phòng…) + chụp màn hình |
| `tools/wine_gdb.sh` | chạy dưới `winedbg --gdb` + gdb, tự đăng nhập (`JOIN=1`, `CLICKS=`) |
| `tools/xvfb_login.sh`, `tools/xvfb_login_dbg.sh` | chạy dump trong Xvfb, tự gõ đăng nhập, chụp màn hình (bản `_dbg`: dưới winedbg) |
| `tools/run_xvfb.sh` | chạy bản dump trong Xvfb riêng + chụp màn hình |
| `tools/themida_scan.py` | liệt kê điểm vào section Themida → `decomp/themida_entries.json` |
| `tools/launch.ps1`, `tools/launcher/boomlaunch.c` | patch bộ nhớ client gốc (PowerShell / exe mingw) |
| `tools/live_dump.ps1`, `tools/dump_exports.ps1`, `tools/peek.ps1` | dump bộ nhớ / export DLL / đọc biến lúc chạy (PowerShell 32-bit) |
| `tools/ida_apply_names.py`, `tools/ida_export_names.py` | nạp / xuất `decomp/ida_names.json` (IDA) |
| `win/*.bat` | chạy trong Windows qua RDP RemoteApp: `unpack`, `watch2` (client gốc + patch + chụp màn hình), `live_dump`, `peek`, `run_*`, chẩn đoán (`diag`, `evlog`, `getcrash`, `status`) |
| `decomp/ida_names.json` | toàn bộ tên + comment đã đặt trong IDA |
| `decomp/iat_resolved.json` | IAT gốc đã giải (489 ô) |
| `decomp/themida_entries.json` | 117 điểm vào Themida + phân loại |
| `decomp/opcode_dispatch.json`, `decomp/handlers/`, `decomp/net/` | dispatch, pseudocode handler, hàm mạng + bảng opcode |
| `rtti.txt`, `ca_strings.txt` | RTTI, strings |

## Lưu ý / bẫy đã gặp

- Hằng số trong pseudocode Hex-Rays là **thập phân** — đổi hex cẩn thận (đã sai `1674226915` ≠ `0x63CA5EE3`; đúng là `0x63CAACE3`).
- Biến toàn cục = `0xFFFFFFFF` trong dump là chưa khởi tạo lúc OEP → đọc lúc runtime (`tools/peek.ps1`).
- `Map/*` dword thứ 2 = 2 → dễ nhận nhầm là sprite; nhận dạng bằng dword đầu = 1000/1001.
- Python `-I` không thêm thư mục script vào `sys.path` (tools đã tự xử lý).
- unlicense: không sửa IAT gốc; và **gán sai** những wrapper mà Themida giả lập chung nhiều API (xem `docs/runtime.md`).
- Dump IAT/export **phụ thuộc lần boot của Windows** (địa chỉ DLL hệ thống); kết quả đã chốt ở `decomp/iat_resolved.json`.
- QMP screendump chỉ chụp console, không thấy phiên RDP → chụp bằng PowerShell trong phiên.
- Lệnh `pkill -f <chuỗi>` có thể giết luôn shell đang chạy lệnh đó nếu chuỗi khớp chính nó.
