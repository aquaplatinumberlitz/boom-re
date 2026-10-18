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


## 6. Opcode map (stage 1B + 2) — kết quả mới

Ghép 3 nguồn: **bảng handler tĩnh** (opcode → địa chỉ), **trace** (opcode → kích thước VI),
và phân tích tĩnh handler (đặc trưng). Lệnh:

```
python3 tools/vmdevirt.py opcodes --snap logs/snap/8F346C/pre.snap --site 8F346C \
        --disp 11F9E81 --ctx 11EDDEC --json decomp/vm_opcodes.json
```

Kết quả trên khối `8F346C` (4.6M lệnh, 11.340 dispatch):

| chỉ số | giá trị |
|---|---|
| opcode quan sát được | **46** |
| opcode có handler trong bảng tĩnh | **46/46** |
| opcode đo được kích thước | **44/46** |
| histogram kích thước | 1 byte ×34, 2 byte ×5, 3 byte ×1, 5 byte ×4 |
| opcode nhánh (VIP không tuần tự) | **0x67, 0x7B, 0x80** |
| xung đột kích thước | **0** |

**Kiểm chứng bảng tĩnh:** tại mỗi dispatch, so `[ctx + op*4]` với EIP thực tế của handler kế tiếp —
**3.680/3.680 khớp, 0 lệch** (1.5M lệnh đầu). ⇒ Bảng tĩnh là authoritative, phân tích tĩnh đáng tin.

### Bytecode bị mã hoá — không decode tĩnh được

Thử decode tuyến tính toàn stream `0x1350128..0x135B33B` (45.587 byte) bằng bảng kích thước:
**33.151 byte ra opcode lạ** ⇒ sai. Nguyên nhân: handler đọc byte bằng `lodsb al,[esi]; xor al,bl`,
tức byte trong file **không phải** opcode. Đã kiểm tra khoá:

| giả thuyết | kết quả |
|---|---|
| `img[vip] ^ op` | 255 giá trị khác nhau |
| `img[vip-1] ^ op` | 255 |
| `img[vip-2] ^ op` | 255 |
| `img[vip] ^ bl` (bl tại dispatch) | 262 giá trị |

⇒ **khoá rolling**, đổi mỗi lệnh. Muốn decode tĩnh phải hiểu hàm cập nhật khoá (việc RE sâu hơn).

**Hệ quả thực dụng:** không cần decode tĩnh. Trace cho `(vip, opcode)` trực tiếp — đó chính là listing
của đoạn đã chạy, và nó khớp với bảng tĩnh. Với devirt một khối, chương trình *đã chạy* là đủ.

## 7. Fake native

Thêm `--fake-native`: sau khi đã vào VM, mọi lần rời VM ra ngoài image (hàm game hoặc DLL) đều **không
chạy** — tool đọc return address ở `[esp]`, set `eax`, chỉnh `esp` theo `ret imm16` của stub, rồi trả về VM.
Có xử lý `jmp far` (WoW64 syscall: set eax, pop stub).

Đo trên `8F346C` (6M lệnh): 20 lần gọi native được fake, và **vẫn chưa tới `cont`** — vì khối này chạy
45 KB bytecode rồi gọi native, tức `cont` không phải điểm dừng khả dụng cho khối loop/keep-alive. Kết luận
này khớp với việc harness của repo (`tools/vmemu.py`) cũng không exit sau 3M bước.


## 8. Báo cáo độ phủ so với mục tiêu

| Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|
| Stage 1 — discovery (section, site, stub head) | ✅ **xong** | 607 site → 390 head; head `0x11EE3B0` = 73 lần = 73 marker |
| Stage 1B — VM context | ✅ **xong** | `0x11EDDEC`, tự dò qua spinlock `0x11EECB0`; xác nhận bằng `edi` cuối khối + tại dispatch |
| Stage 1B — bảng handler | ✅ **xong** | 178 entry trong `ctx+0x94..+0xF48`; tĩnh (3 snapshot + file); **3.680/3.680 dispatch khớp** |
| Stage 1B — phân loại handler | 🟡 **một phần** | 46 opcode có handler; phân loại *cấu trúc* (pushfd/lods/dispatch/size) xong; **ngữ nghĩa chưa** |
| Stage 2 — encoding VI | ✅ **xong** | 44/46 opcode có kích thước nhất quán, 0 xung đột; 3 opcode nhánh (0x67, 0x7B, 0x80) |
| Stage 2 — decode toàn stream | ❌ **bị chặn** | bytecode mã hoá rolling key (4 giả thuyết khoá đều fail); chỉ decode được đoạn **đã chạy** qua trace |
| Stage 2 — CFG | 🟡 **một phần** | có danh sách VI đã chạy + nhánh; chưa dựng đồ thị đầy đủ |
| Stage 3 — emit C | ❌ **chưa** | phụ thuộc ngữ nghĩa 46 opcode; "semantics" hiện chỉ là sketch, bị junk chi phối |
| Verify với 6 khối `tools/devirt.py` | ❌ **chưa** | mới verify bảng handler vs runtime |
| `decomp/vm_profile.json` | ✅ | sinh tự động |
| Áp dụng sang KR | ⏸ **chờ dump** | KR đang pack, không có dump thì không chạy được gì |

**Chặn hiện tại (theo thứ tự):**
1. Ngữ nghĩa 46 opcode — phải đọc từng handler như bài gốc (nhìn lệnh ngay trước `pushfd`, nhìn
   thao tác trên ngăn xếp ảo). Sketch tự động hiện tại bị hằng số rối chi phối, **không dùng được**.
2. `cont` không dùng được cho khối loop ⇒ cần đơn vị "một vòng" (chưa chốt được fingerprint đúng).
3. Bytecode rolling cipher ⇒ không decode được nhánh chưa chạy.

