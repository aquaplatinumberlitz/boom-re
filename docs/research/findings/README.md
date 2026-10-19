# Findings — kết quả kỹ thuật hiện có

Các tài liệu dưới chủ yếu mô tả **client VN** và hạ tầng tham chiếu. Mỗi phép áp dụng sang KR phải
ghi đúng mức bằng chứng; không lấy trạng thái runtime VN làm trạng thái runtime KR.

| Tài liệu | Dùng khi |
|---|---|
| [VN_FEATURES_REFERENCE](VN_FEATURES_REFERENCE.md) | Tra chức năng/opcode VN; không phải catalog KR |
| [VN_RUNTIME_REFERENCE](VN_RUNTIME_REFERENCE.md) | Tra cách chạy Wine/WinBoat và giới hạn snapshot cũ |
| [VN_DEVIRT_STATUS](VN_DEVIRT_STATUS.md) | Tra các site/patch và giới hạn RE VN |
| [DEVIRT_METHOD](DEVIRT_METHOD.md) | Tra phương pháp điều tra khối VM |
| [VM_METHOD](VM_METHOD.md) | Tra hạ tầng snapshot/emulation |

Nghiên cứu KR chuyên sâu hiện ở `/home/admin/boomkr-re/docs/`; xem `kr.md`, `kr-content.md`,
`kr-data.md`. Đây là repo tham chiếu ngoài worktree; không copy code hoặc coi mọi kết luận cũ đã được audit.
Manifest/probe trong [evidence](../../evidence/README.md) là dữ liệu đã quét trực tiếp cho baseline hiện tại.

Kết quả mới gắn với ID trong [QUESTIONS](../QUESTIONS.md), có nguồn, kết luận và giới hạn.
Chỉ thêm một file khi chủ đề độc lập; không sinh file tổng kết theo agent/phiên.
