# Việt hoá chữ của Boom Online KR (cho engine Rust viết lại)

Mục tiêu: toàn bộ chữ của bản KR (patch Nexon 00967, 13 pack) sang tiếng Việt, dùng lại bản dịch có sẵn của bản VN.
Catalog ban đầu dùng cho engine Rust viết lại (UTF-8, font vector). Công cụ ghi thử client gốc được mô tả ở cuối tài liệu; chưa nghiệm thu trên client.
Ảnh nghi có chữ được thống kê (`images_todo.csv`) và có trang duyệt KR/VN;
chưa vẽ lại hoặc Việt hóa ảnh. Xem hướng dẫn duyệt ảnh (`/home/admin/boom-rs/docs/specification/localization/IMAGE_REVIEW.md`).

## File

| File | Nội dung |
|---|---|
| `catalog.csv` | mỗi chuỗi một dòng: `id, source, ko, vi_base, vi, status, notes` (UTF-8, CSV chuẩn, xuống dòng giữ nguyên trong ô có ngoặc kép) |
| `design_rows.csv` | 64 dòng nguồn design thêm ngoài cache trích; giữ đủ các trường gốc |
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
| `/home/admin/boom-rs/docs/specification/localization/IMAGE_REVIEW.md` | cách mở trang ảnh KR/VN, duyệt, xuất/nhập kết quả và tạo lại trang |
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
| `csysstr.ssd` (thư mục game) | `.ssd`: `"ssi1"`, u32 ?, u8 `0x18`, u32 block_len @9 = file_size − 13, cờ @13, u32 raw_len @14, **zlib từ offset 0x12**. Raw: `u16 count`, count × (`u32 len + key cp949`, `u32 len + value cp949`). Là cache của FxClientString (S->C 2) | 8.442 | [VERIFIED] parse vừa khít, raw_len khớp |
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

| `fxstock0.ini`–`fxstock3.ini` | 8.165 record, tên cp949; ID catalog `stock:<id số>` ổn định theo record stock KR | [VERIFIED] đọc đúng hết bốn file; tên trùng theo ID khác nhau được giữ từng dòng, bản dịch tra `tm.csv` theo nguyên văn |

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

## 2c. Xưng hô, lệnh chat và tên riêng

Quy ước chốt sau lượt dịch lại 2026-11-15 và lượt review cùng ngày. Câu mới hoặc câu sửa phải theo các quy ước này.

**Xưng hô.** Mỗi câu chỉ dùng một cặp xưng hô, và **cùng một nhân vật giữ một cặp trong mọi câu của nó**
(cùng tiền tố `id`, ví dụ `q:WelcomeToBnB_InfoMsg*`, `monseal12generala*`).

| Người nói | Cặp | Ghi chú |
|---|---|---|
| Quái, trùm, NPC thù địch | ta – mi | Số nhiều: tụi bây. **Không dùng "ngươi"** |
| NPC thân thiện, thú cưng, NPC giao nhiệm vụ (kể cả ông nhà nghiên cứu RPG) | tui – bạn | Không xen "mình" để tự xưng |
| Lính nói với chủ (câu Hàn dùng 제가/저희, kính ngữ) | tôi / chúng tôi – ngài | Ví dụ lính hải cẩu `monseal*` |
| Hệ thống, hướng dẫn, thông báo | bạn | Nhãn UI kiểu 내 … giữ "… của tôi" |

**Lệnh chat** (`*_CmdMsg`, `SpeakerMacro*`, `LobbySquare_Cmd_*`, `ChatRenew_ChatInfo*`, `FxDesktop:Help/Help:*`):
không dấu, không khoảng trắng (`/loa`, `/bangdien`, `/phao`). Câu hướng dẫn nhắc tới lệnh phải dùng **đúng** chuỗi
lệnh đã dịch, không để lại lệnh Hàn (`/전광` → `/bangdien`).

**Tên riêng.**
- Tên nhân vật theo `character_names.csv` (다오 → Nhanh Nhẩu, 배찌 → Khò Khò…).
- Tên người chơi trong câu Hàn được phiên âm Latin theo romanization chuẩn (`[입소증]` → `[Ipsojeung]`).
- Tên người trong credit, tên GM và tên hội vẫn giữ chữ Hàn (có ghi chú trong `notes`).
- Một câu Hàn lặp lại với tên khác nhau phải dịch cùng một khuôn (ví dụ `UserContest02–05`: `[Giải Giỏi lắm]`).

**Chữ Hàn sót.** Ngoài các tên giữ nguyên ở trên, không để chữ Hàn trong bản Việt (`(토,일)` → `(T7, CN)`).
Emoticon bằng chữ cái Hàn (ㅠㅠ, ㅎㅎ, +ㅁ+) hiện vẫn giữ nguyên; xem việc còn mở ở §11.

