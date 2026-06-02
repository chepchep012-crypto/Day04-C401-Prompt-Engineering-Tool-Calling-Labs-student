---
name: knowledge
track: extra
kind: local_storage
provider: local JSON (knowledge/kb.json)
requires_env: []
inputs: [action, query, content, title, url, tags, top_k, entry_id]
outputs: [id, title, snippet, results, status]
side_effect: true  # for save/delete
---
# knowledge

Lưu và tìm kiếm knowledge base cục bộ. Dùng để xây dựng nguồn kiến thức riêng từ nội dung đã fetch/tìm kiếm.

## Khi nào dùng

| Tình huống | Action |
|---|---|
| User nói "lưu lại", "ghi nhớ", "lưu vào knowledge" | `save` |
| User hỏi và có thể có thông tin trong KB | `search` trước khi ra ngoài |
| User hỏi "trong knowledge có gì" | `list` |
| User nói "xóa entry kb0001" | `delete` |

**Luồng lý tưởng khi user hỏi:**
1. Gọi `knowledge(action=search, query=...)` trước
2. Nếu KB có kết quả tốt → trả lời từ KB (ghi rõ nguồn)
3. Nếu KB không có → dùng `lookup` / `fetch` như bình thường, rồi hỏi user có muốn lưu không

## Params

| Param | Action cần | Mô tả |
|---|---|---|
| `action` | tất cả | "save", "search", "list", "delete" |
| `content` | save | Nội dung cần lưu (text đầy đủ) |
| `title` | save | Tiêu đề (tùy chọn, tự sinh từ content) |
| `url` | save | URL nguồn (tùy chọn) |
| `tags` | save | Danh sách tag, ví dụ ["AI", "2026"] |
| `query` | search | Truy vấn tìm kiếm |
| `top_k` | search | Số kết quả trả về (mặc định 3) |
| `entry_id` | delete | ID entry cần xóa, ví dụ "kb0001" |

## Ví dụ

```yaml
# Lưu nội dung bài báo vừa fetch
knowledge(action=save, content="...", title="GPT-5 Overview", url="https://...", tags=["AI","OpenAI"])

# Tìm kiếm trước khi hỏi web
knowledge(action=search, query="GPT-5 capabilities", top_k=3)

# Liệt kê toàn bộ
knowledge(action=list)
```

Knowledge được lưu tại `knowledge/kb.json` trong thư mục project.
