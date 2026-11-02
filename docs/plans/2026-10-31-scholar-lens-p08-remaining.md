# Scholar Lens — P08 Remaining Modules (M1, M2, M3, M5, M4, M9) Implementation Plan

For agentic workers: REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox ( - [ ] ) syntax for tracking.

Goal: Complete P08 on top of the first plan:
- M1: verified researcher profiles with an expertise taxonomy.
- M2: a publication register with ORCID/Crossref import, fuzzy duplicate detection and author matching.
- M3: expertise search.
- M5: collaboration suggestions and a graph.
- M4: a research openings board and an application workflow.
- M9: institutional research analytics.

Architecture:
- Extend the existing apps (`researchers`, `papers`, `search`, `collaboration`, `dashboard`) and add two new apps (`opportunities`, `analytics`).
- PostgreSQL does the heavy lifting: `pg_trgm` produces duplicate candidates, `rapidfuzz` scores them, and a stored `SearchVectorField` with a GIN index powers expertise search.
- External APIs (ORCID public API, Crossref REST) are called with the already-installed `requests`. No habanero and no Celery.
- Long jobs are management commands, scheduled like the first plan's jobs.

Tech Stack: Django 4.2, PostgreSQL 15 (`pg_trgm`, full-text search), `rapidfuzz` (the only new dependency), `requests`, Chart.js (already loaded), Cytoscape.js 3.28.1 from cdnjs (graph page only).

Spec: Details.pdf P08 §3–§13, §15, §17 and §22.

Depends on: `2026-10-31-scholar-lens-ums-shell.md` (the first plan) being finished. This plan relies on the following from it:
- PostgreSQL being required
- the ResearchActivity notification pattern
- the UMS sidebar
- `funding.FundingCall` and `projects.Milestone`
- the facilities utilisation report

Global Constraints
- The only new dependency is `rapidfuzz>=3.6`, added to `requirements.txt`.
- Roles (no new UserProfile.role values):
  - Research Office = `is_staff`.
  - Dean of Research = a member of the Django Group "Dean of Research", or a superuser. The helper `dashboard.permissions.is_dean(user)` checks this.
  - Faculty = `profile.is_faculty_or_admin`.
  - Student = `profile.role == 'STUDENT'`.
