---
name: dedup
track: extra
kind: local
provider: local
requires_env: []
inputs: [items, key, title_threshold]
outputs: [items, original_count, removed]
side_effect: false
---
# dedup

Bỏ các kết quả trùng lặp từ một danh sách `items` (kết quả từ `lookup`, `papers`, `social_search`, v.v.).

Dùng khi:
- Ghép kết quả từ nhiều nguồn / nhiều lần gọi tool và cần loại trùng
- Danh sách trả về có cùng bài viết từ nhiều nguồn aggregate

Không dùng khi:
- Danh sách chỉ có 1 nguồn, ít kết quả — overhead không cần thiết

Params:
- `items` (required): danh sách dict có trường `url` và/hoặc `title`
- `key` (default: "url"): chiến lược so sánh — `"url"` (exact URL), `"title"` (fuzzy title), `"both"` (loại nếu url HOẶC title trùng)
- `title_threshold` (default: 0.80): ngưỡng overlap từ khóa để coi là trùng title (0.0–1.0)