**Tên riêng đã chốt (bản Việt).** Vua Cát (샌드킹, cả tên map), quái sao (별몬, danh từ chung), Kong Kong (콩콩),
Munppak (문빡이), Kdasu (크다수), bà Palpal (팔팔할매), Fortune Star (포츈스타, nhân vật AI) và Mister Fortune
(미스터포츈, NPC quảng trường).

**Nhân vật AI đối kháng** (`AIBattleSay_*_CAHero_N`, `AIBattleSay_*_N`) đều xưng ta – mi, kể cả nhân vật dễ thương
như Indi, Pinky. Nhân vật tự gọi tên mình (Pinky, Indi) thì giữ tên, phần còn lại vẫn ta – mi.

**Bản tiếng Anh.**
- Tên nhân vật tiếng Anh ghi riêng trong [`character_names_en_review.csv`](character_names_en_review.csv).
  Cột `client_evidence_id` trỏ đến ID trong `english_sources.csv` của PopTag; nếu tên do chủ dự án chốt,
  cột `official_source` ghi quyết định thay cho nguồn client. Số trong `en_variants_in_catalog` đếm
  dòng có cụm tên tiếng Anh, ưu tiên tên dài nhất khi trùng (ví dụ `Posh Ike` không tính vào `Ike`).
  `consistent` tính cả biến thể có trong PopTag (`Dizini` ở `EP6_Name`); `n/a` nghĩa là không có tên
  trong catalog chuỗi. Tên chỉ có trong bản máy chọn một cách viết và dùng cho mọi câu:
  Sand King, Moonbbak, Granny Palpal, Starfish (별몬, theo PopTag), Little Caterpillar (꼬물이).
- Lệnh chat viết thường, không khoảng trắng (`/speak`, `/christmas`, `/allpink`). Lệnh nào câu Hàn có kèm bí danh
  Latin thì dùng bí danh đó (`/누구` → `/who`, `/어디` → `/where`, `/초대` → `/in`, `/퇴장` → `/ban`, `/방제` → `/rt`,
  `/자동` → `/ar`); câu hướng dẫn không được để lệnh Hàn.
- Sửa tay theo mã chuỗi ghi ở `en_id.csv` (`id, en, notes`), được áp sau cùng khi dựng `catalog_en.csv`. Dòng không
  qua `formatting()` của `l10n_extract_en.py` sẽ bị bỏ khi dựng lại.

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
Duyệt ảnh KR–VN: `/home/admin/boom-rs/docs/specification/localization/IMAGE_REVIEW.md`.

Mở terminal và chạy:

```sh
xdg-open /home/admin/boom-re-l10n/l10n/.cache/image-review/index.html
```

Từ 2026-11-14 trang duyệt có ba cột KR / VN / Bắc Mỹ, hiện chữ do máy đọc trên từng ảnh (`images_text.csv`), lọc theo
nhãn máy đọc và theo đối chiếu với bản Bắc Mỹ, và ghi hai quyết định riêng cho tiếng Việt (`status`) và tiếng Anh
(`status_en`). Dựng lại bằng `python3 tools/l10n_images_review.py`; mặc định đọc client KR ở
`/home/admin/boom/clients/kr-00967` và client PopTag ở `l10n/.cache/poptag-client`.

Mở sẵn bộ lọc qua phần sau dấu `#`, ví dụ 268 mục có chữ Hàn và có cả ảnh VN lẫn ảnh Bắc Mỹ khác nội dung. Phải
đưa cho trình duyệt một địa chỉ `file://`; `xdg-open` với đường dẫn thường kèm `#` sẽ coi cả phần `#…` là tên file:

```sh
firefox "file:///home/admin/boom/repos/boom-re-l10n/l10n/.cache/image-review/index.html#label=ko&relation=diff_bytes&enrel=diff_bytes"
```

Chủ dự án chấp nhận (2026-11-14) ảnh bản VN dùng giọng Bắc ở vài nút (`XEM NHIỆM VỤ`, `HỦY BỎ`) dù phần chữ theo
giọng Nam: ảnh VN dùng được thì lấy, không vẽ lại vì lý do giọng. CSV xuất ra có thêm cột `status_en`; CSV cũ bốn cột vẫn nhập được.

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

## 6. Nguồn tiếng Anh PopTag 0.7.8

