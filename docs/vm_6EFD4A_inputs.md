# Đầu vào để viết lại khối VM 0x6EFD4A (`sub_6EFD24`) — chỉ phần native quanh khối

Soạn 2026-10-18 (Claude Opus 5.5) cho chủ dự án. **Không có phân tích bên trong khối VM**: chỉ gồm khung hàm, cổng
native, hàm gọi, tham số (tĩnh + giá trị runtime), object `this`, các hàm "song sinh" native cùng lớp và phía flush gói.
Phần "suy luận" được đánh dấu rõ — cần kiểm lại khi viết lại.

Nguồn: IDA `unpacked_ca.exe.i64`; runtime gdb bằng `tools/match_gdb.sh tools/gdb/msgcache_6efd24.gdb <outdir>`
(fakeserver `TURN_MODE=1 PLAY_START=4`, bấm Space ở ô spawn).

---

## 1. Khung hàm `sub_6EFD24` (0x6EFD24 – 0x6EFEE3)

| Mục | Giá trị |
|---|---|
| Quy ước gọi | `__thiscall`, **12 tham số stack** (`retn 30h`), trả về `eax` |
| Prolog | `push ebp; mov ebp,esp; sub esp,24h; push ebx; push esi; push edi; mov [ebp-24h],ecx` (lưu `this`) |
| Cổng native | `push [ebp+arg_4]` → `call sub_41C791` (trả `dword_E60884` = room ctx) → `mov ecx,eax` → `call sub_8EAC0E` → `test eax,eax` |
| Cổng ≠ 0 | `xor eax,eax` → `jmp 0x6EFEDC` (trả **0**, không vào VM) |
| Cổng = 0 | `0x6EFD4A: jmp 0x133B0DB` (vào VM) |
| Vùng bị đè | 0x6EFD4F – 0x6EFEDB: byte rác (Themida), không còn code gốc — **không** có đuôi native nào để đối chiếu |
| Điểm nối tiếp | **0x6EFEDC**: `pop edi; pop esi; pop ebx; leave; retn 30h` (epilog của chính hàm; `vmtriage.md` §2) |
| Kích thước khối gốc | 0x18F byte (devirt.md) — lớn hơn nhiều so với setter song sinh `sub_6F0227` (0x64 byte cả hàm) |

Hệ quả cho bản viết lại: code thay thế đặt ở 0x6EFD4A phải giữ nguyên frame (ebp, 3 thanh ghi đã push, `this` ở
`[ebp-24h]`, tham số ở `[ebp+8]…[ebp+34h]`), đặt `eax` = giá trị trả về rồi nhảy tới 0x6EFEDC.

## 2. Cổng `sub_8EAC0E(roomctx, slot)` (native, đủ)

```
if (sub_8E9A84(slot) != 0) return 0;          // box ở roomctx[121] + 580*slot + 36 (slot hợp lệ < roomctx[120])
if (sub_8E9D4B(slot) != 0) return sub_8E9D77(slot);   // box roomctx[123] + 36*slot + 12, rồi +24
return 1;
```
`sub_6EFD24` chỉ vào VM khi kết quả = 0. Mọi method khác của `CGameMsgCache` dùng **đúng cổng này** với cùng tham số
`slot` (= `arg_4`). Runtime khi đặt bom ở slot 0: cổng = **0** → vào VM.

## 3. `this` = `CGameMsgCache` (singleton)

- `this` ở mọi caller trong trận = `sub_6FFF99(stage)` = **`CGameStage + 0x4AC0`**; ctor `sub_6F4FD1` (gọi trong ctor
  stage `sub_70CBAF` 0x70CC73) và cũng là `dword_E608D0` (caller `sub_4A4E70` dùng thẳng global). vt `vt_CGameMsgCache`
  0xC546AC (runtime: `ecx=…, vt=c546ac` ✓).
- Bố cục (dword index): `this[3]` = số slot (runtime **0x10**); 16 `std::vector` (begin/end/cap) ở `this[5], [9], …,
  [65]`; `this[69..72]` mốc thời gian flush; `this[73]` = SendPkt buffer dùng cho các gói "nhóm" (opcode 111/112/145).
