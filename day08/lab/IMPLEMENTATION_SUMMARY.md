# Sprint 2 + 3 Implementation Summary

## ✅ Hoàn thành

### Sprint 2: Baseline RAG Pipeline

**1. Dense Retrieval (`retrieve_dense`)**
- ✅ Sử dụng ChromaDB để query với embedding similarity
- ✅ Embed query bằng OpenAI text-embedding-3-small
- ✅ Trả về top-k chunks với score (1 - cosine distance)

**2. LLM Generation (`call_llm`)**
- ✅ Sử dụng OpenAI GPT-4o-mini
- ✅ Temperature = 0 để output ổn định
- ✅ Max tokens = 512

**3. Grounded Answer Pipeline (`rag_answer`)**
- ✅ Pipeline hoàn chỉnh: Query → Retrieve → Generate
- ✅ Build context block với format [1], [2], [3]
- ✅ Grounded prompt với 4 quy tắc:
  - Evidence-only: chỉ trả lời từ context
  - Abstain: nói không biết khi thiếu context
  - Citation: gắn source [1], [2]
  - Short & clear: output ngắn gọn

### Sprint 3: Hybrid Retrieval

**1. Sparse Retrieval - BM25 (`retrieve_sparse`)**
- ✅ Sử dụng rank-bm25 (BM25Okapi)
- ✅ Tokenization: lowercase + split
- ✅ Mạnh ở: exact terms, mã lỗi, tên riêng (P1, Level 3)

**2. Hybrid Retrieval - RRF (`retrieve_hybrid`)**
- ✅ Kết hợp Dense + Sparse bằng Reciprocal Rank Fusion
- ✅ Formula: `RRF_score = dense_weight/(60+rank) + sparse_weight/(60+rank)`
- ✅ Default weights: dense=0.6, sparse=0.4
- ✅ Mạnh ở: giữ cả semantic understanding VÀ exact keyword matching

**3. Comparison Function (`compare_retrieval_strategies`)**
- ✅ So sánh Dense vs Hybrid với cùng query
- ✅ Dùng để justify lựa chọn variant

---

## 📁 Files Modified/Created

### Modified Files
1. **`rag_answer.py`**
   - ✅ Implemented `retrieve_dense()`
   - ✅ Implemented `retrieve_sparse()`
   - ✅ Implemented `retrieve_hybrid()`
   - ✅ Implemented `call_llm()`
   - ✅ Updated main section to run comparisons

2. **`docs/tuning-log.md`**
   - ✅ Documented baseline config
   - ✅ Documented Variant 1 (Hybrid) rationale
   - ✅ Added predictions and analysis framework

### Created Files
1. **`test_sprint2_3.py`**
   - ✅ Test suite for all retrieval methods
   - ✅ Test RAG pipeline (baseline + hybrid)
   - ✅ Test abstain behavior

2. **`IMPLEMENTATION_SUMMARY.md`** (this file)
   - ✅ Implementation summary
   - ✅ Usage instructions
   - ✅ Next steps

---

## 🚀 How to Run

### Prerequisites
```bash
# 1. Cài dependencies (nếu chưa)
pip install -r requirements.txt

# 2. Kiểm tra .env có OPENAI_API_KEY
cat .env

# 3. Build index (nếu chưa)
python index.py
```

### Run Tests

**Option 1: Quick Test Suite**
```bash
python test_sprint2_3.py
```

**Option 2: Full Demo**
```bash
python rag_answer.py
```

---

## 📊 Expected Results

### Sprint 2 (Baseline - Dense)

**Strong queries**:
- q01: "SLA xử lý ticket P1 là bao lâu?" → semantic match ✓
- q02: "Khách hàng có thể yêu cầu hoàn tiền trong bao nhiêu ngày?" → semantic match ✓
- q08: "Nhân viên được làm remote tối đa mấy ngày mỗi tuần?" → semantic match ✓

**Weak queries**:
- q07: "Approval Matrix để cấp quyền là tài liệu nào?" → alias/tên cũ ⚠
- q09: "ERR-403-AUTH là lỗi gì?" → không có trong docs (test abstain) ⚠

