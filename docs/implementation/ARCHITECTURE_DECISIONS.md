# Scholar Lens — Architecture Decision Records (ADR)

**Document Version:** 1.0.0  
**Last Updated:** November 6, 2026  

---

## ADR 001: Preservation of the Django Modular Monolith

- **Status:** Accepted
- **Context:** Scholar Lens integrates 13 interrelated applications (profiles, publications, projects, facilities, funding, opportunities, analytics, AI engine, evaluation). Previous suggestions pondered splitting into microservices.
- **Decision:** Retain the Django modular monolith architecture. Business logic resides in dedicated service layers (`papers.dedup`, `papers.importers`, `collaboration.services`, `ai_engine.services`, `analytics.metrics`, `evaluation.services`).
- **Consequences:** Eliminates distributed transaction failures, network latency, and orchestration overhead while preserving clean separation of concerns and high maintainability.

---

## ADR 002: PostgreSQL as Primary Database Engine

- **Status:** Accepted
- **Context:** Several core P08 requirements rely on advanced database engine capabilities:
  - GiST indexing and `ExclusionConstraint` for facility booking overlap prevention (`RangeOperators.OVERLAPS`).
  - GIN indexing with `pg_trgm` for trigram similarity scanning in publication deduplication.
  - Pre-computed `SearchVectorField` with GIN indexing for sub-second weighted full-text expertise search.
- **Decision:** PostgreSQL 15+ is required for production, acceptance testing, and benchmark certification. SQLite is retained only as an optional dev fallback with documented exclusions.
- **Consequences:** Ensures 100% compliance with strict P08 database-level concurrency and search requirements.

---

## ADR 003: LPU Institutional Design System & Token Consolidation

- **Status:** Accepted
- **Context:** The application contained conflicting styles: legacy neo-brutalist styling with 3.5px black borders and pastel colors (`style.css`), alongside an overlay university portal shell (`ums.css`).
- **Decision:** Establish `static/css/institutional_tokens.css` as the canonical source of truth for all colors, typography, spacing, elevations, and geometry. Refactor `style.css` to eliminate all brutalist black borders and drop shadows, aligning all components with the LPU institutional palette:
  - Primary Maroon: `#9B2335`
  - Dark Maroon: `#7A1B29`
  - Maroon Tint: `#FBEFF1`
  - Primary Action Orange: `#F37021`
  - Neutral Canvas: `#F5F5F7`
  - Neutral Borders: `#E2E4E8`
- **Consequences:** Guarantees a cohesive, institution-grade, professional visual identity across all views and viewports.

---

## ADR 004: Centralized Global Role Context Processor

- **Status:** Accepted
- **Context:** Role-based navigation in templates previously used ad-hoc checks such as `'dean' in user.username.lower`, which is fragile and violates security principles.
- **Decision:** Inject `is_dean` and `is_office` flags into all templates via `scholar_lens.context_processors.site_settings`, backed by `dashboard.permissions`.
- **Consequences:** All templates can cleanly and securely evaluate user authorization without fragile username heuristics.

---

## ADR 005: Reversible Soft-Merge Publication Architecture

- **Status:** Accepted
- **Context:** Merging duplicate publications must never permanently destroy citations, historical metadata, or provenance.
- **Decision:** Use a self-referential foreign key `ResearchPaper.merged_into = ForeignKey('self', null=True)`. Normal catalog queries filter `merged_into__isnull=True` via `ActivePaperManager`. An idempotent `unmerge_paper` view and action can restore any merged record at any time, backed by an immutable `AuditEntry`.
- **Consequences:** 100% data preservation and full reversibility for institutional audit compliance.