`catalog_en.csv` là bản ghép **ứng viên**, giữ nguyên từng dòng Hàn–Việt và trạng thái Việt trong
`catalog.csv`. Các cột bổ sung là `en`, `source_en`, `en_status`, `en_notes`. Ghép theo ID chính
xác không chứng minh nghĩa hoặc giao diện hai phiên bản tương đương; mọi bản Anh đều cần duyệt.
Không dùng trực tiếp làm bản vá client. Hai dòng Lua trong catalog gốc có cùng ID được giữ nguyên.

- `candidate`: chữ PopTag theo đúng ID. `en_notes` cho biết kết quả soát nghĩa so với câu Hàn
  (`en_review.csv`): `meaning_checked` là khớp nghĩa, `whitespace_from_kr` là giữ câu chữ PopTag
  nhưng lấy xuống dòng và khoảng trắng đầu cuối của câu Hàn (PopTag viết liền một dòng),
  `meaning_unsure` là không đủ ngữ cảnh nên giữ chữ PopTag, `settled_poptag_variant` là một trong
  nhiều biến thể PopTag được chọn (`en_override.csv`).
- `casefold_candidate`: như trên nhưng ID chỉ khớp khi bỏ phân biệt hoa/thường; `en_notes` ghi ID gốc.
- `machine`: bản dịch máy từ câu Hàn. Nguồn là `tm_en.csv`, hoặc `en_review.csv` khi chữ PopTag lệch
  nghĩa câu Hàn (`replaces_poptag_text`), hoặc `en_override.csv` cho dòng từng treo (`settled_machine`).
- `conflicting_variants`, `stock_icon_candidate`, `machine_review`: dòng còn treo, chưa dùng để dựng.
  Sau lượt chốt 2026-11-14 không còn dòng nào ở ba trạng thái này.
- `missing`: không có bản Anh. Hiện gồm dòng không có câu Hàn, dòng không có chữ Hàn (dùng nguyên)
  và chuỗi trong exe (chưa có đường thay).

Kiểm định dạng dùng chung cho cả công cụ dựng (`formatting` trong `tools/l10n_extract_en.py`): tham số
printf đúng số lượng và thứ tự (tham số có số thứ tự `%1$s` được đổi chỗ), thẻ `<font …>` và `{…}`
giữ nguyên. Chữ thường trong ngoặc nhọn như `<주의>` không phải thẻ. Dấu `%` nghĩa đen không được
đứng trước chữ cái hoặc dấu cách rồi chữ cái (`50% for`, `20% nha` bị đọc thành tham số).

- `english_sources.csv` cũng giữ các ID chỉ có trong PopTag, không tự gán sang KR.
- `english_sources_manifest.json` ghi SHA-256 của các file nguồn, catalog gốc và thống kê.

Nguồn đã trích gồm cache `csysstr.ssd`, `fx/ClientData/ClientString` (LangID 1033) tên
hiển thị trong `fxdynmapinfo.ssd`, 610 tên stock từ `fxstock.ini` và năm tên kênh từ
`channel2_000.ssd`. Tên stock dùng tiền tố `poptag:stock:`; số lượng khớp count nhưng chỉ
trích theo cấu trúc header, chưa giải toàn bộ record hoặc đối chiếu ID KR. Tên kênh dùng
`poptag:channel:` vì số thứ tự không chứng minh đồng nhất với kênh KR. JSON `Swish/Catalog`
đóng góp 61 tên hiệu ứng với tiền tố `poptag:swish:`, không ghép KR. Các chuỗi viết cứng
trong `poptagdll.dll` chưa được trích. Những nguồn khác như ảnh, chuỗi do server gửi, quest,
script và chữ trong exe chưa được kiểm kê đầy đủ. File Help trong pack PopTag đã xem vẫn có
chữ Hàn, nên không giả định mọi thứ trong client này đều là tiếng Anh. Các tên map trùng
ID cũng chỉ là ứng viên: cùng tên nội bộ có thể đổi nội dung theo bản game.

Bản bung của bộ cài PopTag 0.7.8 nằm ở `l10n/.cache/poptag-client` (thư mục `.cache/` bị Git bỏ qua, không commit;
không chạy file thực thi nào trong đó). Các công cụ mặc định đọc ở đó; tái tạo bằng:

```sh
python3 tools/l10n_extract_en.py            # hoặc --client /duong/dan/khac
```

Không sửa `catalog.csv`, `tm.csv`, `tm_id.csv` hoặc client nguồn. Để ghi sang thư mục khác,
thêm `--out /duong/dan/thu-muc`; muốn đối chiếu catalog khác dùng `--catalog /duong/dan/catalog.csv`.

