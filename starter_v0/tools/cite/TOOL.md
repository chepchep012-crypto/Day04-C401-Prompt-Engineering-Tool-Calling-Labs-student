---
name: cite
track: core
kind: local_formatter
requires_env: []
inputs: [items, style]
outputs: [citations, item_count]
side_effect: false
---
# cite

Tạo danh sách trích dẫn nguồn từ các item ĐÃ thu thập. Local, không gọi API.

`style="numbered"` (mặc định) xuất `[1] Tiêu đề. Nguồn. URL`; `style="markdown"`
xuất `- [Tiêu đề](URL)`. Nếu thiếu `source` thì suy ra từ domain của URL. Không
bịa nguồn — chỉ định dạng lại dữ liệu sẵn có.

Dùng ở bước cuối để gắn nguồn cho bản tin/digest.
