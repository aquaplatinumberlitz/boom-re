# Boom Online — Master Plan viết lại engine bằng Rust (giữ ~100% cảm giác chơi)

> Trạng thái: **ĐỀ XUẤT (2026-10-19)**. Bổ sung cho `docs/MASTER_PLAN.md` (kế hoạch RE/bảo tồn);
> tài liệu này chi tiết hoá nhóm PORT-* thành kế hoạch viết lại cụ thể.
> Quy ước tag giống `docs/MASTER_PLAN.md`: **[VERIFIED]** đã kiểm trong repo, **[DOC]** theo tài liệu sẵn có,
> **[HYPOTHESIS]** giả thuyết, **[UNKNOWN]** chưa biết.

## 0. Bối cảnh & quyết định

Engine gốc (Crazy Arcade/BnB, bản VN `VBNB_116`) đã 25 năm tuổi, source và asset gốc phần lớn đã thất lạc.
Định hướng: **RE client còn lại → viết lại engine bằng Rust, dùng asset trích từ client**.

Quyết định đã chốt (2026-10-19):

| Chủ đề | Quyết định |
|---|---|
| Tương thích client gốc | **Không.** Giao thức v2 mới; giao thức gốc chỉ dùng để đối chiếu/replay test |
| Nền tảng | Desktop: Windows / Linux / macOS |
| Hiển thị | **Pixel-perfect**: render đúng độ phân giải gốc vào framebuffer, phóng to nguyên lần; có chế độ "gốc 100%" để so sánh |
| Release 1 | Trận đấu (chế độ chính) + kênh/sảnh/phòng chờ + online. Shop/túi đồ/guild/sự kiện để sau |

## 1. Kết luận khả thi

**Khả thi.**

- Asset đã gỡ hết **[DOC]** (`docs/assets.md`): 108.726 PNG, 645 ogg, 965 map, `Attr/*`.
- Giao thức và luồng trận đã thông **[DOC]** (`docs/protocol.md`, `docs/oc_e-game.md`).
- Client gốc chạy được dưới Wine + gdb, nên có thể **đo trực tiếp** hành vi gốc (`tools/wine_gdb.sh`, `tools/match_gdb.sh`, `tools/gdb/`).

Rào cản thật: **gần như chưa có hằng số gameplay nào được khôi phục**. Thiếu tốc độ, hitbox, fuse bom,
thời gian và cách lan của vụ nổ, timing animation, blend/z-order, tick rate, độ phân giải render (xem §3).
Cảm giác chơi nằm ở chính những con số này.

→ **Nguyên tắc số 1: "Đo, không đoán."**
- Mọi thông số ảnh hưởng cảm giác chơi phải có nguồn từ client gốc (đọc tĩnh trong IDA hoặc đo runtime).
- Mỗi thông số phải có test so sánh tự động.
- "~100%" được định nghĩa bằng số đo (§2), không bằng cảm nhận.

## 2. Fidelity Spec — "giống gốc" nghĩa là gì (đo được)

| Hạng mục | Tiêu chí chấp nhận |
|---|---|
| Mô phỏng (vị trí bomber, bom, nổ, item, bẫy/chết) | Cùng chuỗi input → trace vị trí theo tick **khớp 0 px** với client gốc; sự kiện (nổ, chết, nhặt item) lệch ≤ 1 tick |
| Hình ảnh | Khung hình native-res so pixel với ảnh chụp gốc: ≥ 99,5% pixel trùng trên cảnh tĩnh; đúng frame animation theo tick |
| Âm thanh | Đúng file, đúng tick phát (± 1 tick), đúng âm lượng/kênh/loop, đúng quy tắc chồng tiếng |
| Input | Độ trễ input → chuyển động bằng gốc (đo theo frame); quy tắc ưu tiên phím khi giữ nhiều hướng giống gốc |
| Mạng | LAN: không phân biệt được với offline. Online: client prediction giữ cảm giác ở ping ≤ ~100 ms |
| Playtest | Người chơi cũ chơi A/B mù (gốc và mới) không phân biệt được ở các tình huống chuẩn |

## 3. Đã biết / chưa biết

### 3.1 Đã biết

