# Sáu ảnh màn đăng nhập KR 00967 (vi)

`l10n_login_art_vi.py` đọc sáu entry `FxDesktop/LoginStage` từ pack KR và dùng chung
bộ vẽ DejaVu Sans Bold / Condensed Bold với bản tiếng Anh. Giữ hàng chọn máy chủ,
ô nhập 1P/2P, checkbox và nhãn `1PLAYER`/`2PLAYER`. Các nhãn vẽ lại là “CHỌN MÁY CHỦ”,
“ID”, “MẬT KHẨU”, “DREAM” và “HAPPY”.

| Entry | Vùng chữ (x trái, y trên, x phải, y dưới; phải/dưới không tính) |
|---|---|
| `LO_LogTable00` | Tiêu đề (172, 5, 285, 21); ID (139, 94, 221, 111); mật khẩu (139, 120, 221, 137) |
| `LO_LogTable01` | Tiêu đề (204, 5, 312, 21); ID (123, 94, 199, 111); mật khẩu (123, 120, 199, 137) |
| `LO_SerDre`/`LO_SerDre2P` | (25, 4 + 24i, 87, 20 + 24i), i = 0..4 |
| `LO_SerHa`/`LO_SerHa2P` | (25, 4 + 24i, 87, 20 + 24i), i = 0..3; giữ cả 5 bản ghi frame |

Mỗi dòng pixel lấy trung vị màu từ các cột lân cận để giữ chuyển màu theo chiều dọc.
Hai nhãn có dấu tự giảm cỡ chữ vừa đủ để nét viền cách mép trên và dưới ít nhất một pixel.
Script từ chối đầu vào khác hash KR, nhãn không vừa và thay đổi pixel ngoài vùng hoặc đổi alpha.
Script kiểm I16 sau mã hóa lại: kích thước, dữ liệu frame, alpha và pixel ngoài vùng chữ phải khớp.

```sh
python3 tools/l10n_login_art_vi.py --kr CLIENT_KR --out local/login-art-vi
```

Dùng Python, Pillow từ 10 và font DejaVu Sans. Xem cỡ chữ đã dùng trong `receipt.json`.
Sau khi ảnh được duyệt, dùng `tools/l10n_build.py --lang vi --image-dir local/login-art-vi/vi-drawn`
với các tham số dựng gói đang dùng. Không cần `--allow-shape-change` cho sáu entry này.
Không commit ảnh nguồn, ảnh dựng hoặc pack.
