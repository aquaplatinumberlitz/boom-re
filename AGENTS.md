# Quy tắc agent — `boom-re-l10n`

Quy tắc dự án Boom KR Rust nằm ở **`/home/admin/boom-rs/AGENTS.md`** (nguồn duy nhất). Đọc file đó và
`/home/admin/boom-rs/docs/README.md` trước khi làm bất kỳ task nào của dự án viết lại.

Repo này (nhánh `claude/l10n-kr-vi`) chỉ còn giữ:

- Việt hóa: `l10n/`, `tools/l10n_*`, gallery duyệt ảnh.
- Tool đọc pack/kiểm kê: `tools/idf.py`, `tools/kr_feature_inventory.py`, `tools/kr_v1_content.py`
  (ghi kết quả vào `/home/admin/boom-rs/docs/evidence/`).
- Snapshot server/tool RE cũ; bản mới hơn ở `/home/admin/boom-re` main.

Docs, catalog, plan, ADR và kết quả research đã chuyển sang `boom-rs`
([ADR 0003](/home/admin/boom-rs/docs/decisions/0003-engine-repo-and-docs-home.md)); không tạo lại ở đây.
Các quy tắc chung (chỉ stage file của task, không `git add -A` khi có agent khác, không sửa pack/binary,
giữ thay đổi của người khác) áp dụng như trong `boom-rs/AGENTS.md`.