Rà bổ sung: quét 538 entry `Map/` trong toàn bộ index PopTag đọc được; bộ đọc `map_says`
nhận 44.012 tham chiếu không rỗng, gồm 42.222 khớp chính xác ID trong bảng nguồn, 37 giá trị
có chữ Hàn và 1.753 lượt chưa khớp (471 giá trị khác nhau, 348 trong đó có ID cùng chữ khi
không phân biệt hoa/thường). Đây là tham chiếu, không tự coi là câu dịch; ghép không phân biệt
hoa/thường cần kiểm tra trùng và ngữ cảnh. Trong `clientextensions/custommap`, các mô tả trùng
2.174 ID catalog KR đã xem vẫn là tiếng Hàn, không đưa vào cột Anh. Kết quả quét không khẳng
định đã bao phủ mọi đoạn text nhúng, ảnh hoặc chuỗi được tải lúc chạy.

### Đối chiếu ảnh và stock

`images_en_candidates.csv` giữ các cột gốc trong `images_todo.csv` cho 1.187 mục trùng tên.
Cột `comparison` là so byte payload sau giải mã pack: 611 mục có ít nhất một bản giống,
576 mục khác. `kr_sizes` là danh sách kích thước mọi ảnh con; `kr_frames` là số frame.
`poptag_details` là JSON giữ từng pack và entry PopTag, kích thước mọi ảnh con, số frame,
so byte và kết quả so kích thước/số frame. Có một mục trùng tên trong nhiều pack nên phải
xem từng kết quả trong JSON. Trùng tên, khác byte hay khớp kích thước không chứng minh ảnh
có chữ Anh hoặc có thể thay vào client KR.

`stock_names_en.csv` ghép theo ID số và giữ tên, loại, icon, file và offset KR. Bốn file
`fxstock0.ini`–`fxstock3.ini` có 8.165 record, đều được đọc tới đúng cuối dữ liệu giải nén.
`fxstovi.ini` và `fxstovs.ini` chứa record số; chưa thấy tên trong mẫu đã đọc. So tên nguyên
văn thấy 588 record stock KR, gồm 155 tên khác nhau, trùng chữ Hàn của một hoặc nhiều dòng
trong catalog, nhưng trùng chữ không chứng minh ID catalog là ID vật phẩm.

Trong 610 tên stock PopTag, có 113 ID số trùng KR. Kiểm toàn bộ 113 cặp: **0/113** khớp
đồng thời loại và đường dẫn icon (cả hai trường đều khác trong cả 113 cặp). Các dòng này
không dùng làm bản dịch. Các phép ghép chỉ theo ID số đã được loại khỏi file ứng viên; so
loại/icon là kiểm chứng tĩnh và không chứng minh đầy đủ ngữ nghĩa vật phẩm.

## 7. Stock KR và bản dựng thử cho client gốc

Bốn file stock KR có 8.165 ID, 4.968 tên nguyên văn (4.967 sau bỏ khoảng trắng đầu/cuối).
Catalog stock có 8.140 dòng `translated`, 25 dòng `review` do cờ bàn giao; không còn dòng stock `untranslated`. Đã nhập nguyên văn 4.675 cặp Hàn–Việt từ bàn giao vào `tm.csv`. `design_rows.csv` lưu 64 dòng nguồn design thiếu trong cache cũ;
`sources` nạp lại các dòng này cùng stock. Kiểm tra so từng trường xác nhận 25.321 dòng
gốc không đổi. `review_pending.csv` được sinh lại từ catalog. Validator chạy hết, 0 lỗi.
49 tên stock ban đầu bị quy tắc miền Nam gắn cờ (`mũ`, `mày`, `cửa hàng`) đã được sửa trong `tm.csv` (Mũ → Nón, ăn mày → ăn xin, cửa hàng → tiệm); validator không còn coi "lông mày", "chân mày" là đại từ `mày`.

Nguồn VN đã tìm trong mã server boom-re/boom-re-l10n và file cache
`boom-re/wine/Boom/fxstock.ini`: server và cache chỉ có hai mục giả `Test A`, `Test B`,
không có bộ tên VN kèm loại/icon đáng tin. Không gán `vi_base` từ nguồn này. So PopTag
theo loại và icon cho 365/610 ID PopTag ít nhất một ứng viên KR, tổng 235.132 cặp do
nhiều stock dùng chung icon. Chỉ 28 ID PopTag có kết quả quy về đúng một tên KR: 59 cặp
được giữ trong `stock_names_en.csv` (~28 KiB). Trong catalog Anh, 43 dòng có trạng thái
`stock_icon_candidate`, bốn dòng có nhiều bản Anh được đánh dấu mâu thuẫn. Cùng loại/icon
không chứng minh cùng vật phẩm, vẫn phải duyệt.

Chạy build thử vào thư mục riêng, không đặt output trong client gốc:

