# Việt hoá chữ của Boom Online KR (cho engine Rust viết lại)

Mục tiêu: toàn bộ chữ của bản KR (patch Nexon 00967, 13 pack) sang tiếng Việt, dùng lại bản dịch có sẵn của bản VN.
Bản dịch dùng cho engine Rust viết lại (UTF-8, font vector), **không** patch vào client cũ.
Ảnh có chữ chỉ được liệt kê (`images_todo.csv`), không dịch.

## File

| File | Nội dung |
|---|---|
| `catalog.csv` | mỗi chuỗi một dòng: `id, source, ko, vi_base, vi, status, notes` (UTF-8, CSV chuẩn, xuống dòng giữ nguyên trong ô có ngoặc kép) |
| `tm.csv` | bộ nhớ dịch `ko → vi` (một chuỗi Hàn dịch một lần, dùng cho mọi id trùng chuỗi) |
| `tm_id.csv` | ghi đè theo `id` (khoá trùng bản VN nhưng nghĩa KR khác…) |
| `reused_review.csv` | các dòng lấy từ VN cần rà riêng: lệch placeholder/ngắt dòng hoặc nghi khác nghĩa KR; kèm câu Hàn, bản VN gốc và câu sau chỉnh giọng |
| `glossary_seed.csv` | thuật ngữ chốt tay (lấy từ bản VN: XU, VÀNG, BẠC, Siêu thị, Túi đồ, chế độ chơi…) |
| `glossary.csv` | seed + cặp ngắn rút từ catalog |
| `images_todo.csv` | ảnh có thể chứa chữ: `pack, entry, kind, size, dims, vn_same_name, reason` |
| `../tools/l10n_extract.py` | trích, ghép, xuất CSV; đọc pack bằng `tools/idf.py` (import, không copy) |

Quy trình:
```sh
python3 tools/l10n_extract.py sources     # quét KR + VN → l10n/.cache/sources.json (~25 s)
python3 tools/l10n_extract.py todo -n 300 /tmp/b01.tsv     # chuỗi Hàn chưa dịch: "n<TAB>ko" (\n, \r, \t escape)
#   dịch → /tmp/b01.vi.tsv: "n<TAB>vi[<TAB>status<TAB>notes]"
python3 tools/l10n_extract.py import /tmp/b01.vi.tsv       # gộp vào tm.csv
python3 tools/l10n_extract.py catalog     # → catalog.csv, glossary.csv, in thống kê
python3 tools/l10n_extract.py images      # → images_todo.csv (~20 s)
```
Đường dẫn mặc định: `--kr /home/admin/boom-re/boomKR`, `--vn ~/Downloads/Boom`,
`--kr-exe /home/admin/boomkr-re/out/kr-full.exe`, `--vn-strings /home/admin/boom-re/server/src/strings.rs`.

## 1. Nguồn chữ và cách đọc

Khoá pack: VN dùng `idf.KEYS`; KR dùng **khoá tự thân** = dword đầu `.idx` (`boomkr-re/docs/kr.md` §16). Tên entry cp949.

### KR

