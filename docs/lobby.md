# Lobby (vào kênh → stage 11) — đặc tả tĩnh cho server giả

Phạm vi: phân tích **tĩnh** client `unpacked_ca.exe` (nhánh `VBNB_116`), phục vụ viết
đặc tả `tools/fakeserver.py` để đi tiếp từ màn chọn kênh (stage 10) vào lobby (stage 11).
Không chạy động, không sửa code.

Quy ước độ tin cậy: ✅ đã kiểm chứng động · 🟢 đọc rõ từ decompile (chưa chạy) ·
❓ suy đoán / chưa rõ. Mỗi khẳng định ghi nguồn (địa chỉ hàm).

## 0. Bối cảnh, stage id

- Bảng `switch` trong `CStageMgr__ChangeStage` (0x8F8EEC, code gốc từ 0x8F8FCA;
  xem `docs/devirt.md` → "Stage"): **10 = `CSelectServerStage`**
  (size 0x7354, ctor 0x85817A), **11 = lobby**.
- Stage 11 có 3 biến thể, chọn theo `sub_994378(server hiện tại)` (nguồn `docs/devirt.md`):
  loại 0 → `CLobbySquareStage` (size 0x570F0, ctor 0x4E56DF),
  loại 2 → `CLobbyStageWithSquareUI` (0x57CFC, 0x4C1F4D),
  còn lại → `CLobbyStage` (0x5525C, ctor 0x6B3EDD). Mặc định loại 1 nếu feature 0x2E tắt;
  0x7B tắt UI square. 🟢
- Rời màn Login (`sub_84FABC` 0x84FABC): `sub_98E763()` → `sub_8E28F4` →
  `sub_84F482()` → `sub_993EF4(cache kênh)` → `sub_8F391D(dword_E6092C, 10)`
  (đặt id đích) → `sub_8FE6C7`. Vào stage 10 client gửi opcode 298 + 40
  (xem `docs/protocol.md`). 🟢

## (a) Luồng vào kênh — opcode 7 (`On_7`)

### a1. Client gửi opcode 7 — `sub_98E763` (0x98E763) 🟢

```
sub_481256() → đường dẫn "%s\%s.log" trong thư mục Windows
                (tên file từ chuỗi toàn cục dword_E25550)
CreateFileA(..., OPEN_EXISTING) → ReadFile (tối đa 0xFFFF byte)
SendPkt__Begin(7) + SendPkt__EncodeStr(nội dung file) + SendPkt__Send
CloseHandle + DeleteFileA (xóa file sau khi gửi)
```

- Body client→server: `[opcode u16 = 7][str]` (str = nội dung file, mã hoá chuỗi
  mode 1/2 như thường lệ). Nếu file không tồn tại → **không gửi gì cả**.
- Nội dung/kẻ ghi file này ❓ chưa truy (có thể là token phiên do bước login viết;
  cần test động: log body opcode 7 trong fakeserver để xem).
- Gọi từ duy nhất `sub_84FABC` (rời màn Login, **trước** `ChangeStage(10)`),
  và file cache tên `channel2_%03d%s.ssd` (`sub_993EF4` 0x993EF4) cũng chỉ có từ đây —
  khớp ghi chú trong `docs/protocol.md` rằng opcode 14/16 phải gửi sau khi vào stage 10.

### a2. Server trả opcode 7 — `CSelectServerStage__On_7` (0x8558C4) 🟢

Dispatcher: `CSelectServerStage__vf51` (0x859C70) → opcode 7 → `sub_8558C4`.
Điều kiện tiên quyết (không phải mã lỗi): `this[5915] == 1`, ngược lại hiện
`ErrDisconnect` + `sub_854C2B` (thoát màn). Field đầu tiên là **u8 mã kết quả**:

