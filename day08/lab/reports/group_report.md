# Báo Cáo Nhóm — Lab Day 08: Full RAG Pipeline

**Tên nhóm:** Nhom5b_E402
**Thành viên:**

| Tên | Vai trò | Email |
|-----|---------|-------|
| Trương Đăng Nghĩa | Tech Lead / Indexing Owner | (trống) |
| Bùi Lâm Tiến | Retrieval Owner | (trống) |
| Trần Thương Trường Sơn | Eval Owner, Documentation Owner | (trống) |

**Ngày nộp:** 14/04/2026  
**Repo:** Nhom5b_E402_Day08-09-10  
**Độ dài khuyến nghị:** 600–900 từ

---

> **Hướng dẫn nộp group report:**
>
> - File này nộp tại: `reports/group_report.md`
> - Deadline: Được phép commit **sau 18:00** (xem SCORING.md)
> - Tập trung vào **quyết định kỹ thuật cấp nhóm** — không trùng lặp với individual reports
> - Phải có **bằng chứng từ code, scorecard, hoặc tuning log** — không mô tả chung chung

---

## 1. Pipeline nhóm đã xây dựng (150–200 từ)

**Chunking decision:**
Nhóm sử dụng `chunk_size = 450` tokens và `overlap = 75` tokens. Về quy tắc, văn bản được ưu tiên tách theo cấu trúc tự nhiên bằng regex dựa trên section heading (`=== Section ===`). Nếu section quá giới hạn sẽ dùng các đoạn `\n\n` để ngắt. Tại vùng biên, nhóm xử lý overlap ở đuôi chunk trước nối sang đầu chunk sau để tránh rớt văn cảnh. Bằng cách này, hệ thống đã index thành công 29 chunks từ 5 tài liệu với đầy đủ metadata (source, department, effective_date, v.v.).

**Embedding model:**
Nhóm cấu hình sử dụng mô hình OpenAI `text-embedding-3-small`.

**Retrieval variant (Sprint 3):**
Nhóm chọn cấu hình **Hybrid Retrieval (Dense + BM25)** kết hợp phương pháp **Reciprocal Rank Fusion (RRF)**. Vì file corpus có cả văn bản chính sách thuần lẫn những mã lỗi quy định riêng biệt (ERR-403, P1), Dense lo mặt trích xuất ý nghĩa ngữ cảnh, còn Sparse được dùng như một thành phần bổ trợ để nhận diện chính xác các từ khóa hóc búa, đặc biệt để chống lại nhóm ảo giác (Hallucination) ở thế hệ sinh văn bản.

---

## 2. Quyết định kỹ thuật quan trọng nhất (200–250 từ)

**Quyết định:** Tinh chỉnh cơ cấu weighting của Hybrid Retrieval (Dense / Sparse) từ 0.6 / 0.4 sang 0.8 / 0.2 để tối ưu hóa Faithfulness và loại trừ nhiễu Hallucination.

**Bối cảnh vấn đề:**
Khoảng thời gian test Sprint 3 với mô hình Hybrid 0.6/0.4 (Variant 1) đã gây thất vọng khi các chunk từ Sparse (BM25) kéo theo quá nhiều text nhiễu, đẩy lùi các metric Relevance và Completeness. Câu `gq05` (quản lý Access Control) không còn trả lời sai mà abstain thẳng vì context hỗn loạn. Nhóm nhận định việc để Sparse chiếm tận 0.4 làm suy giảm mạnh năng lực paraphrase vốn có của mô hình Dense.

**Các phương án đã cân nhắc:**

| Phương án | Ưu điểm | Nhược điểm |
|-----------|---------|-----------|
| Dense Retrieval Khởi điểm | Khả năng quy tụ semantic đồng nghĩa ưu việt, Recall 5/5 max điểm. | Dễ cho xuất hiện Hallucination cho vài query phức tạp mã chuyên ngành. |
| Hybrid 0.6 / 0.4 (Variant 1) | Thể hiện sự cân bằng giữa Keyword và Semantic trên lý thuyết. | Quá nhiễu. Điểm Faithfulness và Completeness đồng loạt đi lùi. |
| Hybrid 0.8 / 0.2 (Variant 2) | Khôi phục ưu thế của Dense (0.8), ép Sparse chỉ làm còi báo (0.2) cho thuật toán RRF. | Vấp phải tính bảo thủ trong context khiến hệ thống sinh từ mất một phần Completeness. |

**Phương án đã chọn và lý do:**
Nhóm chính thức dùng **Variant Hybrid 0.8/0.2** làm cấu hình chiến lược. Kĩ thuật cốt lõi là Retrieval Dense. Dẫu Completeness có thu hẹp đi một tí, việc hệ thống tuyệt đối không xuất ra Hallucination trong sản phẩm hỗ trợ Doanh nghiệp là điều quan tâm nhất. Điểm Tuning-log chỉ ra Faithfulness đẩy nhanh từ 4.70 lên thành mức đỉnh 5.0 ngay sau khi nhóm quyết định tinh chỉnh.

---

## 3. Kết quả grading questions (100–150 từ)

**Ước tính điểm raw:** ~88 / 98 (Dựa trên trung bình đánh giá Faithfulness 4.5, Relevance 4.6, Recall 5.0, Completeness 3.8).