| Nguồn | Định dạng | Số chuỗi | Tag |
|---|---|---|---|
| `csysstr.ssd` (thư mục game) | `.ssd`: `"ssi1"`, u32 ?, u8 `0x18`, u32 comp_len, u32 raw_len @14, **zlib từ offset 0x12**. Raw: `u16 count`, count × (`u32 len + key cp949`, `u32 len + value cp949`). Là cache của FxClientString (S->C 2) | 8.442 | [VERIFIED] parse vừa khít, raw_len khớp |
| `FxDesktop/ClientData/ClientString` | `u32 len` + XML cp949 `<Elem><LangID>1042</LangID><key/><string/></Elem>` | 6.993 | [VERIFIED] |
| `csysqstr.ssd` | như csysstr (FxQuestString, S->C 12); cặp đầu có key rỗng | 7.845 | [VERIFIED] vừa khít |
| `csysfxmg.ssd` | raw: `u16 count`, count × (`u8 kind`, `u32 len + text`); tip hiển thị, có `{ComponentType\|N}` | 31 | [VERIFIED] vừa khít |
| `fxdynmapinfo.ssd` | raw: `u16 count`, mỗi record = `u32 id, u8 mode, lstr name, lstr display, u8, u8, lstr theme, lstr file, u8, u8, u32 color, u8, u8, u8, u16 idx, u8, u32` (cùng thứ tự với `dyn_map_blob` trong `server/src/maps.rs`). Lấy `display`, gộp theo `name` | 1.090 record → 773 map | [VERIFIED] vừa khít |
| `channel2_001.ssd` | raw: `u16 count`, count × (`lstr name`, 27 byte cấu hình kênh) | 48 | [VERIFIED] vừa khít |
| `spcc.ssd` | raw: `u16 count`, count × `lstr` = câu hỏi bảo mật; phần sau là mật khẩu cấm (`0000`, `1234`…) + URL | 12 | [VERIFIED] phần câu hỏi; phần sau [HYPOTHESIS] |
| `multisvr.ssd` | raw: `u8 count`, record (lstr name, lstr mô tả, …) – trường sau mô tả chưa rõ ⇒ quét mọi lstr có chữ Hàn | 3 | [HYPOTHESIS] |
| `fx/ObjectTable/SpeakerTable` | `u32 len` + Excel 2003 XML (UTF-8); cột 2 `Name` = tên loại loa | 63 | [VERIFIED] |
| `FxDesktop/Help/Help` | text cp949, CRLF; mỗi dòng một id (`…:Help/Help:<số dòng>`) | 80 | [VERIFIED] (VN cũng là bản Hàn y hệt) |
| `FxDesktop/Quest/c*` | script Lua cp949; lấy literal `"…"` có chữ Hàn (`StringData.QuestName = "…"`) | 48 | [VERIFIED] |
| `fx/CustomMap/CustomTileList`, `CustomMap_*` | `u32 len` + XML **UTF-8**; thuộc tính `Desc`/`Name`/`Title` (mô tả ô gạch trong trình tạo map) | 2.174 | [VERIFIED] |
| `FxMap/Map/*` (`.map`) | khối `<mapscript>` cp949 sau lưới; thuộc tính `sayNN` của action `Say` (bong bóng thoại). Bỏ comment `<!-- -->`, `#…` và tên action list | 56 | [VERIFIED] |
| `FxStage/StageCredit/Credit` | text cp949, lệnh `#ChangeColor`; tên người giữ nguyên | 183 | [VERIFIED] |
| `FxDesktop/NoticeImg/Contract`, `Notice2PW` | text cp949: điều khoản Nexon/NHN, đồng ý thu thập dữ liệu | 2 khối | [VERIFIED]; **không dịch** (status `review`): thay bằng điều khoản của dự án |
| `CA.exe` (image đã unpack `boomkr-re/out/kr-full.exe`, chỉ đọc) | chuỗi C cp949 kết thúc NUL, ≥ 3 âm tiết Hàn liền nhau (lọc nhiễu khi đọc code thành chữ). Chuỗi debug/dev gắn `notes=dev_debug` | 134 | [VERIFIED] một phần: lọc heuristic, có thể sót chuỗi ngắn ≤ 2 âm tiết |

Không phải chữ hiển thị (bỏ qua): `Attr/*` (chỉ đường dẫn resource, [VERIFIED]), `ObjectTable` (tên object),
`MapScriptTemplate/*` (chỉ comment dev + 1 file test), `Pet/*`, `MotionBlur/*` (comment), `RPG/SkillTable`,
`SandBox/GadgetTable` (comment `#`), `fxstagemap.ssd`, `fxdynimginfo.ssd` (đường dẫn ảnh), `Etc/FxLang`
(bảng `ISTF`, giống hệt VN, chưa giải – [HYPOTHESIS] bảng IME/ngôn ngữ), `filterstr.ssd` (danh sách từ cấm, không dịch).

### VN (nguồn `vi_base`)

