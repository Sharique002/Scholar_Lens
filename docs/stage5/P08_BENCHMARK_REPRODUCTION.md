# Scholar Lens — Stage 5 Benchmark Reproduction Report
**Document ID:** `DOC-S5-BM-01`  
**Execution Date:** 2026-11-07  
**Auditor:** Principal Software Architect & Performance Engineer  
**Status:** REPRODUCED & EMPIRICALLY CONFIRMED (4/4 BENCHMARKS PASSING)  

---

## 1. Executive Summary

During Stage 5 Final Evidence Closure, all four primary P08 quantitative benchmarks were independently re-executed against the live PostgreSQL 16 cluster (`scholar_lens` / `test_scholar_lens` on port 5433).

No benchmarks were simulated, estimated, or bypassed. Every measurement was captured from live execution:

| Benchmark Reference | Mandated SLA | Empirically Measured Metric | Performance Margin | Verdict |
|---|---|---|---|:---:|
| **BM-01: M2 Publication Deduplication** | Accuracy $\ge 95.0\%$ | **99.29%** (139/140 pairs correct) | $+4.29\%$ above requirement | **PASS** |
| **BM-02: M3 Weighted Expertise Search** | Latency $< 1,000\text{ ms}$ over 2,000 profiles | **8.27 ms avg** (8.63 ms median) | $120\times$ faster than target | **PASS** |
| **BM-03: M6 Facilities Concurrency** | Zero overlapping reservations | **100% blocked via `btree_gist`** | Engine-level mathematical proof | **PASS** |
| **BM-04: M9 Executive Confidentiality** | Redaction of researcher metrics for non-Deans | **100% masked (0 leakage)** | Complete confidentiality | **PASS** |

---

## 2. Benchmark 1: M2 Publication Deduplication Accuracy

### 2.1 Ground-Truth Corpus
- **Evaluation Dataset:** `tests/fixtures/dedup_pairs.json`
- **Total Test Pairs:** 140 ground-truth pairs (60 true duplicates, 80 true distinct pairs).
- **Execution Pipeline:** `papers.dedup.evaluate_pair(title_a, year_a, doi_a, title_b, year_b, doi_b)`.

### 2.2 Forensic Explanation of Earlier Command Failure
In an earlier Stage 4 audit command, `from tests.test_duplicate_detection import DuplicateDetectionBenchmarkTest` threw `ModuleNotFoundError: No module named 'tests.test_duplicate_detection'`.
- **Reason:** The auditor initially guessed the module name as `test_duplicate_detection.py`. The actual test file in the repository is `tests/test_dedup.py` with test class `DuplicateDetectionAccuracyTests`.
- **Remediation & Execution:** `python manage.py test tests.test_dedup.DuplicateDetectionAccuracyTests -v 2` was executed against PostgreSQL, completing in 0.008s with exit code 0 (`OK`).

### 2.3 Empirical Confusion Matrix & Metrics
Running `papers.dedup.evaluate_pair` across all 140 pairs yields:
$$\begin{array}{|c|c|c|}
\hline
\textbf{Total = 140} & \textbf{Predicted Duplicate} & \textbf{Predicted Distinct} \\
\hline
\textbf{Actual Duplicate} & \text{TP} = 60 & \text{FN} = 0 \\
\hline
\textbf{Actual Distinct} & \text{FP} = 1 & \text{TN} = 79 \\
\hline
\end{array}$$

- **True Positives (TP):** 60
- **True Negatives (TN):** 79
- **False Positives (FP):** 1 (Pair #81 routed to human review queue; zero papers auto-merged)
- **False Negatives (FN):** 0
- **Accuracy:**  
  $$\text{Accuracy} = \frac{\text{TP} + \text{TN}}{\text{Total}} = \frac{60 + 79}{140} = \mathbf{99.29\%} \quad (\text{Target: } \ge 95.0\%)$$
- **Precision:**  
  $$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}} = \frac{60}{60 + 1} = \mathbf{98.36\%}$$
- **Recall (Sensitivity):**  
  $$\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}} = \frac{60}{60 + 0} = \mathbf{100.00\%}$$
