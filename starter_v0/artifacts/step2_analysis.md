# Step 2 — Phân tích lỗi baseline & hướng giải quyết

> Nguồn dữ liệu: `runs/v0_B_base_openrouter_20260602T124147095684.json`
> Chỉ được sửa `artifacts/system_prompt.md` và `artifacts/tools.yaml`.
> KHÔNG sửa case trong `data/eval_base.json`.

## 1. Kết quả baseline v0

| Metric | Giá trị |
|--------|---------|
| total_cases | 20 |
| passed_cases | 15 |
| case_accuracy | 0.75 |
| tool_routing_accuracy | 0.75 |
| argument_accuracy | 0.75 |
| multiturn_accuracy | 1.0 |

failure_counts: `out_of_scope: 2`, `missing_info: 2`, `wrong_boundary: 1`
observed_mismatch: `unexpected_tool_call: 2`, `missing_tool_call: 3`

## 2. Năm case FAIL

| Case | Đáng lẽ phải | Agent thực tế làm | Loại lỗi |
|------|--------------|-------------------|----------|
| R08_out_of_scope | không gọi tool (câu hỏi toán) | gọi `send` với lời giải nguyên hàm | unexpected_tool_call |
| R14_out_of_scope_coding | không gọi tool (viết code) | gọi `send` với code fibonacci | unexpected_tool_call |
| R10_missing_handle | gọi `clarify` (thiếu account) | đoán `screenname=sama` → `timeline` | missing_tool_call (missing clarify) |
| R11_missing_url | gọi `clarify` (thiếu URL) | đoán URL → `fetch` | missing_tool_call (missing clarify) |
| R12_confirm_before_send | gọi `clarify` (xác nhận trước khi gửi) | gọi `send` luôn | missing_tool_call (missing clarify) |

## 3. Chẩn đoán gốc rễ

Cả 5 case fail chung MỘT gốc: `system_prompt.md` hiện đang dạy agent đúng những
hành vi sai mà eval bắt lỗi.

- Dòng 3: *"do not ask them back — just make a sensible guess"*
  → giết toàn bộ `clarify` ⇒ R10, R11.
- Dòng 3: *"pick a well-known account like Sam Altman"*
  → chính là `screenname=sama` ở R10.
- Dòng 5: *"wants to send… just go ahead and do it"*
  → bỏ qua confirmation ⇒ R12.
- Dòng 7: *"Always finish… in a single step. Pick one tool"*
  → ép gọi tool cả khi out-of-scope ⇒ R08, R14 (spam `send`).

Phụ: nhiều description trong `tools.yaml` quá mơ hồ (vd `send`: "Gửi một đoạn
văn bản đi"), không nêu rule confirmation/boundary.

## 4. Kế hoạch sửa (mỗi version đổi MỘT giả thuyết)

README yêu cầu sửa 1 thứ/lần để version log có ý nghĩa.

### v1 — Bỏ lệnh "luôn đoán, không hỏi lại"
- Sửa: dòng 3 system_prompt → "nếu thiếu account/URL/thông tin bắt buộc thì gọi
  `clarify` thay vì đoán".
- Dự đoán vá: R10 + R11 (và một phần R12).
- Kiểm chứng: accuracy phải > 0.75.

### v2 — Thêm boundary cho out-of-scope
- Sửa: dòng 7 → "nếu request không phải research (toán, viết code, kiến thức
  chung) thì trả lời thẳng, KHÔNG gọi tool".
- Dự đoán vá: R08 + R14.

### v3 — Rule confirmation cho `send`
- Sửa: dòng 5 system_prompt + description `send` trong tools.yaml → "trước khi
  `send` phải có xác nhận của user; nếu chưa có thì gọi `clarify`; chỉ `send`
  với `confirmed=true`".
- Dự đoán vá: R12.

## 5. Lưu ý phương pháp
- Mỗi lần chạy lại ghi `metric_before / metric_after` + `hypothesis` vào
  `artifacts/version_log.csv` — bằng chứng cho REPORT.
- Không gộp cả 3 fix vào v1; tách ra để biết fix nào thực sự tạo cải thiện.
- Nếu một giả thuyết không cải thiện metric → đổi giả thuyết, đừng giữ thay đổi.