| Mã (u8 đầu) | Chuỗi hiển thị (tên symbol IDA — nghĩa suy từ tên, ❓) | Hành động |
|---|---|---|
| 0 | `ErrCannotConnect` | dialog + `sub_8549D5` (reset `this[5915]=0`) |
| 2 | `PremiumRecommend` | dialog + reset |
| 4 | `ErrVersionMismatch` | dialog + reset |
| 5 | `ErrServerNotActive` | dialog + reset |
| 11 | `ErrCheckingServer` | dialog + reset |
| 12 | `ErrEtcChecking` | dialog + reset |
| 13 | `AdultOnlyCh` | dialog + reset |
| 14 | `NexClubRegNoti` | dialog + reset |
| 15 | + thêm **str** | dialogข้อความ đó + reset |
| 16 | `TournamentAlready…` | dialog + reset |
| 17 | `2PCannotEnterT…` | dialog + reset |
| 18 | `TournamentChan…` | dialog + reset |
| 19 | + thêm **u8, u32, u32** | dialog `ChannelNotEnoughLucci%d` (format `aChannelnotenou`, tra cứu kênh qua `sub_994AB9`/`sub_994D51`) + reset |
| 20 | `DontHaveEntran…` | dialog + reset |
| 21/23/24/25 | `2PCannotEnterB/S/H/R…` | dialog + reset |
| 22 | `BigMonsterChan…` | dialog + reset |
| 26 | `ShutdownTermin…` | dialog + `sub_854CC5` |
| 27/28 | `HiddenCatch2PC…` / `WinningMode2PC…` | dialog + reset |
| 29/30/31 | `ConnectResult_O/S/N…` (khớp `ConnectResult_OneClick/SimpleGameUser/NoNexonId…ConnectFail` trong `ca_strings.txt`) | dialog + reset |
| **mặc định (gồm 1, 3, 6–10…)** | **thành công** | đọc tiếp **u8, u32, u32, u16**; nếu `u32 thứ hai != 0 && u16 != 0` → lưu vào object stage (`this[6403]=u8`, `[6404]=u32`, `[6405]=u32`, `+12812=u16`) → `sub_855254()`; ngược lại `ErrCannotConnect` + reset |

- Giá trị các mã: 🟢 (đọc trực tiếp từ `switch` trong decompile 0x8558C4).
  Nghĩa tiếng Việt chính xác của chuỗi: ❓ (chỉ suy từ tên symbol; cần mở dialog thật).
- Nhánh thành công `sub_855254` (0x855254): hiện dialog chờ (`sub_859F12`,
  chuỗi `SelectServerStage` + `WaitDialog`), gọi hàm ảo `(this+24484, 0, 1, 1)`;
  nếu trả 2 → `sub_854CC5` (không dịch được pseudocode — ❓, khả năng là yêu cầu
  đổi stage; cần xem thêm hoặc bắt động).
- Hai handler **cùng wire-format** ở stage khác (để đối chiếu, 🟢):
  - `CLobbyStage__On_7` (0x6AFEDF): cùng `u8, u8, u32, u32, u16`, điều kiện thành công
    giống hệt; khi thành công gọi `sub_9999A9` + `sub_999702(u8, u32, u32, u16)`
    (lưu địa chỉ/mã server vào `dword_E60784`: `+16=u8`, `+20=u32`,
    `+24=sub_994AB9(u8,u32)` = **chỉ số kênh tra từ cache opcode 14**,
    `+28=u32`, `+32=u16`), rồi **gửi opcode 6** (xem b1) — nếu `sub_8F6D35(1)=0`
    thì `SetExitError(1,0)` + thoát. Nhận opcode 7 khi đã ở lobby ≈ đổi kênh
    trong lobby (❓, cần kiểm động).
  - `OnPkt_multi_7_7` (0x690A31, dùng chung cho `CSessionStage`/`CExchangeStage`):
    cùng layout, thành công → `sub_8F314D` + `sub_999702` + `sub_8F6D35(0)`.

### a3. Hệ quả cho server giả: nên trả gì khi nhận opcode 7

- Reply tối thiểu để đi tiếp (🟢 từ nhánh default ở a2):
  `opcode 7 : u8 <mã thành công> , u8, u32, u32, u16`
  với `u32_thứ_hai != 0 && u16 != 0`. Mã thành công **không nằm** trong bảng lỗi
  trên — **`u8 = 1` là ứng viên đầu tiên** (1 không xuất hiện ở nhánh lỗi nào).
- Giả thuyết cần kiểm (❓): các field sau mã phải **khớp bản ghi kênh đã gửi ở
  opcode 14**, vì `sub_999702`/`sub_994AB9` (0x994AB9) dò cache kênh theo cặp
  `(u8, u32)` — dò trượt (`return -1`) ở nhánh 19 đã dẫn tới dialog lỗi, và ở nhánh
  thành công giá trị `-1` có thể gây lỗi sau. Cụ thể `sub_994AB9` duyệt
  `sub_414543(this+12)` bản ghi, khớp `sub_994A5A(i)==u8 && ...==u32`.
  Fakeserver hiện gửi bản ghi 14 với `u32 = i+1`, còn lại 0 — nên thử
  `u8/u32 = (0?, i+1)` trước, rồi biến thể theo kết quả động.