```sh
python3 tools/l10n_build.py --kr /home/admin/boom/clients/kr-00967 --lang vi --encoding utf-8 --out /tmp/boom-l10n-vi
python3 tools/l10n_build.py --kr /home/admin/boom/clients/kr-00967 --lang en --encoding cp949 --out /tmp/boom-l10n-en
python3 tools/l10n_build.py --kr /home/admin/boom/clients/kr-00967 --lang ko --encoding cp949 --out /tmp/boom-l10n-ko
```

Hỗ trợ `ko`, `vi`, `en` và `cp949` hoặc `utf-8`; nếu chuỗi chưa có bản dịch được duyệt,
khác nội dung gốc, hoặc lệch thứ tự tham số/thẻ thì giữ chuỗi gốc. Bản dịch có ký tự không mã hóa được trong bảng mã chọn được giữ lại bằng tiếng Hàn; số dòng và ký tự được ghi vào build-report.json. Không hỗ trợ những nguồn khác ở mục 1. Với SSI,
checksum Adler-32 khởi tạo 0 tại byte 4–7 tính trên toàn bộ dữ liệu từ byte 8, byte 8 là 0x18, độ dài khối tại 9 bằng độ dài luồng
nén cộng 5 (hay kích thước file trừ 13), byte 13 là 1, độ dài
giải nén tại 14; phần thân nén zlib. Kiểm 13 file KR đều khớp checksum. Theo phân tích tĩnh exe VN, hàm đọc 0xA62D10 từ chối nếu checksum sai; hàm ghi 0xA62C20 và hàm tính 0xA0E1E0. Chưa xác minh hàm tương ứng của exe KR.
`FxDesktop` ghi entry đã đổi ở cuối `.idd`, cập nhật offset/size index; không đổi entry khác.

Kiểm `ko/cp949`: bảy SSI có parser được dựng lại dữ liệu và ghi qua bộ nén thực sự;
phần giải nén trùng gốc, byte đầu khác là offset 9 do luồng nén khác độ dài. Kiểm thêm sáu
SSI ở mức header và zlib: `csysfxmg.ssd`, `channel2_001.ssd`, `spcc.ssd`, `multisvr.ssd`,
`fxstovi.ini` giống từng byte; `filterstr.ssd` khác từ offset 9, giải nén giống gốc. Đã
thử level 1–9, wbits 9–15, memLevel 1–9, năm strategy (loại nhanh tổ hợp sai header zlib);
không tìm được luồng gốc của tám file khác. Index pack được giải và mã hóa lại trùng byte,
`.idd` không đổi được chép nguyên. Khi viết UTF-8, khóa `csysstr`/`csysqstr`, tên map,
theme, tên file và khóa XML được giữ nguyên byte; quan sát 29 khóa ngoài ASCII trong
`csysstr`, một trong `csysqstr`, 30 trong XML, và không có tên map/theme/file ngoài ASCII.

Kiểm thử khô sau khi nhập dữ liệu: 13 checksum nguồn và các checksum file mới đều khớp;
năm SSI nhỏ ở trên vẫn giống từng byte, tám SSI còn lại giải nén giống gốc khi dựng ko/cp949.
Stock khi dựng vi/utf-8 lần lượt thay 2.493, 2.492, 2.485, 661 chuỗi; khi dựng en/cp949
lần lượt thay 2.283, 2.379, 2.441, 661. `build-report.json` ghi số chuỗi thay, còn Hangul,
lệch định dạng và không thể mã hóa theo từng file. Số liệu thay chuỗi ở đoạn này là của lượt
dựng đầu; số hiện hành ở mục 8. Chưa file nào được nạp thử vào client.

Nguồn tiếng Anh `tm_en.csv` có 18.132 câu: 17.983 câu nguyên văn từ hai file bàn giao (4.675 tên stock
và 13.308 câu còn lại) cộng 149 câu bổ sung sau đó cho các tên stock đã có bản Việt từ trước. Bản PopTag và các biến thể mâu thuẫn được ưu tiên, không ghi đè.
Số liệu catalog Anh của lượt nhập đầu (trước lượt chốt ở mục 8): candidate 6.082, casefold_candidate 199, stock_icon_candidate 43, conflicting_variants
106, machine 26.133, machine_review 97 và missing 826. Trong missing, 105 không có chữ gốc,
358 có nguồn không chứa Hangul, 363 cố ý giữ tiếng Hàn như bản Việt (tên người, danh sách tên cấm); 19 dòng machine_review
được bàn giao có cờ giữ Hangul, không cộng vào missing.

## 8. Lượt soát và chốt 2026-11-14

