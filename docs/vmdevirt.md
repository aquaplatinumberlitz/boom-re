# VM Themida: kiến trúc thực tế của bản VN (2015) và công cụ devirt

Tài liệu này trả lời: **VM trong `unpacked_ca.exe` có giống FALCON trong bài của Shablyko không**, và
công cụ `tools/vmdevirt.py` khai thác được gì. Số liệu đều từ chạy thật trên `unpacked_ca.exe` +
`logs/snap/8F346C/pre.snap`, không suy đoán.

## 1. Kết luận ngắn

| Khía cạnh | FALCON (bài, 2026) | VM trong `unpacked_ca.exe` (2015) |
|---|---|---|
| Prologue | `pushfq` + junk stack shuffle | **giống** (`pushfd` tại `0x11EE128`, junk y hệt) |
| Đồng bộ | `lock cmpxchg [ctx+0xD3],1` + `pause` | **giống**, nhưng field `ctx+0x7C` (`lock cmpxchg` tại `0x11EECB0`) |
| Phân rã code | 1 handler = 1 basic block liền mạch, tự chain | **chia vụn**: mean straight-line run **6.66 lệnh**, median 5, 63.6% run ≤6, nối bằng `jmp` trực tiếp |
| Dispatch | `jmp [table + idx*8]` | `jmp [ctx + offset riêng từng site]` (slot cache trong ctx) |
| Bảng handler | 658 entry liền nhau | **không có** bảng liền nhau; slot rải trong ctx (`ctx+0xB8..ctx+0x31C` quan sát được) |
| Ý nghĩa | phân loại 650 handler là đủ | **phải trace**; không có "handler" để phân loại |

⇒ Với bản VN, phương pháp "enumerate + classify handler" của bài **không áp dụng**. Cái áp dụng được là
phần **trace → lift → emit**, đúng hướng `tools/vmemu.py` + `tools/devirt.py` đang làm tay.

## 2. Context của VM (bản VN)

Anchor xác định bằng spinlock: lần ghi `1` vào `0x11EDE68` tại `0x11EECB0` là `lock cmpxchg [edi+0x7C]`
⇒ **ctx base = `0x11EDDEC`**, field khoá `sync` ở `+0x7C`.

Offsets quan sát được (ghi trong lúc entry / trong vòng chạy):

| offset | nội dung | nguồn |
|---|---|---|
| `+0x00..+0x1C` | vùng lưu host register (8 dword, ghi ngay sau entry) | write trace |
| `+0x08..+0x1C` | giá trị trỏ vào stack (`0x0019C6E8`, `0x0019C4BC`, …) | snapshot |
| `+0x7C` | `sync` (spinlock) | `0x11EECB0` |
| `+0xB8..+0x31C` | **slot cache đích nhảy** của từng dispatch site (170 slot đã thấy ở snapshot) | snapshot + trace |
| `+0xA0` (theo base `0x11EDE80`) | bắt đầu dãy con trỏ vào section VM | snapshot |

Không có immediate nào bằng `0x11EDDEC` trong section VM (đã quét: 0 lần) ⇒ ctx được tính từ hằng số
rối, nên phải lấy **động** qua spinlock, không hardcode được.

## 3. Dispatch thực tế

- 400k lệnh: **977 lần** `jmp/call [mem]`, **0 lần** `jmp reg`.
- 32 slot khác nhau, ví dụ `[0x11EDFF0] → 0x11F7467` (277 lần), `[0x11EDEF8] → 0x11F6CB8` (142 lần).
- Nghĩa là **mỗi site dispatch có slot riêng** trong ctx (không phải `table[idx]`).

Hệ quả cho devirt: "handler" không phải đơn vị; đơn vị là **đoạn thẳng** (mean 6.66 lệnh) và luồng thật
chỉ lấy được bằng trace. Bản KR (2026) nhiều khả năng dùng thiết kế FALCON, nên tool phải hỗ trợ **cả hai
backend**: `threaded` (VN) và `chained` (FALCON).

## 4. `tools/vmdevirt.py` — trạng thái

```
python3 tools/vmdevirt.py discover            # sections, 603 site, 388 stub head
python3 tools/vmdevirt.py jumps --snap ... --site 8F346C   # dispatch + slot
python3 tools/vmdevirt.py ctx   --snap ... --site 8F346C   # dump context sau 1 khối
```

Đã có: PE 32-bit, nhận diện section Themida, quét site (`E8/E9` từ `.text` vào vùng VM), follow stub,
snapshot replay (BSNP), FS qua GDT, log ghi bộ nhớ + chuyển nhánh gián tiếp, dò bảng/slot, dump ctx.

Số liệu chạy được:

- `discover`: 603 site → 388 stub head; head `0x11EE3B0` xuất hiện **73 lần** = đúng 73 marker `EB 10 57 4C 20`.
- `jumps`: phân biệt `jmp [mem]` vs `jmp reg`, dựng histogram slot→đích.
- `ctx`: chạy tới lần rời VM đầu tiên, dump ctx; phát hiện `0x11EDDE0..0x11EDE0F` + slot cache.

Chưa có (kế hoạch): `trace` (ghi toàn bộ trace 1 khối tới `cont`, lọc junk), `summary` (tóm tắt tác dụng
khối: ctx field, global/object write, native call), `emit` (sinh C), backend `chained` cho FALCON.

## 5. Đường áp dụng sang bản KR

Bản KR (`~/Downloads/boom_kr_lastest00967/PatchData/CA.exe`) **đang bị pack**:

- entry `RVA 0x1E5D000` nằm trong section `gsowkarq` (512 byte) = stub unpacker;
- section VM `gulxdsye` (1.99 MB) entropy 7.95, **0 marker** `EB 10 57 4C 20` (bản VN có 73);
- không có run ≥16 dword trỏ vào section VM ⇒ bảng handler/bytecode chưa tồn tại ở dạng đọc được;
- `.idata` chỉ 0x200 byte ⇒ IAT đã bị bóc.

⇒ Phải dump tại OEP rồi mới chạy `discover`. Tool đã tách "profile" khỏi engine để sau khi có dump KR chỉ
cần chạy lại `discover`/`jumps`/`ctx` trên ảnh mới, không sửa code.
