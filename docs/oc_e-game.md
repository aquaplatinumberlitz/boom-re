# e-game: Stage TRẬN ĐẤU (stage 13) — phân tích tĩnh (IDA `~/boom-re-oc/ida/e-game.i64`, bản copy riêng)

Tiền đề (docs/lobby.md Cập nhật 10): phòng chờ = stage 12 `CPrepareStage`; bấm BẮT ĐẦU → `CPrepareStage__vf5` →
`sub_6CB7B6` (0xBBA = chọn bản đồ, 0xBBB) → `sub_6C95AD` → `sub_6C63B6`. Quy ước: handler `On_N` = opcode N;
`CStage__OnPacket` case = opcode−2; đọc bằng `RecvPkt__Decode1/2/4/8/Str/Blob`, gửi bằng `sub_88849F(op)` +
`SendPkt__Begin` + `SendPkt__Encode*` (mọi field bị obf XOR như protocol.md). Field game là "value box"
(`sub_413F32` set / `sub_414625` get u8 / `sub_414543` get u32); offset getter = offset lưu + 0x18 (Errata).

## 1. Nhận diện stage trận

### `sub_6C95AD` (0x6C95AD) → `sub_6C63B6` (0x6C63B6)
- `sub_6C95AD`: guard `sub_8DAB40`, `sub_8DADCA`, `sub_8DADE6`, `sub_8DAD87`, `sub_8DAD95()`: nếu `sub_8DAB40` ≠0 → đường
  `sub_6C2888`; 3 cái giữa ≠0 → `sub_6C2B69`; tất cả 0 → `sub_6C63B6` (đường trận thường).
- `sub_6C63B6`: kiểu chơi `v18 = sub_8E75EA(dword_E60884)` (room type?) và `v19 = sub_8E78DB(dword_E60884)` (battle kind?);
  `sub_975083(v19) != 0` → đường thường `sub_6C5EC8(v20, tên, v23, &v18, &v19)` (chỉ dựng cấu hình UI, không thấy gửi
  opcode); v19 ∈ {15, 17} → đường `CSimpleModifyRoomInfoDlg__vf44` + `sub_6C5D8C`. Bấm BẮT ĐẦU chỉ đổi UI — **không thấy
  gửi gói xin bắt đầu**; server tự quyết bằng gói 501. CHƯA KIỂ: xem `sub_6CB7B6` 0xBBB có gửi gói gì.

### On_501 → stage 13 ✅
`CPrepareStage__On_501` (0x6C4978): nhánh bản đồ hợp lệ → **`sub_8F391D(13)`**; nhánh tên bản đồ lệch (`aInvalidmapretu`,
hộp thoại "Invalid map...") → `sub_8F391D(this[15141])` + `sub_8F2F14` (quay về phòng chờ).
⇒ **Trận thường = stage 13, lớp `CGameStage`** (bảng vtable +: vf44 OnEnter 0x71B519, vf51 OnPacket 0x71B631,
kế thừa `CChatStage` → cuối OnPacket chuyển tiếp `CSessionStage__vf51`).

## 2. OnEnter — `CGameStage__vf44` (0x71B519) → `sub_71A9EC` (0x71A9EC) ✅
CALog: chuỗi `"[XRpt] Sg - INT(dne:%d)..."` (0xC7B204) — pattern stage 11/12 đều log `Sg - INT(dne:<stage-id>)`;
log cho stage 13 suy theo cùng pattern (CHƯA KIỂ xref trực tiếp). Luồng theo thứ tự code:
1. gọi vtable **vf146** (offset 584) của this (`CGameStage__vf146` 0x700F05);
2. `a1[4926] = 0`, rồi `CChatStage__vf44(a1)` (stage 13 kế thừa CChatStage);
3. `a1[155] = 1`; `sub_6FFC52`, `sub_71C46A(0)`, `sub_7056BD(a1)`;
4. build mảng 16 slot: `v25[i] = sub_8E9BF6(i)` (i = 0..15; getter đọc box `*(this+121)+124+580*i`) — dữ liệu người chơi
   đã lưu từ On_501 qua các setter `sub_8E977D` / `sub_8EA539` / `sub_8E8F21` (định dạng trong §4) — OnEnter KHÔNG cần
   gói bổ sung;
