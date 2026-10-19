# Việt hoá chữ của Boom Online KR (cho engine Rust viết lại)

Mục tiêu: toàn bộ chữ của bản KR (patch Nexon 00967, 13 pack) sang tiếng Việt, dùng lại bản dịch có sẵn của bản VN.
Bản dịch dùng cho engine Rust viết lại (UTF-8, font vector), **không** patch vào client cũ.
Ảnh nghi có chữ được thống kê (`images_todo.csv`) và có trang duyệt KR/VN;
chưa vẽ lại hoặc Việt hóa ảnh. Xem [hướng dẫn duyệt ảnh](../docs/l10n-image-review.md).

## File

| File | Nội dung |
|---|---|
| `catalog.csv` | mỗi chuỗi một dòng: `id, source, ko, vi_base, vi, status, notes` (UTF-8, CSV chuẩn, xuống dòng giữ nguyên trong ô có ngoặc kép) |
| `tm.csv` | bộ nhớ dịch `ko → vi` (một chuỗi Hàn dịch một lần, dùng cho mọi id trùng chuỗi) |
| `tm_id.csv` | ghi đè theo `id` (khoá trùng bản VN nhưng nghĩa KR khác…) |
| `reused_review.csv` | các dòng lấy từ VN còn cần rà sau đợt sửa nghĩa mới nhất |
| `review_audit.csv` | đối chiếu trước/sau và quyết định duyệt cho toàn bộ 1.030 dòng review ban đầu, cộng 15 câu hỏi được bản địa hóa |
| `review_pending.csv` | toàn bộ dòng hiện còn `review`, kèm lý do cụ thể |
| `quiz_vi.csv` | 15 câu đố chơi chữ Việt, bốn lựa chọn và vị trí đáp án đúng tương ứng câu Hàn |
| `QUIZ_VI.md` | bản đọc câu đố dân gian ĐBSCL, có lời giải, vùng miền và ghi chú câu phỏng theo |
| `glossary_seed.csv` | thuật ngữ chốt tay (lấy từ bản VN: XU, VÀNG, BẠC, Siêu thị, Túi đồ, chế độ chơi…) |
| `glossary.csv` | seed + cặp ngắn rút từ catalog |
| `images_todo.csv` | ảnh có thể chứa chữ: `pack, entry, kind, size, dims, vn_same_name, reason` |
| `../docs/l10n-image-review.md` | cách mở trang ảnh KR/VN, duyệt, xuất/nhập kết quả và tạo lại trang |
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
- Sau khi chủ dự án xác nhận bản VN có câu sai nghĩa, đã rà theo **câu Hàn** và sửa trong
  `tm_id.csv` (`ko_reviewed`). Các câu này có thể khác ý bản VN cũ; `vi_base` vẫn giữ nguyên.
- Theo yêu cầu mới, câu đố chính tả/chơi chữ Hàn được thay đồng bộ bằng câu đố chơi chữ Việt,
  giữ nguyên ID và vị trí lựa chọn đúng (`quiz_vi_localized`).

## 3. Ảnh có chữ (`images_todo.csv`)

Quét mọi entry sprite (`CDataI16Alpha` v2) và JPEG trong 13 pack KR. Heuristic theo tên entry (token đứng đầu đoạn
`/ _ -` hoặc sau chữ thường/số và trước chữ hoa/số/`_`/hết tên):
`Bt_ Bt Btn Button Dlg_ Dlg Title Tab Txt Text Banner Logo Result Notice Tooltip ToolTip Msg Popup Name Word Label
Menu Rank Win Lose Draw Start Ready Help Guide Tutorial Event Font Num Digit Info Intro Mission Quest Ending Clear
Fail Success Ok Cancel Close Confirm`, cộng `hangul_name` (tên có chữ Hàn) và `jpg_background` (mọi JPEG: nền stage
thường có chữ). `dims` = `rộng x cao × số ảnh` của ảnh đầu. `vn_same_name`: `no` (VN không có entry cùng tên),
`same_bytes` (VN dùng y hệt ảnh KR ⇒ không có bản Việt), `diff_bytes` (VN có ảnh khác ⇒ **có thể dùng ảnh VN**).
OCR: máy có `tesseract` nhưng chỉ có `eng`/`osd`, **không có `kor`** ⇒ không có cột `ocr_ko`.