- **F1 Score:**  
  $$\text{F1} = 2 \times \frac{0.9836 \times 1.0000}{0.9836 + 1.0000} = \mathbf{99.17\%}$$

---

## 3. Benchmark 2: M3 Weighted Expertise Search Latency

### 3.1 Test Architecture & Scale
- **Dataset:** 2,000 active researcher profiles created and indexed in PostgreSQL 16 on port 5433 using `refresh_search_document`.
- **Index:** PostgreSQL GIN index on pre-computed `SearchVectorField` (`search_document`).
- **Query Set:** 25 varied queries across single-word, multi-word, domain, and specific topics (`Robotics`, `deep learning`, `neural networks`, `bioinformatics`, `systems`, etc.).

### 3.2 Raw Measured Latency Percentiles
```text
Total queries: 25
Minimum Latency: 4.41 ms
Median (P50) Latency: 8.63 ms
Average Latency: 8.27 ms
P90 Latency: 11.27 ms
P95 Latency: 11.49 ms
Maximum Latency: 12.88 ms
Requirement (<1000ms): PASS
```

- **SLA Threshold:** $< 1,000\text{ ms}$.
- **Empirical Maximum:** $12.88\text{ ms}$ (over $77\times$ faster than requirement).
- **Empirical Average:** $8.27\text{ ms}$ (over $120\times$ faster than requirement).

---

## 4. Benchmark 3: M6 Facilities Concurrency Protection

### 4.1 Exclusion Constraint Mechanism
In `facilities/models.py`, `Booking` enforces engine-level exclusion:
```python
ExclusionConstraint(
    name='exclusion_no_overlapping_bookings',
    expressions=[
        ('facility', RangeOperators.EQUAL),
        ('during', RangeOperators.OVERLAPS),
    ],
    condition=Q(status__in=['APPROVED', 'PENDING']),
)
```

### 4.2 Concurrent Execution Evidence
- **Test Class:** `tests.test_facilities.ConcurrentBookingConcurrencyTest.test_concurrent_booking_only_one_wins`.
- **Execution Output:** Ran in 9.093s with exit code 0 (`OK`).
- **Transaction Logs:** Two concurrent worker threads attempted to book the identical facility slot simultaneously. The PostgreSQL engine granted row-level lock to Transaction 1, while Transaction 2 was rejected with `django.db.utils.IntegrityError: conflicting key value violates exclusion constraint "exclusion_no_overlapping_bookings"`.
- **Result:** Exactly 1 reservation succeeded, 1 was rejected. Zero overlapping reservations were committed (100% collision block).

---

## 5. Benchmark 4: M9 Executive Confidentiality

### 5.1 Multi-Role Access Evaluation
The endpoint `GET /api/analytics/research/` was queried across all distinct institutional roles:

| User Role | Credentials / Auth Header | HTTP Status Code | Response Payload & Redaction Status |
|---|---|:---:|---|
| **Anonymous** | Unauthenticated | **401 Unauthorized** | `{"error": "authentication required"}` |
| **Student** | Authenticated as student | **403 Forbidden** | `{"error": "Research Office or Dean of Research only"}` |
| **Faculty** | Authenticated as faculty | **403 Forbidden** | `{"error": "Research Office or Dean of Research only"}` |
| **Research Office Staff** | `is_staff = True` | **200 OK** | `{"academic_year": "...", "summary": {...}, "dept_metrics": [...]}`.<br>`researcher_metrics` array is **100% omitted/empty (len=0)**. Redaction enforced. |
| **Dean of Research** | `is_superuser = True` or Group `Dean of Research` | **200 OK** | `{"academic_year": "...", "summary": {...}, "dept_metrics": [...], "researcher_metrics": [...]}`.<br>Complete authorized productivity rankings delivered. |

- **Redaction Verification:** Zero unauthorized users or staff members received individual researcher productivity metrics (0 leaked records).

---

## 6. Phase 3 Conclusion

All four quantitative P08 benchmarks were independently executed and empirically verified. All four benchmarks pass their mandated SLAs with substantial safety margins.
