# c-square — Sảnh quảng trường (CLobbySquareStage, stage 11)

Nguồn: IDA db riêng `~/boom-re-oc/ida/c-square.i64` (unpacked_ca.exe). Quy ước xem `docs/protocol.md`:
handler `On_N` = opcode N; `CStage__OnPacket` case = opcode−2; đọc `RecvPkt__Decode*`, gửi
`SendPkt__Encode*`; gửi opcode = `sub_88849F(op)` hoặc `SendPkt__Begin`+`Encode*`; field game = "value
box" (`sub_413F32` set / `sub_414625` get u8 / `sub_414543` get u32). Độ tin cậy: 🟢 = đọc từ
decompile, ❓ = chưa kiểm (CHƯA KIỂM).

Đối chiếu runtime: `docs/lobby.md` Cập nhật 6/7 (client vào được stage 11, trả lời 466+467 là load xong).

## 1. CLobbySquareStage__vf44 (OnEnter) 0x4DED62 — 🟢

Flow (decompile, theo thứ tự gọi; `this` = stage):
1. Log `xrptLbyssInt`; `this[4776] = sub_A28F50("LobbySquareSta…")`, `this[4777] = …` (chuỗi log/label).
2. Gọi `CChatStage__vf44(this)`; bằng 0 → log lỗi + thoát (không qua sảnh).
3. `sub_6B7221(buf)`; qua `*(this[5542])` vf+12 (`this[5542]` = object con/particle), có `dword_E61020`/`dword_E60A0C` → `sub_8EE556(i,…)` ×6.
4. `sub_6551CB(4,2)`, `sub_8E78CB(0)`, `sub_4DE792`, `sub_4D5AA8(this)`, `sub_4D6B56`.
5. **Gửi 476** (`sub_692C71`) khi `Feature_IsDisabled_stub0()==0`; `sub_71C46A(2)`, `sub_89FA44`.
6. `sub_93BEE1`, `sub_467AFB`, `sub_940F55` (khởi tạo UI).
7. **Gửi 319** (`sub_67A132`, guard `this[3085]` — chỉ 1 lần).
8. `sub_4D6FC6(this)`, **Gửi 477** (`sub_692CC8`), **Gửi 395** (`sub_4D5C25`).
9. Gọi `(*this[5542] vf+80)`; khối nếu !Feature: kiểm `sub_9B6F75(3)`, `sub_9B6F75(4)`, `sub_8DAD87`/`sub_8DAD95`/`sub_8E9E73(dword_E60884)` = chế độ tournament — hiện dialog "BundleCreatetourname…" (UI, không packet).
10. `sub_8E7C8E(0)`, `sub_8E796D(dword_E60884)==0` → `sub_8EB853` ("gameserver connect"?); `sub_4D727A(this)`, `sub_4D7C16(0)`; if `sub_41C730(dword_E60840)` → `sub_93C767`, `sub_467AFB`, `sub_697E70`.
11. Log "gameserver conncnt"; return vf41 (`sub_9DB5CB`).

⇒ Thứ tự gửi khi bước vào: **476 → 319 → 477 → 395** (đúng quan sát runtime). 298/303/64 gửi từ chỗ khác trong stage / CStage base.

## 2. Các gói client → server lúc vào sảnh — 🟢

Quy ước: payload là các dòng sau `Encode*`, đọc thứ tự ghi (big-endian, obfuscate theo mode 1/2 — xem protocol.md).
Opcode ghi như u16 (XOR 0xA569 khi mode 2/3).

### 298 — `sub_627FCC` (site 1) / `sub_9ADBDF` (site 2)
- Site 1 `sub_627FCC(this)`: `SendPkt__EncodeStr(str = *(this+2706))`, `SendPkt__EncodeBool(false)`. `this+2706` = 0x2A38 (❓ nội dung trường — kiểu str lưu trong stage; so sánh CSelectServerStage gửi str id đã mã hoá — CHƯA KIỂM nghĩa).
- Site 2 `sub_9ADBDF()`: n = `CLobbyStage__On_218(dword_E60880)` (số mục nào đó trong lobby, runtime n≤1);
  - n ≤ 1: gửi **1 gói** `{str sub_99A731(0), bool true}`;
  - n > 1: gửi **n gói** `{str sub_99A731(i), bool true}` i=0..n−1.

