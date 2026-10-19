# Register nguồn web KR / CN / TW

Cập nhật: 2026-10-19. Nguồn chuẩn về các web source đã được đọc trong phiên research trước;
lượt dọn docs này chỉ hợp nhất ghi chú, **không xác minh lại truy cập hoặc luật**.
Target **KR PC build 00967**. Tất cả nguồn dưới đây có `target_build_match: unconfirmed`;
không claim nào tự trở thành ruleset đã nghiệm thu. Backlog: [QUESTIONS](../QUESTIONS.md).

Ngày truy cập của sáu nguồn: **2026-10-19**, theo ghi nhận research trước.
Chất lượng official và mức phù hợp build là hai trục riêng. Không suy ngày bài từ copyright footer.

| Source ID / khu vực | URL / locator | Ngày xuất bản / phạm vi | Kết luận hỗ trợ và giới hạn |
|---|---|---|---|
| WEB-KR-001 / KR official Nexon | [Patch notice](https://ca.nexon.com/News/Notice/Content/140373), mục 5–6; mục 4 là recipe event | Bài 2023-03-08, áp dụng 2023-03-09; patch lịch sử | Recipe bột cơ bản và đổi xác suất phân giải Magic Market; hạng ★★★ vàng 20% / đỏ 60% / trắng 20%. Chưa kiểm chuỗi patch sau tới 00967; không trộn recipe event vào recipe thường. Ngoài V1. |
| WEB-CN-001 / CN official SDO | [Item guide](https://bnb.web.sdo.com/web3/intro/items.asp), mô tả từng item | Không xác định ngày/build; PC BnB CN | Kim thoát bẫy, phi tiêu kích nổ, khiên 2 giây, spring vượt bom/vật cản. Không đủ cooldown/collision/tick; không xác nhận khiên KR. Các item này ngoài V1. |
| WEB-CN-002 / CN official SDO | [PvP modes](https://bnb.web.sdo.com/web5/gameinfo/gameinfo_2.asp?CategoryID=3018&cid=1&id=121355), đoạn theo mode | Không xác định ngày/build | Điều kiện thắng/cơ chế Zombie, Hunting, Race, Captain, Bomb; Zombie ít nhất 5 người, bắt đầu 2 zombie. Chưa xác nhận mode/rules tương ứng KR; ngoài V1, không dùng suy luật Battle FFA. |
| WEB-CN-003 / CN official SDO | [Controls](https://bnb.web.sdo.com/web5/gameinfo/gameinfo_1.asp?id=121317), ready/start/kick và room/chat | Không xác định ngày/build | Tham khảo luồng ready/cancel, quyền chủ phòng và room/chat commands. Hỗ trợ checklist UI; không chứng minh wire protocol, authority hoặc toàn bộ policy V1. Liên quan Q-008/Q-012. |
| WEB-CN-004 / CN official SDO | [Equipment](https://bnb.web.sdo.com/web5/gameinfo/gameinfo_1.asp?id=121319), equip/use và Hero | Không xác định ngày/build | Cách trang bị/phím dùng item, Hero có trang bị riêng. Checklist UI/backend cho later; không đủ mô hình inventory hoặc xác nhận KR. |
| WEB-TW-001 / TW official Beanfun | [SnowBall event guide](https://tw.beanfun.com/bnb/event/20120116_snow/p1.html), hướng ném/range/snowman/rescue | Event 2012-01-16–2012-03-01; ngày xuất bản chưa xác nhận | Ném hướng nhìn, range cơ bản 3 ô, gặp vật cản/người thì nổ; ba giai đoạn snowman, đồng đội chạm hồi một giai đoạn. Cách đếm range và phiên bản KR chưa xác nhận. Ngoài V1. |

## Khi bổ sung nguồn hoặc dùng một claim

- Ghi source ID, URL, title/locator, access date, publication date nếu biết, region/build/event,
  claim hỗ trợ và giới hạn. Link source từ findings/spec; không chép một bảng luật sang nhiều plan.
- Claim có ID riêng, feature ID, giá trị/đơn vị, thuật ngữ gốc, reviewer, phản chứng và trạng thái
  candidate/reviewed/accepted/rejected/unresolved. Theo quy tắc [AGENTS](../../../AGENTS.md).
- Nguồn official khác region chỉ là `archive_other_region`; chứng minh tương ứng build là task riêng.
  Nguồn trùng nội dung không tính độc lập; search snippet chưa đọc chỉ là đầu mối.
- Một số deep link Nexon từng redirect Home/lỗi tải; không kết luận website mất hết dữ liệu.
  Khi lỗi, ghi URL/thời điểm/phạm vi truy cập, tìm archive hoặc nguồn khác có xuất xứ.
- Chưa có nguồn web trong register xác nhận fuse/tick/collision KR chính xác hoặc toàn bộ recipe
  build 00967. Đây là giới hạn của lượt tìm trước, không phải kết luận Internet không có thông tin.

Không lưu toàn bài có bản quyền vào repo. Bổ sung ghi chú ngắn có locator; nếu cần artifact,
ghi provenance/hash/phạm vi sử dụng ở evidence. Research mới theo task ưu tiên trong QUESTIONS.
