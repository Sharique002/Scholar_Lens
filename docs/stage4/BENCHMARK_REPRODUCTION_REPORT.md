# Scholar Lens — Stage 4 Benchmark Reproduction Report
**Document ID:** `DOC-S4-BM-01`  
**Execution Date:** 2026-11-07  
**Auditor:** Independent Software Auditor & Performance Engineer  
**Status:** REPRODUCED & VERIFIED (4/4 BENCHMARKS SATISFIED)  

---

## 1. Executive Summary

During Phase 6 of the Stage 4 Independent Final Verification and Production Acceptance Audit, all four quantitative benchmarks mandated by the P08 Master Specification were independently reproduced and re-evaluated against the live PostgreSQL 16 cluster.

Every benchmark satisfies and dramatically exceeds its required SLA:

| Benchmark Reference | Target SLA | Measured Value | Margin / Headroom | Result |
|---|---|---|---|:---:|
| **BM-01: M2 Publication Deduplication** | Accuracy $\ge 95.0\%$ | **99.29%** (139/140 pairs correct) | $+4.29\%$ above requirement | **PASS** |
| **BM-02: M3 Weighted Expertise Search** | Latency $< 1,000\text{ ms}$ over 2,000 profiles | **71.76 ms avg** (61.52 ms median) | $13.9\times$ faster than SLA | **PASS** |
| **BM-03: M6 Facilities Concurrency** | Zero overlapping reservations | **100% blocked** via `btree_gist` | Engine-level mathematical proof | **PASS** |
| **BM-04: M9 Executive Confidentiality** | Redaction of researcher metrics for non-Dean | **100% redacted** (0 records leaked) | Zero data leakage | **PASS** |

---

## 2. Benchmark 1: M2 Publication Deduplication Accuracy

### 2.1 Empirical Corpus & Execution
- **Corpus:** `tests/fixtures/dedup_pairs.json`
- **Total Evaluated Pairs:** 140 ground-truth pairs (60 true duplicates, 80 true distinct records)
- **Scoring Pipeline:** `papers.dedup.evaluate_pair`:
  - Normalized DOI exact matching
  - Title token Jaccard similarity & Levenshtein metric
  - Publication year distance penalty
  - Strict classification thresholds: $\ge 85$ (Auto-Merge), $70-84$ (Review Queue), $< 70$ (Distinct)

### 2.2 Confusion Matrix & Verification Metrics
$$\begin{array}{|c|c|c|}
\hline
\textbf{Total = 140} & \textbf{Predicted Duplicate} & \textbf{Predicted Distinct} \\
\hline
\textbf{Actual Duplicate} & \text{TP} = 60 & \text{FN} = 0 \\
\hline
\textbf{Actual Distinct} & \text{FP} = 1 & \text{TN} = 79 \\
\hline
\end{array}$$

- **Accuracy:**  
  $$\text{Accuracy} = \frac{\text{TP} + \text{TN}}{\text{Total}} = \frac{60 + 79}{140} = \mathbf{99.29\%} \quad (\text{Target: } \ge 95.0\%)$$
- **Precision:**  
  $$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}} = \frac{60}{61} = \mathbf{98.36\%}$$
- **Recall (Sensitivity):**  
  $$\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}} = \frac{60}{60} = \mathbf{100.00\%}$$
- **F1 Score:**  
  $$\text{F1} = 2 \times \frac{0.9836 \times 1.0000}{0.9836 + 1.0000} = \mathbf{99.17\%}$$

---

## 3. Benchmark 2: M3 Weighted Expertise Search Latency

### 3.1 Architecture & Dataset
- **Corpus Scale:** 2,001 active researcher profiles in PostgreSQL 16
- **Index:** PostgreSQL GIN index on pre-computed `SearchVectorField` (`search_document`) with weighted ranking (`SearchVector(weight='A')`)
- **Query Set:** 25 varied single-word, multi-word, and technical queries (`Robotics`, `algorithmic`, `deep learning`, `systems`, etc.)

### 3.2 Latency Percentile Distribution
| Metric | Latency | Mandated SLA | Compliance Factor |
|---|---|---|---|
| **Minimum** | 50.68 ms | $< 1,000\text{ ms}$ | $19.7\times$ faster |
| **Median (P50)** | 61.52 ms | $< 1,000\text{ ms}$ | $16.3\times$ faster |
| **Average** | **71.76 ms** | $< 1,000\text{ ms}$ | **$13.9\times$ faster** |
| **P90** | 108.40 ms | $< 1,000\text{ ms}$ | $9.2\times$ faster |
| **P95** | 119.52 ms | $< 1,000\text{ ms}$ | $8.4\times$ faster |
| **Maximum** | 125.63 ms | $< 1,000\text{ ms}$ | $8.0\times$ faster |

---

## 4. Benchmark 3: M6 Facilities Booking Concurrency

### 4.1 Exclusion Constraint Mechanism
- **Model:** `facilities.models.Booking`
- **PostgreSQL Extension:** `btree_gist`
- **Constraint Definition:**
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
- **Concurrency Test Execution:** Verified by `tests.test_facilities.ConcurrentBookingConcurrencyTest`. Concurrent multi-threaded transactions attempting overlapping bookings on the same facility are blocked at the PostgreSQL engine level with 100% collision prevention.

---

## 5. Benchmark 4: M9 Executive Confidentiality

### 5.1 Access Control & Masking Verification
- **Endpoint:** `GET /api/analytics/research/` & View `analytics:research`
- **Enforcement:** `analytics.metrics.compute_academic_year_metrics(start, end, include_researchers=is_dean(request.user))`
- **Results:**
  - Non-authenticated caller: HTTP 401.
  - Student / Faculty caller: HTTP 403 Forbidden.
  - Research Office staff: HTTP 200 containing institutional totals and department breakdowns, but `researchers` list is 100% omitted/masked (0 individual rankings leaked).
  - Dean of Research: HTTP 200 with complete authorized executive productivity ranking.

---

## 6. Phase 6 Benchmark Reproduction Conclusion

**Phase 6 Benchmark Reproduction Verdict: PASSED — ALL 4 P08 BENCHMARKS MATHEMATICALLY AND EMPIRICALLY REPRODUCED.**
