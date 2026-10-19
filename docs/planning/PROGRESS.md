# Tiến độ so với catalog KR

> GENERATED — không sửa tay. Chạy `python3 tools/kr_catalog.py`.

Baseline mẫu số: **`KR-00967-V1-scope-1`**.
Nguồn: [features.json](../specification/features.json) và [execution.json](execution.json).
Kế hoạch thực hiện: [REWRITE_PLAN](REWRITE_PLAN.md); danh mục: [FEATURE_CATALOG](../specification/FEATURE_CATALOG.md).

## Số mục đã nghiệm thu

| Phạm vi | Done / tổng | Tỷ lệ số mục |
|---|---:|---:|
| Release 1 | 0 / 37 | 0.00% |
| Toàn catalog cần triển khai | 0 / 112 | 0.00% |

Có **2 mục drop_legacy** hiển thị riêng trong CSV, không cộng vào done hoặc mẫu số.
Đây là tỷ lệ **số mục nghiệm thu**, không phải % công sức, thời gian hay fidelity KR.
Không chia điểm cho in_progress/in_review/blocked. Scope đổi phải đổi revision và giải thích mẫu số.

| Trạng thái | V1 | Toàn catalog cần triển khai |
|---|---:|---:|
| Chưa làm | 37 | 112 |
| Đang làm | 0 | 0 |
| Bị chặn | 0 | 0 |
| Chờ review | 0 | 0 |
| Đã nghiệm thu | 0 | 0 |

## Planning và gate phát hành — không cộng vào feature %

Pha đang hoạt động: **P1, P2**. Chuẩn bị P0–P3: **1/4 pha hoàn tất**; các pha không có độ lớn bằng nhau.
Cổng phát hành: **0/6 passed**. Milestone P8: **Chưa làm**.
Chỉ release khi feature V1 đã nghiệm thu, tất cả gate passed và P8 done.

| Pha | Trạng thái | Owner | Đầu ra | Gate hoàn thành |
|---|---|---|---|---|
| P0 Tổ chức docs/scope | Đã nghiệm thu | integrator | Index, rules, registry, scope và migration | Nguồn chuẩn/link/tool rõ, giữ bằng chứng |
| P1 Tìm thông tin còn thiếu | Đang làm | research | Claim/source/fixture và backlog câu hỏi | Câu hỏi chặn kiến trúc có trả lời hoặc phương án kiểm chứng rõ |
| P2 Cấu trúc dự án/interface | Đang làm | architecture | Architecture và contract draft/ADR | Boundary/contracts review và giả định quan trọng được ghi nhận |
| P3 Review sẵn sàng | Chưa làm | integrator | Readiness và task prototype | Checklist readiness trong REWRITE_PLAN có kết luận |
| P4 Nền móng/asset/oracle | Chưa làm | assets/RE | Workspace nhỏ, content resolver và oracle fixture | Legacy vẫn chạy, content unknown rõ và schema phù hợp |
| P5 Core/offline | Chưa làm | core | Simulation/replay V1 | Rule scenarios/state hash tái lập và giới hạn nguồn rõ |
| P6 Client hình/tiếng/input | Chưa làm | client | Scene/animation/render/audio/input | Content/presentation contract và acceptance tương ứng |
| P7 Authority/mạng/phòng | Chưa làm | net/backend | Server/client round lifecycle | Authority/convergence, lifecycle và mạng có fixture |
| P8 Tích hợp/QA/phát hành V1 | Chưa làm | integrator/QA | V1 end-to-end trên3OS | Tất cả37feature V1done và6gate releasepassed |
| P9 Mở rộng full feature | Chưa làm | integrator | Các đợt W1–W4 theo registry | Toàn bộ112mục trong baseline hiện hành done; scope mới phải revision riêng |

| Gate | Trạng thái | Owner | Bằng chứng |
|---|---|---|---|
| G1 Content/map | open | assets/RE | — |
| G2 Movement/stats | open | RE/core | — |
| G3 Bomb/damage/items | open | RE/core | — |
| G4 Protocol/state | open | core/net | — |
| G5 UX/localization | open | client/QA | — |
| G6 Release toàn bộ V1 | open | QA/integrator | — |

## Từng feature V1

Owner là luồng; assignee/reviewer là người hoặc agent nhận task cụ thể.
Chi tiết mọi mục, proof/review/dependency nằm trong [CSV](../specification/features.csv) và JSON nguồn.

