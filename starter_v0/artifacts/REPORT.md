# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: 05
- Members: Phạm Thị Tuyết Nga - 2A202600877, Nguyễn Đức Toàn - 2A202600733
- Provider/model: openrouter / openai/gpt-4o-mini

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent: tìm tin tức theo từ khóa, lấy tweet theo tài khoản, đọc nội dung URL, tìm bài báo khoa học trên arXiv, tổng hợp thành digest, và gửi lên Telegram khi được người dùng xác nhận.

**Link dùng thử (deploy):**

> URL: _(chạy local qua Cloudflare Tunnel — xem README để lấy link tunnel hiện tại)_

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng khi thiếu thông tin bắt buộc (text hoặc yes/no) | Không |
| timeline | Lấy các bài đăng gần đây của một tài khoản Twitter/X | Không |
| social_search | Tìm kiếm nội dung trên mạng xã hội theo từ khóa | Không |
| lookup | Tra cứu tin tức / thông tin trên internet theo từ khóa và khoảng thời gian | Không |
| fetch | Lấy và đọc nội dung từ một URL bất kỳ | Không |
| format | Trình bày dữ liệu đã có thành văn bản theo nhiều template | Không |
| send | Gửi văn bản (yêu cầu xác nhận trước khi gửi) | Không |
| papers | Tìm bài báo khoa học trên arXiv theo từ khóa | Không |
| paper_text | Lấy nội dung text đầy đủ của một bài báo arXiv | Không |
| policy | Tìm kiếm trong tài liệu nội bộ của công ty | Không |
| notify | Gửi thông báo qua Telegram, Gmail, hoặc cả hai (yêu cầu xác nhận) | Không |
| knowledge | Lưu và tìm kiếm knowledge base cục bộ (save/search/list/delete) | Không |
| translate | Dịch văn bản giữa các ngôn ngữ qua MyMemory API | **Có** |

## A3. Câu hỏi mẫu để thử

1. "Cho tôi 5 bài báo mới nhất về AI tháng này"
2. "Tin tức AI nổi bật hôm nay là gì?"
3. "Tóm tắt tweet mới nhất của Sam Altman"
4. "Tìm bài viết tại https://example.com/article và dịch sang tiếng Việt"
5. "Đăng bản tin AI hôm nay lên Telegram"

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

- Final version: v3
- Final artifact_version: v3+p7701addc8fa0+t6dbf7260b213
- Best base run file: runs/v3_B_base_openrouter_20260602T125231911688.json
Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline — starter prompt intentionally wrong | Establishes baseline | — | 0.70 | runs/v0_B_base_openrouter_20260602T124546254673.json |
| v1 | system_prompt.md | Thay "không bao giờ hỏi / đoán bừa" bằng quy tắc clarify rõ ràng khi thiếu handle/URL → fix R08 R10 R11 R14 | 0.70 | 0.80 | runs/v1_B_base_openrouter_20260602T124823123118.json |
| v2 | tools.yaml | Thêm `response_type` vào `required` của `clarify` → agent buộc truyền giá trị, fix wrong_arg_value R10 R11 | 0.80 | 0.90 | runs/v2_B_base_openrouter_20260602T125050966130.json |
| v3 | system_prompt.md | Thêm quy tắc confirm-before-send và bỏ giới hạn single-step → fix R12, cho phép parallel tools R13 | 0.90 | 0.90 | runs/v3_B_base_openrouter_20260602T125231911688.json |

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope | out_of_scope | `send(text="x³/3+C")` | Prompt bảo đoán/làm ngay → gọi tool với câu toán học ngoài scope | v1: thêm quy tắc scope vào system_prompt |
| R10_missing_handle | missing_info (v0), wrong_arg_value (v1) | v0: `timeline(screenname="sama")` / v1: `clarify` thiếu response_type | v0: đoán handle; v1: gọi đúng tool nhưng thiếu arg bắt buộc | v1: clarify rule; v2: response_type required |
| R11_missing_url | missing_info (v0), wrong_arg_value (v1) | v0: `fetch(url="example.com")` / v1: `clarify` thiếu response_type | Tương tự R10 nhưng với URL | v1 + v2 |
| R12_confirm_before_send | wrong_boundary | `send(text=...)` không qua confirm | Prompt bảo "cứ gửi luôn" → gửi không hỏi | v3: thêm confirm-before-send rule |
| R13_parallel_web_and_tweets | wrong_tool | Chỉ gọi 1 trong 2 tools | Prompt giới hạn single-step → bỏ lỡ tool thứ 2 | v3: bỏ single-step restriction |
| R14_out_of_scope_coding | out_of_scope | Gọi tool với câu hỏi code Python | Tương tự R08 | v1: scope rule |
| R01_user_tweets_routing (v3) | wrong_tool | `clarify(response_type="yes_no")` thay vì `timeline` | v3 prompt confirm-before-send quá rộng, agent hỏi confirm cho cả timeline | Cần tinh chỉnh: confirm chỉ áp dụng cho `send`, không cho read-only tools |
| R05_limit_arg (v3) | wrong_arg_value | `clarify(response_type="yes_no")` thay vì `timeline` | Tương tự R01 v3 — side-effect của v3 fix | Cần thêm rule: clarify yes_no chỉ khi tool có side-effect |

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

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

