# Day 04 Lab v2 Report — Research Agent

## Team

- Team: C401-Group
- Members: Phạm Thị Tuyết Nga - 2A202600877, Nguyễn Đức Toàn - 2A202600733
- Provider/model: openrouter / openai/gpt-4o-mini

## Final Metrics

- Final version: v3
- Final artifact_version: v3+p7701addc8fa0+t6dbf7260b213
- Best base run file: runs/v3_B_base_openrouter_20260602T125231911688.json
- Base case accuracy: 0.90 (18/20)
- Base tool routing accuracy: 0.90
- Base argument accuracy: 0.90
- Group eval run file: runs/v3_B_group_openrouter_20260602T125556836101.json
- Group eval accuracy: 0.80 (8/10)
- Chat transcript file: transcripts/v3_openrouter_20260602T132825143308.transcript.json

## Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline — starter prompt intentionally wrong | Establishes baseline | — | 0.70 | runs/v0_B_base_openrouter_20260602T124546254673.json |
| v1 | system_prompt.md | Thay "không bao giờ hỏi / đoán bừa" bằng quy tắc clarify rõ ràng khi thiếu handle/URL → fix R08 R10 R11 R14 | 0.70 | 0.80 | runs/v1_B_base_openrouter_20260602T124823123118.json |
| v2 | tools.yaml | Thêm `response_type` vào `required` của `clarify` → agent buộc truyền giá trị, fix wrong_arg_value R10 R11 | 0.80 | 0.90 | runs/v2_B_base_openrouter_20260602T125050966130.json |
| v3 | system_prompt.md | Thêm quy tắc confirm-before-send và bỏ giới hạn single-step → fix R12, cho phép parallel tools R13 | 0.90 | 0.90 | runs/v3_B_base_openrouter_20260602T125231911688.json |

## Failure Analysis

Dữ liệu từ `results[*].result.failures` trong run JSON.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix Applied |
|---|---|---|---|---|
| R08_out_of_scope | out_of_scope | `send(text="x³/3+C")` | Prompt bảo đoán/làm ngay → gọi tool với câu toán học ngoài scope | v1: thêm quy tắc scope vào system_prompt |
| R10_missing_handle | missing_info (v0), wrong_arg_value (v1) | v0: `timeline(screenname="sama")` / v1: `clarify` thiếu response_type | v0: đoán handle; v1: gọi đúng tool nhưng thiếu arg bắt buộc | v1: clarify rule; v2: response_type required |
| R11_missing_url | missing_info (v0), wrong_arg_value (v1) | v0: `fetch(url="example.com")` / v1: `clarify` thiếu response_type | Tương tự R10 nhưng với URL | v1 + v2 |
| R12_confirm_before_send | wrong_boundary | `send(text=...)` không qua confirm | Prompt bảo "cứ gửi luôn" → gửi không hỏi | v3: thêm confirm-before-send rule |
| R13_parallel_web_and_tweets | wrong_tool | Chỉ gọi 1 trong 2 tools | Prompt giới hạn single-step → bỏ lỡ tool thứ 2 | v3: bỏ single-step restriction |
| R14_out_of_scope_coding | out_of_scope | Gọi tool với câu hỏi code Python | Tương tự R08 | v1: scope rule |
| R01_user_tweets_routing (v3) | wrong_tool | `clarify(response_type="yes_no")` thay vì `timeline` | v3 prompt confirm-before-send quá rộng, agent hỏi confirm cho cả timeline | Cần tinh chỉnh thêm: confirm chỉ áp dụng cho `send`, không áp dụng cho read-only tools |
| R05_limit_arg (v3) | wrong_arg_value | `clarify(response_type="yes_no")` thay vì `timeline` | Tương tự R01 v3 — side-effect của v3 fix | Cần thêm rule: clarify yes_no chỉ khi tool có side-effect |

