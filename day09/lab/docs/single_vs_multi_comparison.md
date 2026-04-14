# Single Agent vs Multi-Agent Comparison — Lab Day 09

**Nhóm:**  Nhóm 5b
**Ngày:** 14/4

> **Hướng dẫn:** So sánh Day 08 (single-agent RAG) với Day 09 (supervisor-worker).
> Phải có **số liệu thực tế** từ trace — không ghi ước đoán.
> Chạy cùng test questions cho cả hai nếu có thể.

---

## 1. Metrics Comparison

> Điền vào bảng sau. Lấy số liệu từ:
> - Day 08: chạy `python eval.py` từ Day 08 lab
> - Day 09: chạy `python eval_trace.py` từ lab này

| Metric | Day 08 (Single Agent) | Day 09 (Multi-Agent) | Delta | Ghi chú |
|--------|----------------------|---------------------|-------|---------|
| Avg confidence | 0.016 | 0.807 | +0.791 (+4943%) | Day 09 tự tin hơn nhiều |
| Avg latency (ms) | 2737 | 4150 | +1413 (+51.6%) | Multi-agent chậm hơn do routing |
| Abstain rate (%) | 26.7% (4/15) | N/A | N/A | Day 09 chưa track abstain |
| Multi-hop accuracy | 0.0% (0/3) | N/A | N/A | Day 08 fail tất cả multi-hop |
| Routing visibility | ✗ Không có | ✓ Có route_reason | N/A | Day 09 có policy_tool/retrieval |
| Debug time (estimate) | 15-20 phút | 5-10 phút | -10 phút | Trace giúp debug nhanh hơn |
| MCP tool usage | 0% | 46% (7/15) | +46% | Day 09 có thể gọi external tools |

> **Lưu ý:** Day 09 có 15 traces (15 questions)

---

## 2. Phân tích theo loại câu hỏi

### 2.1 Câu hỏi đơn giản (single-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | Tốt (11/12 correct) | Tốt (routing đúng) |
| Latency | 2737ms avg | 4150ms avg |
| Observation | Trả lời đúng nhưng confidence thấp (0.016) | Confidence cao (0.807), routing rõ ràng |

**Kết luận:** Multi-agent có cải thiện không? Tại sao có/không?

Có cải thiện về **confidence** và **debuggability**, nhưng **latency tăng 51.6%** do thêm supervisor routing step. Với câu hỏi đơn giản, single-agent đủ nhanh và chính xác, nhưng multi-agent cho visibility tốt hơn (biết câu nào dùng retrieval, câu nào dùng MCP tool).

### 2.2 Câu hỏi multi-hop (cross-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | 0% (0/3 correct) | Chưa đo chính xác |
| Routing visible? | ✗ | ✓ |
| Observation | Fail tất cả câu multi-hop (q12, q13, q15) | Có route_reason, dễ debug hơn |

**Kết luận:**

Day 08 **fail hoàn toàn** với multi-hop questions vì không có cơ chế phối hợp giữa nhiều documents. Day 09 có **supervisor routing** giúp phân tích câu hỏi và route đến đúng worker, nhưng chưa có synthesis worker chuyên xử lý multi-hop. Cần thêm worker hoặc cải thiện synthesis logic để xử lý cross-document reasoning.

### 2.3 Câu hỏi cần abstain

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Abstain rate | 26.7% (4/15) | Chưa track |
| Hallucination cases | Thấp (có abstain) | Chưa đo |
| Observation | Abstain đúng khi thiếu info (q06, q07, q09, q15) | Chưa có cơ chế abstain rõ ràng |

**Kết luận:**

Day 08 có **abstain mechanism** tốt (26.7% abstain rate), giúp tránh hallucination khi không đủ thông tin. Day 09 chưa track abstain rate trong trace, cần thêm logic để worker báo "không đủ info" thay vì cố gắng trả lời. Đây là điểm **Day 08 tốt hơn** về safety.

---

## 3. Debuggability Analysis

> Khi pipeline trả lời sai, mất bao lâu để tìm ra nguyên nhân?

### Day 08 — Debug workflow
```
Khi answer sai → phải đọc toàn bộ RAG pipeline code → tìm lỗi ở indexing/retrieval/generation
Không có trace → không biết bắt đầu từ đâu
Ví dụ: q12 (multi-hop) sai → phải check retrieval.py, rerank, prompt, generation
Thời gian ước tính: 15-20 phút
```

### Day 09 — Debug workflow
```
Khi answer sai → đọc trace JSON → xem supervisor_route + route_reason
  → Nếu route sai → sửa supervisor routing logic trong graph.py
  → Nếu retrieval sai → test retrieval_worker độc lập
  → Nếu synthesis sai → test synthesis_worker độc lập
Ví dụ: Nếu câu hỏi về policy bị route nhầm sang retrieval → sửa supervisor prompt
Thời gian ước tính: 5-10 phút
```

