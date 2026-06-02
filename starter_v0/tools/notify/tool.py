from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any

import requests

from tools._shared import TIMEOUT, err


def _send_to_telegram(text: str) -> dict[str, Any]:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID env var")
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return {"channel": "telegram", "status": "sent"}


def _send_to_gmail(text: str, subject: str, to_email: str) -> dict[str, Any]:
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    recipient = to_email or os.getenv("GMAIL_TO")
    if not gmail_user or not gmail_password:
        raise RuntimeError("Missing GMAIL_USER / GMAIL_APP_PASSWORD env var")
    if not recipient:
        raise RuntimeError("Missing recipient: set GMAIL_TO env var or pass to_email arg")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject or "Thông báo từ Research Agent"
    msg["From"] = gmail_user
    msg["To"] = recipient
    msg.attach(MIMEText(text, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=TIMEOUT) as server:
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, recipient, msg.as_string())

    return {"channel": "gmail", "status": "sent", "to": recipient}


def send_notify(
    text: str = "",
    channel: str = "telegram",
    confirmed: bool = False,
    subject: str = "",
    to_email: str = "",
) -> dict[str, Any]:
    """
    Gửi thông báo qua Telegram, Gmail, hoặc cả hai.

    Args:
        text: Nội dung tin nhắn.
        channel: Kênh gửi — "telegram", "gmail", hoặc "both".
        confirmed: Phải là True trước khi gửi thực sự.
        subject: Tiêu đề email (chỉ dùng cho Gmail).
        to_email: Địa chỉ người nhận email (tuỳ chọn; mặc định dùng GMAIL_TO env var).
    """
    if not confirmed:
        return {
            "tool": "notify",
            "status": "needs_confirmation",
            "message": "Chưa được xác nhận. Hãy hỏi user trước khi gửi.",
        }

    if not text:
        return err("notify", ValueError("text is required"))

    results: list[dict[str, Any]] = []
    errors: list[str] = []

    try:
        if channel in ("telegram", "both"):
            results.append(_send_to_telegram(text))
    except Exception as exc:
        errors.append(f"telegram: {type(exc).__name__}: {exc}")

    try:
        if channel in ("gmail", "both"):
            results.append(_send_to_gmail(text, subject, to_email))
    except Exception as exc:
        errors.append(f"gmail: {type(exc).__name__}: {exc}")

    return {
        "tool": "notify",
        "channel": channel,
        "results": results,
        "errors": errors,
        "status": "sent" if results and not errors else ("partial" if results else "failed"),
    }
