# Data contract — Lab Day 10

> Bắt đầu từ `contracts/data_contract.yaml` — mở rộng và đồng bộ file này.

---

## 1. Nguồn dữ liệu (source map)

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|-------------------|-------------------|----------------|
| `data/raw/policy_export_dirty.csv` | CSV export từ HR/Policy system | Duplicate records, missing dates, invalid doc_id, non-ISO dates, stale HR version (10 vs 12 days), stale refund window (14 vs 7 days) | `raw_records`, `quarantine_records` |
| `data/docs/*.txt` | Policy documents (5 files) | Document not in allowlist, encoding issues | `cleaned_records` |

**Data Owner:** 
- HR Policy: hr-team@company.com
- IT Helpdesk: it-support@company.com
- Finance/Refund: finance@company.com

**SLA:**
- Freshness: 24 hours (configurable via FRESHNESS_SLA_HOURS)
- Data quality: 0% halt expectation failures

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| chunk_id | string | Có | Stable ID: `{doc_id}_{seq}_{hash}` |
| doc_id | string | Có | Must be in allowlist: policy_refund_v4, sla_p1_2026, it_helpdesk_faq, hr_leave_policy |
| chunk_text | string | Có | Text content, min 8 chars |
| effective_date | date | Có | ISO format: YYYY-MM-DD |
| exported_at | datetime | Có | ISO 8601 timestamp |

---

## 3. Quy tắc quarantine vs drop

### Quarantine reasons (ghi vào `artifacts/quarantine/quarantine_{run_id}.csv`)

| Reason | Severity | Action | Approval process |
|--------|----------|--------|------------------|
| `unknown_doc_id` | High | Quarantine | Manual review: Check if new doc should be added to allowlist |
| `missing_effective_date` | High | Quarantine | Fix source data, re-export |
| `invalid_effective_date_format` | Medium | Quarantine | Auto-fix if possible (DD/MM/YYYY → YYYY-MM-DD), else manual |
| `stale_hr_policy_effective_date` | High | Quarantine | Confirm version with HR team, update cutoff date if needed |
| `duplicate_chunk_text` | Low | Quarantine (keep first) | Review dedup logic, may indicate source issue |
| `missing_chunk_text` | High | Quarantine | Fix source data |
| `excessive_whitespace` | Medium | Quarantine | Clean source data, may indicate encoding issue |

### Drop (không quarantine, bỏ qua hoàn toàn)

**Hiện tại:** Không có rule drop. Tất cả record không pass cleaning đều vào quarantine để audit.

**Future:** Có thể drop record quá cũ (effective_date < 2020-01-01) nếu không cần lưu trữ.

### Approval workflow (chưa implement)

1. Data engineer review `quarantine_{run_id}.csv`
2. Phân loại:
   - **Fix source:** Yêu cầu upstream system sửa data, re-export
   - **Update rule:** Thêm doc_id vào allowlist, adjust cutoff date
   - **Accept:** Merge vào cleaned (manual override)
3. Log decision vào `quarantine_decisions.log`

---

## 4. Phiên bản & canonical source

### Source of truth

| Policy | Canonical file | Version | Effective date | Owner |
|--------|---------------|---------|----------------|-------|
| **Refund policy** | `data/docs/policy_refund_v4.txt` | v4 | 2026-01-15 | Finance Team |
| **P1 SLA** | `data/docs/sla_p1_2026.txt` | 2026 | 2026-01-01 | IT Support |
| **IT FAQ** | `data/docs/it_helpdesk_faq.txt` | 2026-Q1 | 2026-01-01 | IT Helpdesk |
| **HR leave** | `data/docs/hr_leave_policy.txt` | 2026 | 2026-01-01 | HR Team |

### Version conflict resolution

**Scenario:** CSV export chứa 2 chunk từ `hr_leave_policy`:
- Chunk A: "10 ngày phép năm" (effective_date: 2025-06-01)
- Chunk B: "12 ngày phép năm" (effective_date: 2026-01-01)

**Rule:** Quarantine chunk có `effective_date < 2026-01-01` (cutoff trong `data_contract.yaml`).

**Rationale:** Policy 2026 là canonical, policy cũ không nên xuất hiện trong retrieval.

**Evidence:** Log `expectation[hr_leave_no_stale_10d_annual] OK (halt) :: violations=0` chứng minh không còn "10 ngày" trong cleaned.

### Cutoff date configuration

**Hiện tại (hard-code):** `cleaning_rules.py:95`
```python
if doc_id == "hr_leave_policy" and eff_norm < "2026-01-01":
    quarantine.append(...)
```

**Cải tiến (Distinction):** Đọc từ `contracts/data_contract.yaml:31-32`
```yaml
policy_versioning:
  hr_leave_min_effective_date: "2026-01-01"
```

**Lợi ích:**
- Thay đổi cutoff không cần sửa code
- Audit trail: Git history của contract file
- Đồng bộ giữa data team và policy owner

---

## 5. Metrics

### Pipeline metrics (theo dõi trong manifest)

| Metric | Mô tả | Alert threshold |
|--------|-------|-----------------|
| `raw_records` | Tổng số record từ CSV export | < 1 |
| `cleaned_records` | Số record sau cleaning | < 1 |
| `quarantine_records` | Số record bị quarantine | > raw_records * 0.5 |
| `expectations_passed` | Số expectation pass | < total expectations |
| `expectations_failed` | Số expectation fail | > 0 (halt) |
| `embed_upsert_count` | Số vector được upsert | < cleaned_records |
| `embed_prune_removed` | Số vector bị xóa (stale) | > 100 |
| `freshness_age_hours` | Tuổi data (giờ) | > SLA |

### Monitoring dashboard

```bash
# Xem metrics của một run
cat artifacts/manifests/manifest_<run_id>.json | jq '.'
```

### Metric impact (cho báo cáo nhóm)

| Rule/Expectation | Metric Affected | Before | After | Scenario |
|------------------|-----------------|--------|-------|----------|
| strip_bom | cleaned_records | 10 | 6 | BOM removed |
| normalize_unicode | cleaned_records | 10 | 6 | Unicode normalized |
| excessive_whitespace | quarantine_records | 0 | 1 | >5 spaces detected |
| no_html_tags | expectation pass | - | pass | No HTML in text |
| effective_date_not_future | expectation pass | - | pass | Date valid |

---