**Ước lượng:** để emit C cho một khối đơn giản cần (1) ngữ nghĩa ~46 opcode, (2) một mô hình ngăn xếp ảo
(VSP) đúng, (3) emit + verify. Mỗi phần là vài giờ làm việc có kiểm chứng, không phải một bước.


## 9. Fake native — trạng thái và giới hạn (round 4)

Để chạy một khối tới `cont`, code native mà VM gọi phải chạy được. Đã nâng `--fake-native`:

| Cơ chế | Hành vi |
|---|---|
| Hàm native **trong image** (.text) | **chạy thật** (dump đã có code) |
| Hàm **ngoài image** (DLL/hệ thống) | không chạy: đọc return address ở `[esp]`, set `eax`, chỉnh `esp` theo `ret imm16` |
| `jmp far` (WoW64 syscall) | set `eax`, pop stub, `esp += 4` |
| `--skip ADDR[=eax]` | bỏ qua hàm native trong image (anti-cheat/integrity), giả lập return |
| `--fake-ret` | `scratch` = trả con trỏ tới vùng 64 KB zeroed (tránh native deref null) hoặc một số cụ thể |

Đo trên `8F4D46` (`cont 0x8F5468`):

| cấu hình | kết quả |
|---|---|
| fake mọi thứ, `eax=0` | chết ở `0xa1333f` — đúng vùng **anti-cheat** (0xA12E59..0xA17A24) |
| + `--skip A12E50 A14800 A13A10` | chạy 8.0M lệnh, rồi `unmapped 0x0` (native deref null vì API fake trả 0) |
| + `--fake-ret scratch` | chạy **20M lệnh không crash**, nhưng **vẫn không tới `cont`** |

Lý do không tới `cont`: ba snapshot hiện có (`8F346C`, `8F4D46`, `8F5F40`) đều nằm trong **vòng lặp chính**
`sub_8F4D01`; sau khi VM nhả về code native, luồng quay lại vòng lặp (và vào lại VM) chứ không đi thẳng tới
nhãn `cont`. Đây là giới hạn của *bộ snapshot hiện có*, không phải của thuật toán: muốn kiểm chứng emit C
phải có snapshot ở một khối **thẳng** (ví dụ `8F452B`, `8F8F69` — chưa có snap).

**Hệ quả cho mục tiêu:** verify emit C với 6 khối cần thêm snapshot. Việc này cần chạy client gốc trên
Windows/Wine (`win/snap.bat <SITE>`) — nằm ngoài phạm vi tự động của round này.


## 10. CFG + dừng theo "hub" (round 5)

### CFG của stream VI đã chạy

```
python3 tools/vmdevirt.py cfg --snap logs/snap/8F346C/pre.snap --site 8F346C --disp 11F9E81 --max 6000000
insns 4621780  dispatches 11340
basic blocks 24  edges 23  back edges 6
block sizes: min 27  max 3282  mean 472.5
```

- 24 basic block, 23 cạnh, **6 back-edge** ⇒ khối này **có loop**, không phải tuyến tính.
- Hub của loop: `0x135B33B` (đích của nhiều cạnh lùi, cũng là `jmp` target của site `8F346C`).
- Lỗi đã sửa: trước đó tao coi "VIP delta ≤ 16" là tuần tự ⇒ nhảy ngắn bị nuốt, CFG chỉ ra 3 block.
  Đúng phải là: size của opcode = delta **phổ biến nhất**, khác nó thì là nhánh.

### Dừng theo hub ⇒ đúng một vòng

Thêm `--stop-vip ADDR`: dừng khi VIP quay lại hub lần thứ 2. Trên `8F346C`:

```
hub 0x135b33b reached 2 times -> one iteration
insns 3947362  stop cycle  exits 2
```

⇒ Lần đầu tiên có **một đơn vị ngữ nghĩa xác định** cho khối loop: một vòng = 3.947.362 lệnh.

### Kiểm chứng với bản viết tay (đối chiếu đầu tiên)

`tools/devirt.py` viết tay cho `8F346C`: `push 0xF; call 0x888462` (CSendPacket/SendPkt__Begin), sau đó
`0xA65280` ×3 (Encode4), `0x888609` (Send), `0x8884DC` (dtor), `0x8E1C72`, `0x8F2803`.

Tool báo **đích rời VM đầu tiên trong một vòng: `0x888462`** — khớp. Các call sau chưa tới vì biên "một
vòng" hiện tại (hub lần 2) cắt sớm hơn toàn bộ flow của khối.

Đây là **đối chiếu đầu tiên có bằng chứng** giữa tool và bản devirt tay. Chưa phải verify đầy đủ.

### Profile hợp nhất

`decomp/vm_profile.json` giờ gộp cả `opcodes` (46) và `handlers` (178) ⇒ một file đọc là đủ cho emitter.

## 5b. Đường áp dụng sang bản KR

Bản KR (`~/Downloads/boom_kr_lastest00967/PatchData/CA.exe`) **đang bị pack**:

- entry `RVA 0x1E5D000` nằm trong section `gsowkarq` (512 byte) = stub unpacker;
- section VM `gulxdsye` (1.99 MB) entropy 7.95, **0 marker** `EB 10 57 4C 20` (bản VN có 73);
- không có run ≥16 dword trỏ vào section VM ⇒ bảng handler/bytecode chưa tồn tại ở dạng đọc được;
- `.idata` chỉ 0x200 byte ⇒ IAT đã bị bóc.

⇒ Phải dump tại OEP rồi mới chạy `discover`. Tool đã tách "profile" khỏi engine để sau khi có dump KR chỉ
cần chạy lại `discover`/`jumps`/`ctx` trên ảnh mới, không sửa code.