5. `v7 = (u16)sub_8E9977(dword_E60884)` = **map id đang chọn của phòng** (box `this+508`);
6. gọi vf147 (offset 588) = `CGameStage__vf147` 0x718AC8 với `(v7, v25)`: trả 0 → `sub_708FFE(a1, 1, 0)` (thoát về trước);
   trả ≠0 → nhóm lệnh dựng trận:
   `sub_6FFFDB`/`sub_6FFCC4`, `sub_701277`, `sub_7012A3`, `sub_70139A(v7)`, `*(this+4985)+12)`; nếu
   `sub_8E7E3F(dword_E60884)` và `a1[5417] != 0` → `sub_6E1F0C(120000)` (timeout vào trận 120 s);
   `a1[5342] = sub_6E204D(sub_6FFFDB)`, `sub_6FFC94` (nếu arg0==0), `sub_70478D`, `sub_6FFCE2`, `sub_7012AF`,
   `sub_6FFCED`, `sub_71A6E1`, `sub_7EF7DB(dword_E63FD0)`, `sub_7012BD`, `memset(a1+5378, 0x40)`,
   `sub_6E1F0C(120000)` (chế độ ngắm), duyệt `this[5413]` gọi vf15 (offset 60) từng phần tử, reset
   `a1[5400/5401/5536..5539]`, `sub_9682DE(this+5555×2)`, `sub_5ADE62()`.
- **OnEnter không gọi `sub_88849F`/`SendPkt__Begin`** (các nhánh chính) → trận không gửi gói nào lên server chỉ vì vào
  stage (CHƯA KIỂ: chỉ kiểm các nhánh chính, không đệ quy vào từng sub-call).

### vf147 (0x718AC8) — tạo/nạp trận
- `v4 = sub_736FE3(mapid)` = **tên file map theo id từ bảng cache** (bảng `this+4`, mảng std::string stride 0x38);
  `v17 = sub_8E7A7F(dword_E60884) != -1`; `v5 = sub_6FFFDB(this)` (game context);
- `Block = vf158(this, mapid, v17)` — vf158 (0x701316) → `sub_576D99(kind, this, v17)` = **factory theo kind**
  (`sub_8E78DB`) của chế độ chơi;
- nếu vf tại offset 12 của `v5` ≠0: `sub_6EBC30(Block)` (→ `sub_6EACE5` + `sub_6EB9A9` — nạp map/hiệu ứng; chính là hàm
  trong crash trace của Cập nhật 7), vf(v5+16), `sub_6EC237(v11, 1)`, `sub_6E3AFE(v5)`, `sub_70135D(this)`,
  vf offset 640 (=vf160), `sub_70D493(mapid, v17)`, `sub_715C3A(mapid, danh sách slot)`, `sub_70B578`, `sub_701368`,
  `sub_672E6A(1)`, phóng object cũ `this[5394]`, rồi `this[5394] = sub_6F987B(sub_414543(this+4781), sub_9B6F75(4))`
  (object trận mới; malloc 0xE2B8), `sub_704ED0(this)`.

### Map/theme nạp từ đâu
- **Tên map** tra từ bảng cache (`sub_736FE3`; `this = dword_E60A10` ở vf155) — bảng nạp bởi gói **231**
  (`CStage__On_231` 0x6E0C5A, cùng kiểu gói 13): `DecodeBlob` → parse `sub_6E077C` → ghi cache `fxdynmapinfo.ssd`
  (`sub_A62C20`; lỗi mở file → `CAppException` "Cannot open a file..." phải cẩn thận như gói 14).
