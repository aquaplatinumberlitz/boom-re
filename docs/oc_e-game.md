# e-game: Stage TRẬN ĐẤU (stage 13) — phân tích tĩnh (IDA `~/boom-re-oc/ida/e-game.i64`, copy riêng)

Tiền đề (docs/lobby.md Cập nhật 10): phòng chờ = stage 12 `CPrepareStage`; bấm BẮT ĐẦU → `CPrepareStage__vf5` →
`sub_6CB7B6` (0xBBA = chọn bản đồ, 0xBBB) → `sub_6C95AD` → `sub_6C63B6`. Quy ước handler `On_N = opcode N`;
`CStage__OnPacket` case = opcode−2; đọc `RecvPkt__Decode1/2/4/8/Str/Blob`, gửi `sub_88849F(op)` / `SendPkt__Begin+Encode*`.

## 1. Nhận diện stage trận

### `sub_6C95AD` (0x6C95AD) → `sub_6C63B6` (0x6C63B6)
- `sub_6C95AD`: guard `sub_8DAB40(); sub_8DADCA(); sub_8DADE6(); sub_8DAD87(); sub_8DAD95()` — nếu bất kỳ cần đường riêng
  (`sub_8DAB40` ≠0 → `sub_6C2888`; 3 cái giữa ≠0 → `sub_6C2B69`), tất cả 0 mới rơi vào `sub_6C63B6` (đường trận thường).
- `sub_6C63B6`: lấy kiểu phòng qua `v18 = sub_8E75EA(dword_E60884)` (room type?) và `v19 = sub_8E78DB(dword_E60884)`
  (battle kind?); `sub_975083(v19) != 0` → đường thường `sub_6C5EC8(v20, Str(tên), v23, &v18, &v19)` (chỉ dựng cấu hình
  cấu hình UI, không thấy gửi opcode); v19 ∈ {15, 17} → đường `CSimpleModifyRoomInfoDlg__vf44` + `sub_6C5D8C`. Bấm BẮT ĐẦU
  chỉ đổi UI; **không thấy gửi gói xin bắt đầu** — server phải tự quyết (gửi 501) — CHƯA KIỂ (cần xem `sub_6CB7B6` 0xBBB).

### On_501 → stage 13 ✅ (đọc từ IDA)
`CPrepareStage__On_501` (0x6C4978): nhánh bản đồ hợp lệ → **`sub_8F391D(a1: 13)`**; nhánh bản đồ lệch tên (`aInvalidmapretu`,
hộp thoại "Invalid map...") → `sub_8F391D(this[15141])` + `sub_8F2F14` (quay về phòng chờ).
⇒ **Trận thường = stage 13**. Lớp: tìm theo vt — sẽ bổ sung ở §3 (`CGameStage`).

## 2. OnEnter — `CGameStage__vf44` (0x71B519) → `sub_71A9EC` (0x71A9EC) ✅ đọc từ IDA
Call-log: chuỗi `"[XRpt] Sg - INT(dne:%d)...\n"` (0xC7B204, `sub_6734D5(? ,1,0)` in CALog) — vf44 của stage trận log
`Sg - INT(dne:13)` tương tự stage 11/12. Luồng (thứ tự code):
1. gọi vtable **vf146** (offset 584 = 146) của this (`CGameStage__vf146` 0x700F05);
2. `a1[4926] = 0`; rồi `CChatStage__vf44(a1)` (stage 13 kế thừa CChatStage — OnPacket cuối sẽ chuyển tiếp
   `CSessionStage__vf51`, hơi kể CChatStage như CPrepareStage);
3. `a1[155] = 1`; `sub_6FFC52`, `sub_71C46A(0)`, `sub_7056BD(a1)`;
4. build mảng 16 slot: `v25[i] = sub_8E9BF6(i)` với i=0..15 (dữ liệu người chơi đã lưu từ On_501 qua các setter
   `sub_8E977D`/`sub_8EA539`/`sub_8E8F21` — xem §4) — KHÔNG yêu cầu gói thêm lúc OnEnter;
5. `v7 = (u16)sub_8E9977(dword_E60884)` = **map id hiện chọn của phòng** (đọc từ room info);
6. gọi vf147 (`(*this+147)(this, v7, v25)`, CGameStage__vf147 0x718AC8): trả 0 → `sub_708FFE(a1,1,0)` (thoát trận, về
   trước) — vì thế gồm tạo đối tượng trận + nạp map. Trả ≠0 → tiếp:
   `sub_6FFFDB`, `sub_6FFCC4`, `sub_701277`, `sub_7012A3`, `sub_70139A(v7)`, `vf149+12`(this+4985, 0),
   nếu `sub_8E7E3F(dword_E60884)` → `sub_6E1F0C(timeouts 120000)` khi `a1[5417] != 0` (n bounding?),
   `a1[5342] = sub_6E204D(sub_6FFFDB(a1))`; `sub_6FFC94(a1)` nếu a4==0; `sub_70478D`; `sub_6FFCE2`; `sub_7012AF`;
   `sub_6FFCED`; `sub_71A6E1`; `sub_7EF7DB(dword_E63FD0)`; `sub_7012BD`; `memset(a1+5378..+0x40)`;
   `sub_6E1F0C(120000)` khi co chế độ watch; duyệt danh sách this[5413] gọi vf15 (offset 60) từng phần tử;
   reset `a1[5400/5401/5536..5539]`, `sub_9682DE(this+5555[0..1])`, `sub_5ADE62()`.