- Sau reply thành công, client dự kiến: `sub_855254` (dialog chờ) → đổi stage 11 →
  xem (b).

## (b) Các opcode lobby chờ sau khi vào (stage 11)

### b1. Client gửi khi vào lobby (server phải **nhận**, không phải gửi) 🟢

1. **Opcode 6** — gửi ngay trong `CLobbyStage__On_7` thành công (0x6AFEDF),
   trước khi đổi stage (vẫn ở ngữ cảnh stage cũ):
   `Begin(6); EncodeBool(số_người_chơi);` lặp theo `CLobbyStage__On_218`
   (= số người chơi 1P/2P, `sub_99AEE3` 0x99AEE3 chỉ đọc `this+12`):
   `EncodeStr(sub_99A731(i)) + Encode4(sub_99A70C(i))` (tên + u32 chưa rõ).
   Cấu trúc 🟢, ngữ nghĩa từng field ❓ (ngoài count).
2. **Opcode 303** — gửi khi **OnEnter mọi stage** (`CStage__vf44` 0x6A3E34):
   nếu giá trị `GetCompletionList(g_pMainWnd)` ∈ {11,12} → `v11=1`, == 20 → `v11=0`;
   lặp theo số người chơi: `Begin(303); EncodeBool(v11); EncodeBool(i); Send`.
   Giá trị 11/12/20 trùng id stage (11 lobby, 12 phòng, 20 square?) nên đây chính là
   "chào lobby" của client. Tên import `GetCompletionList` nghe không liên quan —
   có thể IDA đặt tên sai, nhưng hằng số so sánh là bằng chứng trực tiếp 🟢/❓.
   Server không có handler 303 ở lobby (dispatch `CGameStage` mới có 303) →
   chỉ cần nhận/log, chưa cần trả lời (❓ có thể cần, kiểm động).
3. Sau đó, các gửi theo hành động người dùng (tìm bằng xrefs tới
   `SendPkt__Begin` 0x888462 / `SendPkt__Send` 0x888609, 🟢 tồn tại, ngữ nghĩa ❓):
   opcode **9 + 84** (`CStage__On_75` 0x697D72), **77** (`sub_6B6441` 0x6B6441 —
   tạo/vào phòng: `Begin(77) + sub_6B61F0(...)`), **78** (chấp nhận mời, xem opcode 26),
   và nhiều gửi từ dialog/UI lobby (`sub_6B9867`, `sub_6B9F39`, `sub_6B76D0`, … chưa xem).

### b2. Server gửi → client: bảng opcode lobby

Nguồn dispatcher: `CLobbyStage__vf51` (0x6B2ED4) + `opcode_dispatch.json`
(`CLobbyStage__OnPacket@6B2ED4`). Lưu ý luồng chung trong `vf51`: sau (gần như)
mọi opcode đều chạy tiếp `RecvPkt__Rewind → sub_4D24BB → sub_512B66 →
CChatStage__OnPacket` (chat base) rồi nhánh `v3-218==0 → sub_99AEE3` (đếm người chơi)
hoặc `v3==234 → sub_6B0D7C`. Tức opcode **218** (bare, không field) và **234**
(không field) được xử lý ở đuôi chung — server có thể gửi opcode trần.