Trạng thái sau lượt này. Tiếng Việt: `translated` 29.671, `reused` 3.813, `review` 2 (hai văn bản pháp lý của
Nexon, phải thay bằng điều khoản của dự án). Tiếng Anh: `candidate` 5.527, `casefold_candidate` 197, `machine`
27.218, `missing` 544 (105 dòng không có câu Hàn, 358 dòng không có chữ Hàn, 81 tên cấm trong exe giữ tiếng Hàn);
không còn dòng `conflicting_variants`, `stock_icon_candidate` hay `machine_review`. Validator 0 lỗi.

| File | Nội dung |
|---|---|
| `en_review.csv` | `ko, en_poptag, verdict, en`: kết quả soát nghĩa 5.417 cặp Hàn–Anh lấy từ PopTag. `ok` 3.910, `whitespace` 861, `fix` 632, `unsure` 14 |
| `en_override.csv` | `ko, en, basis, notes`: 207 câu từng treo đã chốt. `poptag_variant` là một biến thể PopTag được chọn, `machine` là bản dịch từ câu Hàn; `empty_on_purpose` cho bốn trợ từ Hàn đứng riêng |
| `images_text.csv` | `pack, entry, dims, label, text, vn_same_name, poptag`: kết quả đọc chữ trên 3.038 mục ảnh nghi có chữ |

Việc đã làm, đều bằng model và kiểm máy, chưa có người đọc soát toàn bộ:

- **Soát nghĩa chữ PopTag** (`gpt-6.1-terra`, 19 lô): chữ PopTag lệch nghĩa câu Hàn thì thay bằng bản dịch từ câu Hàn
  (652 dòng catalog); chữ PopTag viết liền một dòng trong khi câu Hàn có xuống dòng thì giữ câu chữ, lấy xuống dòng và
  khoảng trắng đầu cuối của câu Hàn (922 dòng).
- **Chốt dòng treo:** 103 câu nhiều biến thể, 80 câu dịch máy bị cờ, 24 tên tạm ghép theo icon; 93 câu nhận một biến thể PopTag, 114 câu dịch từ câu Hàn. Dịch bù 244 câu tiếng
  Anh từng bị bỏ qua vì bản Việt còn giữ chữ Hàn (biểu tượng cảm xúc `ㅠㅠ`, tên người trong bảng ghi công).
- **Tiếng Việt chờ duyệt:** 46 trên 48 dòng được chốt (Claude quyết theo uỷ quyền của chủ dự án); ba câu nguồn có
  `%일권` viết lại không còn dấu `%` lạc; `review_audit.csv` ghi quyết định mới.
- **Soát lần hai** `csysstr.ssd` và `ClientString` (8.964 câu, 33 lô): áp dụng 623 sửa tiếng Việt (364 sửa nội dung,
  259 chỉnh khoảng trắng đầu cuối) và 68 sửa tiếng Anh; không áp dụng 162 đề xuất chạm dòng có trong
  `review_audit.csv` và 10 đề xuất viết lại câu có `%%` vốn đã đúng. `csysqstr.ssd` và tên stock chưa qua lượt này.
- **Dấu `%` nghĩa đen:** bản dịch không được để chữ cái, hoặc dấu cách rồi chữ cái, ngay sau `%` (`50% for`, `20% nha`
  thành tham số printf hợp lệ). Kiểm định dạng bắt các trường hợp này; các câu vi phạm đã viết lại.

Công cụ dựng sau lượt này: bản dịch rỗng có chủ ý của trợ từ Hàn được áp dụng; chữ Latin có dấu và gạch dài được hạ
về ký tự gần nhất khi ghi `cp949`; bản UTF-8 chuyển cả khoá có chữ Hàn sang UTF-8 (29 khoá `csysstr`, một khoá
`csysqstr`, 30 khoá XML), `--keep-key-bytes` giữ byte gốc. Quét image exe đã unpack, 13 file SSI và 51.467 entry của
mọi pack KR không thấy tham chiếu nào tới các khoá này bằng byte `cp949` ngoài chỗ định nghĩa.

Dựng thử sau lượt này: `vi/utf-8` thay 32.098 chuỗi, `en/cp949` thay 32.102 chuỗi, không chuỗi nào bị loại vì lệch
định dạng hoặc không mã hóa được. Kiểm lại trên file dựng ra: bảy SSI của mỗi bộ đúng checksum, hai trường độ dài và
độ dài giải nén; bộ `ko/cp949` giải nén giống gốc cả bảy file; pack của bộ `vi` và `en` giữ 2.076 trên 2.077 mục
index, phần `.idd` gốc không đổi, bảng chuỗi mới đọc lại trọn vẹn theo một bảng mã, đủ 6.993 mục. Chưa file nào
được nạp thử vào client.

