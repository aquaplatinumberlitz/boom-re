# Boom KR — nghiên cứu và thiết kế bản viết lại Rust

Chỉ còn client, source/server gốc thất lạc. Repo giữ RE và server giả lập VN làm nguồn tham chiếu,
catalog/asset KR cùng công việc Việt hóa. Mục tiêu sản phẩm mới là client + server Rust,
giao thức mới và server-authoritative.

**Hiện tại: lên kế hoạch, tìm thêm thông tin và chốt cấu trúc dự án trước khi viết engine.**
Chưa có workspace engine Rust mới; `server/` là công cụ tham chiếu giao thức client VN.

## Bắt đầu

1. Agent bắt buộc đọc [AGENTS.md](AGENTS.md).
2. Mở [docs/README.md](docs/README.md) để tới nguồn chuẩn đúng task.
3. Theo [ROADMAP](docs/planning/ROADMAP.md), [SCOPE V1](docs/planning/SCOPE_V1.md),
   [QUESTIONS](docs/research/QUESTIONS.md) và [ARCHITECTURE](docs/planning/ARCHITECTURE.md).

V1 đã chốt scope: Battle cá nhân 2–4 người, Village00, C00/C01, Bomb/Fire/Roller;
auth dự án → sảnh/phòng → trận → kết quả → vòng tiếp. [Catalog](docs/specification/FEATURE_CATALOG.md)
có 114 mục: 37 V1, 75 later, 2 drop legacy. Scope khác với mức xác nhận runtime KR.

## Tra cứu

| Nội dung | Đi tới |
|---|---|
| Catalog và registry nguồn | [FEATURE_CATALOG](docs/specification/FEATURE_CATALOG.md) |
| Workflow team/agents | [TEAM_WORKFLOW](docs/planning/TEAM_WORKFLOW.md) |
| Nguồn Hàn–Trung và câu hỏi còn thiếu | [Research](docs/research/QUESTIONS.md) |
| Việt hóa text/ảnh | [l10n/README](l10n/README.md), [duyệt ảnh](docs/specification/localization/IMAGE_REVIEW.md) |
| RE VN, pack/map/protocol | [Specification](docs/specification/README.md), [Findings](docs/research/findings/README.md) |
| Chạy công cụ VN cũ và nhật ký | [Archive](docs/archive/README.md), [README lịch sử](docs/archive/re/README_VN_HISTORY.md) |
| Hash client/pack và metadata V1 | [Evidence](docs/evidence/README.md) |

Client/pack/database/capture lớn nằm ngoài git hoặc bị ignore. Không thêm chúng chỉ để làm docs.
Thay đổi hiện ở worktree `boom-re-l10n`; main có server tham chiếu mới hơn, cần kiểm baseline khi tích hợp.

## Kiểm tra docs/catalog

```bash
python3 tools/kr_catalog.py --check
python3 tools/docs_check.py
git diff --check
```

Không tạo thêm plan song song. Cập nhật nguồn chuẩn; bản đồ file cũ→mới ở
[DOCS_MIGRATION.json](docs/evidence/DOCS_MIGRATION.json).
