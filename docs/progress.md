# Tiến độ & handoff (cập nhật 2026-10-17)

File này dành cho **người mới vào dự án**: đọc từ trên xuống là biết đang ở đâu, chạy thử thế nào, việc gì còn dở.
Chi tiết kỹ thuật từng bước nằm ở các file khác (link ở từng mục).

---

## 1. Tóm tắt 1 phút

- Game: **Boom Online** (VNG, bản Việt của *Crazy Arcade / BnB*). Server gốc đã chết; ta dịch ngược client để viết
  **server giả lập**. Hiện server giả là `tools/fakeserver.py` (Python); sau này viết lại bằng **Rust**.
- Client gốc bị pack Themida. Ta dùng **bản dump đã unpack + sửa** (`ca_fixed_patched.exe`) chạy trong **Wine**.
- **Đã chạy được:** đăng nhập → chọn kênh → sảnh (quảng trường) → tạo phòng → phòng chờ có người chơi, có map,
  nút BẮT ĐẦU bật → server gửi lệnh bắt đầu trận → client tạo màn trận (stage 13).
- **Đang kẹt:** client crash khi **nạp map lúc vào trận**, chỗ crash nằm trong vùng code còn bị Themida bảo vệ
  (xem [mục 5](#5-chỗ-đang-kẹt-vào-trận)). **Người dùng (chủ dự án) đang tự phân tích phần này** — người khác/Claude
  không đụng vào cho tới khi chủ dự án giao lại.

---

## 2. Bản đồ tiến độ

Game chia thành các "stage" (màn). Client ghi stage hiện tại vào `wine/Boom/CALog.log` dạng `Sg - INT(dne:N)`.

| Stage | Màn | Trạng thái | Ảnh minh hoạ |
|---|---|---|---|
| 1 | Khởi động, intro | ✅ | — |
| 10 | Đăng nhập + chọn kênh (`CSelectServerStage`) | ✅ kênh tự hiện, click vào kênh được | `docs/channel_autoshow.png` |
| 11 | Sảnh quảng trường (`CLobbySquareStage`) | ✅ load xong, nút TẠO PHÒNG chạy | `docs/lobby_loaded.png`, `docs/create_room_dialog.png` |
| 12 | Phòng chờ (`CPrepareStage`) | ✅ có người chơi (trưởng phòng), map Village01, nút BẮT ĐẦU bật | `docs/waiting_room_start.png`, `docs/map_dialog_village.png` |
| 13 | Trận đấu (`CGameStage`) | ❌ crash khi nạp map | — |

Những phần **chưa làm** ở các màn đã qua (không chặn đường vào trận):
- Hộp thoại **chọn map** trong phòng liệt kê 0 map (báo "CantDecideMap"). Server đang tự gán map cho phòng.
- Server chỉ khai báo **3 map** (Village01, Forest01, Camp01) — chưa có danh sách đầy đủ, chưa rõ map có khoá theo cấp
  nhân vật không.
- Danh sách người trong sảnh, danh sách phòng: đang gửi rỗng.
- Nhiều người chơi, đội, nhân vật, sẵn sàng: chưa làm (mới 1 người chơi).

---

## 3. Chạy thử từ đầu

### 3.1 Cần có trên máy (không nằm trong git)
Xem bảng "File không có trong git" trong [README](../README.md#file-không-có-trong-git-nặng--bản-quyền--đang-nằm-trên-máy).
Tối thiểu: `unpacked_ca.exe`, thư mục `wine/Boom/` (bản copy client), Wine, `Xvfb`, `xdotool`, `import` (ImageMagick), `uv`.

### 3.2 Build bản client chạy được
```sh
cd ~/boom-re
tools/rebuild_wine.sh          # unpacked_ca.exe → fix IAT → devirt → patch → wine/Boom/ca_fixed_patched.exe
```
Phải chạy lại mỗi khi sửa `tools/devirt.py` hoặc `tools/patch_client.py`.

### 3.3 Chạy server giả
```sh
python3 tools/fakeserver.py --log logs/fakeserver_host.log &
```
Biến môi trường (đặt trước lệnh):

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `ROOM_TYPE` | 19 | Loại phòng trong gói tạo phòng (83). Loại 19 cho **1 người** bắt đầu được |
| `MAP_INDEX` | 0 | Map của phòng = chỉ số trong `BATTLE_MAPS` (0 Village01, 1 Forest01, 2 Camp01) |
| `AUTO_START` | 0 | > 0: server tự gửi lệnh bắt đầu trận (501) sau N giây kể từ lúc vào phòng chờ |

Log server (mọi gói vào/ra, đã giải mã) ở `logs/fakeserver_host.log`.

### 3.4 Chạy client tự động (Xvfb, không cần màn hình)
```sh
tools/xvfb_join.sh                       # đăng nhập (tester/1234) → chờ màn kênh → click "Kenh 1" → vào sảnh
# vào sảnh → đóng hướng dẫn → TẠO PHÒNG → XÁC NHẬN → phòng chờ:
CLICKS="975,38,3 385,50,4 437,612,10 512,384,8" tools/xvfb_join.sh
```
- `CLICKS="x,y,giây ..."`: sau khi vào sảnh, click lần lượt từng toạ độ rồi chờ số giây; mỗi click chụp `logs/xvfb/click_<i>.png`.
- Kết quả đúng: `wine/Boom/CALog.log` có lần lượt `dne:10`, `dne:11`, `dne:12`.
- Muốn thử vào trận: chạy server với `AUTO_START=5`, rồi chạy lệnh CLICKS ở trên → hiện tại client sẽ crash sau 501.

### 3.5 Debug (gdb)
`tools/wine_gdb.sh <file_lệnh_gdb>` chạy client dưới `winedbg --gdb` + gdb, tự đăng nhập; `JOIN=1` để click vào kênh,
`CLICKS=` như trên. Kết quả ở `logs/xvfb/gdb.txt`. Dưới gdb mọi thứ chậm ~3 lần. Chi tiết:
[docs/runtime.md](runtime.md), memory `reference-winedbg-gdb`.

---

## 4. Luồng gói tin đã làm (theo thứ tự xảy ra)

"C→S" = client gửi lên, "S→C" = server trả về. Hàm tạo gói nằm trong `tools/fakeserver.py`.
Định dạng khung, mã hoá, cách đọc số/chuỗi: [docs/protocol.md](protocol.md).

| Bước | C→S | S→C (hàm trong fakeserver) | Ghi chú |
|---|---|---|---|
| Kết nối | — | hello (`hello_packet`) | version 116 |
| Chào | 0 | 13, 2, 12, 21, 1, 43 (`login_replies`) | mỗi gói `u8 0` |
| Đăng nhập | 1 | 4 (`login_ok`), 15 (`login_net_info`) | id người chơi = 1000+i, phải khớp gói 103 |
| Vào màn kênh | 40 | 14 (`channel_list`), 16 (`channel_status`) | ô kênh cần kind=18; số người tối đa là u32 |
| Chọn kênh | 5 | 7 (`channel_join_ok`) | trỏ client tới "server kênh" (chính ta) |
| Đăng nhập kênh | 6 | 17 (`channel_enter_ok`) | → stage 11 |
| Vào sảnh | 395 | 466 (`square_info`), 467 (`square_users`), 88 (`room_list`), 234 (`map_checksums`), 231 (`dyn_map_info`) | 88 bắt buộc, thiếu thì nút TẠO PHÒNG không chạy |
| Tạo phòng | 77 | 83 (`create_room_ok`) | → stage 12 |
| Vào phòng chờ | 337 | 103 (`room_player`), 106 (`room_slot_state`), 113 (`room_map`) | trưởng phòng, ô 0, map |
| Bấm BẮT ĐẦU | 97 | 501 (`match_start`) | hoặc server tự gửi 501 (`AUTO_START`) |

Chi tiết + địa chỉ hàm client của từng bước: [docs/lobby.md](lobby.md) (mục "Cập nhật 5" → "Cập nhật 12").

---

## 5. Chỗ đang kẹt: vào trận

**Do chủ dự án tự xử lý — đừng làm phần này khi chưa được giao.**

Những gì đã biết:
- Client nhận 501, gửi 298, tạo `CGameStage` (stage 13).
- Trong lúc tạo màn trận có một khối VM `sub_9682DE` (0x9682E5). Đã thay tạm bằng code viết tay trong `tools/devirt.py`
  (suy ra từ hàm khởi tạo/huỷ, **chưa kiểm bằng trace** — có thể sai).
- Sau đó client crash trong vùng VM khi nạp map: backtrace đi qua 0x6ED8A6 → phần nạp map của `CGamePlayMap__Load`
  (khối VM bắt đầu trong hàm ở 0x736C27). Đây là vùng còn bị Themida bảo vệ.
- Ghi chép trước đó: [docs/lobby.md](lobby.md) "Cập nhật 12".

Sau khi qua được chỗ này, việc tiếp theo là làm các gói trong trận — agent `e-game` đã soạn sẵn (mục 7), có phần
"5d Minimum server để trận chạy".

---

## 6. Việc tiếp theo (theo thứ tự ưu tiên)

1. **[chủ dự án]** Qua chỗ crash nạp map (mục 5).
2. **Mở đủ map** (làm được ngay, không phụ thuộc mục 5):
   - Thay 3 map tự soạn trong `BATTLE_MAPS` bằng danh sách đầy đủ: client nạp mọi mục `Map/*` trong pack `fx.idx` theo
     thứ tự chữ cái (1019 mục) → chỉ số = vị trí trong danh sách đó (`tools/idf.py` đọc được pack).
   - Làm cho hộp thoại chọn map liệt kê được: lỗi nằm ở bước nhóm map (bộ lọc `sub_6DEE48` đã cho qua cả 3 map).
   - Tìm xem map có khoá theo cấp nhân vật không (chưa ai phân tích; nghi ở gói map riêng của người chơi cho loại phòng 14,
     hoặc gói 231).
3. **Audit tài liệu của agent OpenCode** trước khi dùng (mục 7).
4. Kiểm lại `sub_9682DE` bằng trace thật.
5. Làm các gói trong trận theo `docs/oc_e-game.md` (sau mục 1).
6. Sảnh/phòng đầy đủ: danh sách người, danh sách phòng, nhiều người chơi (`docs/oc_c-square.md`, `docs/oc_a-room.md`).
7. Viết server thật bằng Rust, dùng `tools/fakeserver.py` + `docs/` làm đặc tả.

---

## 7. Tài liệu do agent OpenCode viết

Agent OpenCode (model `opencode/glm-5.3-flash-free`) phân tích tĩnh bằng IDA, mỗi agent một file. Đã merge vào `main`.
**Agent hay sai offset/định dạng — phần chưa audit phải đối chiếu IDA trước khi đưa vào server.**

| File | Nội dung | Audit |
|---|---|---|
| `docs/oc_d-login.md` | gói đăng nhập 4 + 15 từng field | ✅ đã kiểm, đã dùng |
| `docs/oc_a-room.md` | phòng chờ: 87/97, 94, 501 | 🟡 mới kiểm định dạng 501 |
| `docs/oc_c-square.md` | sảnh quảng trường: 466–481, 492, 613–625… | ⬜ chưa kiểm |
| `docs/oc_e-game.md` | màn trận: hàm vào màn, bảng gói, 189/356/146/571, server tối thiểu | 🟡 mới kiểm đường gọi vào màn (khớp backtrace thật) |

Chạy lại agent: `~/boom-re-oc/launch.sh <task>` (mỗi task một worktree `~/boom-re-oc/<task>`, branch `oc/<task>`, đề bài ở
`~/boom-re-oc/prompts/`). Dừng tất cả: `pkill -f '[o]pencode run --standalone'`.
Bài học: dặn agent **ghi file dần và commit sau mỗi 2–3 mục**, nếu không nó dễ chết vì hết token lúc tóm tắt.

---

## 8. Sửa client đang áp dụng

Tất cả nằm trong pipeline `tools/rebuild_wine.sh`, không sửa tay file exe.

| Sửa gì | Ở đâu | Vì sao |
|---|---|---|
| Sửa IAT | `tools/fix_iat.py` | bản dump không có bảng import đúng |
| Thay khối VM bằng code viết tay (`BLOCKS`) | `tools/devirt.py` | VM Themida không chạy được trong bản dump; quy trình: [docs/devirt.md](devirt.md) |
| Hook: kênh tự hiện (`HOOKS`, sau `On_16`) | `tools/devirt.py` | gốc phải click mới vẽ lại ô kênh |
| Tắt HackShield, bỏ kiểm patch, đổi IP server | `tools/patch_client.py` | chạy với server giả |
| Khôi phục 10 byte hỏng ở 0x592C09 | `tools/patch_client.py` | bản dump hỏng ở đây → crash khi nạp map sảnh |

---

## 9. Bẫy thường gặp

- `pkill -f ca_fixed_patched` có thể **giết luôn shell** đang chạy lệnh (chuỗi khớp chính nó) → dùng `'[c]a_fixed_patched'`.
- Còn tiến trình client cũ thì client mới không chạy (mutex) → các script đã tự pkill trước.
- `/proc/<pid>/mem` không đọc được trong Wine kiểu WoW64 mới → dùng gdb (`tools/wine_gdb.sh`).
- Số trong pseudocode Hex-Rays là **thập phân**.
- Sự kiện bấm nút **không** đi qua `CStage::vf5`, mà qua `CCtrlButton__vf14` → hàm xử lý của cửa sổ cha (`docs/lobby.md` "Cập nhật 8").
- Số đọc từ gói bị XOR theo kích thước (u8 0x5A, u16 0xA569, u32 0x96CA5395, u64 0x71B18589) — `obf_body()` lo phần này.
- Commit cũ có trailer "Claude Opus 4.8" có vài lỗi offset đã sửa: xem "Errata audit" trong `docs/lobby.md`.

---

## 10. Từ điển nhanh

| Từ | Nghĩa |
|---|---|
| opcode | số đầu gói tin, xác định loại gói; hàm xử lý phía client tên `On_<opcode>` |
| stage | màn chơi (10 kênh, 11 sảnh, 12 phòng chờ, 13 trận) |
| bản dump | `unpacked_ca.exe`: client đã gỡ Themida, chạy được sau khi qua `rebuild_wine.sh` |
| khối VM | đoạn code Themida biến thành bytecode riêng; trong bản dump không chạy được, phải viết lại (`devirt.py`) |
| CALog | `wine/Boom/CALog.log`, log của client; `dne:N` = đã vào stage N |