Đã có trang duyệt trực quan tại **`l10n/.cache/image-review/index.html`**: mở trực tiếp
bằng trình duyệt, không cần server. Trang đặt KR/VN cạnh nhau, có lọc, xem đủ ảnh con,
phóng lớn, ghi chú và xác nhận đã có tiếng Việt/cần dịch/không có chữ. Kết quả lưu tại
trình duyệt; bấm **Xuất kết quả CSV** để giữ và nhập vào dự án. Hướng dẫn đầy đủ:
[Duyệt ảnh KR–VN](../docs/l10n-image-review.md).

Mở terminal và chạy:

```sh
xdg-open /home/admin/boom-re-l10n/l10n/.cache/image-review/index.html
```

Sau kiểm tra cấu trúc, đã loại 4 dữ liệu bản đồ bị nhận nhầm thành ảnh. Danh sách còn
**3.038 ứng viên**: 681 khác bản VN, 1.113 giống bản VN, 1.244 không có bản VN cùng tên.
Đã xuất **8.750 ảnh con**, không lỗi giải mã. Chưa có xác nhận ảnh đã dịch từ người duyệt;
không tự suy ra trạng thái dịch từ khác biệt byte.

```sh
python3 tools/l10n_images_review.py
# Mở l10n/.cache/image-review/index.html bằng trình duyệt.
python3 tools/l10n_images_review.py --import-csv /duong/dan/images_review.csv
```

## 4. Font

Không dùng `.fft` bitmap cũ (`CxUni*.fft`, `CxDefault.fft`). Đề xuất (OFL 1.1, chưa đưa vào repo):

- **Chữ Việt (chính): `Be Vietnam Pro`** — thiết kế riêng cho tiếng Việt (dấu chồng, `ơ ư` cân), nhiều độ đậm, hợp
  giao diện game tròn trịa; dự phòng **`Noto Sans`** (phủ Latin Extended Additional đầy đủ, metric ổn định).
- **Fallback Hàn: `Noto Sans KR`** (bao toàn bộ 11.172 âm tiết Hangul + KS X 1001) cho tên riêng giữ chữ Hàn
  (credit, tên người chơi), cùng họ Noto nên chiều cao chữ x khớp với `Noto Sans`.
- Ghép bằng font fallback chain (vd. `cosmic-text`/`fontdue` + danh sách `[Be Vietnam Pro, Noto Sans, Noto Sans KR]`);
  chuẩn hoá chuỗi về **NFC** trước khi shape (bản VN cũ ghi dấu dạng tổ hợp cp1258).

## 5. Thống kê

Cập nhật 2026-10-19, sau lượt đối chiếu và sửa nghĩa theo câu Hàn:

| Trạng thái | Số dòng |
|---|---:|
| Tổng | 25.257 |
| `translated` | 21.421 |
| `reused` | 3.813 |
| `review` | 23 |
| `untranslated` | 0 |

Đã rà toàn bộ **1.030 dòng review** của đợt trước: 1.007 dòng đã được chốt, 23 dòng
còn cần thêm ngữ cảnh hoặc xử lý dữ liệu nguồn. Đồng thời bản địa hóa thêm 15 câu hỏi
để khớp với 60 phương án chính tả tiếng Hàn, thành **15 câu đố chơi chữ tiếng Việt**.

`review_audit.csv` ghi đủ 1.045 dòng được xử lý, trong đó 746 dòng đổi nội dung hoặc
định dạng và 299 dòng giữ nguyên văn bản sau kiểm tra. Mọi câu Hàn và `vi_base` giữ nguyên
so với nguồn, kể cả CR/LF. Không thay từ tự động bằng code; code chỉ nhập các quyết định
viết riêng theo câu, phục hồi kiểu ngắt dòng nguồn, xuất báo cáo và kiểm tra.