| Nguồn | Định dạng | Số chuỗi | Ghép |
|---|---|---|---|
| `fx/ClientData/ClientString` | `u32 len` + BOM `FF FE` + XML **UTF-16LE**, `LangID 1066`; chỉ có lời thoại NPC/monster | 4.307 (4.305 khoá) | theo `key` [VERIFIED] |
| `server/src/strings.rs` (boom-re) | chuỗi UI tự viết của dự án (client VN không có chuỗi UI; server cũ gửi qua S->C 2) | ~150 | theo `key`; nhiều nhãn lệch nghĩa KR ⇒ ghi đè ở `tm_id.csv`, status `review` |
| `fx/Map/*` `<mapscript>` | VN thay `sayNN="chữ Hàn"` bằng **khoá ClientString** (`say01="mongolem12default14"`) | — | cùng entry + cùng thứ tự thuộc tính → tra khoá trong ClientString VN [VERIFIED] |
| `CA.exe` VN | chuỗi cứng vẫn là tiếng Hàn (121 chuỗi); `.rsrc` RT_STRING chỉ có thông báo GameGuard (tiếng Trung) và 2 lỗi đăng nhập tiếng Hàn | — | không có bản Việt |

## 2. Quy tắc ghép và trạng thái

- `id`: khoá gốc cho FxClientString (csysstr + ClientString chung không gian khoá); `q:<khoá>` cho FxQuestString;
  `map:<tên map>`; còn lại `pack:entry:chỉ số` hoặc `file.ssd:chỉ số`, `exe:kr-full.exe:0x<offset>`.
- Khoá có ở cả `csysstr` và `ClientString` KR mà giá trị khác nhau ⇒ thêm dòng `<khoá>@ClientString` (`notes=dup_key_diff`).
- Khoá chỉ có ở VN ⇒ dòng `source=vn-only:…`, `ko` rỗng (giữ bản dịch).
- `reused`: lấy nguyên văn `vi_base`. `review` nếu placeholder printf/`{…}`/tag lệch (`kr_changed?`) hoặc ghi đè ở `tm_id.csv`.
- `translated`: dịch mới Hàn → Việt (`tm.csv`). `review`: chưa chắc nghĩa / chưa dịch (`untranslated`) / văn bản pháp lý.
- Giữ nguyên `%s %d %u…`, `{ComponentType|N}`, `<font …>`, `\r\n`, `|` (ngắt dòng của multisvr); lệch ⇒ `placeholder_mismatch`, `review`.
- `too_long?`: `len(vi) > 1,6 × len(ko)` (tính theo ký tự; chữ Hàn rộng gấp ~2 nên cờ này nhiều, chỉ là gợi ý kiểm tra khung UI).

## 2b. Giọng miền Nam

Bản dịch dùng **giọng và từ ngữ miền Nam** (yêu cầu của chủ dự án): nón (không phải mũ), bóp (ví), ba mẹ, tui/tụi tui,
nha/ha/ta (nhé/nhỉ), đó/vậy cuối câu (đấy/thế), lượm (nhặt), rớt (rơi), mắc (đắt), heo, bắp, ly, chén, muỗng, gởi, lầu, mở/tắt…

- Mọi bản dịch được viết tay (đọc và dịch trực tiếp), **không** đổi từ tự động bằng code.
- Chuỗi `reused` từ bản VN gốc (giọng Bắc) được đọc lại và viết lại giọng Nam trong `tm_id.csv`
  (`notes=nam_bo_rewrite`); cột `vi_base` giữ nguyên văn bản VN để đối chiếu.

## 3. Ảnh có chữ (`images_todo.csv`)

Quét mọi entry sprite (`CDataI16Alpha` v2) và JPEG trong 13 pack KR. Heuristic theo tên entry (token đứng đầu đoạn
`/ _ -` hoặc sau chữ thường/số và trước chữ hoa/số/`_`/hết tên):
`Bt_ Bt Btn Button Dlg_ Dlg Title Tab Txt Text Banner Logo Result Notice Tooltip ToolTip Msg Popup Name Word Label
Menu Rank Win Lose Draw Start Ready Help Guide Tutorial Event Font Num Digit Info Intro Mission Quest Ending Clear
Fail Success Ok Cancel Close Confirm`, cộng `hangul_name` (tên có chữ Hàn) và `jpg_background` (mọi JPEG: nền stage
thường có chữ). `dims` = `rộng x cao × số ảnh` của ảnh đầu. `vn_same_name`: `no` (VN không có entry cùng tên),
`same_bytes` (VN dùng y hệt ảnh KR ⇒ không có bản Việt), `diff_bytes` (VN có ảnh khác ⇒ **có thể dùng ảnh VN**).
OCR: máy có `tesseract` nhưng chỉ có `eng`/`osd`, **không có `kor`** ⇒ không có cột `ocr_ko`.

