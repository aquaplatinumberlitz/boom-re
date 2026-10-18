# Danh sách tính năng client VN — checklist 100%

Mục đích: một danh sách **đầy đủ** để theo dõi tiến độ, thay vì mỗi lần lại hỏi "còn gì nữa".
Mỗi dòng có **bằng chứng** (class/opcode/tài liệu), không có dòng nào là phỏng đoán.

Cập nhật số liệu tự động: `python3 tools/feature_stats.py` (đọc `decomp/opcode_dispatch.json`,
`decomp/ida_names.json`, `server/src/*.rs`, `tools/fakeserver.py`).

## Quy ước trạng thái

| Ký | Nghĩa |
|---|---|
| ✅ | **kiểm chứng runtime**: client thật chạy qua, có log/ảnh |
| 🟡 | đã đọc code / một phần chạy được, còn thiếu |
| ⬜ | chưa làm |
| ⛔ | bị chặn bởi thứ khác |
| — | không áp dụng (client-side, không cần server) |

## Số liệu nền (tự sinh)

| chỉ số | giá trị |
|---|---|
| opcode client biết (từ bảng dispatch tĩnh) | **520** |
| dispatcher (`<Stage>__OnPacket` + component) | **59** |
| handler có tên từ RTTI | 812 / 1113 |
| class C++ có tên | **2305** |
| hàm/vtable đã đặt tên | 20.682 / 3699 vtable |
| opcode server giả đã xử lý | **84 / 520 (16,2%)** |
| khối VM Themida | 73 (14 trong `devirt.py`) |
| stage đã chơi được | 1 → 13 |

Phân bố opcode theo nhóm:

| nhóm | dispatcher | opcode | handler có tên |
|---|---|---|---|
| khác (base `CStage` + component chưa rõ) | 32 | 331 | 327 |
| lobby/room | 10 | 197 | 210 |
| battle | 6 | 134 | 148 |
| social | 4 | 56 | 59 |
| auth/login | 5 | 46 | 46 |
| economy | 2 | 22 | 22 |

---

## A. Hạ tầng & runtime (client-side)

| ID | Tính năng | Bằng chứng | Trạng thái | Tài liệu |
|---|---|---|---|---|
| A1 | unpack Themida + tìm OEP | `unpacked_ca.exe`, OEP `0x9E5EFE` | ✅ | `runtime.md` |
| A2 | sửa IAT bản dump | `ca_fixed_patched.exe`, `tools/fix_iat.py` | ✅ | `runtime.md` |
| A3 | tắt anti-cheat bằng công tắc game | `Feature_IsDisabled(212)` → 1, 22 chỗ | ✅ | `runtime.md` |
| A4 | phục hồi RTTI → tên class/hàm | 3699 vtable, 20.7k tên | ✅ | `decomp/ida_names.json` |
| A5 | bảng dispatch opcode tĩnh | 59 dispatcher / 520 opcode | ✅ | `opcode_dispatch.json` |
| A6 | render D3D9 | chạy trong Wine, `CxUni*.fft` | ✅ | `runtime.md` |
| A7 | render DDraw7 / D3D7 (fallback) | `CRenderDDraw7` (75 hàm), `CRenderD3D7` (75) | ⬜ | — |
| A8 | cửa sổ web trong game | `CWebWnd` (74), `ADAD_BrowserControlPane` (58) | ⬜ | — |
| A9 | input bàn phím/chuột | đi được trong trận | ✅ | `progress.md` §5 |
| A10 | audio/BGM/SFX | chưa điều tra | ⬜ | — |
| A11 | font bitmap `.fft` | `CxUni.fft`, `CxUniBold.fft` | 🟡 | `assets.md` |
| A12 | pack `.idx/.idd` | `CharTE.idd` 368 MB, `EmoTE.idd` 275 MB | ✅ | `assets.md` |
| A13 | sprite → PNG | `docs/*.png` sinh từ pack | ✅ | `assets.md` |
| A14 | devirt khối VM | 73 khối, 14 xong, 58 anti-cheat | 🟡 | `devirt.md` |
| A15 | chạy client trên host có GPU | Wine + Mesa llvmpipe / WinBoat | ✅ | `runtime.md` |
| A16 | điều khiển guest WinBoat từ host | `tools/qmp_guest.py` | ✅ | `vmdevirt.md` §20 |

## B. Mạng & protocol

