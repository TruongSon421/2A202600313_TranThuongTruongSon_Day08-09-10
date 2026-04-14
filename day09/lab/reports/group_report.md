# Báo Cáo Nhóm — Lab Day 09: Multi-Agent Orchestration

**Tên nhóm:** Nhóm 5b-E402  
**Thành viên:**
| Tên | Vai trò | Email |
|-----|---------|-------|
| Trương Đăng Nghĩa | Supervisor Owner | nyclone569@gmail.com |
| Bùi Lâm Tiến | Worker Owner | tienbuilam@gmail.com |
| Trần Thượng Trường Sơn | MCP Owner | tranthuongtruongson@gmail.com |
| Trần Thượng Trường Sơn | Trace & Docs Owner | tranthuongtruongson@gmail.com |

**Ngày nộp:** 14/04/2026  
**Repo:** https://github.com/TruongSon421/Nhom5b_402_Day08-09-10
**Độ dài khuyến nghị:** 600–1000 từ

---

## 1. Kiến trúc nhóm đã xây dựng (150–200 từ)

**Hệ thống tổng quan:**

Hệ thống gồm 4 thành phần chính: Supervisor Node (`graph.py`), Retrieval Worker (`workers/retrieval.py`), Policy Tool Worker (`workers/policy_tool.py`), và Synthesis Worker (`workers/synthesis.py`). Ngoài ra có Human Review node (placeholder auto-approve) và MCP Server (`mcp_server.py`) với 4 tools. Toàn bộ state được quản lý qua `AgentState` — một `TypedDict` chứa tất cả dữ liệu đi xuyên suốt graph, từ input task đến final answer, routing decisions, và trace logs.

Luồng xử lý: `Input → Supervisor → [Retrieval | PolicyTool | HumanReview] → Synthesis → Output`. Supervisor không tự trả lời — chỉ phân tích task rồi route sang worker phù hợp. Sau khi worker chạy xong, Synthesis Worker tổng hợp answer có citation từ retrieved chunks.

**Routing logic cốt lõi:**

Supervisor dùng keyword matching với 3 priority levels:
1. **Policy keywords** (`hoàn tiền`, `refund`, `flash sale`, `cấp quyền`, `access`, `level 3`) → `policy_tool_worker` + gọi MCP
2. **Retrieval keywords** (`p1`, `sla`, `ticket`, `escalation`) → `retrieval_worker`
3. **Risk keywords** (`emergency`, `khẩn cấp`, `2am`, `err-`) → set `risk_high=True`; nếu kết hợp với unknown error code (`err-`) → `human_review`

**MCP tools đã tích hợp:**

- `search_kb`: Tìm kiếm knowledge base, trả về top-k chunks có score. Được gọi từ `policy_tool_worker` khi cần evidence từ tài liệu.
- `get_ticket_info`: Lấy thông tin ticket (priority, status, assignee, SLA deadline). Gọi khi task chứa keyword ticket/P1/Jira.
- `check_access_permission`: Kiểm tra điều kiện cấp quyền theo access level và role.
- `create_ticket`: Tạo ticket mới (MOCK mode).

---

## 2. Quyết định kỹ thuật quan trọng nhất (200–250 từ)

**Quyết định:** Dùng keyword-based routing thay vì LLM classifier trong Supervisor Node.

**Bối cảnh vấn đề:**

Khi thiết kế Supervisor, nhóm cần quyết định cơ chế routing: dùng một LLM call để classify task, hay dùng keyword matching đơn giản. Đây là quyết định ảnh hưởng đến toàn bộ pipeline về latency, cost, và debuggability.

**Các phương án đã cân nhắc:**

| Phương án | Ưu điểm | Nhược điểm |
|-----------|---------|-----------|
| LLM classifier | Linh hoạt hơn với câu hỏi mơ hồ, tự xử lý edge case | +500–1200ms mỗi query, tốn thêm API call, khó debug khi route sai |
| Keyword matching | ~2–5ms, deterministic, `route_reason` rõ ràng, dễ sửa khi sai | Kém linh hoạt với câu hỏi không chứa keyword, cần maintain keyword list |

