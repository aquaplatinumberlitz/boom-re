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

## 3. Server → client trả gói nào (handler client tương ứng)

(đang phân tích — sẽ điền)
