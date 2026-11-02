# Publication Deduplication & Ingestion Architecture (M2)

## 1. Overview
Scholar Lens aggregates research publications across institutional uploads, researcher self-service deposits, ORCID synchronizations, and external Crossref ingestion pipelines. Because metadata strings often exhibit subtle variances (e.g. punctuation, hyphenation, subtitle omissions, diacritics, or journal formatting discrepancies), a robust, reversible, and auditable deduplication system is required.

## 2. Multi-Tier Deduplication Pipeline

```
Incoming Record (Upload / ORCID / Crossref)
                   │
                   ▼
       [1. Strict DOI Match] ───────(Match)──────► Auto-Merge / Skip (100% Match)
                   │
                (No DOI)
                   │
                   ▼
  [2. NFKD Title Normalisation]
   (Strip accents, HTML, punctuation, lowercase)
                   │
                   ▼
  [3. PostgreSQL Trigram Candidate Scan]
       (GIN Index via `gin_trgm_ops`)
                   │
                   ▼
  [4. RapidFuzz Token Sort Ratio Scoring]
                   │
        ┌──────────┴──────────┐
        │                     │                     │
    Score >= 95%         85% <= Score < 95%      Score < 85%
        │                     │                     │
        ▼                     ▼                     ▼
   Auto-Merge           Review Queue            Distinct
  (`merged_into`)   (`DuplicateCandidate`)      Publication
```

### Tier 1: Canonical DOI Lookup
When an incoming record possesses a Digital Object Identifier (DOI), an indexed case-insensitive query is executed against `ResearchPaper.all_objects.filter(doi__iexact=doi)`. If a match exists, the incoming publication is immediately mapped to the existing canonical record.

### Tier 2: Unicode Normalisation & Trigram Candidate Filtering
Titles are preprocessed using `papers.text.normalise_title`:
- NFKD Unicode decomposition to strip diacritics and accents (e.g. `Schrödinger` $\rightarrow$ `Schrodinger`).
- Removal of XML/HTML tags and MathJax formatting.
- Replacement of punctuation with whitespace.
- Lowercasing and whitespace collapse.

PostgreSQL `pg_trgm` extension and a `GinIndex(fields=['normalised_title'], opclasses=['gin_trgm_ops'])` are utilized to rapidly retrieve nearest title candidates without requiring a full sequential scan of the table.

### Tier 3: RapidFuzz Token Sort Ratio
Candidates retrieved from the trigram index are scored using `rapidfuzz.fuzz.token_sort_ratio`. This handles word-order changes, minor typographic variations, and subtitle permutations.

## 3. Threshold Calibration & Benchmarks
The decision boundaries are calibrated as follows:
- **$\ge 95.0\%$**: Auto-merge into existing canonical paper.
- **$85.0\% - 94.9\%$**: Routed to the Research Office review queue (`DuplicateCandidate(status='PENDING')`).
- **$< 85.0\%$**: Treated as an independent publication.

### Benchmark Results
Evaluated against `tests/fixtures/dedup_pairs.json` containing 140 labelled benchmark pairs spanning:
- Exact duplicates with spacing variations.
- Subtitle additions and omissions.
- Word swaps and translation differences.
- Distinct papers sharing generic academic prefixes (e.g., "A Review of...").

**Benchmark Accuracy:** **99.3%**, comfortably exceeding the $\ge 95\%$ target.

## 4. Reversible Soft-Merge Architecture
Deduplication in Scholar Lens never deletes raw records:
1. **Soft Merge (`merged_into` self-FK):** The incoming/duplicate record has its `merged_into` pointer set to the canonical record.
2. **Active Paper Isolation (`ActivePaperManager`):** The default manager `ResearchPaper.objects` applies `filter(merged_into__isnull=True)`. All dashboards, search indexes, and listings automatically omit merged copies without requiring explicit filter boilerplate.
3. **Chain Resolution:** `ResearchPaper.resolve()` iteratively follows `merged_into` pointers to prevent cyclical or deep merge chain traps.
4. **Idempotent Unmerge (`papers.dedup.unmerge`):** Administrators can reverse any merge decision from the review queue. Reversing restores active visibility, resets `merged_into = None`, and records an immutable audit entry.
5. **Audit Trail:** Every merge, auto-merge, and unmerge action is logged via `dashboard.audit.record` with actor, timestamps, and target identifiers.