- Blob của 231 (đọc qua subreader obf như gói 14): `u16 count` (`sub_A62F70`), rồi **check `sub_A62570 == this[3]`**
  (khác → `sub_6DB3ED` rồi thoát); mỗi bản ghi: `u32` (`sub_A62FB0`, dùng `sub_911168`), `u8`, `str` **tên file map**
  (nạp `"Map/%s"`), `str` (theme?), `u8`, `u8` (mã theme: 89 = "Theme/SweetCandy", 138 = "Theme/ThemeDefault", khác →
  `"Theme/%s"`%), `str`, `str`, `u8`, `u8`, `u32` màu (sub_A2A5E0(B2,B1,B0)), `u8` (style: `/10==1` → `%=10` + cờ),
  `u8`, `u8`, `u16`, `u8`, `u32`. Sau mỗi bản ghi `sub_6E03A8(&record)`; cuối `sub_6E048D`, `sub_6E06A0`.
- BGM: vf155 (0x70EEF3) chọn `"%s.mp3"` theo map id (`sub_6DDBAB` từ bảng).
- CHƯA KIỂ: ý nghĩa từng field của bản ghi 231; nhưng **phải gửi 231 (đúng tên map id) trước 501** để `sub_736FE3`
  trả tên không rỗng (rỗng thì `_mbsnbcmp` với tên gói 501 lệch → rơi nhánh aInvalidmapretu).

## 3. `CGameStage__OnPacket` (vf51, 0x71B631) — bảng opcode → handler ✅
Đọc opcode bằng `RecvPkt__Decode2` (u16). Phân rẽ 4 dải: op ≤ 214 → case = op−20 (1 switch); 215..396 (nhánh so sánh
riêng); 397..578 → case = op−397; op 214/517 bắt riêng. Kết thúc mỗi nhánh (kể default) là fallback:
nếu `this[5417]` ≠ 0 → `RecvPkt__Rewind` rồi gọi vf12 (offset 48) của object đó; tiếp theo Rewind + gọi vf16 (offset 64)
từng phần tử danh sách `this[5413]`; cuối cùng `CSessionStage__vf51` (chuyển tiếp, có `sub_8883BE(a2)`).

