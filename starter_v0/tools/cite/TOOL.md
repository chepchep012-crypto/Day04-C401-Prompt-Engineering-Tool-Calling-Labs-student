---
name: cite
track: extra
kind: local
provider: local
requires_env: []
inputs: [items, style, numbered]
outputs: [citations, markdown, count, style]
side_effect: false
---
# cite

Tạo danh sách trích dẫn có định dạng từ danh sách bài viết / bài báo.

Dùng khi:
- User muốn trích dẫn nguồn sau khi đọc kết quả từ `lookup`, `papers`, `fetch`
- Tạo bibliography cho bản tin / báo cáo
- User hỏi "liệt kê nguồn", "danh sách tài liệu tham khảo"

Không dùng khi:
- Items không có trường `title` hoặc `url`

Params:
- `items` (required): danh sách dict, mỗi item có thể có `title`, `url`, `source`, `authors`, `published`
- `style` (default: "plain"): kiểu trích dẫn — `"plain"` (đơn giản), `"apa"` (học thuật), `"mla"`
- `numbered` (default: true): có đánh số thứ tự không