- **OnEnter KHÔNG thấy gọi sub_88849F/SendPkt__Begin** trong 0x71A9EC → trận thường không gửi gói lên server lúc vào
  (CHƯA KIỂ: chỉ các vị trí sub-call không gửi). Map/theme nạp trong vf147 (0x718AC8) — xem dưới.

vf147 (0x718AC8): `v4 = sub_736FE3(mapid)` = **tên file map theo id từ bảng cache** (bảng `this+4`, stride 56 = mảng
std::string; cùng bảng đã nạp bởi gói 231 — xem §5), dựng `std::string(v4)`; `v17 = sub_8E7A7F(dword_E60884) != -1`;
`v5 = sub_6FFFDB(this)` = đối tượng "game context"; `Block = vf158(this, mapid, v17)` (0x701316 → `sub_576D99(kind, this, v17)`
= **factory theo loại chơi** `"sub_8E78DB"` — tạo 1 object CGamePlayMap v.v.); *(chỉ khi vf tại offset 12 của v5 ≠0)*:
`sub_6EBC30(Block)` (→ `sub_6EACE5` + `sub_6EB9A9` — nạp map/hiệu ứng; chính là hàm trong crash trace của Cập nhật 7),
`vf`(v5+16), `sub_6EC237(v11,1)`, `sub_6E3AFE(v5)`, `sub_70135D(this)`, `vf offset640` (=vf160), `sub_70D493(mapid, v17)`,
`sub_715C3A(mapid, Block-player-list)`, `sub_70B578`, `sub_701368`, `sub_672E6A(1)`, đổi `this[5394]` (flag đối tượng trận
đang hoạt động), `this[5394] = sub_6F987B(sub_414543(this+4781), sub_9B6F75(4))` (object trận; malloc **0xE2B8**).

## 3. `CGameStage__OnPacket` (vf51, 0x71B631) — bảng opcode → handler
Đọc opcode bằng `RecvPkt__Decode2` (u16). Range phân rẽ: ≤214 → case = op−20 (một lệnh switch); 215..396 (các nhánh so
gián tiếp); 397..578 (case = op−397); >518 → case = op−518; op 214/517 đặc biệt; default & các nhánh trượt đề không khớp
→ `LABEL_138` fallback: nếu `this[5417]` ≠0 → Rewind + gọi vf12 (offset 48) của object đó; tiếp Rewind + vf16 (offset 64)
từng phần tử danh sách `this[5413]`; cuối cùng `CSessionStage__vf51` (chuyển tiếp), có gọi `sub_8883BE(a2)` (phục hồi?).

Chuyển tiếp → handler (`= function đế received at, alias trong IDA`):

| opcode | handler | địa chỉ |
|---|---|---|
| 25 | `CGameStage__On_25` | 0x7127B3 |
| 81 | `CGameStage__On_81` | 0x70C8C1 |
| 106 | `sub_7019AE` | 0x7019AE |
| 107 | `CGameStage__On_107` | 0x703D01 |
| 119 | vf148 (offset 592) | — |
| 128 | `sub_71458E` | 0x71458E |
| 135 | `sub_9B5934` trực tiếp (u8) | dispatcher nội bộ |
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
| 173 | `sub_708FFE(0,0)` nếu `sub_8DB058()` ≠0, khác vf149 (offset 596) | 0x712E49 |
| 174 | `sub_70264F` | 0x70264F |
| 176 | `sub_706C42` | 0x706C42 |
| 177 | `sub_706D3C` | 0x706D3C |
| 178 | `sub_7150E7` | 0x7150E7 |
| 184 | `CGameStage__On_184` | 0x709101 |
| 189 | `sub_70E5C4` — **LỆNH ROUND (quan trọng nhất)** | 0x70E5C4 |
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
| 396 | u8 → `sub_9B5648` | dispatcher |
| 397 | `sub_704EF2` | 0x704EF2 |
| 398 | `sub_70BA8F` | 0x70BA8F |
| 399 | `sub_70813F` | 0x70813F |
| 502 | `sub_70BA63` | 0x70BA63 |
| 503 | `sub_70F090` | 0x70F090 |
| 517 | `sub_717791` | 0x717791 |
| 518 | `sub_70F7A3` / nếu `this[5395]≠0 && sub_6FA585()==0` | — |
| 519 | `sub_70054E` | 0x70054E |
| 523 | `sub_717B87` | 0x717B87 |
| 526 | `sub_711B3A` | 0x711B3A |
| 529 | `CGameStage__On_529` 0x6FA585 (guard `this[5395]`) | 0x6FA585 |
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
| 553 | blob → `sub_6A5A5E` | A62490 |
| 555 | `sub_703A20` | 0x703A20 |
| 568 | `sub_705016` | 0x705016 |
| 569 | `sub_7038CD` | 0x7038CD |
| 570 | `sub_70C70D` | 0x70C70D |
| 571 | `sub_71ADEC` | 0x71ADEC |
| 572 | `sub_709D5E` | 0x709D5E |
| 578 | `CGameStage__On_578` | 0x70065D |