| ID | Tính năng | Bằng chứng | Trạng thái | Tài liệu |
|---|---|---|---|---|
| B1 | lớp socket (kết nối, đóng, timeout) | kiểm chứng với client thật | ✅ | `protocol.md` |
| B2 | frame: header + seq + length | khớp traffic | ✅ | `protocol.md` |
| B3 | mã hoá payload | khớp traffic | ✅ | `protocol.md` |
| B4 | obfuscate số nguyên (mode 1/2) | khớp traffic | ✅ | `protocol.md` |
| B5 | bảng tráo opcode (mode 0) | nghịch đảo nhau, `decomp/net/*.bin` | ✅ | `protocol.md` |
| B6 | Hello (packet đầu mọi kết nối) | chạy với client thật | ✅ | `protocol.md` |
| B7 | keep-alive opcode 15 | mỗi 5 s | ✅ | `protocol.md` |
| B8 | endpoint multisvr / launcher | 6×u32 trong opcode 0 **chưa rõ nghĩa** | 🟡 | `protocol.md` |
| B9 | byte thứ 2 của header khi A=2 | `0xF4`, client không kiểm tra | 🟡 | `protocol.md` |

## C. Account / auth / session

| ID | Tính năng | Bằng chứng | Trạng thái |
|---|---|---|---|
| C1 | đăng nhập bằng tài khoản | opcode 1 → 4, 15 | ✅ |
| C2 | danh sách kênh | opcode 14, stage 10 | ✅ (field chưa rõ) |
| C3 | chọn kênh → vào sảnh | stage 10 → 11 | ✅ |
| C4 | `CSessionStage` (9 opcode) | dispatcher | 🟡 |
| C5 | `CLoginStageChina` (12 opcode) | dispatcher — có thể của bản KR/TQ | ⬜ |
| C6 | đăng ký / đổi mật khẩu | chưa thấy dispatcher | ⬜ |
| C7 | chọn server (nhiều server) | multisvr endpoint | ⬜ |

## D. Social

| ID | Tính năng | Bằng chứng | Trạng thái |
|---|---|---|---|
| D1 | chat phòng/kênh | `CChatStage` 21 opcode, `CChattingStage` 17 | ⬜ |
| D2 | whisper / chat riêng | trong D1 | ⬜ |
| D3 | danh sách bạn | chưa thấy dispatcher riêng | ⬜ |
| D4 | trao đổi (exchange) | `CExchangeStage` 16 opcode | ⬜ |
| D5 | chợ người chơi (user market) | `CUserMarketStage` 13 opcode | ⬜ |
| D6 | clan/guild | chưa thấy dispatcher | ⬜ |
| D7 | thư/mail | chưa thấy dispatcher | ⬜ |

## E. Lobby & phòng

| ID | Tính năng | Bằng chứng | Trạng thái |
|---|---|---|---|
| E1 | `CLobbyStage` (23 opcode) | dispatcher | 🟡 |
| E2 | sảnh quảng trường `CLobbySquareStage` (49) | load xong, nút TẠO PHÒNG | ✅ |
| E3 | `CSquareStage` (41) | 395/466/467 trả lời được | 🟡 |
| E4 | tạo phòng | dialog tạo phòng, map Village01 | ✅ |
| E5 | danh sách phòng / vào phòng | một phần | 🟡 |
| E6 | phòng chờ `CPrepareStage` (36) | người chơi, trưởng phòng, nút BẮT ĐẦU | ✅ |
| E7 | chọn map trong phòng | hiện `Village01`; hộp thoại từng trống | 🟡 |
| E8 | sẵn sàng / bắt đầu | 501 → 189 → 190 → 191 | ✅ |
| E9 | kick / đổi chủ phòng / option phòng | trong E6 dispatcher | ⬜ |
| E10 | `CHiddenCatchPrepareStage` (33) | mode riêng, dispatcher | ⬜ |
| E11 | vào kênh (enter channel) | stage 10 → 11 | ✅ |

## F. Trận đấu

