---
name: dedupe
track: core
kind: local_formatter
requires_env: []
inputs: [items, key]
outputs: [items, kept_count, removed_count]
side_effect: false
---
# dedupe

Loại bỏ các item trùng lặp trong một danh sách ĐÃ thu thập (từ nhiều lần
`lookup` / `social_search` / `timeline`). Local, không gọi API.

`key="url"` (mặc định) coi hai item trùng nếu cùng URL (đã chuẩn hoá bỏ dấu `/`
cuối và viết thường); `key="title"` so theo tiêu đề đã bỏ dấu tiếng Việt. Giữ
lần xuất hiện đầu tiên, bỏ các bản sau. Trả về `removed_count` để biết đã gộp
bao nhiêu mục.

Dùng sau khi gộp kết quả từ nhiều nguồn, trước `rank` / `format`.
