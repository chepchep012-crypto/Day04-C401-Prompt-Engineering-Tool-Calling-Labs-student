---
name: notify
track: extra
kind: live_api
provider: Telegram Bot API + Gmail SMTP
requires_env: [TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GMAIL_USER, GMAIL_APP_PASSWORD, GMAIL_TO]
inputs: [text, channel, confirmed, subject, to_email]
outputs: [status, results, errors]
side_effect: true
---
# notify

Gửi thông báo văn bản qua **Telegram**, **Gmail**, hoặc **cả hai**.

## Dùng khi

- User muốn gửi bản tin / tóm tắt ra ngoài
- User nói "gửi lên Telegram", "gửi email", "gửi cho mình", "đăng bản tin"

## Không dùng khi

- User chưa xác nhận (phải gọi `clarify(response_type="yes_no")` trước)
- Chưa có nội dung cụ thể để gửi

## Params

| Param | Type | Required | Mô tả |
|---|---|---|---|
| `text` | string | ✅ | Nội dung tin nhắn |
| `channel` | "telegram" \| "gmail" \| "both" | ✅ | Kênh gửi |
| `confirmed` | boolean | ✅ | Phải là `true` — chỉ truyền sau khi user xác nhận |
| `subject` | string | — | Tiêu đề email (chỉ dùng cho Gmail) |
| `to_email` | string | — | Địa chỉ email người nhận; mặc định dùng `GMAIL_TO` env var |

## Env vars cần thiết

| Kênh | Env var |
|---|---|
| Telegram | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |
| Gmail | `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `GMAIL_TO` |

`GMAIL_APP_PASSWORD` là App Password tạo từ Google Account → Security → 2-Step Verification → App passwords (không phải password thường).

## Ví dụ

```python
send_notify(
    text="Bản tin AI hôm nay: ...",
    channel="both",
    confirmed=True,
    subject="AI Digest 2026-06-02",
    to_email="toan@example.com",
)
```