- Method flush: `vf4` (mỗi ≥ 200 ms: bảng 5 → vf7, bảng 9 → `sub_6F058C`, bảng 57 → `sub_6F0650`), `vf5` (theo slot:
  bảng 21/25/33/**41**/29/45/…), `vf8` (bảng vòng 13/17 → opcode 111).

### Ma trận bảng ↔ setter/flush (quét toàn bộ method 0x6EF5E8–0x6F5800)

| Bảng (`this[n]`) | Bản ghi | Setter native | Flush native |
|---|---|---|---|
| 5 | 44 B | `sub_6EFC81` (11 tham số) | `vf7` |
| 9 | 28 B | `sub_6F1879` | `sub_6F058C` |
| 13 / 17 | 68 B vòng | `sub_6EFEE3` (16 tham số) | `vf8` → **op 111** |
| 21 | 40 B | `sub_6F001E`, `sub_6F2ECE` | `vf9` (`*a1+36`, qua vf5) |
| 25 | 20 B | `sub_6EFFA1`, `sub_6F007D` | `sub_6F0956` |
| 29 | | `sub_6F02D4`, `sub_6F0320` | `sub_6F09F0` |
| 33 | 32 B | `sub_6F00E4` | `sub_6F0A85` |
| **41** | **36 B** | **— không có setter native nào** | **`sub_6F0B2A` → op 112** |
| 45 | 36 B | `sub_6F0227` (9 tham số) | `sub_6F0BE7` → op 145 |
| 49 | | `sub_6F01DB` | `sub_6F0361` |
| 53 | | `vf6`, `sub_6F4365`, `sub_6F4B01` (chưa phân loại setter/flush) | ? |
| 57 | 20 B | `sub_6F028B` | `sub_6F0650` |

**Suy luận (chưa kiểm):** bảng 41 là bảng duy nhất có flush mà không có setter native → `sub_6EFD24` (bị ảo hoá,
caller toàn đường đặt bom) rất có thể là setter của bảng 41, tức "đặt bom" được gửi lên server bằng **C→S 112**.
Cách kiểm sau khi viết lại: bp `0x6F0B2A` (FLUSH112) phải bắn và fakeserver phải log `C->S opcode 112`.

## 4. Hàm song sinh native (mẫu khuôn)

Cả ba cùng mẫu: cổng `sub_8EAC0E(slot = a3)` → con trỏ bản ghi `this[n] + size*slot` → ghi field → bật cờ `[+4] = 1`
(→ flush sau), có khi flush ngay.

- **`sub_6F0227`** (bảng 45, 36 B — **cùng kích thước và cùng bộ mã hoá flush với bảng 41**): chỉ ghi khi `rec[1]==0`;
  `rec[0]=a2, rec[2]=a4, rec[3]=a5, rec[4]=a6, rec[5]=a7, rec[6]=a8, rec[7]=a9, rec[1]=1, rec[8]=a10`; trả a10.
- **`sub_6EFC81`** (bảng 5, 44 B): `rec[1]=1, rec[0]=a2, rec[2..4]=a4..a6, rec[6..10]=a8..a12`; nếu `a7≠0` →
  `rec[5]=a7` + flush ngay qua vf7.
- **`sub_6EFEE3`** (bảng vòng 68 B, 16 tham số): `rec+8 = sub_6EFBCA()` (tick), ghi field, `++count[slot]`, rồi
  `sub_6EFC44`/`sub_6EFC07` (đếm theo `a13 & 1`). Được gọi **cạnh** `sub_6EFD24` trong `sub_5B0053`.

### Định dạng flush bảng 41 (`sub_6F0B2A`, C→S **112**, cùng format với 145 của bảng 45)
```
sub_88851B(112)                      // mở gói nhóm vào this[73]
u8  rec[+0]
u8  (slot & 0xF) | (rec[+8] << 4)
u16 rec[+12]
u8  rec[+16]
u8  rec[+20]
u8  rec[+24]
u8  rec[+28]
u16 rec[+32]
sub_88861B(this+73); rec[+4] = 0     // đóng gói, xoá cờ
```

## 5. Tham số — call site `CGOCAHeroGameBomber__vf6_2` 0x5B1FB5 (đường Space/đặt bom)

`ecx = var_14 = sub_6FFF99(dword_E60924)` (CGameMsgCache). `v6` = object bom lấy từ `(bomber-0xE4)->vf18(1)`
(`[eax+48h]`), `a2` = out-param của vf6_2.

