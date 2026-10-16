# Devirtualize hàm bị Themida ảo hoá (hướng 1)

Mục tiêu: chạy được bản dump `ca_fixed.exe` (không còn Themida) trong Wine trên host có GPU.
IAT đã sửa xong (`docs/runtime.md` → "Sửa IAT"). Việc còn lại là các đoạn code bị Themida ảo hoá.

## Trạng thái (2026-10-16)

- ✅ **Bản dump chạy được trong Wine trên host (GPU), mở cửa sổ game và đăng nhập vào `tools/fakeserver.py`** (127.0.0.1).
- Đã devirtualize: **1 khối** (`sub_8F4421` site 0x8F452B) — xem [Khối đã xong](#khối-đã-xong).
- Sửa thêm: unlicense nhầm `CreateWindowExW` ↔ `CreateWindowExA` (cửa sổ chính không tạo được → `CSysException "CreateWindow failed"`).
- Các khối VM khác chưa bị chạm tới trên luồng khởi động → làm khi gặp (lobby, phòng, ván chơi sẽ chạm `CGamePlayMap__Load`, `CGOBomber__vf21`…).

## Khối đã xong

### 0x8F452B — `sub_8F4421` (bước khởi tạo trong `CFxApp__InitMain`)
- Ranh giới: site 0x8F452B → tiếp tục ở **0x8F45A7** (`lea ecx,[esi+14h]; push ebx; call 0x413F32`). Byte giữa là rác.
- Quan sát (`tools/vmtrace.py`, client gốc trong WinBoat): thanh ghi edi/esi/ebp/ebx giữ nguyên; eax/ecx chết. Bộ nhớ:
  - `0xEED860[256]` = bảng CRC32 reflected, poly **0xDD10EC81** (chỉ code Themida ở 0x1330A69 đọc);
  - `0xEEE07C = 0x4A65000A`, `0xEEE088 = 1`, `0xEEE08C = GetTickCount()` (không có xref từ code game);
  - `0xEEE650..65C` = callback `0x8F2C5D, 0x8F30F7, 0x8F2C4F, 0x8F31F6` (nhiều hàm game gọi, ví dụ `sub_413F32`).
- Viết lại: `tools/devirt.py` `BLOCKS[0]` (dữ liệu ghi thẳng vào image + `GetTickCount` lúc chạy).

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

## Chẩn đoán màn hình logo (2026-10-16)

Bản dump dừng ở logo Nexon/VNG. Thực chất process thoát mã 9 (`App__SetExitError(9)`), không treo.

- CALog: `116 : InitBeforePatch` rồi dừng.
- winedbg (break first-chance): page fault `EIP=0x1388`, tức một `call [reg+N]` với con trỏ rác.
- Nguồn: `CStageMgr__ChangeStage` (`0x8F8EEC`) có một khối ở site `0x8F8F69` (tiếp tục ở `0x8F9392`) chưa viết lại → cần làm block thứ 2.
- Đã quan sát block này trên client gốc: `tools/vmtrace.py build 8F8F69 8F9392`, dump ở `logs/vmtrace/8F8F69/dump.bin`.
  - reloc (5 byte site đè): `call 0x9DB5B7`; điểm tiếp tục thật là epilog `0x8F9392` (call `__EH_epilog3`), back `0x8F9397`.
  - Hàm ngữ cảnh: chuyển stage (Login → SelectServer → Lobby…). vtable stage: `CLoginStage` ctor `0x84F4A7`, `CStage` ctor `0x6A588F`.
  - diff: nhiều thay đổi trên object `CMainWnd` ([esi]) + ~18 dword global; cần đọc kỹ để tái hiện (chưa xong).

Các script phụ thêm: `tools/wine_bt.sh` (attach winedbg lấy bt), `tools/wine_dbg.sh` (break first-chance trong Xvfb).