## 4. Font

Không dùng `.fft` bitmap cũ (`CxUni*.fft`, `CxDefault.fft`). Đề xuất (OFL 1.1, chưa đưa vào repo):

- **Chữ Việt (chính): `Be Vietnam Pro`** — thiết kế riêng cho tiếng Việt (dấu chồng, `ơ ư` cân), nhiều độ đậm, hợp
  giao diện game tròn trịa; dự phòng **`Noto Sans`** (phủ Latin Extended Additional đầy đủ, metric ổn định).
- **Fallback Hàn: `Noto Sans KR`** (bao toàn bộ 11.172 âm tiết Hangul + KS X 1001) cho tên riêng giữ chữ Hàn
  (credit, tên người chơi), cùng họ Noto nên chiều cao chữ x khớp với `Noto Sans`.
- Ghép bằng font fallback chain (vd. `cosmic-text`/`fontdue` + danh sách `[Be Vietnam Pro, Noto Sans, Noto Sans KR]`);
  chuẩn hoá chuỗi về **NFC** trước khi shape (bản VN cũ ghi dấu dạng tổ hợp cp1258).

## 5. Thống kê

Cập nhật 2026-10-19, sau H000–H041 và R000–R014:

| Trạng thái | Số dòng |
|---|---:|
| Tổng | 25.257 |
| `translated` | 20.414 |
| `reused` | 3.813 |
| `review` | 1.030 |
| `untranslated` | 0 |

Đã xử lý đủ 4.356 ID trong 15 đợt chuyển giọng R000–R014, gồm cả các dòng bị loại ở lần nhập trước.
1.035 câu có ghi đè `nam_bo_rewrite` trong `tm_id.csv`; câu đã phù hợp giữ nguyên.
`vi_base` và câu Hàn giữ nguyên theo cache nguồn, kể cả ký tự CR/LF.
Các câu được đọc và viết lại riêng; code chỉ ghép kết quả theo ID và kiểm tra, không thay từ tự động.

Số `review` tăng từ 487 lên 1.030 vì đánh dấu thêm 543 dòng lấy từ bản VN:
313 dòng lệch placeholder/ngắt dòng so với KR và 230 dòng cần đối chiếu nghĩa
(đặc biệt các nhóm NPpen22–NPpen27). Đây là vấn đề có sẵn trong bản VN; phần chuyển giọng
giữ ý bản VN, chưa dịch lại các nhóm này. Danh sách cụ thể nằm trong `reused_review.csv`.
Một số kết quả R000–R005 đã sửa nghĩa trước khi tiếp quản (ví dụ “Ta sẽ đối đầu”)
được giữ lại; thống kê này không khẳng định mọi câu đã được duyệt nghĩa.

Ba tên AI đã chốt vẫn dùng đúng: **Chiến binh huyền thoại**, **White Angel**, **Mister Fortune**;
các tên này đã có trong prompt H. Tên cá đã dịch ở H032 giữ nguyên.

Kiểm tra lại từ gốc repo:

```sh
python3 tools/l10n_extract.py catalog
python3 tools/l10n_validate.py
```

Bộ kiểm tra đối chiếu ID, câu Hàn và `vi_base` với cache nguồn; kiểm tra ghi đè,
placeholder/thứ tự printf/ngắt dòng của các câu chuyển giọng so với `vi_base`,
ba tên AI và từ cấm trên toàn catalog. Kết quả cuối: **0 lỗi kiểm tra, 0 từ cấm**.
Các khác biệt KR/VN được đánh dấu `review` vẫn cần rà nội dung riêng.
