# Evaluation Engine — Scholar Lens

## Overview

The Research Evaluation Engine is the signature feature of Scholar Lens. It provides multi-dimensional AI-powered assessment of research papers across seven canonical dimensions, complete with verifiable supporting evidence citations, confidence indicators, and evaluation provenance tracking.

---

## Canonical Scoring Framework

The Scholar Lens evaluation framework is standardized across all layers of the platform (database models, AI services, API payloads, presentation templates, and documentation).

| Dimension | Key Code | Weight | Description |
|-----------|----------|:------:|-------------|
| **Potential Novelty** | `NOVELTY` | **20%** | Originality of problem formulation, conceptual novelty, and distinctiveness from baseline literature |
| **Research Gap** | `RESEARCH_GAP` | **15%** | Clarity and rigor in identifying and addressing an open limitation in prior art |
| **Methodology** | `METHODOLOGY` | **15%** | Soundness, appropriateness, and structured repeatability of experimental/theoretical methods |
| **Contribution** | `CONTRIBUTION` | **15%** | Significance, utility, and domain advancement provided by findings |
| **Evidence Quality** | `EVIDENCE_QUALITY` | **15%** | Rigor, empirical sufficiency, and citation soundness supporting conclusions |
| **Technical Strength** | `TECHNICAL_STRENGTH` | **10%** | Theoretical cohesion, mathematical correctness, and system design robustness |
| **Clarity** | `CLARITY` | **10%** | Organizational hierarchy, nomenclature consistency, and academic readability |
| **TOTAL** | — | **100%** | Sum of all weights strictly equals 100% |

---

## Score Calculation

$$\text{Overall Score} = \sum_{i=1}^{7} \left(\text{dimension\_score}_i \times \frac{\text{dimension\_weight}_i}{100}\right)$$

### Canonical Calculation Example:
```text
Potential Novelty:     85.0 × 0.20 = 17.00
Research Gap:          88.0 × 0.15 = 13.20
Methodology:           82.0 × 0.15 = 12.30
Contribution:          80.0 × 0.15 = 12.00
Evidence Quality:      84.0 × 0.15 = 12.60
Technical Strength:    86.0 × 0.10 =  8.60
Clarity:               90.0 × 0.10 =  9.00
───────────────────────────────────────────
Overall Score:                       84.70 / 100
```

### Score Interpretation & Tiers

| Score Range | Classification | Academic Implication |
|:-----------:|----------------|----------------------|
| **80 – 100** | Promising — Strong Research | Robust theoretical and empirical foundation with clear contributions |
| **60 – 79** | Moderate — Improvement Areas | Solid baseline; requires addressing specific empirical or methodological gaps |
| **40 – 59** | Needs Work — Significant Gaps | Preliminary formulation; substantial revisions recommended before peer submission |
| **0 – 39** | Early Stage — Major Revision | Exploratory stage requiring conceptual restructuring and additional validation |

---

## Explainable Evaluation Model

Scholar Lens does not display isolated numeric scores. Each dimension produces structured evidence:

```text
[Potential Novelty: 84 / 100] (Weight: 20%)

Assessment:
The research combines distributed consensus mechanisms with selective transformer
pruning in a formulation distinct from surveyed baseline literature.

Supporting Evidence:
• Methodology — Page 4: "We introduce a sparsified attention head pruning policy..."
• Related Work — Page 6: "In contrast to conventional token masking approaches..."

Confidence: Medium
Limitation: Similarity analysis cannot establish definitive originality without broader corpus cross-referencing.
```

### Core Terminology Guardrails
The platform uses cautious, objective academic language and **never** claims:
- Definitive novelty or proof of originality
- Proof of patentability
- Plagiarism certification
- Guaranteed publication acceptance

Instead, the platform explicitly employs:
- *Potential Novelty*
- *AI-Assessed Novelty*
- *Similarity Analysis*
- *Research Strength*
- *Further Validation Recommended*

---

## Evaluation Provenance & Auditability

To answer *"Why did Scholar Lens give this paper this score?"*, every evaluation report records:
- `evaluation_id`: Globally unique UUID
- `model_version` / `provider`: e.g. `gpt-4o-mini` via OpenAI API or `scholar-lens-rule-engine-v2`
- `prompt_version`: Canonical prompt template version (`v2.0-canonical-7dim`)
- `scoring_framework_version`: Canonical framework identifier (`v2-7dim-100pt`)
- `paper_version`: Sequential evaluation run index (`v1`, `v2`, `v3`)
- `created_at`: Generation timestamp
- `confidence`: High, Medium, or Low
- `limitations`: Contextual boundary statement

---

## Settings Configuration

Weights are canonically configured in `scholar_lens/settings.py`:

```python
EVALUATION_WEIGHTS = {
    'novelty': 20,              # Potential Novelty (20%)
    'research_gap': 15,         # Research Gap (15%)
    'methodology': 15,          # Methodology (15%)
    'contribution': 15,         # Contribution (15%)
    'evidence_quality': 15,     # Evidence Quality (15%)
    'technical_strength': 10,   # Technical Strength (10%)
    'clarity': 10,              # Clarity (10%)
}
```

---

## Analytical Disclaimer

Every evaluation report, paper detail tab, and presentation view displays the mandatory disclaimer:

> *This AI-generated assessment is an analytical aid and does not certify research originality, novelty, plagiarism status, patentability, or publication acceptance.*