**Phương án đã chọn và lý do:**

Nhóm chọn keyword matching vì 3 lý do: (1) domain của lab đủ hẹp — chỉ có 3 routes với vocabulary khá rõ ràng; (2) latency thấp hơn đáng kể khi xử lý 15 test questions; (3) khi routing sai, debug chỉ cần xem keyword list thay vì phải đoán LLM nghĩ gì. Với test set hiện tại đạt 100% routing accuracy, trade-off là chấp nhận được.

**Bằng chứng từ trace/code:**

```python
# graph.py — supervisor_node()
policy_keywords = ["hoàn tiền", "refund", "policy", "flash sale", "license", "cấp quyền", "access", "level 3"]
risk_keywords   = ["emergency", "khẩn cấp", "2am", "không rõ", "err-"]
retrieval_keywords = ["p1", "escalation", "sla", "ticket"]
```

Trace gq09 minh họa kết quả routing phức tạp nhất:
```json
{
  "supervisor_route": "policy_tool_worker",
  "route_reason": "task contains policy/access keyword | MCP: search_kb selected | risk_high flagged",
  "workers_called": ["policy_tool_worker", "retrieval_worker", "synthesis_worker"]
}
```

Keyword `access` + `2am` đủ để supervisor nhận diện đúng câu cần cả policy check lẫn risk flag, không cần LLM call thêm.

---

## 3. Kết quả grading questions (150–200 từ)

**Tổng điểm raw ước tính:** ~94 / 96

**Câu pipeline xử lý tốt nhất:**

- **gq07** (abstain, 10đ) — Pipeline abstain đúng hoàn toàn. Câu hỏi về mức phạt tài chính vi phạm SLA P1 — tài liệu không có thông tin này, synthesis worker trả về `"Không đủ thông tin trong tài liệu nội bộ."` với `confidence: 1.0` và cite đúng nguồn `sla-p1-2026.pdf`.
- **gq09** (multi-hop, 16đ) — Pipeline gọi đúng 3 workers (`policy_tool_worker → retrieval_worker → synthesis_worker`), lấy được thông tin từ cả 2 tài liệu (`sla-p1-2026.pdf` và `access-control-sop.md`), trả lời đầy đủ cả 2 phần SLA notification và điều kiện cấp Level 2 access.

**Câu pipeline fail hoặc partial:**

- **gq02** (temporal policy scoping, 10đ) — Pipeline phát hiện đúng rằng đơn ngày 31/01/2026 phải áp dụng chính sách v3, không phải v4. Nhưng vì v3 không có trong tài liệu, answer là partial: xác định đúng policy version nhưng không kết luận được có hoàn tiền không → **Partial ~5đ**.

**Câu gq07 (abstain):**

Pipeline abstain rõ ràng, không bịa số. Cite đúng nguồn tài liệu. Đây là kết quả tốt nhất có thể cho câu này.

**Câu gq09 (multi-hop khó nhất):**

Trace ghi 3 workers được gọi. `policy_tool_worker` gọi MCP `search_kb` rồi conditional edge kiểm tra thấy cần thêm evidence → route sang `retrieval_worker` để lấy chunks từ ChromaDB → `synthesis_worker` tổng hợp từ cả 2 nguồn. Sources trong trace: `["it/access-control-sop.md", "support/sla-p1-2026.pdf"]`. Confidence: `0.9`.

---

## 4. So sánh Day 08 vs Day 09 — Điều nhóm quan sát được (150–200 từ)

**Metric thay đổi rõ nhất (có số liệu):**