## B4. Live Chat Evidence

### Session 1 — CLI chat (v3)
Transcript: `transcripts/v3_openrouter_20260602T132825143308.transcript.json`

| Turn | User Request | Tool Calls | Outcome |
|---|---|---|---|
| 1 | "chào bạn" | _(không gọi tool)_ | PASS — agent chào lại bình thường |
| 2 | "cho t 5 bài báo về ai tháng 5" | `papers(query="AI", max_results=5, sort_by="lastUpdatedDate")` | PASS — trả về 5 paper arXiv đúng chủ đề |
| 3 | "Tin tức AI nổi bật hôm nay là gì?" | `lookup(query="AI", topic="news", timeframe="day")` | PASS — 5 tin tức AI từ Washington Post, PitchBook, Skift, v.v. |
| 4 | "Tóm tắt tweet mới nhất giúp mình" (thiếu account) | `clarify(question="...", response_type="text")` | PASS — agent hỏi lại tên tài khoản đúng hành vi |
| 5 | "Của Sam Altman" (bổ sung sau clarify) | `timeline(screenname="sama", limit=5)` | PASS — agent map tên người → handle, gọi đúng tool |
| 6 | "Đăng bản tin lên Telegram: ..." | `clarify(question="...", response_type="yes_no")` | PASS — agent hỏi xác nhận trước khi gửi |

### Session 2 — UI chat: Tin tức AI hôm nay (14:29)
Transcript: `transcripts/ui_v3_openrouter_20260602T142959158997.transcript.json`

| Turn | User Request | Tool Calls | Outcome |
|---|---|---|---|
| 1 | "Tin tức AI hôm nay" | `lookup(query="AI", topic="news", timeframe="day", max_results=5)` | PASS — 5 tin tức từ Marketing Week, PitchBook, Washington Post, Insurance Journal, Skift |

### Session 3 — UI chat: Bài báo AI tháng này (14:35)
Transcript: `transcripts/ui_v3_openrouter_20260602T143502848624.transcript.json`

| Turn | User Request | Tool Calls | Outcome |
|---|---|---|---|
| 1 | "5 bài báo về AI tháng này" | `papers(query="AI", max_results=5, sort_by="lastUpdatedDate")` | PASS — 5 paper arXiv: WorldLens, STABLEVAL, Autonomous Cosmology, U4D LiDAR, AI Weather Forecasting |

### Session 4 — UI chat: Bài báo AI (14:50)
Transcript: `transcripts/ui_v3_openrouter_20260602T145050270066.transcript.json`

| Turn | User Request | Tool Calls | Outcome |
|---|---|---|---|
| 1 | "5 bài báo về AI tháng này" | `papers(query="AI", max_results=5, sort_by="lastUpdatedDate")` | PASS — cùng kết quả 5 paper arXiv, agent trả lời bằng tiếng Việt |