| Thông tin | Nguồn |
|---|---|
| Ô 40 px (`idiv 0x28`), map thường 15×13; toạ độ gói bomber x = col·40, y = row·40+39 | `docs/map.md`, `docs/oc_e-game.md` **[DOC]** |
| `.map` v1000/1001 giải gần hết: lưới (tile, obj, overlay), điểm spawn, bảng drop | `docs/map.md`, `decomp/CGamePlayMap__Load.c` **[DOC]** |
| Sprite `CDataI16Alpha` v2: RLE, RGB565 colorkey `0xF81F` hoặc BGR24 + kênh alpha (alpha = 255 − v) | `tools/i16.py`, `docs/assets.md` **[DOC]** |
| Frame record 48 byte: chỉ số ảnh, rect nguồn, canvas, pivot, offset (**chưa có thời lượng**) | `docs/map.md` **[DOC]** |
| `CGameClock`: base = `timeGetTime()` − ping/2, có pause/resume; giới hạn trận 90/120/180/300 s theo chế độ | `docs/oc_e-game.md` **[DOC]** |
| Tick trận: `CGameStage` vf46 `0x70572A` → vf159 `0x71BF9A` mỗi tick | `docs/oc_e-game.md` **[DOC]** |
| Bị bẫy → chết ~6–6,3 s; tầm nổ = 1, tăng theo ItemFire | `docs/oc_e-game.md` **[DOC]** |
| Bảng ItemAttr đầy đủ (tên, sprite, trọng số drop, nhóm, tham số); Shield 2000/1000 ms | `docs/items.md`, `decomp/item_kinds.json` **[DOC]** |
| Âm thanh: Miles (`mss32.dll`, `_AIL_*`), SFX `.ogg`, BGM `.mp3` theo map | `decomp/iat_resolved.json`, `docs/oc_e-game.md` **[DOC]** |
| Renderer `CRenderD3D9` (d3dx9_30), dự phòng DDraw7/D3D7; font `CxUni*.fft`; video Bink | `rtti.txt`, `ca_strings.txt` **[DOC]** |
| Mô hình lai: client tự quyết di chuyển, phá gạch, bẫy/chết; server quyết bom id, **thời điểm nổ (151)**, item layout, duyệt nhặt item; vị trí đồng bộ P2P UDP | `docs/oc_e-game.md` **[DOC]** |

### 3.2 Chưa biết **[UNKNOWN]** (đều phải đo ở R1)

| Thông số | Ghi chú |
|---|---|
| Tick rate; vòng lặp fixed-step hay variable-step | Client import `timeGetTime`, `QueryPerformanceCounter`, `Sleep`; có chuỗi `"FPS: %d"` |
| Tốc độ di chuyển theo cấp, gia tốc, cách trượt qua góc ô | Va chạm tính ở client, chưa phân tích (`docs/features.md` F12) |
| Hitbox bomber, bom, vụ nổ | — |
| Fuse bom | 2,5 s trong `server/src/session.rs` (`BOMB_FUSE`) chỉ là giá trị tạm |
| Thời gian vụ nổ tồn tại, cách lan, nổ dây chuyền, xuyên/chặn | Server gốc tính vùng nổ thế nào chưa rõ |
| Timing animation từng sprite | Trường f2 của frame record chưa rõ |
| Blend mode, z-order/layer | Chỉ biết map v1001 có lớp overlay theo ô |
| Hiệu ứng item chi tiết (tốc độ, kim, khiên…) | Mới chắc kind 0 (+1 bom), kind 1 (+tầm) |
| `BomberAttr.bin` (41 bản ghi × 11 i32) | Có thể là chỉ số gốc của nhân vật, độ tin cậy thấp |
| Độ phân giải render thật | Cửa sổ 800×600 trong guest; chưa log `Init Renderer D3D9 %dx%d` |
| Định dạng font `.fft` | — |

## 4. Chiến lược đo: "Feel Oracle" (WS-ORACLE, làm đầu tiên)

Dựng trên hạ tầng sẵn có: `tools/wine_gdb.sh`, `tools/match_gdb.sh`, `tools/match_play.sh`, `tools/gdb/*.gdb`
(`phase_clock`, `clock_start`, `bomb_path`, `input_dispatch`, `input_gates`, `items`…), `tools/snapdiff.py`,
`tools/xvfb_*.sh`, `tools/duo.sh`.

