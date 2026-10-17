# Phòng chờ (stage 12, CPrepareStage) — đặc tả tĩnh cho server giả

Phạm vi: phân tích tĩnh `unpacked_ca.exe` (bản copy DB riêng `boom-re-oc/ida/a-room.i64`),
tia tiếp docs/lobby.md (Cập nhật 6/7, Errata audit) và docs/protocol.md. Độ tin cậy:
🟢 decompile rõ · ❓/CHƯA KIỂ = suy đoán.

## 0. Khung chung — vòng lặp sự kiện phòng chờ

- Handler sự kiện (click nút/ô) của **CPrepareStage**: `sub_6CB7B6` (0x6CB7B6). Gate đầu:
  vf(44) của `*(stage+15139)` (stage-mgr) trả 0 mới xử lý; `a2` = id sự kiện.
  Bản ghi event: `0xBBA`=chọn bản đồ→`sub_6BE40F`; `0xBBB`=→`sub_6CB78F`
  (đến `sub_8EA9B0()!=0` mới chạy `sub_6C95AD`); `3616..3624`(0xE20..0xE28)=cửa
  hàng/nhặt; `3620`=clear cờ; `3350`(0xD16+)=`sub_6C1A53`; `3500`(0xDAC)=BẮT ĐẦU→
  `sub_6C93B0`; `3617/3618/3619` hướng về các nút; `3616/3618`→`sub_6C3A62(3617)`/
  `sub_6587B8(447)`; `3200`(0xC80)=`sub_6C0585`; event đồng thời `0xCE3..0xCEB` →
  `sub_6C1947`. 🟢
- O kak raz: a2 ∈ [3400..3400+this+4776): click **ô slot hàng 1** → `sub_6C9413`;
  `a2 ∈ [3600..3615]`: **sub_6C62A4** (gửi opcode 212, ❓ mục 4).
- Đvény chờ/lock **`this[4777]`** (pre-stage):
  `0`=rảnh · `1`=đã gửi 88 (xin đổi chỗ/phòng) · `2`=đã gửi 94 (toggle slot) ·
  `4`=đã gửi 87 (BẮT ĐẦU).While != 0 các hàm gửi đều từ chối. 🟢
- `sub_8EA9B0()` (0x8EA9B0): trả 1 nếu **ØNG chơi+khiên (host) của phòng có bit1(0x2)**
  (? — đọc `CLobbyStage__On_218(dword_E60880)` số người chơi, duyệt mỗi slot qua
  `sub_8EA779(&3byte, i)` — slice trạng thái 3 byte = bit0 sẵn sàng, bit1 host, bit2
  một cờ trạng thái; dung trường hợp `state&2`). = "có host trực tuyến". ❓ "MỌI LUỒNG
  GỬI 88/87/94 ĐỀU ĐÒI HÀM NÀY ≠0" — tức chỉ người phòng nào đã trong ô mới gửi được. 🟢

## 1. Luồng Ô người chơi / SẴN SÀNG (opcode 94)

### 1a. Client gửi — `sub_6BE8AF` (0x6BE8AF) 🟢

Click **ô của chính mình** (sub_6CB7B6 × slot-range 3400 → `sub_6C9413`;
điều kiện `(state&0x1C)!=4` — không phải trạng thái bị khóa? ❓; và `sub_8EA9B0()!=0`,
cùng `sub_8DADA3()/sub_8DAD4C()` bỏ qua một vài chế độ ❓). Đổi state cục bộ, lật bit0
(sẵn sàng) rồi GỬI:

```
opcode 94 (client→server): bool slot (SendPkt__EncodeBool — 1 byte),
                           bool bit-sẵn-sàng-mới (1 byte)
```
- Giới hạn slot: chỉ nhận khi `slot ∈ 4..15` HOẶC mã mode đặc biệt (117; 128/125;
  133) theo 3 nhóm kiểm `sub_988B51/988B7D/988DB8(mode)` — nghĩa ❓ (slot 0..3(
  =peers) bị chặn gửi riêng).
- Sau gói (sub_999526 ≠0): tiếp tục đặt `this[4777]=2`, gọi **vf153(0)** (tắt nút
  BẮT ĐẦU chờ server_callback); `sub_5A71F(slot, state-payload-6-byte)` áp cục bộ.
- Hằng phi đễn: `sub_6918DD` (0x6918DD, sibling của CSessionStage — đưга
  `sub_68D847`, nhánh slot hàng 2 3450+ dùng point khác `sub_68C244` ❓) gửi cùng
  format và đặt `this[4772]=2`. ⚠ Chưa suy luận được tại sao tồn tại song song
  2 luồng gửi 94 (khả năng 2 component khác nhau render cùng UI). CHƯA KIỂ.

### 1b. Server phải trả — **On_94 → `sub_6C450D` (0x6C450D)** 🟢 (đổi thông tin phòng)

CPrepareStage__On_94 = `sub_6C9241` (0x6C9241): nếu `sub_8DAB40()/8DAD87/8DAD95` bất kỳ
≠0 → nhánh đặc biệt `sub_6C43BA` (❓ chưa đọc); ngược lại `sub_6C450D` — đọc:

```
opcode 94 (server→client): str A, str B, u8 (= số người chơi? cộ слот phòng — trong
                           code so với field +118 của room-object), u8 (= mã mode)
```
- So: nếu str B rỗng-none… logic: nếu `(str B khác cache) || sub_8E75EA(E60884)!=u8#1
  || sub_8E78DB(E60884)!=u8#2` → thông báo `aRoominfochange` ("room info change");
  else nếu str A đổi → `aRoomnamechange`. 🟢
