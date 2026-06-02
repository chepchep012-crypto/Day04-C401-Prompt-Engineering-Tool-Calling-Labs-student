---
name: keywords
track: extra
kind: local
provider: local
requires_env: []
inputs: [text, items, top_k, include_bigrams]
outputs: [keywords, top_k, source_length]
side_effect: false
---
# keywords

Trích xuất các từ khóa nổi bật (unigram và bigram) từ văn bản hoặc danh sách bài viết, xếp theo tần suất xuất hiện.

Dùng khi:
- Muốn biết chủ đề chính trong nội dung fetch được hoặc tập kết quả tìm kiếm
- User hỏi "chủ đề nổi bật là gì?", "những từ khóa chính trong bài này là gì?"
- Chuẩn bị tag / label cho bài viết trước khi lưu vào knowledge base

Không dùng khi:
- Text rỗng hoặc quá ngắn (< 50 ký tự)

Params:
- `text` (default: ""): văn bản thô để phân tích (thay thế hoặc bổ sung cho `items`)
- `items` (default: []): danh sách dict có `title` và `summary` — nối lại thành văn bản
- `top_k` (default: 10): số từ khóa trả về
- `include_bigrams` (default: true): có tính cặp từ liền nhau không