Các lỗi đã sửa gồm: đảo chủ thể thắng/thua, nhầm bị phản bội thành phản bội người khác,
nhầm phép nhân thành phép cộng, lấy câu Việt không liên quan trong NPpen22–NPpen27,
thiếu ngắt dòng, thiếu thẻ font và nhầm đơn vị `개` thành “Chó”. Các tên riêng khác
không có trong bảng chốt được giữ theo quy tắc phiên âm Latin.

Theo yêu cầu mới, bộ câu đố dùng **dân gian ĐBSCL** từ nội dung chủ dự án cung cấp:
8 câu về sản vật/sông nước, 4 câu đố láy từ và 3 câu đố tục giảng thanh.
Giữ cách nói như quày cau, dĩa dầu, dầm, cẳng; lời giải đều là sản vật, con vật hoặc
đồ vật gần gũi. Hai câu về cỏ năng và khô/mắm được thêm vế thơ và ghi rõ “phỏng theo”.
Không gán phần thêm vào cho nguyên bản dân gian. Các cặp lời giải khô/mắm và dầm/chèo
được gộp trong cùng một lựa chọn để không có hai đáp án đúng.

Trong `quiz_vi.csv`, mỗi câu lưu câu Hàn gốc, đáp án Hàn đúng, vị trí từ 1–4, bộ câu hỏi/
lựa chọn Việt, lời giải dự kiến, loại đố, vùng miền và ghi chú nguồn. Bản đọc dễ duyệt
nằm ở `QUIZ_VI.md`. Vị trí đúng giữ theo phương án Hàn gốc, không đảo thứ tự khóa trả lời.
Câu thơ có ngắt dòng riêng; bộ kiểm tra cho phép thay ngắt dòng ở nhóm bản địa hóa này,
nhưng vẫn kiểm tra placeholder, thẻ và nội dung khớp bộ câu đố đã chốt.
Đây là kiểm tra dữ liệu; chưa chạy thử luồng câu đố và độ vừa khung chữ trong engine.
Ví dụ:

| Câu hỏi Việt | Đáp án | Vị trí |
|---|---|---:|
| Giữa lừng trời có vũng nước trong / Cá lòng tong lội không tới. | Trái dừa | 3 |
| Ghe bầu chìm tại biển Đông / Cái mui nó mất, cái công nó còn. | Con còng | 3 |
| Vật gì đem cúng ngày rằm / Tụng kinh lầm thầm, búng cánh bay lên. | Bánh cúng | 2 |

23 dòng còn lại nằm trong `review_pending.csv`: 4 dòng có token định dạng bất thường
(`%일권`, `$s`), 8 dòng có tên/nhãn cần thêm ngữ cảnh, 6 dòng nói méo tiếng hoặc chuỗi phím
vô nghĩa, 1 dòng lẫn khoá tài nguyên vào lời thoại, 2 chuỗi exe nghi giải mã sai và
2 khối điều khoản/thông báo dữ liệu cũ cần thay bằng nội dung của dự án.
Không chốt các dòng này chỉ để đưa số review về 0.

Ba tên AI vẫn dùng đúng: **Chiến binh huyền thoại**, **White Angel**, **Mister Fortune**.
Tên cá ở H032 giữ nguyên. Phần ảnh đã có trang duyệt KR/VN; chưa vẽ lại hay Việt hóa ảnh.

Kiểm tra từ gốc repo:

```sh
python3 tools/l10n_extract.py catalog
python3 tools/l10n_validate.py
```

Bộ kiểm tra đối chiếu toàn bộ ID, câu Hàn và `vi_base` với cache nguồn; kiểm tra ghi đè,
placeholder/thứ tự printf/thẻ font/ngắt dòng của các câu đã duyệt theo câu Hàn,
ba tên AI, từ cấm, bộ câu đố và báo cáo review. Kết quả: **0 lỗi kiểm tra, 0 từ cấm**.