| opcode | handler | địa chỉ |
|---|---|---|
| 25 | `CGameStage__On_25` (str → token → cửa sổ/nhạc) | 0x7127B3 |
| 81 | `CGameStage__On_81` | 0x70C8C1 |
| 106 | `sub_7019AE` | 0x7019AE |
| 107 | `CGameStage__On_107` | 0x703D01 |
| 119 | vf148 (offset 592, thiscall với packet) | — |
| 128 | `sub_71458E` | 0x71458E |
| 135 | xử lý trong dispatcher (u8 → `sub_9B5934`, có thể `sub_6FFBD4(5)`) | — |
| 145 | `sub_701A48` | 0x701A48 |
| 146 | `sub_70DE4C` | 0x70DE4C |
| 147 | `CGameStage__On_147` | 0x701AB1 |
| 148 | `sub_704CD8` | 0x704CD8 |
| 149 | `sub_704D77` | 0x704D77 |
| 150 | `sub_6FFF78` | 0x6FFF78 |
| 151 | `CGameStage__On_151` | 0x70205B |
| 152 | `CGameStage__On_152` | 0x7064AC |
| 153 | `CGameStage__On_153` | 0x70679A |
| 155 | `CGameStage__On_155` | 0x701E8B |
| 157 | `CGameStage__On_157` | 0x7068DE |
| 158 | `CGameStage__On_158` | 0x715E90 |
| 159 | `sub_703F52` (không đọc packet) | 0x703F52 |
| 160 | `CGameStage__On_160` | 0x7164BB |
| 161 | `CGameStage__On_161` | 0x704962 |
| 163 | `CGameStage__On_163` | 0x716735 |
| 164 | `CGameStage__On_164` | 0x701765 |
| 165 | `sub_7018D7` | 0x7018D7 |
| 166 | `CGameStage__On_166` | 0x708EB0 |
| 168 | `sub_719D08` | 0x719D08 |
| 169 | `sub_7090AD` | 0x7090AD |
| 170 | `sub_70FF80` | 0x70FF80 |
| 171 | `sub_7069DF` | 0x7069DF |
| 173 | `sub_708FFE(0,0)` nếu `sub_8DB058()`, khác vf149 (offset 596) | 0x712E49 |
| 174 | `sub_70264F` | 0x70264F |
| 176 | `sub_706C42` | 0x706C42 |
| 177 | `sub_706D3C` | 0x706D3C |
| 178 | `sub_7150E7` | 0x7150E7 |
| 184 | `CGameStage__On_184` | 0x709101 |
| 189 | `sub_70E5C4` — **LỆNH ROUND (quan trọng nhất, xem §5a)** | 0x70E5C4 |
| 190 | `sub_70E7D6` | 0x70E7D6 |
| 191 | `sub_709A38` | 0x709A38 |
| 192 | `sub_7173A5` | 0x7173A5 |
| 193 | `sub_715210` | 0x715210 |
| 194 | `sub_706823` | 0x706823 |
| 195 | `CGameStage__On_195` | 0x701D15 |
| 196 | `sub_707101` | 0x707101 |
| 204 | `sub_7071AC` | 0x7071AC |
| 205 | `CGameStage__On_205` | 0x701B11 |
| 209 | `sub_70EE54` | 0x70EE54 |
| 214 | `sub_70DD0E` | 0x70DD0E |
| 215 | `sub_7129C4` | 0x7129C4 |
| 216 | `sub_70DDB4` | 0x70DDB4 |
| 267 | `sub_69BABE` | 0x69BABE |
| 298 | `sub_7035C4` | 0x7035C4 |
| 303 | `sub_70727E` | 0x70727E |
| 311 | `sub_719A3C` | 0x719A3C |
| 312 | `sub_70AF9C` | 0x70AF9C |
| 313 | `sub_707D14` | 0x707D14 |
| 314 | `sub_7101FA` | 0x7101FA |
| 315 | `sub_7158EC` | 0x7158EC |
| 324 | `sub_703E0C` | 0x703E0C |
| 339 | `sub_7100B2` | 0x7100B2 |
| 356 | `sub_7155DA` | 0x7155DA |
| 358 | `sub_707673` | 0x707673 |
| 359 | `sub_70777C` | 0x70777C |
| 366 | `sub_70058C` | 0x70058C |
| 394 | `CGameStage__On_394` | 0x712567 |
| 396 | `u8 → sub_9B5648` (dispatcher) | — |
| 397 | `sub_704EF2` | 0x704EF2 |
| 398 | `sub_70BA8F` | 0x70BA8F |
| 399 | `sub_70813F` | 0x70813F |
| 502 | `sub_70BA63` | 0x70BA63 |
| 503 | `sub_70F090` | 0x70F090 |
| 517 | `sub_717791` | 0x717791 |
| 518 | `sub_70F7A3`; nếu `this[5395] ≠0` và `sub_6FA585()==0` → `sub_6FC976(39, 371, this)` | — |
| 519 | `sub_70054E` | 0x70054E |
| 523 | `sub_717B87` | 0x717B87 |
| 526 | `sub_711B3A` | 0x711B3A |
| 529 | `CGameStage__On_529` (guard `this[5395]`), thất bại → `sub_6FC976(39, 371, this)` | 0x6FA585 |
| 531 | `sub_70A158` | 0x70A158 |
| 532 | `sub_70A04B` | 0x70A04B |
| 536 | `sub_70FC1B` | 0x70FC1B |
| 538 | `sub_703951` | 0x703951 |
| 539 | `sub_71798F` | 0x71798F |
| 540 | `sub_703921` | 0x703921 |
| 545 | `sub_717EFC` | 0x717EFC |
| 547 | `sub_707E78` | 0x707E78 |
| 548 | `sub_71824D` | 0x71824D |
| 552 | `sub_71580C` | 0x71580C |
| 553 | `DecodeBlob → sub_6A5A5E` | A62490 |
| 555 | `sub_703A20` | 0x703A20 |
| 568 | `sub_705016` | 0x705016 |
| 569 | `sub_7038CD` | 0x7038CD |
| 570 | `sub_70C70D` | 0x70C70D |
| 571 | `sub_71ADEC` | 0x71ADEC |
| 572 | `sub_709D5E` | 0x709D5E |
| 578 | `CGameStage__On_578` | 0x70065D |