1. **Tracer.** Script gdb ghi mỗi tick thành JSONL:
   - input;
   - vị trí, hướng, trạng thái bomber (`CGOCAHeroGameBomber`);
   - bom (`CGOGameBomb`), ô nổ (`sub_7324C0`), item;
   - lệnh phát âm thanh (`_AIL_*`);
   - sprite và frame được vẽ, kèm render state D3D9 (`SetRenderState`, `SetTextureStageState`).
2. **Input tất định.** Chuỗi phím có kịch bản (`xdotool`, như `tools/duo.sh`) để tái lập y hệt.
3. **Thư viện trace chuẩn** `tests/oracle/*.jsonl` (đề xuất), mỗi trace kèm ảnh chụp:
   - đi thẳng; rẽ góc; trượt góc;
   - đặt bom, nổ dây chuyền, nổ chặn bởi gạch/khối;
   - từng loại item;
   - bẫy, giải cứu, chết; hết giờ.
4. **Đọc tĩnh song song** trong IDA để lấy hằng số chính xác (tốc độ dạng fixed-point, bảng timing).
   Trace dùng để xác nhận; khối Themida VM thì đo black-box (`docs/vmdevirt.md`).
5. Mỗi hằng số ghi vào **`docs/spec/rules.md`** (đề xuất) kèm địa chỉ hàm và trace chứng minh.
   Không hằng số nào vào `boom-core` mà thiếu nguồn.

Sau R2, `boom-oracle` chạy trên CI: mỗi PR đụng `boom-core`, `boom-render` hoặc `boom-audio` phải replay
toàn bộ trace và so ảnh xanh.

## 5. Kiến trúc Rust

Một Cargo workspace; `server/` hiện tại chuyển thành `crates/boom-server`.

```
crates/boom-core    luật chơi tất định: fixed tick, số nguyên/fixed-point (không float), không IO, replay được
crates/boom-assets  port tools/idf.py + tools/i16.py (+ frame record, .map, Attr/*, .fft); CLI `boom-convert`
crates/boom-render  wgpu: framebuffer native-res → integer scale; sprite batch; colorkey/alpha/blend đúng gốc
crates/boom-audio   kira: SFX ogg + BGM mp3; mô phỏng kênh/ưu tiên/âm lượng của Miles
crates/boom-ui      widget skin bằng sprite gốc (dialog, list, nút, ô nhập); layout data-driven tái tạo màn gốc
crates/boom-proto   giao thức v2 (serde + postcard, có version)
crates/boom-net     client prediction + reconciliation/rollback trên boom-core
crates/boom-server  từ server/ (tokio; hub/room/session tái sử dụng), server-authoritative chạy boom-core
crates/boom-client  winit + wgpu + kira; vòng lặp fixed-tick tách khỏi render
crates/boom-oracle  so trace gốc ↔ boom-core, ảnh ↔ ảnh, sự kiện âm thanh
```

**Vì sao không dùng engine lớn (Bevy…):** để khớp 0 px cần kiểm soát tuyệt đối thứ tự tick, pipeline vẽ và timing.
Stack mỏng (winit/wgpu/kira) ít "phép thuật", dễ tất định, dễ debug so với gốc.

**Hiện đại hoá ở đâu:**
- tách luật / hiển thị / âm thanh / mạng;
- dữ liệu (map, item, UI layout) đọc từ file, không hardcode;
- test tự động bằng oracle;
- build cho 3 hệ điều hành;
- không còn anti-cheat hay packer cũ.

**Netcode:**
- Gốc là mô hình lai: client tự quyết di chuyển, vị trí đồng bộ P2P qua UDP.
- Bản mới là **server-authoritative**: server chạy chính `boom-core` cùng tick; client dự đoán (prediction)
  rồi reconcile hoặc rollback.
- Kết quả: LAN giống hệt offline, chống gian lận tự nhiên, không cần P2P/NAT.
- Giao thức gốc (`server/` + `server/tests/golden.rs`) giữ lại làm công cụ đối chiếu hành vi.

## 6. Lộ trình

Mỗi pha có exit criteria đo được. Ước lượng cho 1–2 người toàn thời gian; đây là con số định hướng, chưa phải cam kết.

