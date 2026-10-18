# VM Themida: kiến trúc thực tế của bản VN (2015) và công cụ devirt

Tài liệu này trả lời: **VM trong `unpacked_ca.exe` có giống FALCON trong bài của Shablyko không**, và
công cụ `tools/vmdevirt.py` khai thác được gì. Số liệu đều từ chạy thật trên `unpacked_ca.exe` +
`logs/snap/8F346C/pre.snap`, không suy đoán.

## 1. Kết luận ngắn

| Khía cạnh | FALCON (bài, 2026) | VM trong `unpacked_ca.exe` (2015) |
|---|---|---|
| Prologue | `pushfq` + junk stack shuffle | **giống** (`pushfd` tại `0x11EE128`, junk y hệt) |
| Đồng bộ | `lock cmpxchg [ctx+0xD3],1` + `pause` | **giống**, nhưng field `ctx+0x7C` (`lock cmpxchg` tại `0x11EECB0`) |
| Bảng handler | 658 entry, base ở `ctx+0xD7`, `idx*8` | **178 entry, base = chính `ctx`, `idx*4`, idx đã nhân sẵn** |
| Tính chất bảng | fixup bằng image base lúc entry | **tĩnh tuyệt đối** (xem §3) |
| Phân rã code | 1 handler = 1 basic block liền mạch, tự chain | **chia vụn**: mean straight-line run **6.66 lệnh**, median 5, 63.6% run ≤6, nối bằng `jmp` trực tiếp |
| Dispatch | `jmp [table + idx*8]` | `jmp [edi + eax*4]` với `edi = ctx`, `eax = idx` (đo thực tế: `0x43`, `0x81`, `0x56`) |
| Ý nghĩa | phân loại 650 handler là đủ | bảng enumerate được **tĩnh**, nhưng thân handler bị xé nhỏ ⇒ ngữ nghĩa phải lấy bằng **trace** |

⇒ Cái áp dụng được từ bài: enumerate + phân loại handler theo mẫu (`pushfd` → flag-op), và tách
"profile" khỏi engine. Cái **không** áp dụng: giả định mỗi handler là một block tự chứa.

## 2. Context của VM (bản VN)

Anchor xác định bằng spinlock: lần ghi `1` vào `0x11EDE68` tại `0x11EECB0` là `lock cmpxchg [edi+0x7C]`
⇒ **ctx base = `0x11EDDEC`** (lấy `edi` tại chính lệnh đó), field khoá `sync` ở `+0x7C`.

Kiểm chứng độc lập: cuối một khối, `edi = 0x11EDDEC`; tại site dispatch, `edi = 0x11EDDEC` và
`[edi + eax*4]` cho đúng handler.

| offset | nội dung | nguồn |
|---|---|---|
| `+0x00..+0x1C` | vùng lưu host register / VM register (ghi ngay sau entry) | write trace |
| `+0x64`, `+0x74` | field dữ liệu (vd `+0x64` nhận `0x02752BE8` rồi `xor edx`) | lift |
| `+0x7C` | `sync` (spinlock) | `0x11EECB0` |
| `+0x94..+0xF48` | **bảng handler**: 178 entry, mỗi entry 4 byte, chỉ số = `offset/4` (0x25..0x3D2) | đọc file |

## 3. Bảng handler là tĩnh (đã kiểm chứng)

So 3 snapshot độc lập (`8F346C`, `8F4D46`, `8F5F40`) và so với byte trong `unpacked_ca.exe`:

- 178/178 entry **giống nhau** giữa 3 snapshot;
- 178/178 entry **giống byte trong file** (0 khác).

⇒ Không phải cache runtime. Đây là bảng hằng nằm trong section VM, nên **enumerate được mà không cần chạy**:

```
python3 tools/vmdevirt.py handlers --ctx 11EDDEC --json decomp/vm_handlers.json
handler table at ctx 0x11eddec: 178 entries
classes: {'block': 117, 'bytecode_read': 45, 'flagop': 16}
```

`decomp/vm_handlers.json` ghi: opcode, địa chỉ, class đoán, số `pushfd`/`lods`/`dispatch`/`pop`.
Class ở đây là **đoán theo mẫu tĩnh** (walk 40 lệnh theo `jmp` trực tiếp), chưa phải ngữ nghĩa — vì thân
handler bị xé nhỏ nên walk tĩnh không đi hết được. Bước tiếp theo: chạy từng entry bằng Unicorn và ghi
tác dụng thật (thanh ghi/flags/bộ nhớ) → đó mới là ngữ nghĩa dùng để emit.

## 4. `tools/vmdevirt.py` — trạng thái

```
python3 tools/vmdevirt.py discover [--json out.json]     # sections, site, stub head
python3 tools/vmdevirt.py profile  --snap ... --site ...  # ctx + dispatch form -> decomp/vm_profile.json
python3 tools/vmdevirt.py handlers --ctx ...               # bảng handler -> decomp/vm_handlers.json
python3 tools/vmdevirt.py ctx      --snap ... --site ...   # dump context sau 1 khối
python3 tools/vmdevirt.py trace    --snap ... --site ... --cont ...  # tác dụng khối (ctx/image/heap, regs)
python3 tools/vmdevirt.py lift     --snap ... --site ... --cont ... --ctx ...
```

Số liệu chạy thật:

- `discover`: **607 site → 390 stub head**; head `0x11EE3B0` xuất hiện **73 lần** = đúng 73 marker.
- `profile`: tự tìm spinlock (`0x11EDE68`) → tự suy `ctx = 0x11EDDEC`; dispatch chỉ **một dạng duy nhất**
  `jmp [base+idx*4+0x0]`, 1469 lần trong 600k lệnh; field ctx bị ghi: `+0x00..+0x1C`, `+0x74`, `+0x7C`.
- `lift`/`trace` khối `8F346C`: **7094 lệnh unique**, chỉ **36 lệnh có ngữ nghĩa** (chạm ctx/image/heap) —
  tỉ lệ junk ~99.5%, phần ngữ nghĩa in kèm offset ctx (vd `add dword ptr [edx], ebp ; ctx+0x84`).
  `trace` ghi 15 write vào ctx, 9 write vào image, 105 write stack/heap, `edi` cuối = ctx.

  **Cảnh báo (đã kiểm chứng):** cả 3 khối `8F346C`, `8F4D46`, `8F5F40` đều dừng vì `budget` chứ **chưa tới
  `cont`** — tức trace đang chứa cả pool VM chung, *không phải riêng một khối*. Số "7094 unique" là pool,
  không phải kích thước khối. Muốn có ngữ nghĩa khối phải sửa điều kiện dừng (hiện tool in WARNING khi
  điều này xảy ra). Đây là việc tiếp theo trước khi tin bất kỳ output `lift` nào.

## 5. Đường áp dụng sang bản KR

Bản KR (`~/Downloads/boom_kr_lastest00967/PatchData/CA.exe`) **đang bị pack**:

- entry `RVA 0x1E5D000` nằm trong section `gsowkarq` (512 byte) = stub unpacker;
- section VM `gulxdsye` (1.99 MB) entropy 7.95, **0 marker** `EB 10 57 4C 20` (bản VN có 73);
- không có run ≥16 dword trỏ vào section VM ⇒ bảng handler/bytecode chưa tồn tại ở dạng đọc được;
- `.idata` chỉ 0x200 byte ⇒ IAT đã bị bóc.

⇒ Phải dump tại OEP rồi mới chạy `discover`. Tool đã tách "profile" khỏi engine để sau khi có dump KR chỉ
cần chạy lại `discover`/`jumps`/`ctx` trên ảnh mới, không sửa code.