| Metric | Day 08 | Day 09 | Delta |
|--------|--------|--------|-------|
| Avg confidence | 0.016 | 0.807 | +4943% |
| Avg latency (ms) | 2737 | 4150 | +51.6% |
| Multi-hop accuracy | 0% (0/3) | Có routing visibility | N/A |
| Debug time (ước tính) | 15–20 phút | 5–10 phút | −10 phút |
| MCP tool usage | 0% | 46% (7/15 câu) | +46% |

**Điều nhóm bất ngờ nhất khi chuyển từ single sang multi-agent:**

Confidence tăng từ `0.016` lên `0.807` — tức là Day 08 gần như không có khả năng tự đánh giá mức độ tin cậy của answer, trong khi Day 09 synthesis worker có đủ context (chunk scores + policy exceptions) để calibrate được. Không phải model thông minh hơn — chỉ là pipeline cho model đủ thông tin hơn.

**Trường hợp multi-agent KHÔNG giúp ích hoặc làm chậm hệ thống:**

Latency tăng 51.6% (2737ms → 4150ms). Với câu hỏi đơn giản single-document như gq04 ("store credit bao nhiêu %"), single agent đủ nhanh và chính xác — routing step thêm overhead không cần thiết. Multi-agent mang lại giá trị rõ nhất ở câu phức tạp như gq09 (multi-hop) và gq07 (abstain), không phải câu lookup đơn giản.

---

## 5. Phân công và đánh giá nhóm (100–150 từ)

**Phân công thực tế:**

| Thành viên | Phần đã làm | Sprint |
|------------|-------------|--------|
| Trương Đăng Nghĩa | `graph.py` — AgentState schema, supervisor_node, route_decision, build_graph, run_graph | Sprint 1 |
| Bùi Lâm Tiến | `workers/retrieval.py`, `workers/policy_tool.py`, `workers/synthesis.py` | Sprint 2 |
| Trần Thượng Trường Sơn | `mcp_server.py` — 4 tools (search_kb, get_ticket_info, check_access_permission, create_ticket) | Sprint 3 |
| Trần Thượng Trường Sơn | `eval_trace.py`, `artifacts/`, `docs/` | Sprint 4 |

**Điều nhóm làm tốt:**

AgentState schema được thiết kế đầy đủ ngay từ Sprint 1, giúp các worker owners (Sprint 2) implement đúng contract mà không cần back-and-forth. Trace format nhất quán giữa tất cả runs — trace nào cũng có đủ `supervisor_route`, `route_reason`, `workers_called`, `mcp_tools_used`.

**Điều nhóm làm chưa tốt hoặc gặp vấn đề về phối hợp:**

HITL chưa implement thật — `human_review_node()` chỉ là auto-approve placeholder. Nếu có thêm thời gian, cần integrate LangGraph `interrupt_before` để có human-in-the-loop thật sự. Abstain rate cũng chưa được track chủ động trong trace.

**Nếu làm lại, nhóm sẽ thay đổi gì trong cách tổ chức?**

Khai báo worker contract (input/output schema) trước khi bắt đầu code — Sprint 1 và Sprint 2 đôi khi bị block vì contract chưa được thống nhất sớm.

---

## 6. Nếu có thêm 1 ngày, nhóm sẽ làm gì? (50–100 từ)

**Cải tiến 1 — Dynamic routing với confidence threshold:**

Trace gq02 cho thấy `confidence: 1.0` nhưng answer là partial (thiếu v3). Confidence cao không đồng nghĩa answer đầy đủ — cần thêm logic kiểm tra sau synthesis: nếu answer chứa "Không đủ thông tin" nhưng confidence cao, supervisor retry với worker khác hoặc trigger HITL thay vì trả kết quả thiếu.

**Cải tiến 2 — Thực hiện HITL thật bằng LangGraph `interrupt_before`:**

`human_review_node()` hiện auto-approve. Với câu như gq02 (thiếu v3) hoặc error code lạ, escalate lên human thật sự sẽ tránh được partial answer không rõ ràng.

---

*File này lưu tại: `reports/group_report.md`*  
*Commit sau 18:00 được phép theo SCORING.md*
