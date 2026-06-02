---
name: rank
track: core
kind: local_formatter
requires_env: []
inputs: [items, query, top_k]
outputs: [ranked, item_count]
side_effect: false
---
# rank

Sắp xếp lại các item ĐÃ thu thập (từ `lookup` / `social_search` / `timeline`)
theo độ liên quan với một truy vấn, rồi trả về `top_k` item điểm cao nhất.

Local, không gọi API. Điểm liên quan = số từ khóa trùng nhau giữa `query` và
phần `title + summary` của mỗi item (dùng chung bộ tách từ với `_shared.terms`,
đã bỏ dấu tiếng Việt và stopwords). Không sửa nội dung item, chỉ lọc + sắp xếp.

Dùng tool này TRƯỚC `format` khi danh sách kết quả dài và cần thu gọn về những
mục liên quan nhất; không dùng để tìm dữ liệu mới.