| Arg | `[ebp+]` | Nguồn (caller) | Runtime (slot 0, spawn góc phải-trên) |
|---|---|---|---|
| arg_0 | +08 | `sub_6E2000(ctx)` = `ctx[490549]` (ghi đè `var_1C` ở 0x5B1EDF) | 0 |
| arg_4 | +0C | bomber `vf10` (`[edi]+28h`) — **slot**, dùng cho cổng | 0 |
| arg_8 | +10 | `*a2 = sub_5910BF(v6)` (box `v6+280`) | 0 |
| arg_C | +14 | `(u8) sub_59119D(v6)` (`sub_578290(v6+376)`) | 1 |
| arg_10 | +18 | `var_24` — từ bomber `vf25(&var_28)` (`[edi]+64h`), dword thứ 2 = **hàng (y)** | 0 |
| arg_14 | +1C | `var_28` — dword thứ 1 = **cột (x)** | 0xE (14) |
| arg_18 | +20 | `(bomber-0xE4)->vf31()` (`+7Ch`) | 1 |
| arg_1C | +24 | `sub_591066(v6)` (box `v6+192`) | 1 |
| arg_20 | +28 | `sub_5911A8(v6)` (box `v6+328`) | 0 |
| arg_24 | +2C | `sub_5911B3(v6)` (box `v6+340`) | 0 |
| arg_28 | +30 | `v6->vf22()` (`+58h`) | 0 |
| arg_2C | +34 | hằng `0` | 0 |

Giá trị trả về: vf6_2 **bỏ qua**; sau lời gọi nó gọi `(bomber-0xE4)->vf49` (`+0C4h`), trả 0 thì `sub_708FFE(67,0)`.

### Các caller khác (8 tổng — `vmtriage.md`)
| Caller | Call | Khác biệt đáng chú ý |
|---|---|---|
| `sub_4A4E70` (← `CGOIamBossBomber__vf18`) | 0x4A5179 | `ecx = dword_E608D0` trực tiếp |
| `CGOCAHeroGameBomber__vf12` | 0x59AA1A | sau lời gọi `xor eax,eax` |
| `sub_5B0053` (← vf6_2, `sub_5B19B3`) | 0x5B03AB | gọi cạnh `sub_6EFEE3` |
| `sub_5B089D` (← `CGOCAHeroGameBomber__vf7`) | 0x5B0979 | arg_18 = hằng **1**; sau đó `byte [esi+3124h] = 0`; dùng giá trị trả về |
| `CGOCAHeroGameBomber__vf6_2` | 0x5B1FB5 | bảng trên |
| `sub_6E3E58` (← `sub_7029D3`) | 0x6E4002 | |
| `sub_74E76F` (← `sub_74E9B9`) | 0x74E85F | `ecx = sub_6FFF99(...)`; arg lấy từ `sub_591045/050/05B` |
| `CGOSquareBomber__vf6` (sảnh) | 0x86635B | đường bom ở quảng trường |

## 6. Kiểm chứng (bước 3)

1. Build lại với bản viết lại (thay skip/khối trong `tools/devirt.py`), `tools/rebuild_wine.sh`.
2. `GREP='ENTRY|ARGS|GATE|FLUSH112|CRASH' TURN_MODE=1 PLAY_START=4 tools/match_gdb.sh tools/gdb/msgcache_6efd24.gdb <out>`.
3. Mong đợi: không CRASH; `FLUSH112 slot=0` sau Space (nếu suy luận §3 đúng); `<out>/fakeserver.log` có `C->S opcode 112`
   với các byte khớp args (cột 14, hàng 0…); bom hiện trên map (`<out>/match_after.png`).

## 7. Chưa biết
- Ánh xạ chính xác 11 tham số dữ liệu → 8 field của bản ghi 36 B (bảng 41 có ít field hơn số tham số → khối có thể
  làm thêm việc ngoài ghi bản ghi; kích thước 0x18F cũng gợi ý vậy).
- Ý nghĩa `ctx[490549]` (arg_0), các box `v6+280/+376/+192/+328/+340`.
- Giá trị trả về mong đợi (`sub_5B089D` có dùng).
