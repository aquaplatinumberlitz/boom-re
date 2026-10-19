# Dùng chung MCP IDA với Codex

## Cấu hình hiện có

Máy đã có MCP `ida-mcp` phiên bản `20261008.0.1`, dùng qua `uvx`, và IDA tại:

`/mnt/m2sata/ida-pro-9.4-linux`

Claude cấu hình `uvx ida-mcp stdio`. OpenCode dùng cùng gói và thêm
`--agent=opencode`, cùng biến `IDADIR`. Không cài đè hoặc sửa cấu hình hai ứng dụng đó.

Codex đã có cấu hình dự án tại:

`/home/admin/boom-re-l10n/.codex/config.toml`

```toml
[mcp_servers.ida]
command = "/home/admin/.local/bin/uvx"
args = ["--offline", "ida-mcp", "stdio", "--agent=codex"]
startup_timeout_sec = 60
tool_timeout_sec = 120

[mcp_servers.ida.env]
IDADIR = "/mnt/m2sata/ida-pro-9.4-linux"
```

`--offline` dùng gói đã có trong cache, không tự tải phiên bản mới.
Cấu hình dự án là cấu hình máy cục bộ, không commit đường dẫn cá nhân này vào repo.
Cấu hình dự án còn phụ thuộc việc Codex tin cậy thư mục làm việc.

## Launcher đã tạo

Do `~/.codex/` bị gắn chỉ đọc trong phiên thực hiện, lệnh `codex mcp add` không ghi
được cấu hình toàn cục. Đã tạo launcher có thể dùng ngay khi chạy Codex trên máy:

```sh
/home/admin/bin/codex-ida -C /home/admin/boom-re-l10n
```

Launcher truyền các giá trị `mcp_servers.ida.*` bằng cờ `-c`, không cần ghi vào
`~/.codex/config.toml`. Kiểm tra cấu hình hiệu lực:

```sh
/home/admin/bin/codex-ida mcp list
```

Kết quả đã kiểm: server `ida` hiện `enabled`, lệnh trỏ tới `uvx --offline ida-mcp
stdio --agent=codex`. Đây là server stdio nên không yêu cầu đăng nhập OAuth;
trường `Auth: Unsupported` của CLI không phải lỗi kết nối.

Một phiên đang chạy không tự nhận thêm tool chỉ vì file cấu hình thay đổi. Mở Codex
qua launcher, rồi dùng `/mcp` để kiểm tra danh sách server của phiên mới.

## Nếu muốn cấu hình toàn cục

Chạy từ terminal bên ngoài sandbox đang gắn `~/.codex/` chỉ đọc:

```sh
/home/admin/.local/bin/codex mcp add ida \
  --env IDADIR=/mnt/m2sata/ida-pro-9.4-linux \
  -- /home/admin/.local/bin/uvx --offline ida-mcp stdio --agent=codex
```

Không ghi nhận bước này đã thành công trong phiên hiện tại; launcher là phương án
đã thiết lập và kiểm tra danh sách cấu hình được.

## Quyền chạy

Nếu dùng Codex CLI, `/permissions` mở lựa chọn quyền. Khi người dùng chủ động chọn
chạy toàn quyền, có thể mở phiên với:

```sh
/home/admin/bin/codex-ida --sandbox danger-full-access --ask-for-approval never \
  -C /home/admin/boom-re-l10n
```

Ứng dụng desktop có thể có lựa chọn **Full access** bên dưới ô nhập. Chính sách quản
lý của host có thể vẫn giới hạn quyền; các cờ này không bỏ được sandbox của một tiến
trình cha. Agent trong phiên đang bị hạn chế không tự thay đổi quyền thực thi của nó.

Tài liệu chính thức:

- [MCP: cấu hình stdio và CLI](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)
- [Sandbox và Full access](https://learn.chatgpt.com/docs/sandboxing)

## Mức kiểm thử thực tế

- Lệnh trợ giúp của `ida-mcp stdio` chạy được, hỗ trợ `--agent=codex`.
- Khởi động stdio và nhận được trả lời `initialize` từ server `ida`, đúng phiên bản.
- Registry của gói đăng ký đủ 6 tool: `open_database`, `execute_python`, `reference`,
  `list_databases`, `save_database`, `close_database`.
- Lời gọi `tools/list` qua stdio chưa trả lời trong thời hạn kiểm tra tại sandbox này.
  Vì vậy chưa coi đây là xác nhận kết nối đầu-cuối hoàn chỉnh.
- Không mở hay sửa IDB để thử; chưa kiểm tra việc attach GUI hoặc chạy phân tích IDA.
- Trong phiên làm việc hiện tại, tool IDA chưa được host đưa vào danh sách tool khả dụng.

Khi chạy ngoài sandbox, cần kiểm `/mcp` và thử thao tác đọc trước khi dùng phân tích.
MCP này dùng chung phần mềm và dữ liệu với Claude/OpenCode; mỗi ứng dụng có kết nối
riêng, không tự ý giành hoặc đóng database đang được ứng dụng khác sử dụng.