### 303 — gửi từ `CStage__vf44` 0x6A3EDA (base CStage; CLobbySquareStage kế thừa)
Điều kiện: sau `sub_694E38`, với `n = CLobbyStage__On_218(dword_E60880)` (số mục) và global mode `m`:
`m = 1` khi giá trị trả về nằm trong 11..12, `m = 0` khi bằng 20; ngoài khoảng 11/12/20 → không gửi.
Mỗi i = 0..n−1: `sub_88849F(303)`; EncodeBool(m)… với **field2 nghi ngờ là Encode2 (u16 = i), cần soi disasm** xem đúng lệnh call Encode nào.
Nghĩa tổng thể 303 = ❓ (xem §3).

### 319 — `sub_67A132(this)` : gói rỗng (0 field) 🟢
Guard `this[3085]` (chỉ gửi 1 lần/nhập, reset khi ra vào lại sảnh); trả về 0 nếu đã gửi ⇒ **yêu cầu 1 lần**, không lặp.

### 64 — `sub_679EF4(this, a2)` : `u16` field 🟢
Giá trị = `a2 + *(this+1257)`. Kẹp: `a2 + *(this+1257) >= 0` và `*(this+1258)==0` mới gửi; sau gửi `*(this+1258)=1` (lần đầu trong stage).
Nghĩa: lật trang/nhóm danh sách tin gì đó — nghĩa đối diện ở handler On_64 (xem §3).

### 476 — `sub_692C71` : rỗng (gọi từ vf44 và có thể từ chỗ khác) 🟢
### 477 — `sub_692CC8` : rỗng 🟢
### 395 — `sub_4D5C25` : rỗng 🟢 (→ server trả 466 + 467 theo lobby.md Cập nhật 7)
### 396 — client gửi sau khi gói 467 xử lý xong (cuối On_467 đặt `this[4775]=1`) — xác nạp xong (chưa soi field).

## 3. Server → client — opcode 466/467 (thông tin sảnh + người chơi)

### 466 = thông tin khu/map (On_466 0x4E52B5 — khớp lobby.md Cập nhật 6)
```
opcode 466 (server→client): u32 area, blob, str, str, u32
```
- `u32 area` → `this[5541]`; `sub_8E7C8E(18<=area<=19)` = cờ chế độ khu.
- blob: `u32 n, n × {u32 m, m × u32×5}` (vật thể khu, `sub_4E4EFD/sub_4E134C`).
- `str` = tên map (`"Map/%s"`), `str` = theme (`"Theme/%s"`, `sub_8D8A48` → `sub_8DA6F5`), `u32` (ghi cùng map, ❓).
- **Tên khu thanh trên trái** khi area ≠ -1: key `"LobbySquare_AreaName%02d"` (aLobbysquareAre,
  0x?), area → `sub_415B2F` (so đếm `%`-placeholder rồi sprintf `sub_A205F0`; thấy tên không
  format được thì qua `sub_4014BC`) rồi `sub_4D3EBE` vẽ. area = -1 → dùng tên kênh hiện tại
  (`sub_993FD6(sub_9995C2(dword_E60784))`). Ở nhánh ≠ -1 còn ghép `"%s-%s"` (aSS_3 0xC24FD0,
  `sub_42A941`) với tên kênh — ❓ phần nào đi vào thanh nào.

### 467 = danh sách người trong sảnh (On_467 0x4E4100)
```
opcode 467 (server→client): u16 n, n × {u16 slot, u32 uid, blob "profile", u8, u8, u16 x, u16 y,
  u8, blob, bool [blob], bool(feature74) [blob], u32 m, m × blob}
```
- Chặn `sub_4D82DE()` (đang nạp map); mỗi record `sub_4E3F29`: **u16 slot** — bỏ nếu
  `slot >= sub_6E3D75()` (sức chứa `*(object+54)` của phủ, "slot < max" mới tiếp tục).
