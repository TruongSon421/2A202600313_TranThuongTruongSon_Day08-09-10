# So sánh Day 08 (Single Agent) vs Day 09 (Multi-Agent)

## Metrics Comparison

| Metric | Day 08 (Single Agent) | Day 09 (Multi-Agent) | Delta | Ghi chú |
|--------|----------------------|---------------------|-------|---------|
| Avg confidence | 0.823 | 0.856 | +0.033 | Độ tin cậy retrieval |
| Avg latency (ms) | 1456 | 2134 | +678 | Thời gian xử lý |
| Abstain rate (%) | 6.7% | 13.3% | +6.6% | % câu trả về "không đủ info" |
| Multi-hop accuracy | 66.7% | 100.0% | +33.3% | % câu multi-hop trả lời đúng |
| Routing visibility | ✗ Không có | ✓ Có route_reason | N/A | Khả năng debug |
| Debug time (estimate) | ~15-30 phút | ~5-10 phút | Faster | Thời gian tìm ra 1 bug |

## Analysis

### 1. Confidence
- **Day 08**: 0.823 - Dựa trên retrieval scores từ hybrid search
- **Day 09**: 0.856 - Dựa trên worker confidence và routing logic
- **Delta**: +0.033 - Day 09 tốt hơn

### 2. Latency
- **Day 08**: 1456ms - Single RAG pipeline
- **Day 09**: 2134ms - Multi-agent với routing overhead
- **Delta**: +678ms - Day 09 chậm hơn do routing

### 3. Abstain Rate
- **Day 08**: 6.7% - Dựa trên prompt grounding rules
- **Day 09**: 13.3% - Dựa trên HITL trigger và confidence threshold
- **Delta**: +6.6% - Day 09 abstain nhiều hơn (an toàn hơn)

### 4. Multi-hop Accuracy
- **Day 08**: 66.7% - Single retrieval pass
- **Day 09**: 100.0% - Multi-worker coordination
- **Delta**: +33.3% - Day 09 tốt hơn cho câu phức tạp

### 5. Routing Visibility
- **Day 08**: ✗ Không có - Black box, khó debug
- **Day 09**: ✓ Có route_reason - Mỗi câu có trace rõ ràng: supervisor route → workers called → MCP tools
- **Benefit**: Day 09 dễ debug hơn nhiều, có thể test từng worker độc lập

### 6. Debug Time
- **Day 08**: ~15-30 phút - Phải đọc code và log để tìm bug
- **Day 09**: ~5-10 phút - Có trace file chi tiết, dễ identify worker nào sai
- **Benefit**: Day 09 giảm thời gian debug ~50%

## Kết luận

### Ưu điểm Day 09 (Multi-Agent):
1. **Modularity**: Mỗi worker có trách nhiệm rõ ràng, dễ maintain
2. **Debuggability**: Trace file chi tiết, routing visibility
3. **Extensibility**: Thêm worker mới không ảnh hưởng code cũ
4. **MCP Integration**: Có thể extend capability qua MCP tools
5. **Multi-hop**: Tốt hơn cho câu hỏi phức tạp cần nhiều bước suy luận

### Ưu điểm Day 08 (Single Agent):
1. **Simplicity**: Code đơn giản hơn, ít moving parts
2. **Latency**: Nhanh hơn (không có routing overhead)
3. **Easy to understand**: Toàn bộ logic trong 1 file
4. **Lower abstain rate**: Trả lời nhiều hơn (nhưng có thể kém chính xác hơn)

### Trade-offs:
- **Day 08** phù hợp cho: RAG đơn giản, không cần extend, team nhỏ, cần latency thấp
- **Day 09** phù hợp cho: Hệ thống phức tạp, cần scale, nhiều loại câu hỏi khác nhau, cần debug dễ dàng

### Recommendation:
- Nếu bạn cần **accuracy cao** cho câu hỏi phức tạp và **dễ maintain**: chọn **Day 09**
- Nếu bạn cần **latency thấp** và **đơn giản**: chọn **Day 08**

---

Generated: 2026-04-14T17:31:18
