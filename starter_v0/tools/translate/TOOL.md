---
name: translate
track: extra
kind: live_api
provider: MyMemory
requires_env: []
inputs: [text, source_lang, target_lang]
outputs: [translated, original, source_lang, target_lang, match_quality]
side_effect: false
---
# translate

Dịch một đoạn văn bản từ ngôn ngữ nguồn sang ngôn ngữ đích dùng MyMemory API (miễn phí, không cần API key).

Dùng khi:
- User muốn dịch nội dung fetch được từ URL tiếng nước ngoài
- User hỏi "dịch cái này ra tiếng Việt" hoặc "translate to English"
- Cần hiểu nội dung bài báo/tweet bằng ngôn ngữ khác

Không dùng khi:
- Câu hỏi đã bằng ngôn ngữ user muốn
- User không yêu cầu dịch

Params:
- `text` (required): văn bản cần dịch
- `source_lang` (default: "auto"): mã ngôn ngữ nguồn, ví dụ "en", "vi", "ja"; "auto" để tự detect
- `target_lang` (default: "en"): mã ngôn ngữ đích, ví dụ "vi" cho tiếng Việt, "en" cho tiếng Anh