| Opcode | Handler | Field server→client (thứ tự đọc) | Nhận định |
|---|---|---|---|
| 7 | 0x6AFEDF | `u8==0` fail; ok: `u8, u32, u32, u16` (u32#2≠0, u16≠0) | 🟢 đã rõ (a2); đổi kênh trong lobby |
| 19 | 0x6B0357 | **không đọc field**; kênh guild-only → `SetExitError(5,1999)` + thoát | 🟢 |
| 26 | 0x6B167A | `u16 roomId, u32, str inviter, str, [u8…]` (có nhánh `sub_8DAD14`); nhánh chấp nhận → **client gửi opcode 78** (`Encode2 + Encode4 + Bool(0) + Bool(count) + mỗi người Bool`) | 🟢 cấu trúc; ❓ ngữ nghĩa (mời vào phòng) |
| 125 | 0x6B1358 | **không field** (huỷ ladder) | 🟢 |
| 218 | (đuôi vf51) | **không field** (`sub_99AEE3` đếm người chơi) | 🟢 |
| 234 | 0x6B0D7C | **không đọc packet** (kiểm tra guild từng người chơi + chuyển UI `sub_8DD721(100)`…) | 🟢 — ứng viên "đẩy client đi tiếp" tốt nhất: gửi opcode trần, không sợ sai field |
| 259 | 0x6B27BB | `str, u32×6` (thông báo hạng/điểm; chỉ hiển thị) | 🟢 |
| 265 | 0x6B147E | `u16 n, n×str` ( afforded mỗi str hiện dialog) | 🟢 |
| 268 | 0x6B25E3 | `u8 idx(<số người chơi), str, u32 (1..6), u32` | 🟢 |
| 363 | 0x6ADF1C | → `CStage__On_363` + `sub_67C5C9/67BDA0` (không đọc trực tiếp ở đây) | ❓ chưa xem sâu |
| 368 | 0x6AE770 | `u32, u32` (u32#1 ≤ 0x12 → `sub_9B70B9/sub_67A5AB`) | 🟢 |
| 372 | 0x6ADFAD | → `sub_67BA96` (không đọc trực tiếp) | ❓ |
| 406 | 0x6AEF18 | `u8` | 🟢 |
| 418 | 0x6B1FEC | `str, u32 n, n×u32` (hết hạn item) | 🟢 |
| 419 | 0x6B224E | `str, u32 n, n×(u32,u32)` (bán item) | 🟢 |
| 426 | 0x6B2433 | `u8 + blob` (vòng lặp `sub_A62FB0` lần, magic-book?) | 🟢 một phần |
| 499 | 0x6AE72A | **không field** → `sub_8E79B2(1)` | 🟢 |
| 505 | 0x6B011E | `u8==1` ok: `u8, u32, u32, u16` (địa chỉ square: `hostlong/port`; cả hai 0 → lỗi `SquareErrCannot…`); thành công → `sub_999702` + `sub_99A207(...,0x402,...)` | 🟢 — giống họ opcode 7, liên quan square |
| 553 | (inline vf51) | `blob → sub_6A5A5E` (điều kiện `sub_40176C(47)==0 && sub_8DACD5()`) | 🟢 một phần |
| 554 | 0x6AE817 | rewind + forward cho `dword_E6405C` | 🟢 |
| 576 | 0x6AE836 | → `CStage__On_576` (+ `sub_51607D` nếu feature mở) | ❓ |
| 32/89/124/289 | — | có trong dispatch, chưa đọc pseudocode (289 → virtual subclass) | ❓ |
| base | `CChatStage__OnPacket` + `CStage` (191 opcode chung) | luôn chạy sau mỗi packet lobby (chat, 40, 75, 77, 82, …) | 🟢 tồn tại, chưa liệt kê field |

Biến thể square (`CLobbySquareStage__vf51` 0x4E5A38, `CSquareStage__vf51` tương tự)
xử lý thêm chùm 466–512, 576, 612–625 — chỉ liên quan nếu lobby loại 0;
mặc định (loại 1) dùng bảng trên. ❓ loại lobby thực tế khi vào bằng fakeserver.

Danh sách phòng (room list) ❓: **chưa xác định** opcode nào đẩy danh sách phòng.
Không có handler lobby nào đọc dạng "u16 n + n bản ghi phòng" trong số đã xem;
26 là lời mời đơn lẻ, 234 không field. Khả năng: (i) room list đi qua opcode base
(`CStage`/`CChatStage`) chưa đọc, (ii) client tự xin bằng opcode 77/78/84 sau khi
nhận 234/bare trigger, (iii) thuộc chùm square. Cần test động mục (c).

## (c) Đề xuất test động tiếp theo (thứ tự)

Giả thiết môi trường như README: `python3 tools/fakeserver.py --log ...` +
`tools/xvfb_login.sh` (bản `_dbg` để bắt exception), client đã ở stage 10
(chọn kênh, đã nhận 14+16).

1. **Log request opcode 7**: fakeserver hiện chỉ log hex body — ghi thêm
   `DecodeStr` của body 7 để lộ nội dung file `%Windows%\<?>.log`
   (xem nó là token/auth gì; đối chiếu với `login_ok`/`login_net_info`).
2. **Reply opcode 7 tối thiểu** (khi nhận opcode 7 từ client):
   `obf_body(7, u8=1, u8=0, u32=?, u32=NN≠0, u16=MM≠0)`.
   Thử `NN/MM` theo bản ghi kênh đã gửi ở opcode 14 (đang gửi `u32=id=i+1`):
   cặp `(u8=0, u32=id kênh user đã click?)` rồi biến thể `(u8=1..4, u32=id)`.
   Vì click kênh nào là input người dùng, cách nhanh nhất là auto-click + thử ma trận
   nhỏ (4 kênh × vài cặp field), quan sát dialog lỗi (mã nào trong bảng a2) hay
   chuyển stage. Kỳ vọng: dialog lỗi → sai field; chuyển stage 11 → đúng.
3. **Sau khi sang stage 11**: log và **chưa trả lời vội** opcode 6 + 303 của client;
   chụp màn hình xem client đứng ở UI nào / có timeout dialog gì (tên chuỗi dialog
   sẽ chỉ ra opcode còn thiếu).
4. **Đẩy bare trigger**: gửi `opcode 234` trần (không field) rồi `opcode 218` trần;
   nếu UI lobby đổi (theo `sub_6B0D7C`: kiểm guild + `sub_8DD721(100)`), ta đã có
   "mồi" vào lobby mà không cần room list.
5. **Room list**: nếu sau (4) lobby hiện nhưng trống phòng, thử gửi 26 một bản ghi
   mời (`u16 roomId=1, u32, str inviter, str`) xem dialog mời có hiện không
   (→ client tự gửi 78, ta học tiếp luồng tạo/vào phòng `CPrepareStage`/stage 12);
   song song đọc nốt `CStage`/`CChatStage` opcode phòng (77/78/84 quanh `sub_6B6441`,
   `CStage__On_75`).
6. **Loại lobby**: log xem ctor nào chạy (0x6B3EDD vs 0x4E56DF vs 0x4C1F4D) qua
   breakpoint/winedbg ở test động — quyết định dùng bảng opcode nào long-term
   (bảng (b2) là `CLobbyStage`; square có thêm chùm 466+).

Thứ tự ưu tiên code fakeserver (khi test động xác nhận): `on_opcode_7 → reply 7`
⇒ `on_opcode_6/303 → log (+ sau này reply 234/218)` ⇒ room list (chưa rõ, để sau).

## Phụ lục: địa chỉ tra cứu

- Gửi 7: `sub_98E763` 0x98E763 (tên file: `sub_481256` 0x481256); rời login:
  `sub_84FABC` 0x84FABC; tên file cache kênh: `sub_993EF4` 0x993EF4.
- Nhận 7: `CSelectServerStage__On_7` 0x8558C4 (dispatcher 0x859C70),
  `CLobbyStage__On_7` 0x6AFEDF (dispatcher 0x6B2ED4),
  `OnPkt_multi_7_7` 0x690A31.
- Thành công → `sub_855254` 0x855254 (dialog `sub_859F12` 0x859F12),
  reset-flag `sub_8549D5` 0x8549D5, chuyển stage `sub_8F391D` 0x8F391D /
  `CStageMgr__ChangeStage` 0x8F8EEC (khối VM, xem `docs/devirt.md`).
- Lưu server: `sub_999702` 0x999702; tra kênh: `sub_994AB9` 0x994AB9;
  đếm người chơi: `CLobbyStage__On_218`/`sub_99AEE3` 0x99AEE3.
- OnEnter gửi 303: `CStage__vf44` 0x6A3E34 (`SendPkt__Begin` 0x888462,
  `SendPkt__Send` 0x888609). Stage 11: ctor `CLobbyStage` 0x6B3EDD (size 0x5525C).
- IDA DB chỉ đọc qua MCP idalib, không save. Disasm dài không in ra chat theo quy ước.

## (c) Tại sao kẹt ở "vào kênh" — điều tra 2026-10-16 (chưa xong)

Triệu chứng: vào được stage 10 (CALog `Sg - INT(dne:10)`), nhận opcode 14 (ghi `channel2_001.ssd`,
không crash), **nhưng lưới 8 ô kênh (4×2, 5 trang) trống** → không click vào kênh được → kẹt.

### Điều kiện click được một kênh — `sub_8570DB` (0x8570DB) 🟢
Duyệt `CChannelInfo` (`dword_E60FD8`), chỉ nhận kênh `i` thỏa **cả 3**:
- `sub_994A5A(info, i) == 10` — `0x994A5A`: đọc field `+0x4C` (u8), trả **10 nếu == 18**, else trả giá trị thô.
  ⇒ **field +0x4C của record phải = 18** mới click được.
- `sub_994D51(info, i) == a2` — `0x994D51`: field `+0x40` (u8); `a2` = loại kênh click (trong `sub_856BAC` so
  với `0x80/0x82/0xC8`) ⇒ thử `+0x40 = 0x80`.
- `sub_994C91(info, i) == 0` — `0x994C91`: field `+0xC4` (u32), phải 0.

Trong record opcode 14 (`sub_994663`), 7 u8 lưu theo thứ tự vào `+0x28,+0x34,+0xD0,+0x40,+0x4C,+0x58,+0x64`.
Nên u8 thứ 4 = `+0x40`, u8 thứ 5 = `+0x4C`. Đã sửa `channel_list()`: `u8×7 = [0,0,0,0x80,18,0,0]`.

### Vẫn trống sau khi đặt kind=18 — phần chưa giải 🟡
- Dữ liệu opcode 14 vào **`CChannelCache` (`dword_E61010`)**; click/join đọc **`CChannelInfo` (`dword_E60FD8`)**
  — hai object khác nhau. `CStage__On_14` (0x99514B) copy bằng vòng `sub_9950DA(this=CChannelInfo, i, -1,
  sub_993F7B(i))` nhưng `sub_9950DA` (0x9950DA) chỉ ghi value-box vào **mảng chỉ mục** `this+3*i+59398` /
  `+62470`, **không** copy record 232-byte sang. Vậy record 232-byte trong `CChannelInfo` được điền ở chỗ khác
  (chưa truy ra — có thể `sub_994FB3` khi record đã tồn tại, hoặc broadcast opcode 7/16).
- Lưới ô kênh dựng ở `sub_858AB4` (0x858AB4, chuỗi `aChBtChannel`/`ChannelTab`) — lớn (~7.6KB decompile), chưa đọc hết.
- Field đều là **value-box** (`sub_413F32` set / `sub_414625` get, 6 byte, có `sub_A21D00` + XOR) → đọc runtime
  phải giải mã, không đọc thẳng bộ nhớ được.

### Luồng join sau khi click — `sub_856BAC` (0x856BAC) 🟢 (chưa cần tới vì chưa click được)
Gọi mỗi frame từ `CSelectServerStage__vf5`. Khi chọn kênh hợp lệ: gửi **opcode 71** (`sub_88849F(71)` +
`EncodeBool`), tính toán, **đặt `this[5915]=1`**, `sub_8F391D(dword_E6092C, 11)` (vào lobby) hoặc `(…, 20)` (square),
gửi thêm 1 packet. ⇒ client tự đổi sang stage 11; server cần xử lý opcode 71 + trả `opcode 7` thành công
(định dạng ở mục (a2)/(a3)) để không bị `ErrDisconnect` (do `On_7` đòi `[5915]==1`).

### Bước tiếp đề xuất
1. Runtime: break `sub_858AB4` hoặc dump `CChannelInfo`/`CChannelCache` sau On_14, giải value-box để xem field
   nào quyết định "kênh vào ô nào" (nghi một field = số thứ tự ô/trang).
2. Tìm nơi điền record 232-byte của `CChannelInfo` (xref ghi `dword_E60FD8 + 232*i`).
3. Khi ô kênh hiện + click được: thêm handler opcode 71 + reply opcode 7 (thành công) vào `fakeserver.py`.

### Cập nhật: hàm vẽ ô + điều kiện copy (2026-10-16)
- **Hàm vẽ lưới ô kênh = `CSelectServerDlg__vf19` (0x872672) + `sub_8729D0` (0x8729D0)** (đọc `dword_E60FD8`,
  class `CSelectServerDlg` 0x872xxx). Đây là nơi cần đọc tiếp để biết field nào quyết định ô hiện/trống.
- `sub_9950DA`: nếu `sub_414543(cache_record + 0x1C) == -1` → chỉ set mảng chỉ mục; **else `sub_994FB3`** (0x994FB3)
  copy record cache→Info (value-box các offset +40..+220). Record fakeserver gửi có `+0x1C = i+1` (≠ -1) ⇒ đáng lẽ
  chạy nhánh copy. Cần xác nhận runtime nhánh nào chạy và vì sao `vf19` vẫn vẽ trống (nghi field quyết định ô/trang
  hoặc 1 field hiển thị khác chưa set). Getter kênh (đều value-box, cùng stride 232): `sub_994A5A`(+0x4C kind),
  `sub_994D51`(+0x40 loại), `sub_994C91`(+0xC4), `sub_994A86/994A9F/9949F3`(chuỗi: tên/…).