**Câu tốt nhất:** ID: `gq02`, `gq06` và `gq10` — Pipeline phân tích hoàn hảo vấn đề Cross-Document và Refund. Retrieval lấy trọn ven 100% ngữ cảnh từ các chunk liên đới (Context Recall 5/5). Generation LLM tổng hợp logic không bịa thêm thông tin ngoài.

**Câu fail:** ID: `gq09` (IT Helpdesk) — Lỗi Generation + Chunking. Câu hỏi đa điều kiện hỏi về "quy định 90 ngày", "nhắc trước bao lâu" và "đổi qua đâu". Model trả đủ hai ý đầu và thiếu ý 3 (điểm completeness 3/5). Một góc độ khác từ bài học của `gq03` chỉ ra rằng chính sách Chunking vẫn vô tình bẻ ngang các danh sách dạng Bullet Points khiến cho Context chuyển vào LLM không cung cấp trọn vẹn ngữ nghĩa các list điều khoản liệt kê, buộc AI phải rụt rè lược bớt ý.

**Câu gq07 (abstain):** Đạt điểm tích cực tuyệt đối khi LLM tự nhận định Abstain "Không đủ dữ liệu" trước câu hỏi SLA không hề nằm trong Docs index giúp hệ thống tuân thủ nghiêm Grounded framework.

---

## 4. A/B Comparison — Baseline vs Variant (150–200 từ)

**Biến đã thay đổi (chỉ 1 biến):** Hybrid vs Dense Retrieval Mode (Dense chuyển qua Hybrid Dense+BM25).

| Metric | Baseline (Dense) | Variant (Hybrid) | Delta |
|--------|---------|---------|-------|
| Faithfulness | 4.50/5 | 4.80/5 | +0.30 |
| Answer Relevance | 4.60/5 | 4.60/5 | 0.00 |
| Context Recall | 5.00/5 | 5.00/5 | 0.00 |
| Completeness | 3.80/5 | 3.60/5 | -0.20 |

**Kết luận:**
Biến thể Hybrid xuất sắc giải quyết yêu cầu **Faithfulness (+0.30)** nhờ RRF giúp mô hình chốt exact-match cực chuẩn để xử lý chính những từ khóa khó chịu đánh lừa Dense, làm giảm tối thiểu hiện trạng Hallucination (Điển hình ở query `gq05`). Ngược lại, **Completeness thuyên giảm (-0.20)** do sự dung hợp kết quả làm chật chội không gian Context, khiến vài chunk quan trọng nằm dưới ngưỡng `top_k_select`. Tổng thể, hệ thống an toàn và Grounded chặt chẽ hơn, phản ánh đúng một trợ lý nội bộ đáng tin thay vì tự sáng tác.

---

## 5. Phân công và đánh giá nhóm (100–150 từ)

**Phân công thực tế:**

| Thành viên | Phần đã làm | Sprint |
|------------|-------------|--------|
| Trương Đăng Nghĩa | Làm index.py (Preprocess, Chunking Rule Heading, Embed ChromaDB) | Sprint 1 |
| Bùi Lâm Tiến | Làm rag_answer.py, Setup pipeline Baseline, Dense/Sparse và Hybrid Retrieval | Sprint 2, 3 |
| Trần Thương Trường Sơn | Điều hành quá trình A/B Tuning, kiểm duyệt Scorecard, Phân tích metrics (Eval Owner) | Sprint 4 |

**Điều nhóm làm tốt:**
- Sự kết nối quy trình End-to-End rất mượt mà. 29 tài liệu Chunking sạch (ít bị gãy ngang ý) từ Sprint 1 giúp Metric Recall của Sprint 2, 3 luôn giữ ở đỉnh 5/5.
- Nhóm không tin vào kết quả trung bình bề nổi mà chia nhau nhìn qua từng đánh giá `gq05`, `gq09`, phân biệt rạch ròi được hệ lụy do Retrieval vs Generation gây ra thông qua việc điều chỉnh các trọng số A/B an toàn.

**Điều nhóm làm chưa tốt:**
- Logic Chunking của Sprint 1 còn vướng nhược điểm chia tách những đoạn Bullet Points (list item `*`, `-`) làm ảnh hưởng Completeness ở một số lệnh cần liệt kê.
- Thiết lập Prompt Grounded còn đơn giản, khiến LLM không tự tin trả lời ngay cả khi đã cung cấp đủ Context.

---

## 6. Nếu có thêm 1 ngày, nhóm sẽ làm gì? (50–100 từ)

1. **Ngăn cắt Chunk giữa khối Bullet Points:** Sửa `_split_by_size()` để tự động nhận diện Block List và gom nguyên vẹn, đảm bảo điều kiện liệt kê (vd hoàn tiền ở qg03) không bị thất lạc giữa hai chunk.
2. **Sử dụng Slot-based Prompt / LLM Query Decomposition:** Ép Grounded Prompt theo form checklist để yêu cầu LLM xác nhận bắt buộc từng ý nhỏ cho câu đa cấu trúc (`gq09`) dứt điểm lỗi thiếu Completeness.
3. **Thêm Cross-encoder Reranker:** Mở rộng `top_k_search = 15` kết hợp với Reranker thay vì chỉ dùng RRF, vì Evaluation đã chứng minh hệ thống cần được đánh giá chất lượng độ chi tiết các chunk kỹ hơn trước khi bỏ vào LLM.

---
