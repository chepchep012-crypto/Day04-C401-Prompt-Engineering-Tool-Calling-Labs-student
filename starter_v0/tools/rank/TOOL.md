---
name: rank
track: extra
kind: local
provider: local
requires_env: []
inputs: [query, items, top_k]
outputs: [items, query, top_k]
side_effect: false
---
# rank

Xếp hạng danh sách `items` theo độ liên quan tới một câu truy vấn. Mỗi item được gắn thêm trường `_relevance` (0.0–1.0).

Dùng khi:
- Nhận được nhiều kết quả từ `lookup` / `papers` / `social_search` và muốn sắp xếp theo mức độ liên quan thực sự đến câu hỏi của user
- Kết hợp với `dedup` để lọc và xếp hạng kết quả tổng hợp

Không dùng khi:
- Chỉ có 1–2 items, không cần xếp hạng
- Items đã được tool nguồn sắp xếp theo relevance (ví dụ: `papers(sort_by="relevance")`)

Params:
- `query` (required): câu truy vấn gốc dùng để so sánh
- `items` (required): danh sách dict có trường `title`, `summary`, `source`
- `top_k` (default: 0): số item giữ lại sau khi xếp hạng; 0 = giữ tất cả