## 4. Gói opcode 501 (S→C "bắt đầu trận", handler 0x6C4978) — đọc từ decompile; CHƯA KIỂ runtime
```
opcode 501 (S→C):
  u8 ok                       // Decode1; ==0 → hộp thoại aCannotlaunchas, KHÔNG đổi stage

  // ---- phần 1: người chơi, lặp this[4770] (số người đã lưu từ opcode 103) ----
  u8 c                        // c != 0: chỉ DecodeBuf 3 → sub_8E977D(slot, buf)
                              // c == 0: entry đầy đủ:
                              //   u32 player_id        (sub_679434 + blob)
                              //   blob                 (thông tin người, như 103)
                              //   DecodeBuf 3          (bitfield sẵn sàng/nhân vật/đội; chia cho sub_691BEE)
                              //   u8                   (sub_8E8F21)
                              //   sub_572A05 + CGameStage-vf149 offset 592 (this)
  // ---- phần 2: cấu hình trận (guard sub_8DAB40/8DAD87/8DAD95 đều 0) ----
  u32 seed                    → sub_8E77E4(seed)   ; sub_65412D(3, seed)
  u16 map_id                  → sub_736FE3(map_id) ; sub_8EAB95(map_id)
  str map_name                // u16 độ dài + byte; so _mbsnbcmp với tên map_id: khác → aInvalidmapretu
  u32 type                    // sub_6DE36E(type) != 0 bắt buộc; sub_6DD49B(type) != 0 → cờ (sub_8E7E46)
  u8 p0                       → sub_8E78CB(p0)
  u8 ready_bits               → sub_8E7636(ready_bits) (CHƯA KIỂ)
  u8 pcount                   → sub_8E9027(pcount) (số người phần 3)
  // ---- phần 3: pcount × { u8 slot, u8 x, u8 y, u32, u32, u32 } ----
  u8 slot → sub_8E8EFF(slot, 0)
  u8 x → sub_8E76A3(slot, x)
  u8 y → sub_8E8EBB(slot, y)
  u32 → sub_67900E (dùng làm ô/x?; CHƯA KIỂ)
  u32 → sub_67901A (CHƯA KIỂ)
  u32 → sub_9B69F7(0 nếu là người thứ 0, 1 nếu thứ 1, giá trị) (CHƯA KIỂ)
  // ---- phần 4: lặp 16 slot (0..15) ----
  mỗi slot có người: u8 != 0 → sub_985703(a2)  (sub-packet, CHƯA KIỂ)
  // ---- hợp lệ ----
  sub_6734D5(0x15, 1, 0); sub_8F391D(13)       // đổi stage 13
```
Nhánh lệch bản đồ: hộp thoại `aInvalidmapretu` rồi `sub_8F391D(this[15141])` (quay về phòng chờ) + `sub_8F2F14`.
CHƯA KIỂ: ý nghĩa các u32 loại c/d/e của phần 3 và sub-packet của phần 4.

## 5. Các gói chạy trận (đọc từ decompile; field theo thứ tự Decode/Encode chính xác, ý nghĩa CHƯA KIỂ)

