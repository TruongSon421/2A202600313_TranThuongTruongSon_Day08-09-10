# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Trần Thượng Trường Sơn 
**Vai trò trong nhóm:** Eval Owner and Documentation Owner
**Ngày nộp:** 13/04/2026  

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

> Mô tả cụ thể phần bạn đóng góp vào pipeline:
> - Sprint nào bạn chủ yếu làm?
> - Cụ thể bạn implement hoặc quyết định điều gì?
> - Công việc của bạn kết nối với phần của người khác như thế nào?

Trong Day 08, phần tôi làm gần như dồn vào Sprint 4: tuning và đọc kết quả eval thật kỹ. Tôi chạy nhiều vòng A/B theo đúng rule “mỗi lần đổi một biến”, chủ yếu ở hai hướng: chỉnh trọng số hybrid từ 0.6/0.4 sang 0.8/0.2 và tăng `top_k_search/top_k_select` từ 10/3 lên 15/5. Sau mỗi lần chạy, tôi tổng hợp bốn chỉ số chính (faithfulness, relevance, context recall, completeness), rồi soi xuống từng câu thay vì chỉ nhìn điểm trung bình. Nhờ vậy tôi thấy rõ trade-off giữa trả lời “an toàn, bám context” và trả lời “đủ ý”. Phần này cũng liên kết trực tiếp với teammate viết prompt: tôi gửi lại các case hụt ý như `gq05`, `gq09` để bạn ấy chỉnh format đầu ra phù hợp hơn.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

> Chọn 1-2 concept từ bài học mà bạn thực sự hiểu rõ hơn sau khi làm lab.
> Ví dụ: chunking, hybrid retrieval, grounded prompt, evaluation loop.
> Giải thích bằng ngôn ngữ của bạn — không copy từ slide.

Điều tôi “ngấm” rõ nhất sau Sprint 4 là: lấy đúng tài liệu chưa chắc trả lời hay. Có những run context recall vẫn 5.0/5, nhưng completeness lại thấp vì câu trả lời thiếu một vế quan trọng. Nói cách khác, retrieval làm tròn vai nhưng generation chưa tổng hợp hết yêu cầu người dùng. Tôi cũng hiểu hybrid retrieval thực tế hơn: dense mạnh ở semantic match, BM25 mạnh ở exact keyword, còn kết quả cuối rất nhạy với weighting. Chỉ một thay đổi nhỏ từ 0.6/0.4 sang 0.8/0.2 đã kéo faithfulness lên rõ, nhưng completeness vẫn chưa thắng baseline. Với tôi, bài học kỹ thuật quan trọng là phải tối ưu retrieval và prompt cùng lúc, và dùng eval loop để đo tác động thật thay vì đoán.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

> Điều gì xảy ra không đúng kỳ vọng?
> Lỗi nào mất nhiều thời gian debug nhất?
> Giả thuyết ban đầu của bạn là gì và thực tế ra sao?

Điều làm tôi bất ngờ nhất là tăng top-k không “thần kỳ” như tôi nghĩ. Lúc đầu tôi tin rằng kéo từ 10/3 lên 15/5 sẽ giúp model đủ ý hơn, nhưng thực tế completeness không tăng như kỳ vọng. Có run faithfulness khá hơn, nhưng câu trả lời vẫn thiếu ý quan trọng vì model trình bày chưa tốt. Phần khó nhất là debug các câu nhiều điều kiện: lỗi không nằm riêng ở retrieval hay generation, mà nằm ở cách hai phần này tương tác. Khi đọc note chấm theo từng câu, tôi thấy nhiều câu trả lời nghe rất hợp lý nhưng thiếu chi tiết bắt buộc (thời gian xử lý, yêu cầu đặc biệt). Từ đó tôi rút ra là muốn debug đúng phải đi theo từng case cụ thể; nếu chỉ nhìn điểm trung bình thì dễ tự tin sai.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

> Chọn 1 câu hỏi trong test_questions.json mà nhóm bạn thấy thú vị.
> Phân tích:
> - Baseline trả lời đúng hay sai? Điểm như thế nào?
> - Lỗi nằm ở đâu: indexing / retrieval / generation?
> - Variant có cải thiện không? Tại sao có/không?

**Câu hỏi:** gq05 — “Contractor từ bên ngoài công ty có thể được cấp quyền Admin Access không? Nếu có, cần bao nhiêu ngày và có yêu cầu đặc biệt gì?”

**Phân tích:**

Ở baseline dense, câu này có điểm Faithfulness 3, Relevance 5, Recall 5, Completeness 5. Cảm giác của tôi khi đọc kết quả là: câu trả lời “đủ khung” nhưng còn hơi liều ở một số khẳng định. Note evaluator cũng chỉ ra đúng điểm đó: phần dễ mất điểm nằm ở generation, vì model kết luận mạnh hơn mức dữ liệu hỗ trợ. Tôi kiểm tra lại thì retrieval không phải vấn đề lớn ở case này, vì recall vẫn 5/5 và không thiếu nguồn chính.  

Sang variant hybrid, điểm chuyển thành Faithfulness 4, Relevance 4, Recall 5, Completeness 2. Tức là hệ thống an toàn hơn (ít bịa hơn), nhưng lại hụt ý rõ rệt. Đây là trade-off tôi thấy lặp lại nhiều lần trong Sprint 4: “trả lời chắc” và “trả lời đủ” không tự động đi cùng nhau. Với câu nhiều vế như `gq05`, chỉ chỉnh retrieval là chưa đủ. Theo tôi, cần ép output theo checklist cố định (khả năng cấp quyền, thời gian xử lý, approval chain, yêu cầu training) hoặc thêm reranker để đẩy các chunk đủ thông tin lên cao hơn trước khi generate.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

> 1-2 cải tiến cụ thể bạn muốn thử.
> Không phải "làm tốt hơn chung chung" mà phải là:
> "Tôi sẽ thử X vì kết quả eval cho thấy Y."

Nếu có thêm thời gian, tôi sẽ làm tiếp đúng hai việc đã lộ rõ từ eval. Một là thêm cross-encoder rerank sau hybrid để tăng precision của nhóm chunk đầu, vì hiện tại recall đã đủ nhưng completeness vẫn hụt. Hai là sửa prompt sang dạng “slot-based answer”, bắt buộc model trả lời lần lượt theo từng mục bắt buộc. Tôi chọn hai hướng này vì chúng đánh trực tiếp vào lỗi lặp lại ở `gq05` và `gq09`, thay vì thử thêm nhiều biến mới nhưng khó đo tác động.

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*
*Ví dụ: `reports/individual/nguyen_van_a.md`*
