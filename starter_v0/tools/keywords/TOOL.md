---
name: keywords
track: core
kind: local_formatter
requires_env: []
inputs: [items, text, top_k]
outputs: [keywords, unique_terms]
side_effect: false
---
# keywords

Rút các từ khóa nổi bật từ các item đã thu thập (và/hoặc một đoạn `text`).
Local, không gọi API.

Đếm tần suất từ trên phần `title + summary` của mỗi item bằng chung bộ tách từ
`_shared.terms` (đã bỏ dấu tiếng Việt và stopwords), trả về `top_k` từ xuất hiện
nhiều nhất kèm số lần. Hữu ích để tóm tắt chủ đề chính của một tập kết quả hoặc
gợi ý truy vấn tiếp theo.