### 5a. Opcode 189 (S→C) — LỆNH LƯỢT (`sub_70E5C4` 0x70E5C4) ✅ cấu trúc
```
opcode 189 (S→C):
  u8 mode (Decode1)
  u32 -> this[4887]      (Decode4; CHƯA KIỂ — có vẻ giới hạn thời gian lượt)
  u16 map_id             (Decode2; được phép dùng cho sub_8EAB95, vf147 — giống map id trong 501)
  mode 1: u8×16 → sub_70E357(...): set map id, gọi vf147 (tạo lại round) rồi C→S gửi 139 {bool 1}
  mode 2: u16 (Decode2) + u8 (Decode1) + u32 (Decode4)
          → sub_70DF00(...): nhánh "thiếu 12 bomber" hoặc nhánh đầy đủ (so this[5410]-this[5409] >> 2), sau đó C→S 140
  mode 4: u16 (Decode2) + u8 (Decode1) + u8 (Decode1) → sub_70DFF9(...): đầy đủ 12 bomber có RTTI CGOBomber
          + dùng malloc 0xA18, gửi C→S 140 sau khi sync xong
  mode 0: (không field; nếu this[5402]==2 → sub_70E511)
```
Lưu ý: u32 đọc **trước** u16 (thứ tự trên).
CHƯA KIỂ: mode chính xác tại(decoded role map 2/4), giá trị các u32 để SUMMARY nước.

### 5b. C→S các gói client tự gửi khi chơi
| op | hàm gửi (địa chỉ) | nội dung Encode (thứ tự Encode chính xác) |
|---|---|---|
| 139 | `sub_70E357` 0x70E357 (do On_189 mode 1 dẫn) | `bool 1` |
| 140 | `sub_70DF00` 0x70DF00 / `sub_70DFF9` 0x70DFF9 / `sub_71AD24` 0x71AD24 | `bool 1` |
| 141 | `sub_70E9FC` 0x70E9FC / `sub_70EADB` 0x70EADB — client **tự gửi trong vòng tick** `sub_71B521` (khi hết hạn stamp this[19676] / step theo seed sub_654153(3) % 12 == 0) | `u2 uid` (sub_6E2000), `u2 map_id` (sub_8E9977), `u8 n` (số ô bước, clamp 0..3), n × {`u8`, `u8`} — 2 byte mỗi ô, đọc từ queue di chuyển (sub_6EE7A1 / sub_6ED146) |
| 142 | `sub_71B275` 0x71B275 (vòng tick khi this[21956] != 0, cách nhau ≥ 2000 tick) != 0, thời gian cách nhau ≥ 2000) | `u2 uid`, `u2 map_id`, `u8 nblocks` (clamped 0..10), mỗi block: `u8 ncell`, ncell × {`u8`, `u8`} |
| 143 | `sub_71751A` 0x71751A — *đây là gói đặt bom*, caller: `CMapActionBomb__vf4` 0x752B44 (nút/nhấn bom) + `sub_76D342` | `u2 uid`, `u8 count` (= số cell), `u2 x?`, `u2 y?`, `u8 dir?`, `u32`, `u2` , rồi count × {`u8`, `u8`} |
|—| còn lại: các gói phụ: `sub_702FCA` (209), `sub_702DE4` (115), `sub_70307F` (158), `sub_70326A/70330E/7033A3/7034FF` (126), `sub_703825` (175), `sub_706FC0` (135), `sub_70732A` (99), `sub_707F0F` (192), `sub_7083EC` (211), `sub_70A3EC` (132), `sub_70B0B3` (196), `sub_70D9BE` (207), `sub_70DFF9` Ngoài nói trên (140), `sub_70E7D6` (CHƯA KIỂ opcode), `sub_70EBE4` (179), `sub_70E9FC` tự nói trên (141), `sub_70F090` (174), `sub_7100B2` (197), `sub_716B75` (136), `sub_71751A` bản thân (143), `sub_7190C6` (184), `sub_719A3C` (203), `sub_71B275` nói trên (142), `sub_6F4365` (148), `sub_6FB1FE`/`sub_6FA7AB` (183), `sub_703A3?` (unclear) | (1×) thông tin phụ (CHƯA KIỂ) |

### 5c. Opcode S→C đáng chú ý của CGameStage (ngoài bảng §3; cấu trúc đọc từ decompile, ý nghĩa CHƯA KIỂ)
- **On_106** `sub_7019AE` 0x7019AE: `u8 slot, DecodeBuf 3` → `sub_8E977D(slot, buf)` — cập nhật trạng thái ô/người
  (gọn hơn opcode 103: chỉ 3 byte trạng thái, giống buf3 trong 501).