## 4. Gói opcode 501 (S→C "begin battle", handler 0x6C4978) — đọc từ decompile, CHƯA KIỂ runtime
Điều kiện mở lớn trước (guard `sub_8DAB40()/8DAD87()/8DAD95()`): chỉ nhánh "sảnh thường" đọc đầy đủ — CHƯA KIỂ.

```text
opcode 501 (S→C):
  u8 ok                       // Decode1; ==0 → hộp thoại aCannotlaunchas, DỪNG (không đổi stage)
  // ---- phần người chơi (như opcode 103), lặp v2[4770] (đã lưu từ opcode 103ulus) lần ----
  u8 c                              // c≠0: chỉ DecodeBuf 3 → sub_8E977D(idx, buf)  (update trạng thái ô)
                                    // c==0: entry đầy đủ: u32 id, blob(thông tin như 103), DecodeBuf 3,
                                    //       u8 (sub_8E8F21), sub_572A05 + vf149(this+592)
  // ---- phần trận ----
  u32 seed                    → sub_8E77E4            // seed random của trận
  u16 map_id                  → sub_8EAB95            // so với tên map bên trong csdl (sub_736FE3)
  str map_name                (u16 độ dài + byte)     // phải trùng _mbsnbcmp tên map_id; khác → aInvalidmapretu
  u32 type                    → sub_6DE36E (≠0 bắt buộc), sub_6DD49B (cờ phụ)
  u8 p0                       → sub_8E78CB
  u8 pcount                   → sub_8E9027 (số người trong phần dưới)
  pcount × { u8 slot, u8 a, u8 b, u32 c, u32 d, u32 e }   // slot → sub_8E8EFF(slot,0);
        // khi sub_8E99A3(slot) tìm thấy người: c≥0 → sub_67900E(c) (CHƯA KIỂ), d → sub_67901A (CHƯA KIỂ),
        // e → sub_9B69F7(0/1, e) cho người thứ 0/1 (lưu trù năng vị trí của 2 người chơi đầu)
  // ---- vòng 16 slot ----
  while slot < 16: if ô đó <khác null> và Decode1(u8) != 0 → sub_985703(a2)   // đọc phụ (CHƯA KIỂ)
  // ---- thoát hợp lệ ----
  sub_6734D5(0x15, 1, 0);  sub_8F391D(13)      // ĐỔI stage 13
```

### §2b Map/theme nạp ở vf44/vf147 — tóm lại
- **Tên map** đọc từ bảng cache (sub_736FE3(u16 id) — `cache+4`, từng bản ghi std::string stride 56; `this = dword_E60A10`
  ở BGM-pick vf155) — bảng được \(nạp từ gói **231** (`CStage__On_231` 0x6E0C5A, cùng "bộ dạng" gói 13): `blob` được
  ghi cache `fxdynmapinfo.ssd` (sub_A62C20), phân tách `sub_6E077C(this, reader)`.
- blob của 231 (đọc qua subreader obf): `u16 count` (`sub_A62F70`), rồi **check `sub_A62570 == this[3]`** (khác →
  `sub_6DB3ED` rồi thoaktion); mỗi bản ghi: `u32` (→ sub_A62FB0 `sub_911168`), `u8`, `str` **file map** (nạp `"Map/%s"`),
  `str` (theme?), `u8`, `u8` (mã theme: 89 = `"Theme/SweetCandy"`, 138 = `"Theme/ThemeDefault"`, khác → `"Theme/%s"`),
  `str`, `str`, `u8`, `u8`, `u32` màu (sub_A2A5E0(B2,B1,B0)), `u8` (`/10==1` → `%=10` + cờ phụ), `u8`, `u8`, `u16`, `u8`,
  `u32`. Sau mỗi bản ghi gọi `sub_6E03A8, sub_6E048D`.
- BGM: vf155 (0x70EEF3) tra tên nhạc từ bảng/gói theo map id (`sub_6DDBAB`), các sự kiện đều là hiệu ứng resource.
CHƯA KIỂ: format fieldValue của bản ghi 231 theo Nghena cứng - nhưng **phải gửi 231 trước 501** để có tên map (vf147
truy bảng; nếu thiếu khả năng sẽ lệch/dừng trong sub_736FE3 với bác bảng rỗng → vanney boots VNA hết).
