# 🔎 Hướng Dẫn Sử Dụng Research Agent

Agent nghiên cứu nhỏ chạy thật: nhận yêu cầu → chọn tool → chạy tool → trả kết quả,
ghi log JSON để tối ưu prompt. Có **14 tool** và **giao diện Streamlit** tông xanh lá.

---

## 1. Chuẩn bị (chỉ làm 1 lần)

Tất cả lệnh chạy **trong thư mục `starter_v0`**.

```bash
cd starter_v0
python3 -m venv .venv          # tạo môi trường ảo (nếu chưa có)
source .venv/bin/activate      # bật venv — đầu dòng hiện (.venv)
pip install -r requirements.txt
cp .env.example .env           # tạo file key (nếu chưa có)
```

Mở `.env` và điền key:

```bash
OPENROUTER_API_KEY=...          # BẮT BUỘC để model suy nghĩ + chọn tool
TAVILY_API_KEY=...              # cho tool lookup (tìm web) — tuỳ chọn
FIRECRAWL_API_KEY=...           # cho tool fetch (đọc URL) — tuỳ chọn
RAPIDAPI_KEY=...                # cho timeline / social_search — tuỳ chọn
RAPIDAPI_TWITTER_HOST=twitter-api45.p.rapidapi.com
```

> Nhóm tool xử lý dữ liệu (`rank, dedupe, cite, keywords, format`) chạy **offline**,
> không cần key. Chỉ nhóm "tìm thật" mới cần key tương ứng.

Kiểm tra provider trước khi chạy:

```bash
python scripts/preflight_provider.py --provider openrouter
```

---

## 2. Cách chạy

### Cách A — Giao diện web (Streamlit, khuyến nghị)

```bash
cd starter_v0
source .venv/bin/activate
streamlit run app.py
```

Trình duyệt tự mở `http://localhost:8501`. Trong giao diện:
- Sidebar trái: chọn `provider = openrouter`, `version = v3`.
- Ô chat dưới cùng: gõ yêu cầu rồi Enter.
- Bấm vào ô `🔧 tên_tool(...)` để xem kết quả tool.
- Transcript tự lưu vào `transcripts/`.
- Dừng: quay lại terminal bấm `Ctrl + C`.

### Cách B — Dòng lệnh (chat.py)

```bash
python chat.py --provider openrouter --version v3
```

Gõ từng lượt, `/exit` để thoát. Transcript lưu trong `transcripts/`.

### Cách C — Chạy eval (chấm điểm tự động)

```bash
# 20 case cố định
python run_eval.py --provider openrouter --version v3 --suite base --eval-cases data/eval_base.json
# 10 case nhóm tự viết
python run_eval.py --provider openrouter --version v3 --suite group --eval-cases data/eval_group.json
```

Kết quả lưu trong `runs/*.json` (đọc `summary.case_accuracy`).

---

## 3. Agent làm được gì

### Tìm & đọc thông tin (cần key)
| Việc | Tool | Ví dụ gõ |
|---|---|---|
| Bài đăng gần đây của 1 tài khoản | `timeline` | "Tweet mới nhất của Sam Altman" |
| Tìm bài theo từ khóa | `social_search` | "Tìm bài hot nhất về DeepSeek" |
| Tin tức / tra cứu web | `lookup` | "Tin tức về Nvidia hôm nay" |
| Đọc nội dung 1 URL | `fetch` | "Tóm tắt bài này: https://..." |
| Tìm paper khoa học | `papers` | "Tìm paper về mixture of experts" |
| Trích text từ paper arXiv | `paper_text` | "Lấy nội dung paper 2401.xxxxx" |
| Tra chính sách nội bộ | `policy` | "Quy định trích dẫn nguồn của công ty?" |

### Xử lý dữ liệu đã thu thập (offline, không cần key)
| Việc | Tool |
|---|---|
| Xếp hạng theo độ liên quan | `rank` |
| Bỏ kết quả trùng | `dedupe` |
| Rút từ khóa nổi bật | `keywords` |
| Tạo danh sách trích dẫn | `cite` |
| Dựng digest markdown | `format` |

### Hành vi thông minh (đã tối ưu prompt)
- **Hỏi lại khi thiếu thông tin** (`clarify`) thay vì đoán bừa.
- **Từ chối việc ngoài phạm vi** (toán, code) — không gọi tool.
- **Xác nhận trước khi gửi** (`send`) — chỉ gửi khi bạn đồng ý.
- **Hỗ trợ nhiều lượt**: bổ sung thông tin ở lượt sau.

### Quy trình research điển hình (chuỗi tool)
> "Tổng hợp tin AI tuần này thành bản tin có nguồn"

`lookup` → `dedupe` → `rank` → `format` → `cite` → `clarify` (xác nhận) → `send`.

---

## 4. Tuỳ chỉnh

| Muốn đổi | Sửa file |
|---|---|
| Cách agent suy nghĩ / chọn tool | `artifacts/system_prompt.md` |
| Mô tả & tham số tool | `artifacts/tools.yaml` |
| Thêm tool mới | `tools/<tên>/` (TOOL.md + tool.py) + `tools/__init__.py` + `tools.yaml` |
| Màu giao diện | `.streamlit/config.toml` + CSS trong `app.py` |

Sau khi sửa prompt/tool → chạy lại eval với version mới (vd `--version v4`) để so điểm,
rồi ghi vào `artifacts/version_log.csv`.

---

## 5. Lỗi thường gặp

| Lỗi | Nguyên nhân & cách sửa |
|---|---|
| `command not found: streamlit` | Chưa bật venv → `cd starter_v0 && source .venv/bin/activate` |
| `source: no such file or directory` | Đang ở sai thư mục → phải ở trong `starter_v0` |
| Provider error / 401 | Sai/thiếu `OPENROUTER_API_KEY` trong `.env` |
| Tool tìm-thật trả lỗi | Thiếu key tương ứng (Tavily/Firecrawl/RapidAPI) — xem `TOOL-SETUP.md` |
| Giao diện chưa đổi màu | Tải lại trình duyệt `Cmd/Ctrl + Shift + R` |

---

## 6. Cấu trúc thư mục nhanh

```text
starter_v0/
  app.py              # giao diện Streamlit (bonus)
  chat.py             # chat dòng lệnh + transcript
  run_eval.py         # chấm eval
  artifacts/          # system_prompt.md, tools.yaml, version_log.csv, REPORT.md
  data/               # eval_base.json (cố định), eval_group.json (nhóm viết)
  tools/<tên>/        # mỗi tool 1 thư mục (TOOL.md + tool.py)
  runs/               # kết quả eval JSON
  transcripts/        # log chat
```