- **On_147** `CGameStage__On_147` 0x701AB1: `u8 slot` — tra bomber của slot (`sub_6E5C2B`), nếu hợp lệ → lệnh vô hiệu
  `sub_7264DE(1, -1)`; CHƯA KIỂ ngữ nghĩa.
- **On_148/149** `sub_704CD8`/`sub_704D77`: `u8 slot, bool` → `sub_8E99A3(slot)` + object+1528 gọi vf 36/52
  (bật/tắt chức năng trên người chơi; 148 bật, 149 tắt).
- **On_150** `sub_6FFF78` 0x6FFF78: `u8 slot` → `this[slot + 4895] = 1` (đánh dấu slot).
- **On_145** `sub_701A48`: `u8 slot, u16 which(1..25), u32, u32` → `sub_6EB940(slot, which, …)` (thay đổi object trên
  bản đồ, tới 25 kiểu).
- **On_146** `sub_70DE4C`: đầu tiên `sub_70A647(this, pkt)` (CHƯA KIỂ format), sau đó reset "sẵn sàng" của người chơi;
  nếu `sub_9B6F75(4)` → `this[5400] = 1`. Có vẻ chuẩn bị lượt tiếp.
- **On_155** `CGameStage__On_155` 0x701E8B: `u8` (so id của mình `sub_6E2000`), `u8` (nibble cao = kiểu hành động
  >4, nibble thấp = slot), `u16 idx`, `u8`, `u8`, `u8`, `u8` — hiệu ứng/âm thanh (`sub_6734D5` 0x4C/0x9D/0x9F),
  đổi trạng thái theo hành động (`sub_591045/50`).
- **On_157** `CGameStage__On_157` 0x7068DE: `u8 id, u16, u8, u8, u8, u8, u8` → `sub_730EF4`; nếu thất bại →
  `sub_70307F(id, 2, -1)`. CHƯA KIỂ (hiệu ứng/trạng thái ô?).
- **On_158** `CGameStage__On_158` 0x715E90: `u8, u8 id, u8, u8, u8, u16 type (97/99/100/103...), u16 itemId, bool` —
  vật phẩm/experience lớn (currency/item), nhiều nhánh riêng theo type; CHƯA KIỂ chi tiết.
- **On_164** `CGameStage__On_164` 0x701765: `u16 slot, u32`, sau đó hiệu ứng picking + cộng giá trị (gọi `sub_581ED1`
  với 212) — tiền/điểm thưởng; CHƯA KIỂ.
- **On_151** 0x70205B (chung với `CSquareStage__On_477`): `u8 n`, n × {`u16 id`, `u8`, nếu cần `u32`} → `sub_6E9994`
  (thông báo theo id).
- **On_152** 0x7064AC (chung với `On_478`): đầy đủ fields giống 478 → `sub_6E9AF9` (thông báo lớn; id 19 riêng).
- **On_153** 0x70679A: `u8 (≤4), u16 slot, u32, u8` — hiệu ứng đổi (CHƯA KIỂ).
- **On_107** 0x703D01: `u16 a(≤0xF), u8 flag, u16 c(≤0xF), u16` → `sub_8E8C5C/8E8CB1` (flag on/off thuộc tính người
  chơi).
- **On_128** `sub_71458E` 0x71458E: `u8 subtype {1..25}` rồi field theo subtype (thường `u16 id` + số lượng
  u16/u32/u64/u8/str) — cộng/trừ tài nguyên trong trận; sub-icon + string "ZombieSurvivel..." hàm nhiệm vụ nření
 _subtype 20. CHƯA KIỂ từng subtype.
- **On_25** 0x7127B3: `str` → phân token `sub_70ECEF` → mở cửa sổ/thêm người khác (CHƯA KIỂ).
- **On_81** 0x70C8C1: `u32 slot/uid, str` — hiển thị text trên người chơi.

