# Kiến trúc pipeline — Lab Day 10

**Nhóm:** Nhóm 5B — Lớp 402  
**Cập nhật:** 2026-04-15

---

## 1. Sơ đồ luồng

```
[RAW EXPORT]
  data/raw/policy_export_dirty.csv (10 records)
  exported_at: 2026-04-10T08:00:00
        ↓
[INGEST]  etl_pipeline.py::load_raw_csv
  log: raw_records=10, run_id
        ↓
[TRANSFORM]  transform/cleaning_rules.py::clean_rows
  ├─→ CLEANED (6 records)  →  artifacts/cleaned/cleaned_{run_id}.csv
  └─→ QUARANTINE (4 records)  →  artifacts/quarantine/quarantine_{run_id}.csv
        ↓
[VALIDATE]  quality/expectations.py::run_expectations
  8 expectations — halt nếu severity=halt & failed
        ↓
[EMBED]  etl_pipeline.py::cmd_embed_internal
  Chroma collection: day10_kb
  Idempotent: upsert by chunk_id + prune stale ids
        ↓
[MANIFEST]  artifacts/manifests/manifest_{run_id}.json
  fields: run_id, run_timestamp, raw/cleaned/quarantine counts, latest_exported_at
        ↓
[FRESHNESS CHECK]  monitoring/freshness_check.py     ← đo tại boundary publish
  SLA: 24 hours từ latest_exported_at
        ↓
[SERVING]  eval_retrieval.py / grading_run.py
  Query day10_kb → top-k chunks
```

---

## 2. Ranh giới trách nhiệm

| Thành phần | Input | Output | Owner nhóm | Sprint |
|------------|-------|--------|------------|--------|
| **Ingest** | `data/raw/*.csv` | List[Dict] raw rows | Trần Thượng Trường Sơn | 1 |
| **Transform** | Raw rows | (cleaned, quarantine) | Trần Thượng Trường Sơn | 1 |
| **Quality** | Cleaned rows | (results, halt flag) | Bùi Lâm Tiến | 2 |
| **Embed** | Cleaned CSV | Chroma collection | Bùi Lâm Tiến | 2 |
| **Inject & Eval** | Chroma + questions | CSV eval | Trương Đăng Nghĩa | 3 |
| **Monitor & Docs** | Manifest JSON | (status, detail) | Nhóm | 4 |

---

## 3. Idempotency & rerun

Strategy: upsert theo `chunk_id` + prune id không còn trong cleaned set.

```python
# chunk_id = f"{doc_id}_{seq}_{hash}"
# hash = sha256(doc_id|chunk_text|seq)[:16]

prev_ids = set(col.get(include=[]).get("ids", []))
drop = sorted(prev_ids - set(current_ids))
if drop:
    col.delete(ids=drop)          # xóa vector stale
col.upsert(ids=ids, documents=documents, metadatas=metadatas)
```

Rerun 2 lần với cùng data → không duplicate vector. Sau khi chạy inject-bad rồi chạy sprint3-clean → `embed_prune_removed=1`, chunk "14 ngày làm việc" bị xóa khỏi index.

---

## 4. Liên hệ Day 09

Pipeline này cung cấp và làm mới corpus cho retrieval worker Day 09. Cùng sử dụng `data/docs/` (5 policy files), nhưng dùng collection riêng `day10_kb` để tách biệt testing khỏi Day 09 `day09_kb`.

```
Day 10 ETL  →  embed  →  chroma_db/day10_kb
                                ↓
                    Day 09 Retrieval Worker
                                ↓
                    Day 09 Synthesis Worker
```

---

## 5. Rủi ro đã biết

- **Freshness chỉ đo 1 boundary (publish):** Không phân biệt "data cũ từ nguồn" vs "pipeline chậm". Cải tiến: thêm `ingest_timestamp` vào manifest.
- **Concurrent runs:** 2 pipeline chạy đồng thời trên cùng collection → race condition khi prune. Chưa có lock.
- **Scale chưa test:** CSV mẫu 10 dòng; chưa test 1000+ chunks.
- **Cutoff date hard-code:** `2026-01-01` trong `cleaning_rules.py:147` — nên đọc từ `contracts/data_contract.yaml`.
