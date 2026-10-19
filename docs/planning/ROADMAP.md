# Roadmap trước khi viết lại engine

Cập nhật: 2026-10-19. Nguồn chuẩn về pha, trạng thái và công việc tiếp theo.
Scope: [SCOPE_V1](SCOPE_V1.md). Quy tắc: [AGENTS.md](../../AGENTS.md).

## Pha hiện tại

**P1 Research ưu tiên V1 + P2 Thiết kế kiến trúc.** Chưa mở pha triển khai engine Rust mới.
P0 tổ chức tài liệu đã hoàn tất; link, catalog và migration đã được kiểm tra bằng tool trước bàn giao.
Không cần giải hết client hoặc mọi mode để qua pha planning; cần biết rõ ranh giới đã hiểu và thiết kế mới.

| Pha | Trạng thái | Đầu ra | Gate hoàn thành |
|---|---|---|---|
| P0 Tổ chức docs/scope | Hoàn tất | Index, quy tắc agent, registry, scope V1, archive và migration map | Nguồn chuẩn rõ, tool và link hoạt động, không mất bằng chứng |
| P1 Tìm thông tin còn thiếu | Đang mở | QUESTIONS có owner/ưu tiên, nguồn KR/CN/TW theo build, fixture đo/source map | Mỗi câu hỏi chặn kiến trúc có câu trả lời hoặc ranh giới/DESIGN/plan đo rõ |
| P2 Cấu trúc dự án/interface | Đang thiết kế song song P1 | ARCHITECTURE và ADR; dependency, ownership, contract core/assets/net | Phương án nhất quán, hợp đồng tối thiểu được review, không còn giả định ảnh hưởng cấu trúc bị giấu |
| P3 Review sẵn sàng | Chưa mở | Checklist readiness, task triển khai nhỏ và baseline tích hợp | Kiểm các điều kiện bên dưới; cập nhật phase bằng chứng rõ ràng |
| P4 Prototype/engine Rust | Để sau planning | Workspace tối thiểu rồi lát cắt offline, sau đó online | Theo scope V1 và gate sản phẩm, không tự port toàn game |

Đây là trình tự và điều kiện, chưa phải cam kết thời gian. Các ước lượng cũ trong archive không còn là lịch V1.

## Việc tiếp theo và owner theo luồng

| Ưu tiên | Việc | Owner / reviewer | Đầu ra cập nhật vào |
|---|---|---|---|
| 1 | Phân loại source đúng build/region; xử lý kết luận web và emu đang lẫn nhau | research / RE | QUESTIONS + source register + findings |
| 1 | Map Village00→tile/object/collision; bốn spawn có dùng được không | assets/RE / core | QUESTIONS và spec assets; fixture/metadata vào evidence |
| 1 | C00/C01→Attr; time model, speed, hitbox, fuse/chain/trap còn thiếu | RE / core | QUESTIONS; spec rule khi đã có nguồn, chưa hardcode giả |
| 1 | Chốt boundary core/assets/render/net/backend và hợp đồng input/state/event | architecture / net+QA | ARCHITECTURE + ADR |
| 2 | Quyết transport, persistence tối thiểu, strategy prediction/reconciliation | net/backend / integrator | ADR với phương án và gate kiểm chứng |
| 2 | Chốt UI/content/Việt hóa V1 và đường dẫn nguồn chuẩn | client/l10n / QA | QUESTIONS + spec localization |
| 3 | Lập task prototype và chọn baseline commit để tích hợp main/worktree | integrator / reviewer | P3 readiness + task trong workflow |

Owner là vai trò, chưa phải người/agent được gán cố định. Mỗi task thực tế phải ghi người nhận,
baseline/worktree, file được sửa, dependency, đầu ra và cách kiểm theo TEAM_WORKFLOW.

## Readiness trước khi mở triển khai

- [ ] Scope V1 và registry không mâu thuẫn, không dependency vào mục later.
- [ ] Client/pack/content identity được khóa; biết rõ phần asset chưa resolve và fixture nguồn cần thêm.
- [ ] Timing/số học/collision có hướng kiểm chứng; unknown không bị gắn nhãn verified KR.
- [ ] Workspace/crate boundaries và contracts revision đầu đã được review.
- [ ] Net authority/command/snapshot/replay và event side effects được mô tả đủ để chia task độc lập.
- [ ] Quyết định transport/persistence có phương án, lý do và thí nghiệm cần làm; chưa cần backend production.
- [ ] Baseline tích hợp đã chọn, legacy oracle vẫn chạy theo đường dẫn/command đã kiểm.
- [ ] Có task prototype nhỏ, acceptance, owner và reviewer; cập nhật pha trước khi bắt đầu.

Các gate sản phẩm G1–G6 trong SCOPE_V1 áp dụng dần khi triển khai/phát hành; không cần tất cả xanh
mới bắt đầu prototype. Readiness yêu cầu kiểm soát giả định và biết phần nào prototype sẽ giải quyết.
Yêu cầu mới của người dùng có thể mở rộng task/pha; không yêu cầu xác nhận lại các quyền đã có.

## Baseline và worktree

- Mục tiêu: KR `00967`, scope `KR-00967-V1-scope-1`.
- Docs/catalog đang làm ở `/home/admin/boom-re-l10n`, nhánh `claude/l10n-kr-vi`;
  nền trước các thay đổi planning là `231ac01`; xem `git log -1`/`git status` để biết revision hiện hành.
- Main `/home/admin/boom-re` tại `0e71e8a` có server tham chiếu mới hơn snapshot l10n.
  Không tạo workspace từ bản server cũ trong worktree chỉ vì docs hiện nằm ở đó.
- `/home/admin/boomkr-re` giữ nghiên cứu/binary/metadata KR; không sao chép engine code sang repo này.
- Bản đồ đổi đường dẫn ở [DOCS_MIGRATION](../evidence/DOCS_MIGRATION.json). Không coi đường dẫn mới
  trong docs là đã tồn tại ở main cho tới khi tích hợp; dùng worktree hiện hành để chạy lệnh docs.

## Khi kết thúc một phiên

Cập nhật trạng thái đúng ở đây hoặc QUESTIONS/ADR tương ứng, giữ việc tiếp theo rõ ràng.
Không tạo một plan mới, không chuyển implementation thành done vì đã viết docs, không lấy số agent
hoặc số opcode làm phần trăm hoàn thành engine.