Bề rộng chữ: `tools/l10n_width.py --vi-font <font VN>/CxUni.fft` cộng bề rộng bước từng ký tự và so dòng rộng nhất
của bản dịch với câu Hàn. Bản dịch máy và bản chính thức có cùng phân bố (trung vị 1,16–1,42 lần câu Hàn, mức 95% từ
1,7 tới 2,4 lần). Đây là xếp hạng nguy cơ, không phải phép đo khung thật.

Ảnh có chữ: `gpt-6-luna` đọc 3.038 mục của `images_todo.csv` trên 203 tờ ảnh ghép đánh số (mỗi mục tối đa ba ảnh con:
đầu, giữa, cuối), kết quả ở `images_text.csv`. Nhãn: `ko` 1.104 (746 cụm chữ khác nhau), `latin` 149, `digits` 165,
`none` 1.598 (gồm 18 mục không có ảnh con), `unclear` 22. Trong 1.104 mục có chữ Hàn, 654 mục có ảnh cùng tên khác
nội dung ở client VN (564) hoặc PopTag (358), 450 mục không có bản nào. Đối chiếu tay 15 ô của một tờ: đúng cả 15;
chưa kiểm rộng hơn. 282 mục có nhiều hơn ba ảnh con, có thể sót chữ ở ảnh không được hiện. Cùng tên và khác byte
không chứng minh ảnh kia đã được dịch.

Dựng ảnh offline: `python3 tools/l10n_build.py --lang vi --encoding utf-8 --images --out l10n/.cache/build-vi`
đọc quyết định từ `images_review.csv`; `--images <csv>` chọn file quyết định khác. Với `--lang en`, dùng cột
`status_en` và ảnh PopTag. Có thể thêm `--image-dir <thư-mục>`: PNG đặt tại `<thư-mục>/<pack>/<entry>/<số>.png`,
JPEG tại `<thư-mục>/<pack>/<entry>.jpg`. PNG thay các ảnh con được chỉ định, ảnh con còn lại giữ bản KR;
JPEG được chép nguyên. Ảnh RGB565 được lượng tử hóa về RGB565; alpha bán trong suốt bị từ chối nếu ảnh
gốc không có luồng alpha. Mặc định từ chối ảnh nguồn khác số frame, số ảnh con hoặc kích thước; dùng
`--allow-shape-change` khi chủ đích chấp nhận. Báo cáo dựng ghi số ảnh thay và lý do bỏ qua.
Kiểm offline toàn bộ 48.898 entry `i16` của 13 pack giữ nguyên điểm ảnh qua vòng mã hóa; 36 entry Việt và
37 entry Anh đã đối chiếu pack đầu ra, cả JPEG, entry mã hóa và `FxDesktop`. Kết quả chi tiết ở
`l10n/.cache/image-build-check/verification-report.json`. Chưa nạp vào client.
Dựng với quyết định thật ngày 2026-11-14: bản Việt thay 459 ảnh trong 7 pack, bỏ qua 90 ảnh VN khác hình dạng
(số ảnh con, kích thước hoặc số frame); bản Anh thay 314 ảnh trong 5 pack (35 entry mã hoá), bỏ qua 29. Kiểm độc lập
của Claude: mọi ảnh thay giống từng byte entry nguồn sau giải mã, CRC đúng, mọi entry không đánh dấu giữ nguyên
offset/size/khoá/CRC, phần `.idd` gốc của mỗi pack không đổi. Đầu ra ngoài repo được phép; trong repo chỉ được ghi
vào `l10n/.cache/`.

## 9. Xem và sửa catalog trong trình duyệt

`python3 tools/l10n_catalog_view.py` dựng `l10n/.cache/catalog-view/index.html` (mở bằng
`firefox file:///home/admin/boom/repos/boom-re-l10n/l10n/.cache/catalog-view/index.html`). Bảng bốn cột mã / Hàn /
Việt / Anh, tìm và lọc theo nguồn, trạng thái. Bật "Chế độ sửa" rồi bấm vào ô Việt hoặc Anh để sửa; Ctrl+Enter
hoặc bấm ra ngoài để lưu, Esc để huỷ. Chỗ sửa lưu trong trình duyệt, tô xanh; tô đỏ kèm lý do nếu lệch tham số định
dạng, thẻ, số lần xuống dòng so với câu Hàn hoặc có từ ngoài giọng miền Nam. "Xuất các chỗ đã sửa" tải về
`catalog-edits.csv` (`id, lang, ko, old, new`).