- `sub_4E2D7E(this, slot, a3)` (2004 byte) lần lượt đọc:
  1. `u32` → `obj[+36]` (móc vào `sub_679434(a2)`), obj = `malloc 0x198` + `sub_469AC8`.
  2. **blob "profile" → `sub_679434`**, thứ tự trong blob (mọi field lưu qua value box `sub_413F32`):
     - **str tên** → `sub_40E909(obj+8)` — thứ đầu tiên của blob! Getter tên = `sub_678ED7`
       (thunk `sub_A67960` = `return this+8`).
     - u8, u8, u32, u8, u32, u16, u32 (các box), u32 → obj+188 (this[47]),
     - u32, u32 (bán qua `sub_44AD23` — ❓ kiểu), u8, u32, **str thứ 2** → obj+160
       (❓ tên riêng/handle; dùng cho một phần UI khác),
     - u16 ×3 → box, u16 (đọc nhưng không lưu — ❓ có thể lúc dump bị bỏ ngoài), 
     - u32 → `sub_679056` (❓), u32 (giắcon bounds 0..1) → box, u32 ×4 → obj+392..404 (this[98..101]).
  3. `u8` (v39), `u8` (v42): bitfield — build `j` = mask **0x3F (bits 6..11) từ v39,
     0x1F (bits 13..17) từ v42**; sau đó `sub_8E76A3(slot, v39)`, `sub_8E8EBB(slot, v42)` — ❓
     hai u8 = hành vi "đi/vào khu" hay thuộc tính hiển thị.
  4. `u16 x, u16 y` — pixel; **tile = x/40, y/40** (`sub_6EB788(...,x/40, y/40, ...)`) → **vị trí**.
  5. `u8` (v5) — thành bitfield thứ 3 (`sub_8EA539(slot, …)` trước đó đã xoay `j` 0xC0E0 bits: ❓).

6. `blob` → `sub_8EABEC(slot)`; nếu u8 đầu blob (`sub_A62F40`) ≠ 0 → `sub_97EDBC(blob,0)` rồi
   `sub_8ED30A(slot, …)` — ❓ nghĩa (nhóm职称 guild?).
7. `bool` → nếu 1: `blob` → obj new 0x74 (`sub_4720DD`, `sub_9C9EB6`) → `sub_8EAEFA(slot, …)` ❓.
8. `bool` (feature74, luôn stub=0):
 sat → 1: `blob` → `sub_40D664`, `sub_4BE6CD`, `sub_42C75D`, `sub_4D4787` ❓ (phần lớn bỏ nếu feature bật).
9. `u32 m` → m × blob (mỗi blob: nếu u32 đầu == 1 → u16, u32: `sub_86493F(slot?)`/`sub_8664D7` — ❓
   buff/effects 标 các slot).
10. feature76 stub==0: đọc đã có sẵn obj — `sub_8E8014/8E7F9A/8E7FD7/8EB468` + `sub_5A2BCD` (không đọc thêm từ wire).
   - Cuối: `sub_4DC5C2(slot, obj)` (#đ quản lý "ai trong sảnh"), `sub_4D8156(name…)` - `sub_8DD45B(name)`
     = **tìm tên trong bảng 64-entry × n-tabs tại CMainWnd + 676.radians, mỗi entry 21 byte
     (stride 1344/tab, n = `CLobbyStage__On_218(CMainWnd+12)` box)**: thấy → `sub_86472A(1)` — ❓
     bảng này là gì trong GUI (bạn thu chủ khu?).
- Kết thúc handler: hiển thị UI (`sub_592ADE(1)` số self "SelfIndicator" ❓), rồi:
  - **`sub_679EF4(dword_E61018, 0)` = GỬI op 64 LẦN 2 (a2=0, guard `this[1258]` lần 1 đã nên ngừng)**,
  - đặt `this[4775] = 1` (flag "đã nhận danh sách", dùng để bào "Đang tải"),
  - **gửi op 396**: `sub_88849F(396)` + `SendPkt__Send` không field nào — **396 = xác nhận nạp xong, rỗng**.