- The expertise taxonomy is the existing `researchers.ResearchInterest` (it plays the PDF's ExpertiseTag role). Add an optional `parent` to it; don't create a second tag model.
- Departments: a new `researchers.Department(name unique, code unique 10)`. `ResearcherProfile.department` is a nullable FK to it. Facilities keep their free-text department from the first plan; this plan doesn't migrate them.
- Duplicate detection thresholds (settings):
  - `DEDUP_TRIGRAM_MIN = 0.35`
  - `DEDUP_AUTO_MERGE = 93`
  - `DEDUP_REVIEW_MIN = 80` (`rapidfuzz` token_set_ratio on normalised titles)
  - Also a year check: years must be within ±1.
  - A matching DOI is always a duplicate.
- Author matching thresholds: `AUTHOR_AUTO_MATCH = 92`, `AUTHOR_REVIEW_MIN = 80`. A matching ORCID is always a match.
- Merges are soft: the merged paper gets `merged_into` set and disappears from normal lists. Undo clears it. Nothing is ever deleted.
- Every merge, unmerge, verification decision and author match decision writes a `dashboard.AuditEntry`.
- Academic year: `ACADEMIC_YEAR_START_MONTH = 7` (July–June), so "2025-26" means 1 Jul 2025 – 30 Jun 2026.
- New `ResearchActivity.ACTIVITY_TYPES`: `VERIFICATION`, `OPENING`, `APPLICATION`, `IMPORT`, `SUGGESTION`. Add them all in Task 1 so there is one migration.
- Sidebar:
  - Add 🎯 Openings after Projects, so everyone has 9 items.
  - Add 📊 Reports at the bottom for staff and Dean only.
  - Expertise search lives on the Researchers page, so it gets no new sidebar item.
  - Staff queues are reached through one "Research Office" page, linked from the account menu.
- Explicitly out of scope (state this in docs):
  - Scopus and Web of Science, which need a licence key.
  - Google/Outlook calendar sync and SSO.
  - The institutional repository connector.
  - Scraping Google Scholar. The existing SerpAPI service stays as it is.
  - Embedding-based expertise similarity, which the PDF marks as v2.

Review Focus
1. Malformed external records (missing title, a year as a string like "2021a", null authors list, HTML in the title, a 5 MB abstract) are skipped and counted on the `ImportRun`, never crash the import, and never half-save a paper. Test: `test_import_resilient_to_malformed` (Task 4).
2. A false merge (two genuinely different papers with near-identical generic titles, such as "Introduction" or "Editorial") must not auto-merge. Titles shorter than 4 words go to review, never auto-merge. Test: `test_short_generic_titles_never_auto_merge` (Task 3).
3. Undoing a merge restores the merged paper to every list and search, and undoing it twice is harmless. Test: `test_unmerge_restores_and_is_idempotent` (Task 3).
4. Name variants ("Kumar, R.", "R. Kumar", "Rajesh Kumar", "RAJESH KUMAR", "Rajésh Kumar") attach to the same researcher, while "R. Kumar" from another department goes to review instead of being auto-matched. Test: `test_author_name_variants` (Task 5).
5. A student must not see productivity numbers (per-researcher counts) anywhere, including the CSV export. Test: `test_productivity_dean_only` (Task 11).

Part E — M1 Profiles & expertise

Task 1: Departments, taxonomy, verification, audit log
Files:
- Modify: `researchers/models.py`, `researchers/forms.py`, `researchers/views.py`, `researchers/urls.py`, `researchers/admin.py`, `dashboard/models.py`, `dashboard/admin.py`, `templates/researchers/edit_profile.html` and `templates/researchers/detail.html`.
- Create: `dashboard/permissions.py`, `dashboard/audit.py`, `templates/researchers/verification_queue.html` and the migrations.
- Test: `tests/test_profiles.py`.
- [x] Step 1: Write failing tests.
- [x] Step 2: Implement it, then run makemigrations researchers dashboard. Confirm tests pass, then run full suite.
- [x] Step 3: Commit. `feat(researchers): departments, taxonomy parent, profile verification, audit log`

Part F — M2 Publication register

Task 2: Publication fields, trigram index, soft merge
Files:
- Modify: `papers/models.py`, `papers/admin.py`.
- Create: a migration running `TrigramExtension()` and `GinIndex(fields=['normalised_title'], opclasses=['gin_trgm_ops'], name='paper_title_trgm')`.
- Test: `tests/test_publications.py`.
- [x] Step 1: Write failing tests.
- [x] Step 2: Implement it.
- [x] Step 3: Commit. `feat(papers): DOI, venue, type, normalised title with trigram index, soft merge`

Task 3: Duplicate detection, review queue, reversible merges
Files:
- Create: `papers/dedup.py`, `DuplicateCandidate` model, `templates/papers/dedup_queue.html`, `tests/fixtures/dedup_pairs.json`, `tests/test_dedup.py`.
- Modify: `papers/scholar_service.py:deduplicate_and_store`, `papers/views.py`, `papers/urls.py`.
- [x] Step 1: Build `tests/fixtures/dedup_pairs.json` (at least 120 labelled pairs).
- [x] Step 2: Write failing tests (`test_fixture_accuracy_at_least_95`).
- [x] Step 3: Implement and tune thresholds until accuracy ≥ 95%.
- [x] Step 4: Commit. `feat(papers): fuzzy deduplication with review queue and reversible merges`

Task 4: ORCID + Crossref import
Files:
- Create: `papers/importers.py`, `ImportRun` model, `papers/management/commands/import_publications.py`, `templates/papers/import.html`, fixtures, `tests/test_import.py`.
- Modify: `papers/views.py`, `papers/urls.py`.
- [x] Step 1: Record fixtures.
- [x] Step 2: Write failing tests (`test_import_resilient_to_malformed`).
- [x] Step 3: Implement it.
- [x] Step 4: Commit. `feat(papers): ORCID and Crossref import resilient to malformed records`

Task 5: Author disambiguation and match queue
Files:
- Create: `papers/authors.py`, `templates/papers/author_queue.html`, `tests/test_authors.py`.
- Modify: `papers/models.py` (`PaperAuthor`), `papers/views.py`, `papers/urls.py`, templates.
- [x] Step 1: Write failing tests.
- [x] Step 2: Implement it.
- [x] Step 3: Commit. `feat(papers): author disambiguation with reviewable match queue`

Part G — M3 Expertise discovery

Task 6: Stored search document and faceted expertise search
Files:
- Modify: `researchers/models.py`, `search/views.py`, `search/urls.py`, `templates/researchers/list.html`.
- Create: `researchers/search_index.py`, `rebuild_expertise_index` command, `templates/search/expertise.html`, `tests/test_expertise_search.py`.
- [x] Step 1: Write failing tests (`test_under_one_second`).
- [x] Step 2: Implement it.
- [x] Step 3: Commit. `feat(search): faceted full-text expertise search across departments`

Part H — M5 Collaboration identification

Task 7: Suggestion engine (expertise adjacency + co-authorship gap)
Files:
- Create: `collaboration/suggestions.py`, `compute_collaboration_suggestions` command, `tests/test_suggestions.py`.
- Modify: `collaboration/models.py`, `collaboration/views.py`.
- [ ] Step 1: Write failing tests.
- [ ] Step 2: Implement it.
- [ ] Step 3: Commit. `feat(collaboration): stored suggestions with adjacency and co-authorship gap`

Task 8: Collaboration graph
Files: `collaboration/views.py` (`graph`, `graph_data`), `collaboration/urls.py`, `templates/collaboration/graph.html`, `tests/test_suggestions.py`.
- [ ] Step 1: Write failing tests.
- [ ] Step 2: Implement Cytoscape.js 3.28.1 graph view with accessible table.
- [ ] Step 3: Commit. `feat(collaboration): collaboration network graph`

Part I — M4 Research opportunities

Task 9: opportunities app — openings board and applications
Files: Create `opportunities/` app, views, models, forms, templates, `tests/test_opportunities.py`.
- [ ] Step 1: Write failing tests.
- [ ] Step 2: Implement it.
- [ ] Step 3: Commit. `feat(opportunities): research openings board and application workflow`

Task 10: Funding applications (needed for the M9 success rate)
Files: `funding/models.py` (`FundingApplication`), `funding/views.py`, `funding/urls.py`, `templates/funding/detail.html`, `tests/test_funding.py`.
- [ ] Step 1: Write failing test, implement and commit.
- [ ] Step 2: Commit. `feat(funding): track funding applications`

Part J — M9 Reporting & analytics

Task 11: analytics app — academic-year research report
Files: Create `analytics/` app, metrics, views, templates, `tests/test_analytics.py`.
- [ ] Step 1: Write failing tests (`test_full_year_report_exports`, `test_productivity_dean_only`).
- [ ] Step 2: Implement metrics, Dean-only productivity checks, CSV exports.
- [ ] Step 3: Commit. `feat(analytics): academic-year research report with CSV export`

Task 12: Research Office hub, seed baseline, docs, final check
Files: Create `templates/dashboard/office.html`, `docs/deduplication.md`, `docs/p08-modules.md`. Modify `dashboard/views.py`, `seed_demo_data`.
- [ ] Build Research Office hub.
- [ ] Seed baseline with publications.
- [ ] Author `docs/deduplication.md`.
- [ ] Author `docs/p08-modules.md`.
- [ ] Browser check at 1366px and 375px.
- [ ] Commit. `feat(dashboard): research office hub; docs and seeded baseline`
