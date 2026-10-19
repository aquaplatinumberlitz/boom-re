# Boom KR — nghiên cứu và thiết kế bản viết lại Rust

Chỉ còn client, source/server gốc thất lạc. Repo giữ RE và server giả lập VN làm nguồn tham chiếu,
catalog/asset KR cùng công việc Việt hóa. Mục tiêu sản phẩm mới là client + server Rust,
giao thức mới và server-authoritative.

`server/` ở đây là snapshot cũ của công cụ tham chiếu giao thức client VN; bản mới ở `/home/admin/boom-re`.

## Bắt đầu

Docs dự án, plan, scope, catalog và Cargo workspace engine mới nằm ở **`/home/admin/boom-rs`**
(ADR 0003). Agent đọc `/home/admin/boom-rs/AGENTS.md` trước.

Repo này giữ: Việt hóa ([l10n/README](l10n/README.md)), tool đọc pack/kiểm kê (`tools/idf.py`,
`tools/kr_feature_inventory.py`, `tools/kr_v1_content.py`) và snapshot server/tool RE cũ.
Hướng dẫn duyệt ảnh: `/home/admin/boom-rs/docs/specification/localization/IMAGE_REVIEW.md`.

Client/pack/database/capture lớn nằm ngoài git hoặc bị ignore. Không thêm chúng chỉ để làm docs.
