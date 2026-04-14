# So sánh Day 08 (Single Agent) vs Day 09 (Multi-Agent)

## Tổng quan

Script này cho phép chạy Day 08 RAG pipeline với test data từ Day 09 và so sánh metrics giữa hai approaches.

## Metrics được đo

| Metric | Mô tả |
|--------|-------|
| **Avg confidence** | Độ tin cậy trung bình (dựa trên retrieval scores) |
| **Avg latency (ms)** | Thời gian xử lý trung bình |
| **Abstain rate (%)** | Tỷ lệ câu trả "không đủ info" |
| **Multi-hop accuracy** | Độ chính xác câu hỏi multi-hop (cần nhiều tài liệu) |
| **Routing visibility** | Day 08: ✗ / Day 09: ✓ (có trace) |
| **Debug time** | Ước tính thời gian debug |

## Cách sử dụng

### Option 1: Chạy tự động (khuyến nghị)

```bash
cd day08/lab
./run_comparison.sh
```

Script này sẽ:
1. Chạy Day 08 evaluation với Day 09 test questions
2. Kiểm tra Day 09 metrics (chạy nếu chưa có)
3. Tạo comparison report

### Option 2: Chạy từng bước

#### Bước 1: Chạy Day 08 evaluation

```bash
cd day08/lab

# Mặc định: dùng test_questions.json từ Day 09 (15 câu)
python eval_metrics.py

# Hoặc dùng grading_questions.json từ Day 09 (10 câu)
python eval_metrics.py --grading

# Hoặc dùng test_questions.json từ Day 08 (10 câu)
python eval_metrics.py --day08-data
```

Kết quả lưu tại: `results/day08_metrics.json`

#### Bước 2: Chạy Day 09 evaluation (nếu chưa có)

```bash
cd ../day09/lab
python eval_trace.py
```

Kết quả lưu tại: `artifacts/eval_report.json`

#### Bước 3: So sánh metrics

```bash
cd ../../day08/lab
python compare_with_day09.py
```

Kết quả lưu tại: `results/comparison_report.md`

## Cấu trúc output

### day08_metrics.json

```json
{
  "results": [
    {
      "id": "q01",
      "question": "...",
      "answer": "...",
      "sources": ["..."],
      "confidence": 0.85,
      "latency_ms": 1234,
      "is_abstain": false,
      "is_multi_hop": false,
      "multi_hop_correct": null
    }
  ],
  "metrics": {
    "total_questions": 15,
    "avg_confidence": 0.82,
    "avg_latency_ms": 1500,
    "abstain_rate_pct": 6.7,
    "multi_hop_accuracy_pct": 66.7
  },
  "config": {
    "retrieval_mode": "hybrid",
    "top_k_search": 10,
    "top_k_select": 3
  }
}
```

### comparison_report.md

Bảng so sánh markdown với:
- Metrics comparison table
- Delta analysis
- Ưu/nhược điểm từng approach
- Trade-offs và recommendations

## Câu hỏi multi-hop

Các câu hỏi được đánh dấu là multi-hop (cần nhiều tài liệu hoặc suy luận phức tạp):

- **q12**: Temporal policy scoping (đơn trước effective date)
- **q13**: Access Control + SLA context (cross-document)
- **q15**: SLA + Access Control (multi-doc, multi-worker)
- **gq09**: SLA P1 + Access Control (grading)
- **gq02**: Temporal policy scoping (grading)
- **gq10**: Policy exception (grading)

## Troubleshooting

### Lỗi: File not found

```
❌ File not found: ../day09/lab/data/test_questions.json
```

**Giải pháp**: Đảm bảo cấu trúc thư mục đúng:
```
AIThuchien/
├── day08/lab/
│   ├── eval_metrics.py
│   └── compare_with_day09.py
└── day09/lab/
    └── data/
        ├── test_questions.json
        └── grading_questions.json
```

### Lỗi: Missing Day 09 metrics

```
⚠️  Day 09 metrics not found
```

**Giải pháp**: Chạy Day 09 evaluation trước:
```bash
cd ../day09/lab
python eval_trace.py
```

### Lỗi: OPENAI_API_KEY not found

**Giải pháp**: Đảm bảo file `.env` có:
```
OPENAI_API_KEY=sk-...
```

## Kết quả mẫu

```
========================================
METRICS SUMMARY
========================================
Avg confidence:      0.823
Avg latency (ms):    1456
Abstain rate (%):    6.7% (1/15)
Multi-hop accuracy:  66.7% (2/3)
========================================
```

## Notes

- Day 08 sử dụng **hybrid retrieval** (dense + BM25 RRF) - variant tốt nhất từ Sprint 3
- Confidence được tính từ retrieval scores (không có explicit confidence như Day 09)
- Abstain detection dựa trên keywords trong answer
- Multi-hop accuracy chỉ tính cho các câu được đánh dấu là multi-hop

## Tham khảo

- Day 08 Lab: `day08/lab/README.md`
- Day 09 Lab: `day09/lab/README.md`
- Evaluation code: `eval_metrics.py`
- Comparison code: `compare_with_day09.py`