| ID | Feature | Trạng thái | Owner / assignee | Reviewer | Bước tiếp / blocker |
|---|---|---|---|---|---|
| V1-001 | Auth tài khoản dự án | Chưa làm | backend / chưa giao | — | — |
| V1-002 | Handshake phiên bản/rules/content | Chưa làm | net / chưa giao | — | — |
| V1-003 | Một kênh và sảnh danh sách phòng | Chưa làm | backend / chưa giao | — | — |
| V1-004 | Tạo phòng công khai | Chưa làm | backend / chưa giao | — | — |
| V1-005 | Vào/rời phòng | Chưa làm | backend / chưa giao | — | — |
| V1-006 | Chủ phòng và kick | Chưa làm | backend / chưa giao | — | — |
| V1-007 | Chọn C00/C01 | Chưa làm | client / chưa giao | — | — |
| V1-008 | Ready/cancel/start | Chưa làm | backend / chưa giao | — | — |
| V1-009 | Chat trong phòng chờ | Chưa làm | backend / chưa giao | — | — |
| V1-010 | Start barrier và spawn | Chưa làm | net / chưa giao | — | — |
| V1-011 | Di chuyển và ưu tiên input | Chưa làm | core / chưa giao | — | — |
| V1-012 | Va chạm tường/gạch/bom | Chưa làm | core / chưa giao | — | — |
| V1-013 | Đặt bom và hạn mức | Chưa làm | core / chưa giao | — | — |
| V1-014 | Fuse/nổ/lan/chặn | Chưa làm | core / chưa giao | — | — |
| V1-015 | Nổ dây chuyền | Chưa làm | core / chưa giao | — | — |
| V1-016 | Phá gạch và drop giới hạn | Chưa làm | core / chưa giao | — | — |
| V1-017 | Item Bomb tăng capacity | Chưa làm | core / chưa giao | — | — |
| V1-018 | Item Fire tăng tầm | Chưa làm | core / chưa giao | — | — |
| V1-019 | Item Roller tăng tốc | Chưa làm | core / chưa giao | — | — |
| V1-020 | Bẫy/bong bóng/chết | Chưa làm | core / chưa giao | — | — |
| V1-021 | Thắng/hòa/hết giờ | Chưa làm | core / chưa giao | — | — |
| V1-022 | Kết quả và chơi vòng tiếp | Chưa làm | backend / chưa giao | — | — |
| V1-023 | Disconnect/timeout | Chưa làm | net / chưa giao | — | — |
| V1-024 | Input/snapshot authoritative | Chưa làm | net / chưa giao | — | — |
| V1-025 | Prediction/reconciliation | Chưa làm | net / chưa giao | — | — |
| V1-026 | Replay và state hash | Chưa làm | core / chưa giao | — | — |
| V1-027 | QA mạng 4 client | Chưa làm | qa / chưa giao | — | — |
| V1-028 | Lưu tài khoản và tùy chọn | Chưa làm | backend / chưa giao | — | — |
| V1-029 | Log/health và vận hành test | Chưa làm | backend / chưa giao | — | — |
| V1-030 | Map Village00 + dependency closure | Chưa làm | assets / chưa giao | — | — |
| V1-031 | Animation C00/C01 và bomb | Chưa làm | client / chưa giao | — | — |
| V1-032 | UI luồng V1 bằng asset KR | Chưa làm | client / chưa giao | — | — |
| V1-033 | Input/scale/focus | Chưa làm | client / chưa giao | — | — |
| V1-034 | Audio/volume | Chưa làm | client / chưa giao | — | — |
| V1-035 | Việt hóa UI V1 | Chưa làm | client / chưa giao | — | — |
| V1-036 | Build Windows/Linux/macOS | Chưa làm | release / chưa giao | — | — |
| V1-037 | Đối chiếu và báo sai khác | Chưa làm | qa / chưa giao | — | — |

## Agent phải cập nhật gì

Nhận task theo plan, ghi ID và assignee; sửa trạng thái/proof/review trong JSON nguồn rồi sinh lại report.
Done cần commit tích hợp tồn tại, baseline/spec được chấp nhận, verification passed, reviewer độc lập approved,
bằng chứng tồn tại và dependency done. Validator chỉ kiểm tính nhất quán/tham chiếu; không tự xác minh sự thật của proof.
Planning/research cập nhật execution.json và QUESTIONS tương ứng; không đánh dấu feature done vì đã viết spec hoặc tìm thấy asset.