### 5d. Minimum server để trận chạy (cấu trúc đã đọc từ IDA, chưa kiểm runtime)
1. Gửi **231** trước (cấu trúc nhánh "blob có tag" như gói 14, xem §2b) để bảng map của trận được nạp đủ.
2. Khi bấm BẮT ĐẦU (hoặc tự quyết): gửi **501** đúng §4 — `map_name` phải == tên theo `map_id` trong bảng **231**,
   ngược lại: hộp thoại "Invalid map..." và quay về phòng chờ.
3. Client vào stage 13, load map (đặt theme từ **231**), KHÔNG thêm gói gửi lúc vào stage.
4. Bắt đầu lượt: gửi **189** (mode 2/4 như §5a) — client trả C→S **139**/`140`.
5. Đồng bộ di chuyển: client tự gửi **141** (và 142); SERVER PHẢI phát lại cho người chơi khác — *chưa tìm handler
   nhận được tương ứng trong CGameStage__OnPacket* (CHƯA KIỂ — cần tiếp tục tra).
6. Đặt bom: client gửi **143** (`CMapActionBomb__vf4`); server phải phát hiệu ứng (chuyên 158/145/…) — CHƯA KIỂ.
7. Kết thúc ván: chưa chốt (On_146/128/204?) — CHƯA KIỂ.

### TODO phân tích tiếp
- (a) tìm handler S→C tương ứng C→S 141/142 (broadPath của người khác);
- (b) gói kết thúc ván: On_146, On_128 subtype, On_204;
- (c) gọi lược bắt đầu: bắt server nhận 139/140 (modewire), mode2/mode4 luồng đầy đủ;
- (d) chính từng field của phần 3 (c/d/e) của *501* vẫn CHƯA KIỂ.

### 5e. Bổ sung opcode "sự kiện trong trận" (đọc từ decompile)
- **On_163** 0xC716735: bắt đầu bằng 4 field chung, sau đó switch theo subtype:
  `u8 sub, u8 target, u16 idx, u16 arg`; theo `sub` 0..27: 0/3/13/14 → `sub_706BCB`/`sub_706B26`/`sub_71652D`/
  `sub_716692` (mỗi cái đọc thêm blob); 1/8/12 → `sub_70B8C4(...,1/0)`; 2 → `sub_7022EE` (u8,u8,u8 nibble);
  4 → `sub_70213E` (u32); 6 → `sub_702552` (4×u32); 7/9/10/15/16/19 → phía nhận riêng各有; 21/22/23.. đọc 1× u8/u32/u16.
  Đây là **bộ event/hiệu ứng trong trận**. CHƯA KIỂ chi tiết từng subtype.
- **On_298** `sub_7035C4`: `u8 type(9/12), u16, u16` — type 9: sinh quái/wave (`u8 dir, u8, u8, u8, u8, u32`, sau đó
  đặt cell theo hàng, `sub_729794`, `sub_5C0138`); type 12: `u16 col, u16 row` + text báo lỗi `CreateBoxMon.destroybox
  colrow(%d,%d) failed`. CHƯA KIỂ ngữ nghĩa đầy đủ (nhưng mode đặc biệt/Zombie).
- **On_303** `sub_70727E`: `u8, u16, u16, u16` → `sub_728F9E(-1,-1,..., 93 hoặc 62, 10, ...)` (spawn box mon/npc).
- **On_160** 0x7164BB: phần đầu giống field `On_158` rồi gọi `sub_6F2964(u8, u16)` và tiếp tục trực tiếp **On_158(pkt, 1)**
  — biến thể OCSP item của 158.
- **On_161** 0x704962: `u8 id, u8 target, u8, u8, u8` → `sub_6F007D` rồi kiểm nếu là mình: gửi hiệu ứng `sub_89B623`;
  thất bại → `sub_70307F(target, 4, -1)`.
- **On_215** `sub_7129C4`: `u16 id, u8` → hộp thoại "Banned..." + `sub_708FFE(30/31, 0)` (bị đuổi khỏi trận).
- **On_216** `sub_70DDB4`: hộp thoại `aHordeeventMove` + ra khỏi trận `sub_708FFE(0, 0)` (CHƯA KIỂ).