Nhập: `python3 tools/l10n_catalog_view.py --import catalog-edits.csv`. Bản Việt ghi vào `tm_id.csv` (và
`review_audit.csv` nếu dòng đó đã có quyết định duyệt), bản Anh ghi vào `en_id.csv` với trạng thái `manual`; rồi dựng
lại hai catalog, chạy validator và dựng lại trang. Chỗ sửa lệch định dạng hoặc có từ cấm bị từ chối và in lý do.

## 10. Bảng mã 1258 trong exe 00967 (ghi nhận, không dùng)

Exe 00967 có nhánh bảng mã 1258 của client VN (công tắc vùng `0x138D380`, `push 3B5h` tại `0x138D3B1` cho vùng 1;
nhánh 1258 ở `0x149A7B0`, `0x149AC90`, `0x1499C20`). Chủ dự án chốt UTF-8 cho cả Hàn, Việt, Anh như PopTag, nên công
cụ dựng không có kiểu ghi 1258; ghi lại để biết chỗ khi vá UTF-8.

## 11. Dịch lại giọng Nam và review 2026-11-15

- `7841c9b` (nhánh `claude/l10n-kr-vi`): Terra dịch lại 22.703 câu Hàn theo quy ước §2c.
- PR #3 (merge `fc481f7` trên `main`) đưa `l10n/`, `tools/l10n_*`, `tools/idf.py`, `tools/i16.py` từ nhánh đó vào
  `main`. Phần dời docs sang boom-rs, `AGENTS.md`/`CLAUDE.md`/`opencode.json` và các sửa đường dẫn trong comment
  **không** được merge vì xung đột với `main`; chúng vẫn chỉ có trên `claude/l10n-kr-vi`.
- `57c719d`: sửa sau review, ghi ở `tm.csv`/`tm_id.csv` (notes `sửa 2026-11-15 (review: …)`):
  - lệnh chat `/bangdien`, `/phao`;
  - bỏ hết "ngươi";
  - thống nhất xưng hô cho NPC tân thủ, nhà nghiên cứu RPG (EP004, EP006), lính hải cẩu và chim cánh cụt băng;
  - "A bố Kong" → "Hây da Kong";
  - `UserContest02–05`;
  - `(T7, CN)`, `Phố số 11`.
- Lượt sửa này đồng bộ tay vào `catalog.csv` và `glossary.csv`, **chưa** chạy `l10n_extract.py catalog` và
  `l10n_validate.py` (máy sửa không có pack). Ở máy có pack: dựng lại catalog, chạy validator; nếu catalog dựng
  lại khác bản sửa tay thì lấy bản dựng lại.
- Lượt review thứ hai (tên riêng, xưng hô, lệnh chat; notes `sửa 2026-11-15 (review 2: …)`):
  - Việt, 89 dòng:
    - thống nhất các tên ở §2c (Sand King/vua cát → Vua Cát; Byeolmon/quái vật sao → quái sao; Kongkong → Kong Kong;
      Munbbak; Keudasu; "bà lão khỏe mạnh" → bà Palpal);
    - nhân vật AI Indi, Pinky, Rodumani, Kong Kong, Fortune Star về ta – mi;
    - "giới Indi" → "giới nhạc indie".
  - Anh, 433 dòng trong `en_id.csv`:
    - Su → Sue (260), Huu/Hoo → Hoou (99), nhãn tên `HooU` từng bị dịch "Phew";
    - Sandking, Munppaki, Byeolmon/Star Monster, Grandma Pal Pal, Kkomuli;
    - lệnh chat viết thường, `/보석사탕` → `/jewelcandy`, bỏ lệnh Hàn trong 11 câu hướng dẫn.
  - Cột `vi` của `catalog_en.csv` đồng bộ lại theo `catalog.csv` (lượt sửa trước chưa chép sang).
- Việc còn mở:
  - Lệnh chat bản Việt (`/ai`, `/odau`, `/moi`, `/duoi`, `/tenphong`, `/tudong`, `/trieutap`…) và bản Anh
    (`/summon`, `/broadcast`, `/jewelcandy`…) chỉ chạy được nếu engine nhận các bí danh này; client KR gốc chỉ biết lệnh
    Hàn và bí danh Latin có sẵn.
  - `ForceDeleteItem_Msg_0002` (`스주사위` → "Su Dice") chưa rõ nghĩa.
  - 146 câu có emoticon chữ Hàn (đổi sang T_T, hihi, >.<…?);
  - "Kim" viết hoa 392 chỗ, viết thường 20 chỗ;
  - 15 câu đố Việt nhiều dòng hơn câu Hàn, cần xem tràn khung trên client;
  - `PremiumSlotAdvMotionBlur` ("Vút vút cộng") nghe gượng;
  - `boom-kr-server/docs/content/client-language.md` còn trỏ commit `e5d1bac` và số liệu bản Việt cũ.