**Câu cụ thể nhóm đã debug:** 

Khi test q13 (contractor cần Level 3 access cho P1), Day 08 trả lời sai vì không kết hợp được access_control_sop.txt và sla_p1_2026.txt. Trong Day 09, đọc trace thấy supervisor route sang `retrieval_worker` nhưng không tìm đủ 2 documents. Debug nhanh hơn vì biết ngay vấn đề ở retrieval, không phải check toàn bộ pipeline.

---

## 4. Extensibility Analysis

> Dễ extend thêm capability không?

| Scenario | Day 08 | Day 09 |
|---------|--------|--------|
| Thêm 1 tool/API mới | Phải sửa toàn prompt | Thêm MCP tool + route rule |
| Thêm 1 domain mới | Phải retrain/re-prompt | Thêm 1 worker mới |
| Thay đổi retrieval strategy | Sửa trực tiếp trong pipeline | Sửa retrieval_worker độc lập |
| A/B test một phần | Khó — phải clone toàn pipeline | Dễ — swap worker |

**Nhận xét:**

Day 09 **dễ extend hơn nhiều** nhờ kiến trúc modular:
- **Thêm MCP tool**: Chỉ cần config trong mcp_server.py, supervisor tự động route
- **Thêm worker mới**: Implement worker contract, thêm vào graph.py, không ảnh hưởng workers khác
- **A/B testing**: Có thể test 2 variants của retrieval_worker song song, so sánh metrics
- **Isolation**: Mỗi worker test độc lập, không cần chạy toàn bộ pipeline

Day 08 **khó extend** vì monolithic: Mọi thay đổi đều ảnh hưởng toàn bộ pipeline, phải test lại từ đầu.

---

## 5. Cost & Latency Trade-off

> Multi-agent thường tốn nhiều LLM calls hơn. Nhóm đo được gì?

| Scenario | Day 08 calls | Day 09 calls |
|---------|-------------|-------------|
| Simple query | 1 LLM call | 2-3 LLM calls (supervisor + worker) |
| Complex query | 1 LLM call | 3-4 LLM calls (supervisor + worker + synthesis) |
| MCP tool call | N/A | 2-3 calls (supervisor + policy_tool_worker) |

**Nhận xét về cost-benefit:**

Day 09 tốn **2-3x LLM calls** hơn Day 08, dẫn đến:
- **Cost tăng 2-3x** (mỗi call đều tốn tiền)
- **Latency tăng 51.6%** (2737ms → 4150ms)

Nhưng đổi lại được:
- **Debuggability tốt hơn** (trace rõ ràng)
- **Extensibility cao hơn** (thêm worker/tool dễ dàng)
- **Confidence cao hơn** (0.016 → 0.807)

Trade-off hợp lý cho **production system phức tạp**, không hợp lý cho **simple Q&A** hoặc **high-throughput use case**.

---

## 6. Kết luận

> **Multi-agent tốt hơn single agent ở điểm nào?**

1. **Debuggability**: Trace rõ ràng (supervisor_route, route_reason) giúp debug nhanh hơn 2-3x (5-10 phút vs 15-20 phút)
2. **Extensibility**: Thêm worker/MCP tool mới không cần sửa core logic, chỉ cần thêm route rule
3. **Confidence**: Tăng từ 0.016 → 0.807 (+4943%) nhờ routing rõ ràng
4. **Visibility**: Biết rõ câu nào dùng retrieval, câu nào dùng MCP tool (46% MCP usage)

> **Multi-agent kém hơn hoặc không khác biệt ở điểm nào?**

1. **Latency**: Chậm hơn 51.6% (2737ms → 4150ms) do thêm supervisor routing step
2. **Cost**: Tốn 2-3x LLM calls hơn single-agent
3. **Abstain mechanism**: Day 08 có abstain rate 26.7%, Day 09 chưa track → kém về safety
4. **Multi-hop accuracy**: Day 08 fail (0%), Day 09 chưa đo → chưa rõ cải thiện

> **Khi nào KHÔNG nên dùng multi-agent?**

- **Simple Q&A** với single document: Single-agent đủ nhanh và chính xác
- **High-throughput use case**: Latency +51.6% và cost 2-3x không chấp nhận được
- **Budget hạn chế**: Multi-agent tốn nhiều LLM calls hơn
- **Prototype/MVP**: Overhead phức tạp không cần thiết

> **Nếu tiếp tục phát triển hệ thống này, nhóm sẽ thêm gì?**

1. **Synthesis worker chuyên xử lý multi-hop**: Để cải thiện accuracy với cross-document questions
2. **Abstain mechanism trong worker**: Track abstain rate và tránh hallucination
3. **Caching supervisor routing**: Giảm latency cho câu hỏi tương tự
4. **A/B testing framework**: So sánh performance giữa các worker variants
5. **Cost monitoring**: Track LLM calls và optimize routing để giảm cost