### Sprint 3 (Variant - Hybrid)

**Expected improvements**:
- q07: BM25 matches "Approval" + "Matrix" keywords → better recall ✓
- q01, q06: BM25 matches exact term "P1" → better precision ✓
- q03: BM25 matches exact term "Level 3" → better precision ✓

---

## 🎯 Sprint 4: Next Steps

### 1. Evaluation (eval.py)
```bash
python eval.py
```
- Chạy 10 test questions
- Tính scorecard: Faithfulness, Answer Relevance, Context Recall, Completeness
- So sánh Baseline vs Variant

### 2. Documentation
- [ ] Điền `docs/architecture.md` với system design
- [ ] Update `docs/tuning-log.md` với kết quả eval thực tế
- [ ] Viết báo cáo cá nhân trong `reports/individual/[ten].md`

### 3. Demo
```bash
# End-to-end demo
python index.py && python rag_answer.py && python eval.py
```

---

## 🔍 Debugging Tips

### Issue: "Collection not found"
```bash
# Rebuild index
python index.py
```

### Issue: "OpenAI API error"
```bash
# Check API key
cat .env
```

### Issue: "BM25 returns empty results"
```bash
# Check if index has documents
python -c "import chromadb; client = chromadb.PersistentClient('chroma_db'); print(client.get_collection('rag_lab').count())"
```

---

## 📚 Key Concepts Implemented

### 1. Dense Retrieval
- **Principle**: Semantic similarity via embeddings
- **Strength**: Understands meaning, paraphrase, synonyms
- **Weakness**: Misses exact terms, aliases, codes

### 2. Sparse Retrieval (BM25)
- **Principle**: Keyword matching with TF-IDF weighting
- **Strength**: Exact terms, codes, names
- **Weakness**: No semantic understanding

### 3. Hybrid Retrieval (RRF)
- **Principle**: Combine rankings from multiple methods
- **Strength**: Best of both worlds
- **Formula**: Reciprocal Rank Fusion (RRF)

### 4. Grounded Generation
- **Principle**: Answer only from retrieved context
- **Rules**: Evidence-only, Abstain, Citation, Short & Clear
- **Goal**: Prevent hallucination

---

## 🎓 Learning Outcomes

After completing Sprint 2 & 3, you should understand:

1. **RAG Pipeline Architecture**
   - Indexing → Retrieval → Generation
   - Each component's role and trade-offs

2. **Retrieval Strategies**
   - When to use Dense vs Sparse vs Hybrid
   - How to combine multiple signals (RRF)

3. **Evaluation Methodology**
   - A/B testing: change ONE variable at a time
   - Metrics: Faithfulness, Relevance, Recall, Completeness

4. **Prompt Engineering**
   - Grounded prompts to prevent hallucination
   - Citation format for traceability

---

## 📝 Notes

- **Temperature = 0**: Cho output ổn định, dễ evaluate
- **Top-k tuning**: Search rộng (10) → Select hẹp (3)
- **Chunk size**: 450 tokens là sweet spot cho policy docs
- **Overlap**: 75 tokens để không mất context ở ranh giới chunks
- **RRF constant K=60**: Standard value từ research papers

---

## ✨ Why Hybrid (Not Rerank or Query Transform)?

**Lý do chọn Hybrid:**

1. **Corpus characteristics**: Lab corpus có mix của:
   - Natural language (policy descriptions)
   - Exact terms (P1, Level 3, ERR-403)
   - Aliases (Approval Matrix → Access Control SOP)

2. **Simple & Effective**: 
   - Không cần train model mới (như rerank)
   - Không cần thêm LLM calls (như query transform)
   - Chỉ cần combine 2 methods đã có

3. **Proven approach**:
   - RRF là standard trong IR research
   - Weights dễ tune (dense_weight, sparse_weight)
   - Transparent và explainable

**Trade-offs:**
- Hybrid chậm hơn dense (chạy cả 2 methods)
- Nhưng nhanh hơn rerank (không cần cross-encoder)
- Và đơn giản hơn query transform (không cần LLM)

---

**Good luck with Sprint 4! 🚀**
