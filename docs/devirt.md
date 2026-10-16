# Devirtualize hàm bị Themida ảo hoá (hướng 1)

Mục tiêu: chạy được bản dump `ca_fixed.exe` (không còn Themida) trong Wine trên host có GPU.
IAT đã sửa xong (`docs/runtime.md` → "Sửa IAT"). Việc còn lại là các đoạn code bị Themida ảo hoá.

## Trạng thái (2026-10-16)

- ✅ **Bản dump chạy được trong Wine trên host (GPU), mở cửa sổ game và đăng nhập vào `tools/fakeserver.py`** (127.0.0.1).
- Đã devirtualize: **2 khối** (`sub_8F4421` site 0x8F452B; `CStageMgr__ChangeStage` site 0x8F8F69) — xem [Khối đã xong](#khối-đã-xong).
  Sau khối 2: hết chết ở intro; logo Nexon hiện, CALog `[XRpt] Sg - INT(dne:1)` + `EndOfInit!! exitcode=0`, đăng nhập server giả xong,
  client mở thêm kết nối tới port khác (hello rồi tự đóng — chưa rõ, xem `logs/fakeserver_host.log`).
- **Chặn tiếp theo: vòng lặp chính `sub_8F4D01`** (gọi từ `CFxApp__vf5` 0x8E30DA) — 3 khối VM lớn, xem [Vòng lặp chính](#vòng-lặp-chính-sub_8f4d01--chặn-hiện-tại).
- Sửa thêm: unlicense nhầm `CreateWindowExW` ↔ `CreateWindowExA` (cửa sổ chính không tạo được → `CSysException "CreateWindow failed"`).
- Các khối VM khác chưa bị chạm tới trên luồng khởi động → làm khi gặp (lobby, phòng, ván chơi sẽ chạm `CGamePlayMap__Load`, `CGOBomber__vf21`…).

## Ranh giới khối VM: marker của Themida SDK

Mỗi khối VM **kết thúc bằng marker VM_END của SDK**: `EB 10 57 4C 20 …` (`jmp $+0x12` qua 16 byte, có chữ `WL `), các byte còn lại bị
mutate (`89 xx` / `90`). **Code gốc tiếp tục ngay sau marker** (marker + 0x12). Khối = `[site, marker+0x12)`; vùng giữa là rác
(Themida ghi đè code gốc tại chỗ, nên độ dài vùng ≈ độ dài code gốc). Phần code gốc **sau** marker còn nguyên dù IDA không thấy
(không có xref) → disassemble thẳng bằng capstone.
Kiểm chứng: 0x8F452B → 0x8F45A7 (khớp vmtrace), 0x8F8F69 → 0x8F8FCA (khớp thanh ghi sau khối của vmtrace: `edi=0xE`, `ebx=0`).
73 marker trong `.text`. Ghép site với marker kế tiếp:

| site | hàm | tiếp tục | dài |
|---|---|---|---|
| 0x8E5519 | `CFxApp__vf6` | 0x8E5547 | 0x2E |
| 0x8F346C | `sub_8F3409` | 0x8F38F3 | 0x487 |
| 0x8F452B | `sub_8F4421` | 0x8F45A7 | 0x7C ✅ |
| 0x8F4D46 | `sub_8F4D01` (vòng lặp chính) | 0x8F5468 | 0x722 |
| 0x8F54E4 | `sub_8F4D01` | 0x8F5DFA | 0x916 |
| 0x8F5F40 | `sub_8F4D01` | 0x8F6908 | 0x9C8 |
| 0x8F8F69 | `CStageMgr__ChangeStage` | 0x8F8FCA | 0x61 ✅ |
| 0x966FEC | `sub_966FDE` | 0x9670BD | 0xD1 |
| 0x9682E5 | `sub_9682DE` | 0x968385 | 0xA0 |
| 0x5A6E89 | `CGOBomber__vf21` | 0x5A6F64 | 0xDB |
| 0x6EFD4A | `sub_6EFD24` | 0x6EFED9 | 0x18F |
| 0x6F287E | `sub_6F27EE` | 0x6F2923 | 0xA5 |
| 0x71581A | `sub_71580C` | 0x7158E4 | 0xCA |
| 0x736C27 | `CGamePlayMap__Load` | 0x736D6C | 0x145 |
| 0x754C82 | `CMapScriptStageClear__vf7` | 0x754D20 | 0x9E |

(Site nằm ngoài hàm IDA như 0x8F54E4/0x8F5F40 không có trong `decomp/themida_entries.json`; tìm bằng `jmp` → `push key; jmp 0x11EE128`.)

## Khối đã xong

### 0x8F452B — `sub_8F4421` (bước khởi tạo trong `CFxApp__InitMain`)
- Ranh giới: site 0x8F452B → tiếp tục ở **0x8F45A7** (`lea ecx,[esi+14h]; push ebx; call 0x413F32`). Byte giữa là rác.
- Quan sát (`tools/vmtrace.py`, client gốc trong WinBoat): thanh ghi edi/esi/ebp/ebx giữ nguyên; eax/ecx chết. Bộ nhớ:
  - `0xEED860[256]` = bảng CRC32 reflected, poly **0xDD10EC81** (chỉ code Themida ở 0x1330A69 đọc);
  - `0xEEE07C = 0x4A65000A`, `0xEEE088 = 1`, `0xEEE08C = GetTickCount()` (không có xref từ code game);
  - `0xEEE650..65C` = callback `0x8F2C5D, 0x8F30F7, 0x8F2C4F, 0x8F31F6` (nhiều hàm game gọi, ví dụ `sub_413F32`).
- Viết lại: `tools/devirt.py` `BLOCKS[0]` (dữ liệu ghi thẳng vào image + `GetTickCount` lúc chạy).

### 0x8F8F69 — `CStageMgr__ChangeStage(id)` 0x8F8EEC
- Hàm: nếu `id == [this+D8]` thì thôi; `[this+E8]=1`; stage cũ `vf45` (OnLeave, `[vt+0xB4]`) + dọn UI; `delete` stage cũ; **khối VM**;
  rồi code gốc (còn nguyên từ 0x8F8FCA): `switch(id)` → `malloc(size)` + ctor → `[this+D4]`; null → MessageBox + `App__SetExitError(5,0x1B4)`;
  `stage->vf44()` (OnEnter, `[vt+0xB0]`); CALog `[XRpt] Sg - INT(dne:%d)`; `[this+E8]=0`.
- Khối VM (0x61 byte) chỉ còn: `[this+DC] = [this+D8]` (stage trước, đọc qua `GetPrevStage` 0x8F889A), `[this+D8] = id`.
  Bằng chứng: vmtrace (`D8: 0x17 → 1`), ngoài ctor `sub_8F9800` không code native nào ghi D8/DC; `CStage__vf44` đọc `GetCurStageId` nên D8 phải đặt trước.
  Ngữ cảnh tại site: `esi`=CMainWnd, `ebx`=id, `edi`=0 (dùng làm tham số ở 0x8F8FD0).
- Viết lại: `tools/devirt.py` `BLOCKS[1]`.

## Stage (CMainWnd = `g_pMainWnd`)

`CMainWnd`: `+D4` stage hiện tại, `+D8` id hiện tại (`GetCurStageId` 0x8F8893, 151 nơi gọi), `+DC` id trước, `+E8` đang chuyển stage.
Id 0x17 = chưa có stage. Đổi stage: `sub_8F391D(dword_E6092C, id)` đặt id đích (giá trị được che), vòng lặp chính so với `GetCurStageId` rồi gọi ChangeStage.
Bảng `switch` trong code gốc 0x8F8FE3 (size = tham số `malloc`; `0x40176c(n)` = `Feature_IsDisabled(n)`):

| id | stage | size | ctor | ghi chú |
|---|---|---|---|---|
| 1 | `CLoginStage` | 0x26CC | 0x84F724 | ✅ chạy trong Wine |
| 3 | `CCreditStage` | 0x1024 | 0x68F731 | |
| 10 | `CSelectServerStage` | 0x7354 | 0x85817A | |
| 11 | lobby: loại 0 `CLobbySquareStage` (0x570F0, 0x4E56DF) / loại 2 `CLobbyStageWithSquareUI` (0x57CFC, 0x4C1F4D) / khác `CLobbyStage` (0x5525C, 0x6B3EDD) | | | loại = `sub_994378(server hiện tại)`, mặc định 1 nếu feature 0x2E tắt; 0x7B tắt UI square |
| 12 | phòng: `sub_8F8CFC` → `CPrepareStage` / `CHiddenCatch(Single)PrepareStage` | | | |
| 13 | ván: `sub_8F8C88` → `CGameStage` / `CHiddenCatchGameStage` | | | |
| 14 | `CShopStageNew` | 0xAD64 | 0x807358 | |
| 16 | `CChattingStage` | 0xC134 | 0x68EE57 | |
| 17 | `CExchangeStage` | 0x8D88 | 0x846220 | |
| 19 | `CUserMarketStage` | 0x11B4C | 0x85E898 | feature 7 |
| 20 | `CSquareStage` | 0x7048 | 0x86C926 | feature 8 |
| 21 | `CMagicBookMarketStage` | 0xF8A8 | 0x87F942 | feature 0x3C |

(Đọc từ code gốc, id 1 đã kiểm chứng; ctor là hàm **không** có caller native — hàm stage được gọi từ `vf0` deleting-dtor là **dtor**.
README/devirt cũ ghi `CLoginStage` ctor 0x84F4A7 là sai: đó là dtor.)

## Vòng lặp chính `sub_8F4D01` — chặn hiện tại

`CFxApp__vf5` 0x8E30DA → `sub_8F4D01(ecx = dword_E6092C)`. Trong Wine: first-chance page fault lặp lại ở handler VM 0x11FB494
(`push [edx]`, `edx = 0x19FF68` — địa chỉ gần đỉnh stack main thread **của process gốc**).
Hàm có 3 khối VM lớn (bảng trên: 0x722 + 0x916 + 0x9C8 byte code gốc). Code gốc còn nguyên quanh chúng (0x8F5468–0x8F54E4,
0x8F5DFA–0x8F5F40, 0x8F6908–0x8F6D35): đầu vòng lặp 0x8F54B3 (`sub_8F282C` → thoát; `vf5 [+0x14]` có message?), so stage đích/hiện tại,
gọi `stage->vf44`, `Net_DispatchMainSocket(1)` 0x8F4094, đo thời gian khung hình (`> 0x3681`), `Sleep(5)`…
Khối 1 = phần khởi tạo trước vòng lặp, khối 2 = sau `sub_8F4CEA` khi có message, khối 3 = phần update/render trong scope `0x4E71E6`.

Viết lại 3 khối này bằng tay từ diff là không khả thi (≈5KB code không nhìn thấy). Hướng khả dĩ:
1. **Trace VM trên client gốc** (x32dbg trong WinBoat, ghi lại mọi lệnh ngoài section Themida = lời gọi native + tham số),
   dựng lại code từ chuỗi lời gọi. Vướng: client gốc trong WinBoat không tới được vòng lặp chính (renderer init thất bại vì không GPU)
   → cần patch bỏ qua lỗi renderer, hoặc Windows có GPU.
2. **Cho VM chạy trong bản dump**: VM cần trạng thái Themida lúc runtime (đọc `0x19FF68`, vùng cấp phát ngoài image như `0x1BA6650`).
   Dump toàn bộ bộ nhớ process gốc (không chỉ vùng thực thi như `tools/live_dump.ps1` hiện tại) rồi map lại cùng địa chỉ khi khởi động bản dump.
   Rủi ro: trạng thái có thể chứa địa chỉ DLL của Windows (khác Wine).
3. Client gốc + Wine có WoW64 kiểu cũ (`docs/runtime.md`) — VM chạy thật, không cần devirtualize.

### `tools/vmemu.py` (thử nghiệm, CHƯA dùng được)
Chạy một khối VM của dump bằng Unicorn: lời gọi native (control vào `.text` với `[esp]` trỏ về section Themida) được ghi + giả lập,
dừng khi thoát ra `.text`; `--snapshot logs/vmtrace/<SITE>` khởi đầu từ trạng thái thật và so với "post".
Kết quả với 0x8F8F69: bytecode chạy thẳng (~6400 lệnh VM, `--dispatch 0x11EECBE`) nhưng **không thoát** (>20M lệnh), đọc vùng ngoài image —
cùng triệu chứng như trong Wine → xác nhận VM phụ thuộc trạng thái runtime không có trong dump (kể cả khi phủ section Themida bằng `logs/live/image_00400000.bin`).

## Cách Themida ảo hoá trong binary này

Một **khối code ở giữa hàm** bị thay bằng:
```
<site>:     jmp  0x13xxxxx          ; trong .text của game
0x13xxxxx:  push <key>              ; khoá chọn bytecode, mỗi site một khoá khác nhau
            jmp  0x11EE128          ; VM entry (CISC VM Themida 2.x)
```
VM entry `0x11EE128`: `pushfd; push …; pushad`-kiểu lưu context, hằng số rác xen kẽ (mutation).
Bộ thông dịch nằm trong section Themida của exe (`0x11E4000–0x16AB000`), bytecode cũng ở đó.
Trong bản dump, VM chết vì đọc dữ liệu chỉ có trong process gốc (địa chỉ stack của main thread gốc `0x19FF68`, v.v.).

Code game **không** bị ảo hoá thì vẫn chạy native; một số đoạn bị **mutate** (x86 xáo trộn, nhảy sang `0x13xxxxx` rồi quay về) — vẫn chạy native.

## Danh sách điểm vào (`decomp/themida_entries.json`, sinh bởi `tools/themida_scan.py`)

117 điểm game code nhảy vào section Themida (đã lọc bằng IDA):

| class | số | ý nghĩa |
|---|---|---|
| `vm` | 56 | đi tới VM entry `0x11EE128`, có `key` |
| `unknown` | 59 | gặp `call`/nhánh có điều kiện trước khi tới đích — gần như chắc là mutate (chạy native được) |
| `return` | 2 | quay về `.text` — mutate |

### 15 điểm VM trong hàm game (ưu tiên)

Thứ tự theo luồng khởi động (làm trước) rồi tới gameplay:

| Site | Hàm | Vai trò (đoán từ ngữ cảnh) | Ưu tiên |
|---|---|---|---|
| 0x8F452B | `sub_8F4421` | khởi tạo trong `CFxApp__InitMain` (0x8E5FF8 → gọi ở 0x8E6D79); **đang chết ở đây** | 1 |
| 0x8E5519 | `CFxApp__vf6` (0x8E50D1) | vòng đời app | 1 |
| 0x8F346C | `sub_8F3409` | gần login/mạng (`Login_ConnectMain` 0x8F3978 ở cạnh) | 1 |
| 0x8F4D46 | `sub_8F4D01` | gần `Net_DispatchMainSocket` 0x8F4094 | 1 |
| 0x8F8F69 | `sub_8F8EEC` | gần `CMainWnd`, gọi từ `sub_8F939A` (`CMainWnd__OnPacket`) | 1 |
| 0x966FEC | `sub_966FDE` | ? | 2 |
| 0x9682E5 | `sub_9682DE` | ? | 2 |
| 0xA15F57 | `sub_A15F50` | vùng anti-cheat/system info | 3 |
| 0xA1784E | `sub_A17810` | duyệt cửa sổ con (`GetWindow` GW_CHILD/HWNDNEXT) — anti-cheat? | 3 |
| 0x6EFD4A | `sub_6EFD24` | ? | 2 |
| 0x6F287E | `sub_6F27EE` | ? | 2 |
| 0x71581A | `sub_71580C` | gần `CGameStage__OnPacket` 0x71B631 | 2 |
| 0x736C27 | `CGamePlayMap__Load` 0x7354FD | **nạp map** | 2 |
| 0x754C82 | `CMapScriptStageClear__vf7` | script map: điều kiện qua màn | 2 |
| 0x5A6E89 | `CGOBomber__vf21` (0x5A6244) | **gameplay: nhân vật** | 2 |

### 41 điểm VM ngoài hàm IDA: `0xA12E59–0xA17A24`

Nằm sau `AntiCheat_ScanProcesses` (0xA12C00, chụp toolhelp quét process theo danh sách trong `cavn.ini`).
Giả thuyết: toàn bộ là anti-cheat tự viết → **bỏ qua cả khối** thay vì devirtualize. Cần xác nhận nơi gọi vào vùng này.

## Công cụ quan sát khối VM: `tools/vmtrace.py` + `tools/launcher/inject.c`

Chạy trên **client gốc** (Themida thật) trong WinBoat, nơi VM chạy đúng:
```sh
uv run --with pefile --with capstone --with keystone-engine python tools/vmtrace.py build <SITE> <CONT>   # -> logs/vmtrace/<SITE>/
# tạo win/vmtrace_run.bat gọi: win\vmtrace.bat <SITE> 30000000 230000 30000FF0   (RemoteApp không nhận tham số có dấu cách)
xfreerdp3 ... '/app:program:C:\Windows\System32\cmd.exe,cmd:/c \\host.lan\Data\boom-re\win\vmtrace_run.bat'
uv run --with pefile python tools/vmtrace.py diff <SITE>     # thanh ghi + object [esi] + stack + vùng data 0xE00000–0xF09000 trước/sau
```
- `inject.exe` khởi động `ca.exe`, đặt cave ở 0x30000000, patch HackShield + site + điểm tiếp tục khi Themida giải mã xong, chờ cờ = 2, dump.
- `flag=2` nghĩa là cả hai hook chạy → **điểm tiếp tục đúng**.
- Stack thay đổi **dưới ESP** là vùng nháp của VM, bỏ qua.
- Cần `boomsrv` + DNAT (để qua bước kiểm tra bản vá) nếu khối nằm sau đó trong luồng khởi động.
- Tìm điểm tiếp tục: sau site là byte rác; tìm đoạn x86 hợp lệ chạy tới epilog của hàm (`call 0x9DB5CB; ret`), kiểm chứng bằng vmtrace.

## Chạy bản dump

```sh
python3 tools/fakeserver.py --log logs/fakeserver_host.log &   # server giả trên host
tools/rebuild_wine.sh            # fix_iat -> devirt -> patch_client -> chạy dưới winedbg (cửa sổ hiện trên desktop)
tools/run_xvfb.sh ca_fixed_patched.exe 40   # chạy trong Xvfb :77 riêng, chụp logs/xvfb/shot_*.png (không đụng desktop)
```
Chỉ chạy **một** bản một lúc (mutex `Global\FxClient...`; bản thứ hai thoát mã 9). Dọn bằng `kill` đúng PID, đừng `pkill -f` chuỗi có trong lệnh của chính shell.

## Phương pháp đề xuất (cho từng site)

1. **Xác định ranh giới khối**: site là điểm vào; tìm điểm ra = địa chỉ trong hàm mà VM nhảy về
   (lệnh ngay sau khối bị thay; thường IDA thấy code "mồ côi" sau site, không có xref).
2. **Đọc ngữ cảnh tĩnh** trong IDA: biến/thanh ghi được dùng sau điểm ra, biến được ghi trước site → suy ra khối làm gì.
3. **Quan sát động trên client gốc** (Themida thật, VM chạy đúng) trong WinBoat:
   launcher patch bộ nhớ (`tools/launch.ps1`, `tools/launcher/boomlaunch.c`) có thể chèn `int3`/hook tại site
   và tại điểm ra để ghi thanh ghi + vùng nhớ trước/sau (so sánh = tác dụng của khối).
   Có thể cài x32dbg vào WinBoat nếu cần debugger tương tác.
4. **Viết lại bằng x86** trong section mới của bản dump, sửa `jmp` ở site trỏ sang code mới, cuối code mới `jmp` về điểm ra.
   Đưa vào pipeline: thêm bước trong `tools/fix_iat.py build` (hoặc tool riêng) + ghi lại trong file này.
5. Nếu khối chỉ là kiểm tra chống debug/anti-cheat → thay bằng `jmp <điểm ra>` (bỏ qua).

## Lệnh hay dùng

```sh
tools/rebuild_wine.sh                 # build ca_fixed(_patched).exe, copy vào wine/Boom, chạy winedbg, in backtrace + CALog
uv run --with pefile --with capstone python tools/themida_scan.py unpacked_ca.exe   # sinh lại decomp/themida_entries.json
# exception đầu tiên (first chance) trong winedbg:
printf 'set $BreakOnFirstChance=1\ncont\ncont\nbt\ninfo regs\nquit\n' | WINEDEBUG=-all wine winedbg 'Z:\home\admin\boom-re\wine\Boom\ca_fixed_patched.exe'
WINEDEBUG=+seh,-all wine ca_fixed_patched.exe     # liệt kê mọi exception
WINEDEBUG=+debugstr,-all wine ca_fixed_patched.exe  # OutputDebugString của game
```
Wine đã đặt `HKCU\Software\Wine\WineDbg\ShowCrashDialog = 0` (in backtrace ra console thay vì hộp thoại).

## Chẩn đoán màn hình logo (2026-10-16) — ĐÃ GIẢI QUYẾT (khối 0x8F8F69, xem trên)

Bản dump dừng ở màn hình intro. Thực chất process thoát mã 9 (`App__SetExitError(9)`), không treo.

- CALog: `116 : InitBeforePatch` rồi dừng.
- winedbg (break first-chance): page fault `EIP=0x1388`, tức một `call [reg+N]` với con trỏ rác.
- Nguồn: `CStageMgr__ChangeStage` (`0x8F8EEC`) có một khối ở site `0x8F8F69` (tiếp tục ở `0x8F9392`) chưa viết lại → cần làm block thứ 2.
- Đã quan sát block này trên client gốc: `tools/vmtrace.py build 8F8F69 8F9392`, dump ở `logs/vmtrace/8F8F69/dump.bin`.
  - reloc (5 byte site đè): `call 0x9DB5B7`; điểm tiếp tục thật là epilog `0x8F9392` (call `__EH_epilog3`), back `0x8F9397`.
  - Hàm ngữ cảnh: chuyển stage (Login → SelectServer → Lobby…). vtable stage: `CLoginStage` ctor `0x84F4A7`, `CStage` ctor `0x6A588F`.
  - diff: nhiều thay đổi trên object `CMainWnd` ([esi]) + ~18 dword global; cần đọc kỹ để tái hiện (chưa xong).

Các script phụ thêm: `tools/wine_bt.sh` (attach winedbg lấy bt), `tools/wine_dbg.sh` (break first-chance trong Xvfb).