### Session 5 — UI chat: Bài báo AI (14:54)
Transcript: `transcripts/ui_v3_openrouter_20260602T145427201933.transcript.json`

| Turn | User Request | Tool Calls | Outcome |
|---|---|---|---|
| 1 | "5 bài báo về AI tháng này" | `papers(query="AI", max_results=5, sort_by="lastUpdatedDate")` | PASS — 5 paper arXiv, trả lời tiếng Việt |

### Session 6 — UI chat: Multi-turn (15:06)
Transcript: `transcripts/ui_v3_openrouter_20260602T150650070535.transcript.json`

| Turn | User Request | Tool Calls | Outcome |
|---|---|---|---|
| 1 | "5 bài báo về AI tháng này" | `papers(query="AI", max_results=5, sort_by="lastUpdatedDate")` | PASS — 5 paper arXiv |
| 2 | "Tweet mới nhất của Elon Musk" | `clarify(question="Bạn có muốn xem tweet...?", response_type="yes_no")` | PASS — agent hỏi confirm trước khi lấy timeline (read-only, nhưng đây là over-confirm từ v3 rule) |
| 3 | "có" (xác nhận) | `timeline(screenname="elonmusk", limit=1)` | API trả 403 Forbidden — agent báo lỗi gracefully, không crash |
| 4 | "bài báo ai mới nhất" | `papers(query="AI", max_results=5, sort_by="lastUpdatedDate")` | PASS — agent tiếp tục đúng sau lỗi API trước đó |

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | runs/v3_B_base_openrouter_20260602T125231911688.json (R12) + transcript turn 5 | Agent gọi `clarify(yes_no)` trước khi send, không tự gửi | Cần `confirmed=true` trong args send — tool check flag này trước khi gửi |
| arXiv/company policy | transcript turn 1 + tools/papers/tool.py + tools/policy/tool.py | `papers` gọi arXiv API real-time; `policy` tìm local markdown KB trong company_policy/ | arXiv không cần API key nhưng có rate limit; policy chỉ tìm file local, không real-time |
| UI | templates/index.html + app_ui.py | Giao diện chat qua Flask, hỗ trợ hiển thị tool calls và stream | Chạy local, cần Cloudflare Tunnel để expose public |
| Extra tool: translate | tools/translate/tool.py + tools/translate/TOOL.md | Dịch text qua MyMemory API, không cần API key | Giới hạn 500 ký tự/request free tier; source_lang phải là ISO code, không hỗ trợ "auto" |

## B6. Reflection

- **Fixes thuộc `system_prompt.md`:** Quy tắc clarify khi thiếu handle/URL (hành vi của agent, không phải schema); quy tắc confirm-before-send (boundary write vs read); cho phép parallel tool calls (bỏ giới hạn single-step); định nghĩa scope — loại câu nào không dùng tool.

- **Fixes thuộc `tools.yaml`:** Thêm `response_type` vào `required` của `clarify` (schema — model phụ thuộc vào required field để biết phải truyền arg đó); mô tả rõ hơn trong `description` của `clarify` để hướng dẫn khi nào dùng `text` vs `yes_no`.

- **Failure cần manual review:** R01/R05 trong v3 — agent hỏi confirm cho cả `timeline` (read-only tool), đây là over-correction từ confirm-before-send rule; grader tự động chấm sai nhưng root cause là ambiguity trong prompt. GM01/GM03 trong group eval — agent gọi thêm tool thừa trong multi-turn, có thể hợp lý trong real conversation nhưng eval chấm là fail.

- **Cải thiện tiếp theo:**
  1. Tinh chỉnh confirm-before-send: chỉ áp dụng cho tool có `side_effect: true` (`send`/`notify`), không áp dụng cho read-only tools
  2. Thêm name→handle mapping rõ hơn trong tools.yaml (description của `timeline`)
  3. Viết thêm eval case để test edge case: handle không tồn tại, URL không truy cập được
  4. Cân nhắc model mạnh hơn (gpt-4o) cho multi-turn cases phức tạp