## Team Eval Cases

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| GR01_fetch_explicit_url | Câu có URL → dùng fetch, không dùng lookup | `fetch(url=...)` | PASS |
| GR02_handle_mapping_lecun | Map tên Yann LeCun → handle ylecun | `timeline(screenname="ylecun")` | PASS |
| GR03_out_of_scope_recipe | Yêu cầu nấu ăn → từ chối không gọi tool | no_tool | PASS |
| GR04_timeframe_month | "tháng này" → timeframe=month | `lookup(timeframe="month")` | PASS |
| GR05_missing_search_keyword | Thiếu keyword → clarify trước | `clarify(response_type="text")` | PASS |
| GM01_carryover_search_type | 3 turns: carry query, cập nhật search_type=Top | `social_search(search_type="Top")` | FAIL (extra_tool_call) |
| GM02_carryover_limit_new_handle | 3 turns: đổi handle JeffBezos, carry limit=5 | `timeline(screenname="JeffBezos", limit=5)` | PASS |
| GM03_switch_timeframe | 3 turns: cập nhật timeframe week→month | `lookup(timeframe="month")` | FAIL (extra_tool_call) |
| GM04_multiturn_confirm_then_send | 3 turns: user confirm → send với confirmed=true | `send(confirmed=true)` | PASS |
| GM05_correction_topic | 3 turns: sửa query blockchain→Web3 | `lookup(query="Web3")` | PASS |

## Live Chat Evidence

Transcript: `transcripts/v3_openrouter_20260602T132825143308.transcript.json`

| Turn | User Request | Tool Calls | Outcome |
|---|---|---|---|
| 1 | "cho t 5 bài báo về ai tháng 5" | `papers(query="AI", sort_by="lastUpdatedDate")` | PASS — trả về 5 paper arXiv đúng chủ đề |
| 2 | "Tin tức AI nổi bật hôm nay là gì?" | `lookup(topic="news", timeframe="day")` | PASS — 5 tin tức AI từ Washington Post, PitchBook, v.v. |
| 3 | "Tóm tắt tweet mới nhất giúp mình" (thiếu account) | `clarify` hỏi tên tài khoản | PASS — agent hỏi lại đúng hành vi |
| 4 | "Của Sam Altman" (bổ sung sau clarify) | `timeline(screenname="sama")` | PASS — agent map tên → handle, gọi đúng tool |
| 5 | "Đăng bản tin lên Telegram: ..." | `clarify(response_type="yes_no")` | PASS — agent hỏi xác nhận trước khi gửi |

## Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (confirm) | runs/v3_B_base_openrouter_20260602T125231911688.json (R12) + transcript turn 5 | Agent gọi `clarify(yes_no)` trước khi send, không tự gửi | Cần `confirmed=true` trong args send — tool check flag này trước khi gửi |
| arXiv papers | transcript turn 1, tools/papers/tool.py | `papers` tool gọi arXiv API, trả về 5 paper real-time | Không cần API key, giới hạn rate arXiv |
| company policy | tools/policy/tool.py + tools.yaml | `policy` tool search local markdown KB trong company_policy/ | Chỉ tìm trong file local, không real-time |
| Extra tool: translate | tools/translate/tool.py + TOOL.md | Dịch text qua MyMemory API, không cần API key | Giới hạn 500 ký tự/request free tier; source_lang phải là ISO code, không hỗ trợ "auto" |

## Reflection

**Fixes thuộc `system_prompt.md`:**
- Quy tắc clarify khi thiếu handle/URL (hành vi của agent, không phải schema)
- Quy tắc confirm-before-send (boundary hành động write vs read)
- Cho phép parallel tool calls (bỏ giới hạn single-step)
- Định nghĩa scope: loại câu nào không dùng tool

**Fixes thuộc `tools.yaml`:**
- Thêm `response_type` vào `required` của `clarify` — đây là schema, model phụ thuộc vào required field để biết phải truyền arg đó
- Mô tả rõ hơn trong `description` của `clarify` để hướng dẫn khi nào dùng `text` vs `yes_no`

**Failure cần manual review:**
- R01/R05 trong v3: agent hỏi confirm cho cả `timeline` (read-only tool) — đây là over-correction từ confirm-before-send rule. Grader tự động chấm sai nhưng root cause là ambiguity trong prompt, cần human review để phân biệt.
- GM01/GM03 trong group eval: agent gọi thêm tool thừa trong multi-turn — có thể hợp lý trong real conversation nhưng eval chấm là fail.

**Cải thiện tiếp theo:**
1. Tinh chỉnh confirm-before-send: chỉ áp dụng cho tool có `side_effect: true` (send), không áp dụng cho read-only tools
2. Thêm name→handle mapping rõ hơn trong tools.yaml (description của `timeline`)
3. Viết thêm eval case để test edge case: handle không tồn tại, URL không truy cập được
4. Cân nhắc model mạnh hơn (gpt-4o) cho multi-turn cases phức tạp