| ID | Tính năng | Bằng chứng | Trạng thái |
|---|---|---|---|
| F1 | `CGameStage` core (95 opcode) | dispatcher | 🟡 |
| F2 | bắt đầu trận / đồng hồ | 189 mode 1, 190, 189 mode 0, 191 | ✅ |
| F3 | di chuyển nhân vật | ←↑→↓ đi được | ✅ |
| F4 | đặt bom | Space → C→S 111 | ✅ |
| F5 | bom nổ | S→C 152 (gán id) → 151 (nổ) | ✅ |
| F6 | chết / hồi sinh | bị bom nổ → chết | 🟡 |
| F7 | kết thúc lượt / điểm | 146 (round result) | 🟡 |
| F8 | kết thúc ván → về phòng chờ | 173 gửi được, client chưa xác nhận | 🟡 |
| F9 | nhiều người chơi trong trận | mới 1 người | ⬜ |
| F10 | item / power-up rơi | chưa | ⬜ |
| F11 | map load trong trận | `0x736C27` đang **skip** | 🟡 |
| F12 | va chạm / vật lý | mô phỏng chạy | 🟡 |
| F13 | mode HiddenCatch | `CHiddenCatchGameStage` (76) + 5 component | ⬜ |
| F14 | mode SnowBear | `CGOSnowBearBomber` (94) | ⬜ |
| F15 | mode SnowBall | `CGOSnowBallBomber` (82) | ⬜ |
| F16 | mode MonSeason2 | `CGOMonSeason2Bomber` (72) | ⬜ |
| F17 | mode IamBoss | `CGOIamBossBomber` (63) | ⬜ |
| F18 | mode RPG | `CGORPGBomber` (58) | ⬜ |
| F19 | Fighter of Legend | `CFighterOfLegendComponent` (13 opcode) | ⬜ |
| F20 | Zombie | `CZombieComponent` (10 opcode) | ⬜ |
| F21 | NPC/monster AI | `CGOAINpcBasicMon` (100), `CGONpcSnowMon` (53) | ⬜ |
| F22 | 1019 map | `server/src/maps.rs`, `ALL_MAPS` | 🟡 |

## G. Kinh tế & tiến trình

| ID | Tính năng | Bằng chứng | Trạng thái |
|---|---|---|---|
| G1 | shop | `CShopStageNew` (14 opcode) | ⬜ |
| G2 | mua đồ | `CBuyItemListDlg` (50 hàm) | ⬜ |
| G3 | túi đồ / trang bị | class `CItem*` | ⬜ |
| G4 | cash / nạp tiền | chưa thấy dispatcher | ⬜ |
| G5 | gacha / rương | chưa thấy dispatcher | ⬜ |
| G6 | quest | `CGOLobbySquareQuestNpc` (74) | ⬜ |
| G7 | level / exp | class `CUser*` | ⬜ |
| G8 | ranking | chưa thấy dispatcher | ⬜ |
| G9 | event / season | `CGOMonSeason2*` | ⬜ |

## H. Dữ liệu & định dạng

| ID | Tính năng | Bằng chứng | Trạng thái |
|---|---|---|---|
| H1 | `.idx/.idd` + mã hoá entry | `assets.md` | ✅ |
| H2 | sprite → PNG | ✅ |
| H3 | định dạng map | `map.md` (loader chưa tiêu thụ hết chunk) | 🟡 |
| H4 | avatar/char TE | `CharTE.idd` | 🟡 |
| H5 | emotion TE | `EmoTE.idd` | 🟡 |
| H6 | script map (`csys*`) | `csysstr.ssd`, `csysfxmg.ssd` | 🟡 |

---

## Ưu tiên cho mục tiêu "chơi lại được"

Thứ tự này suy ra từ chỗ đang kẹt, không phải từ danh sách:

1. **F8** kết thúc ván → về phòng chờ (thiếu là không chơi được ván thứ 2).
2. **F9** nhiều người trong trận (mới 1 người).
3. **F7/F6** điểm + chết/hồi sinh đầy đủ (hiện mới một phần).
4. **E5/E7** danh sách phòng + chọn map (để chơi map khác Village01).
5. **D1** chat (để kiểm tra kênh phòng).
6. **F11** `0x736C27` viết lại thật (đang skip — rủi ro trạng thái map).
7. Các mode F13–F20: chỉ làm khi map/mode tương ứng được mở.

## Cách cập nhật checklist này

```bash
python3 tools/feature_stats.py            # số liệu nền
grep -n "opcode" docs/protocol.md         # cái gì đã kiểm chứng
git log --oneline -- docs/                # tiến độ theo ngày
```

Quy tắc: **không đổi trạng thái sang ✅ nếu chưa có log/ảnh chứng minh client thật chạy qua.**
