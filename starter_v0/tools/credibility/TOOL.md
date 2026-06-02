---
name: credibility
track: extra
kind: local
provider: local
requires_env: []
inputs: [items, text, url]
outputs: [items, overall_score, overall_label, item_count]
side_effect: false
---
# credibility

Đánh giá độ tin cậy của danh sách bài viết hoặc một đoạn văn bản dựa trên các tín hiệu heuristic.

Tín hiệu được kiểm tra mỗi item:
- `https`: URL dùng HTTPS
- `trusted_domain`: domain nằm trong danh sách nguồn uy tín (Reuters, BBC, arXiv, VnExpress, v.v.)
- `has_author`: có thông tin tác giả
- `has_date`: có ngày xuất bản
- `has_summary`: summary > 80 ký tự
- `title_not_shouting`: tiêu đề không toàn chữ HOA
- `no_clickbait`: không có cụm "you won't believe", "shocking", v.v.
- `no_excessive_punctuation`: tiêu đề ≤ 3 dấu ! hoặc ?

Score: 0.0–1.0, label: `"high"` (≥ 0.75) / `"medium"` (0.40–0.75) / `"low"` (< 0.40)

Dùng khi:
- User hỏi "nguồn này có đáng tin không?", "đánh giá độ tin cậy bài này"
- Sau khi tổng hợp nhiều nguồn, muốn filter trước khi gửi / lưu

Không dùng khi:
- Items không có `url` hoặc `title` (không đủ tín hiệu để đánh giá)

Params:
- `items` (default: []): danh sách dict có `title`, `url`, `summary`, `authors`, `published`
- `text` (default: ""): văn bản thô (nếu không có `items`, dùng thay thế)
- `url` (default: ""): URL nguồn (dùng kèm `text` khi chỉ có 1 trang)
