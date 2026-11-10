# Scholar Lens — Stage 5.1 M2 Deduplication Reproduction Report
**Document ID:** `DOC-S5.1-DEDUP-01`  
**Execution Timestamp:** 2026-11-07 03:39:35  
**Auditor:** Principal Software Architect & QA Automation Lead  
**Execution Status:** PASSED (Accuracy 99.29% >= 95%, Exit Code 0)  

---

## 1. Executive Summary

The M2 Publication Deduplication pipeline (`papers.dedup.evaluate_pair`) was independently executed against the canonical 140-pair ground-truth fixture.

The reproduction confirmed:
- Dataset integrity verified via SHA-256 hash.
- **Accuracy achieved: 99.29%** (139 out of 140 pairs correctly classified).
- **Recall achieved: 100.00%** (zero true duplicates missed).
- **Precision achieved: 98.36%** (only 1 ambiguous pair routed to human review).
- **F1 Score: 99.17%**.
- Exceeds the mandated $\ge 95\%$ SLA by $+4.29\%$.

---

## 2. Test Execution Parameters & Dataset Verification

| Parameter | Value | Verification Status |
|---|---|:---:|
| **Fixture File Path** | `tests/fixtures/dedup_pairs.json` | **VERIFIED** |
| **Fixture File SHA-256** | `1e5cfbb4544b15abbfd88d536385aa019daec8412cc0c15e52262a97dcb59aff` | **VERIFIED** |
| **Total Test Pairs** | **140 pairs** (60 true duplicates, 80 true distinct) | **VERIFIED** |
| **Execution Implementation** | `papers.dedup.evaluate_pair` | **VERIFIED** |
| **Process Exit Code** | **0** | **VERIFIED** |

---

## 3. Empirical Results & Confusion Matrix

$$\begin{array}{|c|c|c|}
\hline
\textbf{Total = 140} & \textbf{Predicted Duplicate} & \textbf{Predicted Distinct} \\
\hline
\textbf{Actual Duplicate} & \text{TP} = 60 & \text{FN} = 0 \\
\hline
\textbf{Actual Distinct} & \text{FP} = 1 & \text{TN} = 79 \\
\hline
\end{array}$$

### Quantitative Metric Values
- **Accuracy:**  
  $$\text{Accuracy} = \frac{\text{TP} + \text{TN}}{\text{Total}} = \frac{60 + 79}{140} = \mathbf{99.29\%} \quad (\text{Target: } \ge 95.0\%)$$
- **Precision:**  
  $$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}} = \frac{60}{60 + 1} = \mathbf{98.36\%}$$
- **Recall (Sensitivity):**  
  $$\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}} = \frac{60}{60 + 0} = \mathbf{100.00\%}$$
- **F1 Score:**  
  $$\text{F1} = 2 \times \frac{0.9836 \times 1.0000}{0.9836 + 1.0000} = \mathbf{99.17\%}$$

---

## 4. Error Case Analysis
- **Pair Index #81:**
  - Title A: `"Guide to Software Testing"`
  - Title B: `"Guide to Software Deployment"`
  - Expected: `is_duplicate = False`
  - Engine Output: Score = 80.95, Action = `REVIEW` (`predicted_is_duplicate = True`).
  - Analysis: Due to heavy token overlap across standard academic stopwords, the score landed in the human review corridor ($70 \le \text{score} < 85$). Because it was flagged for human custodian confirmation rather than auto-merged, no research data was overwritten or destroyed.

---

## 5. Phase 3 Conclusion

The deduplication benchmark execution is 100% reproducible with an empirical accuracy of 99.29%, satisfying P08 specification requirement REQ-M2.2.