- Luôn áp vào room object `dword_E60884`: tên (`sub_8EB853(str B)`), tít cũ
  (`sub_8EB8CD(str A)`), `sub_8E75D2(u8#1)` (=field +118, clamp >2→1 — mode/chế độ số
  người chơi), `sub_8E78CB(u8#2)` (=field +228, mã phòng/mode); `sub_6BFC2A(u8#2)`;
  nếu `sub_8EA9B0(E60884)!=0`: `v=sub_6DF84B(...)` → **gửi tiếp opcode 88 (u16, u32)**
  (`sub_6C3557`); nếu mode cũ `+228==16` và mới ≠16 → `sub_6C0E47(u8#2,0)` (rơi UI
  team/свой chế độ ❓).
- ⚠ Hệ quả QUAN TRỌNG cho fakeserver: sau khi nhận **94 (toggle slot)** hoặc khi
  client đổi mode qua chọn map → server phải **trả 94 (broadcast phòng: str, str,
  u8, u8)** trước, client sau đó còn gửi tiếp **88**(nếu có người đang sẵn sàng/ô
  chuyển — điều kiện trong hàm, ❓ chính xác điều kiện nhánh).

## 2. Chọn bản đồ (nút 0xBBA → sub_6BE40F → vf152; gói 88)

### 2a. `CPrepareStage__vf152` (0x6D0E02) — hộp thoại chọn map 🟢

- Gate: `sub_8DAD7B()!=0` và **mode phòng `sub_8E78DB(E60884)` (=field +228) ≠14**
  (14 = được phép qua nhánh riêng? — chỉ gọi getter, no-op rõ ràng — ❓).
- Mở dialog map-list theo **mode hiện tại**:
  `+228==14 → sub_647774(1)`; `==16` (14+2) → `sub_9B63AA(0,1)` + `sub_6477DF(…,1)`;
  `==17` (14+3)?? — decomp thứ ba: `sub_9B63C3(0)` + `sub_647816(…)` (nhánh mode
  đặc biệt). Đang xác định `(mode==14 or mode==17)` → `sub_647774`.
  Nghĩa: 14 = map tự chọn thường/17 = "chief map" — 16 = ❓. Đánh dấu „mode 14/16/17"
  là 3 **bộ định dạng bộ chọn map** khác nhau.
- Dialog mod: khi OK (`CBuyItemListDlg__vf38(0,1,1)==3`) → `v33=sub_6483EE(v36)`
  = **id map đã chọn**; nếu mode hiện tại ==17: kiểm "chief prev" (`sub_9C0F6C`)
  → quét 12 slot: người có "khoảng 7 điểm" quá cao bị đuổi (`sub_41C229`, ❓ chi tiết
  rule); nếu đuổi-xoá → thông báo `aCannotselectma` ("cannot select map") GỬI LỆNH
  ❓ — cùngimar till packets? — không packet ở bước chỉ xong — hàm cuối cùng gọi
  **`sub_6C3557(this, id_map, 1)`**.
- Cancel (vf38==4) → vf65(this,-1): không gói.
- ⟹ **khi chọn map client gửi `opcode 88`** (xem 2b).

### 2b. `sub_6C3557` (0x6C3557) — gửi opcode 88 🟢

```
opcode 88 (client→server): u16 (sub_6DC06C(id) = u16 tại bản ghi-map[id]+112
                           = "chỉ số map theo nhóm"?), u32 (id = id-đCV chọn)
```
- Điều kiện: `this[4777]==0` và `sub_8EA9B0()!=0`.
- Chặn 2P: nếu `sub_6DC339(id)==247 && dword_E60848>=2` → chỉ hiện
  `a2pcannotenterg` ("2P cannot enter game…"), **không gửi**.
- Send ok → `this[4777]=1`, **vf153(0)**.
- Caller khác của 6C3557: `sub_6C450D` (On_94 — tự gửi lại 88 khi mode đổi),
  `CPrepareStage__vf149`, `vf150`, `vf152`, `sub_6D5834`. ⟹ **opcode 88 được dùng
  chung cho mọi "cosoj/forum/you/вход phòng / đổi map / đổi mode"** — task phần (3)
  "opcode 88 (u16,u32) khi vào phòng" trớ hộp; field = (u16 chỉ số-nhóm-map,
  u32 id). Hoàn; nghĩa server trả lại = **94** (sub_6C450D) cập nhật phòng. CHƯA KIỂ
  cho giá trị sample.

### 2c. Map/theme id hợp lệ 🟢/❓

- `sub_6DC339(id)` (bản ghi+41): mode/loại của map; `sub_6DC06C(id)` (+112): u16 chỉ số.
- Đến lượt bắt đầu trận, server trả On_501 chứa str tên map; client kiểm:
  `sub_736FE3(field, u16_mapid)` trả **chuỗi mẫu (mảng 56-byte-str `this+56*id`)**
  so sánh phần prefix bằng `_mbsnbcmp` với tên map trong gói, và `sub_6DE36E(u32)`
  kiểm `0<=id<sub_414543(this+72)` + hợp lệ qua `sub_6DD49B` (7 kiểm con
  `sub_6DC65E/6DC706/6DC73E/6DC6CE/6DCBA2/6DC696/6DC776`) — false → dialog
  `aInvalidmapretu` ("invalid map returned"). 🟢 nghĩa field:
  `sub_6DD49B(id)!=0` → lưu `sub_8E7E46(cờ)`. ❓ đối tượng `this+72` chưa định danh.
- Nhóm "bản đồ konnte chuẩn": chuỗi list ở mảng `this+56*i` — cần dump runtime.
  KHÔNG KHIẾT từ file tài nguyên tĩnh — CHƯA KIỂ (xem §5 việc còn lại).