| Pha | Mục tiêu | Exit criteria | Ước lượng |
|---|---|---|---|
| **R0** Nền móng | Workspace; `boom-assets` (port idf/i16, frame record, `.map`, `Attr/*`) | `boom-convert` xuất lại 100% asset; PNG khớp hash với `tools/i16.py`; `cargo test` của server vẫn xanh | 2–3 tuần |
| **R1** Feel Oracle | Tracer + RE hằng số cốt lõi (tick, tốc độ, hitbox, fuse, nổ, animation timing) | ≥ 15 trace chuẩn; `docs/spec/rules.md` có nguồn cho từng hằng số §3.2 cốt lõi | 4–6 tuần (song song R0) |
| **R2** Core | `boom-core`: trận 1 map (Village01), bom, nổ, gạch, item cơ bản, bẫy/chết | Replay mọi trace R1 khớp 0 px / ± 1 tick | 3–4 tuần |
| **R3** Hình + tiếng | `boom-render`, `boom-audio`, client offline 2 người 1 máy | `snapdiff` ≥ 99,5%; sự kiện âm thanh khớp ± 1 tick | 4–6 tuần |
| **R4** Nội dung trận | Toàn bộ item, mọi map và các chế độ battle chính (cá nhân/đội) | Trace từng item/chế độ khớp | 6–8 tuần |
| **R5** Mạng | `boom-server` + `boom-net`, giao thức v2, phòng/ghép trận 2–8 người | Trace trận mạng = trace offline cùng input; chạy ổn ở ping mô phỏng 100 ms | 6–8 tuần |
| **R6** UI ngoài trận | Login, kênh, sảnh, phòng chờ bằng skin gốc | Ảnh từng màn khớp gốc theo Fidelity Spec | 4–6 tuần |
| **R7** QA & phát hành | Playtest A/B mù với người chơi cũ, sửa lệch, build 3 OS | Đạt toàn bộ §2 | 3–4 tuần |

**Tổng Release 1: khoảng 8–12 tháng.**

Sau Release 1, theo thứ tự trong `docs/features.md`:
- các chế độ đặc biệt F13–F21 (HiddenCatch, SnowBear, SnowBall, Boss, RPG, Zombie, AI quái…);
- shop, túi đồ, guild, sự kiện.

## 7. Rủi ro & giảm thiểu

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| Timing gốc phụ thuộc FPS (variable-step) → khó khớp tick | Cao | Việc đầu tiên của R1 là xác định mô hình vòng lặp. Nếu gốc là variable-step thì mô phỏng đúng công thức đó ở tần số cố định |
| Hằng số nằm trong khối Themida VM | Trung bình | 14/15 khối game đã xử lý (`docs/devirt.md`); phần còn lại đo black-box |
| Blend/hiệu ứng D3D9 khó tái tạo | Trung bình | Hook và ghi render state cho từng loại sprite; tái tạo bằng shader wgpu |
| Font `.fft`, video Bink (`nm.bik`) | Thấp–TB | RE format font; chuyển video offline sang định dạng mở |
| Server-authoritative làm lệch cảm giác khi ping cao | Trung bình | Prediction + rollback; đo input latency trong oracle |
| Phạm vi phình to | Cao | Khóa phạm vi Release 1; tính năng mới phải có dòng trong `docs/features.md` và được duyệt |
| Pháp lý asset/IP | Cao | Xác nhận bằng văn bản quyền sử dụng/công khai trước khi public repo hoặc phát hành |

## 8. Việc làm ngay

- [ ] **R1-001**: xác định tick rate và mô hình vòng lặp (`CGameStage` vf46 `0x70572A`, vf159 `0x71BF9A`; `timeGetTime`/`Sleep`).
- [ ] **R0-001**: tạo workspace, chuyển `server/` thành `crates/boom-server` (giữ `server/tests/golden.rs`, `server/tests/bomb.rs` xanh).
- [ ] **R0-002**: port `tools/idf.py` + `tools/i16.py` sang `boom-assets`; test hash khớp bản Python.
- [ ] **R1-002**: script gdb tracer bomber + bom; trace đầu tiên "đi thẳng + đặt 1 bom".
