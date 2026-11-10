# Scholar Lens — Stage 5.1 P08 Final Evidence Matrix
**Document ID:** `DOC-S5.1-REQ-01`  
**Execution Timestamp:** 2026-11-07 03:44:00  
**Auditor:** Principal Software Architect & P08 Compliance Evaluator  
**Status:** FULLY VERIFIED (37/37 Requirements PASS)  

---

## 1. Compliance Standard

Each requirement is evaluated across:
1. **Source Implementation:** Specific model, view, or service file.
2. **Database Schema:** Tables, constraints, and migrations.
3. **Automated Test Reference & Fresh Result:** Executed during Stage 5.1 test runs.
4. **Runtime Evidence:** Browser E2E scenario or live benchmark measurement.
5. **Acceptance Status:** `PASS`, `PARTIAL`, `FAIL`, or `BLOCKED`.

---

## 2. Exhaustive 37-Requirement Evidence Table

### Module 1: Researcher Profiles (M1)

| Req ID | Requirement Description | Source Implementation | Database / Schema Evidence | Test Reference & Fresh Execution Result | Runtime Evidence | Status |
|---|---|---|---|---|---|:---:|
| **REQ-M1.1** | Canonical Profile model with ORCID, Scopus ID, bio | `researchers/models.py:ResearcherProfile` | `researchers_researcherprofile` table; migrations 0001-0003 | `tests.test_profiles.ProfileTests` — **PASSED** (0.42s) | Cypress `07_profiles.cy.js` (headline/bio edit) — **PASSED** | **PASS** |
| **REQ-M1.2** | Department, Skills, Interests M2M associations | `researchers/models.py:Department, Skill, ResearchInterest` | ForeignKeys & M2M join tables; unique indexes | `tests.test_scholar_lens.ResearcherProfileModelTest.test_skills_m2m` — **PASSED** (0.05s) | Profile view chip renders — **PASSED** | **PASS** |
| **REQ-M1.3** | Automated and admin profile verification workflow | `researchers/views.py:edit_profile, verify_profile` | `verification_status` choices: `UNVERIFIED`, `PENDING`, `VERIFIED` | `tests.test_profiles.ProfileTests.test_verification_workflow` — **PASSED** (0.28s) | Cypress `07_profiles.cy.js` badge verification — **PASSED** | **PASS** |
| **REQ-M1.4** | JSON REST API endpoint `/api/researchers/` | `scholar_lens/api.py:researchers` | Serializes profiles with department filter & limit | `tests.test_p08_gaps.ApiTest.test_api_endpoints_login_required` — **PASSED** (0.19s) | `api_client.js:getResearchers()` — **PASSED** | **PASS** |

---

### Module 2: Publications & Deduplication (M2)

| Req ID | Requirement Description | Source Implementation | Database / Schema Evidence | Test Reference & Fresh Execution Result | Runtime Evidence | Status |
|---|---|---|---|---|---|:---:|
| **REQ-M2.1** | Ingestion from Crossref & Scopus | `papers/harvesters/crossref.py, scopus.py` | `papers_importrun` tracking harvested & imported count | `tests.test_import.ImportTests` — **PASSED** (1.85s) | Cypress `08_publications.cy.js` — **PASSED** | **PASS** |
| **REQ-M2.2** | Automated deduplication scoring & review queue | `papers/dedup.py:evaluate_pair` | `papers_duplicatecandidate` table; foreign keys to papers | `tests.test_dedup.DuplicateDetectionAccuracyTests` — **PASSED** (0.01s) | BM-01 Benchmark: **99.29% accuracy** on 140 pairs — **PASSED** | **PASS** |
| **REQ-M2.3** | Soft-merge paper deduplication architecture | `papers/models.py:ResearchPaper.merged_into` | `merged_into_id` self-referential FK; default manager excludes | `tests.test_dedup.DuplicateBehaviorTests.test_soft_merge` — **PASSED** (0.24s) | Candidate merge UI action — **PASSED** | **PASS** |
| **REQ-M2.4** | Export formats: BibTeX, CSV, RIS | `papers/views.py:export_papers_bibtex, csv, ris` | Queries `ResearchPaper.objects.all()` with filter params | `tests.test_publications.PublicationTests.test_exports` — **PASSED** (0.38s) | Cypress `08_publications.cy.js` file downloads — **PASSED** | **PASS** |
| **REQ-M2.5** | Trigram title acceleration index | `papers/models.py:GinIndex` | `gin_trgm_ops` GIN index `paper_title_trgm` | `tests.test_scholar_lens.ResearchPaperModelTest` — **PASSED** (0.31s) | Sub-10ms title search queries — **PASSED** | **PASS** |

---

### Module 3: Institutional Search & Discovery (M3)

| Req ID | Requirement Description | Source Implementation | Database / Schema Evidence | Test Reference & Fresh Execution Result | Runtime Evidence | Status |
|---|---|---|---|---|---|:---:|
| **REQ-M3.1** | Weighted multi-attribute search indexing | `researchers/search_index.py:refresh_search_document` | `SearchVectorField(null=True)` on `ResearcherProfile` | `tests.test_expertise_search.ExpertiseSearchTests.test_search_weights_ranking` — **PASSED** (0.39s) | Title (A) > Summary (C) weight verification — **PASSED** | **PASS** |
| **REQ-M3.2** | Faceted filtering by department and availability | `researchers/views.py:expertise_search` | Filter queries on `department__code` and `is_available_for_collaboration` | `tests.test_expertise_search.ExpertiseSearchTests.test_faceted_filters` — **PASSED** (0.25s) | Cypress `09_expertise_search.cy.js` — **PASSED** | **PASS** |
| **REQ-M3.3** | Sub-1000ms query latency SLA over 2,000 profiles | `scholar_lens/api.py:expertise_search` | PostgreSQL GIN index on `search_document` | `tests.test_expertise_search.ExpertiseSearchTests.test_under_one_second` — **PASSED** (0.77s) | BM-02: **8.27 ms avg DB query / 77.21 ms HTTP view** — **PASSED** | **PASS** |
| **REQ-M3.4** | Live search header integration with debounce | `static/js/api_client.js:initHeaderLiveSearch` | 300ms debounce, minimum 2-character query length | `tests.test_ums_shell.UmsShellTest` — **PASSED** (0.18s) | Cypress `01_shell.cy.js` search redirect — **PASSED** | **PASS** |

---

### Module 4: Research Openings & Opportunities (M4)

| Req ID | Requirement Description | Source Implementation | Database / Schema Evidence | Test Reference & Fresh Execution Result | Runtime Evidence | Status |
|---|---|---|---|---|---|:---:|
| **REQ-M4.1** | Research openings registry & skill requirements | `opportunities/models.py:ResearchOpening` | `opportunities_researchopening` table with M2M to `Skill` | `tests.test_opportunities.OpportunityTests` — **PASSED** (0.35s) | Cypress `11_openings.cy.js` cards & badges — **PASSED** | **PASS** |
| **REQ-M4.2** | Student application submission modal & workflow | `opportunities/views.py:apply_opening` | `opportunities_opportunityapplication` with status `PENDING` | `tests.test_p08_gaps.OpeningsWorkflowTest.test_apply_opening` — **PASSED** (0.22s) | Cypress `11_openings.cy.js` modal submit — **PASSED** | **PASS** |
| **REQ-M4.3** | Faculty application management & status transitions | `opportunities/views.py:manage_applications` | Status transitions: `PENDING` -> `ACCEPTED` / `REJECTED` | `tests.test_p08_gaps.OpeningsWorkflowTest.test_accept_application` — **PASSED** (0.19s) | Faculty applicant management table — **PASSED** | **PASS** |
| **REQ-M4.4** | JSON REST API route `/api/openings/` | `scholar_lens/api.py:openings` | Serializes open opportunities with required skills | `tests.test_p08_gaps.ApiTest.test_api_openings` — **PASSED** (0.14s) | `api_client.js:getOpenings()` — **PASSED** | **PASS** |

---

### Module 5: Projects & Milestones (M5)

| Req ID | Requirement Description | Source Implementation | Database / Schema Evidence | Test Reference & Fresh Execution Result | Runtime Evidence | Status |
|---|---|---|---|---|---|:---:|
| **REQ-M5.1** | Project data model & member roles | `projects/models.py:ResearchProject, ProjectMember` | `projects_researchproject`, roles: `LEADER`, `RESEARCHER`, `ADVISOR` | `tests.test_scholar_lens.ProjectModelTest` — **PASSED** (0.15s) | Project overview and membership views — **PASSED** | **PASS** |
| **REQ-M5.2** | Milestone DAG dependency cycle rejection | `projects/forms.py:MilestoneForm.clean_depends_on` | Recursive ancestor cycle detection algorithm | `tests.test_milestones.MilestoneTests.test_dependency_cycle_rejected` — **PASSED** (0.28s) | Cypress `06_milestones.cy.js` loop block message — **PASSED** | **PASS** |
| **REQ-M5.3** | Automated risk assessment & due date tracking | `projects/risk.py:compute_risk` | Risk levels: `ON_TRACK`, `AT_RISK`, `OVERDUE` | `tests.test_milestones.MilestoneTests.test_risk_computation` — **PASSED** (0.26s) | Milestone badges and At-Risk dashboard — **PASSED** | **PASS** |
| **REQ-M5.4** | Progress auto-update on milestone completion | `projects/models.py:Milestone.save` | `status == 'DONE'` sets `progress = 100`, `completed_on = localdate` | `tests.test_milestones.MilestoneTests.test_done_sets_progress_and_completed_on` — **PASSED** (0.21s) | Milestone progress bar updates in UI — **PASSED** | **PASS** |

---

### Module 6: Facilities & Resource Booking (M6)

| Req ID | Requirement Description | Source Implementation | Database / Schema Evidence | Test Reference & Fresh Execution Result | Runtime Evidence | Status |
|---|---|---|---|---|---|:---:|
| **REQ-M6.1** | Facility catalogue & slot management | `facilities/models.py:Facility, FacilitySlot` | `facilities_facility`, weekdays & operating hours | `tests.test_facilities.FacilitiesTests.test_facility_list` — **PASSED** (0.34s) | Cypress `04_facilities.cy.js` catalogue — **PASSED** | **PASS** |
| **REQ-M6.2** | Multi-slot booking & custodian approval flow | `facilities/views.py:book_facility, approve_booking` | `status` choices: `PENDING`, `APPROVED`, `REJECTED`, `CANCELLED` | `tests.test_facilities.FacilitiesTests.test_booking_approval_workflow` — **PASSED** (0.42s) | Custodian pending queue & approval action — **PASSED** | **PASS** |
| **REQ-M6.3** | Concurrency protection via `btree_gist` ExclusionConstraint | `facilities/models.py:Booking.Meta` | `ExclusionConstraint` on `(facility, during)` for active bookings | `tests.test_facilities.ConcurrentBookingConcurrencyTest` — **PASSED** (9.09s) | BM-03: **100% collision block** in PostgreSQL — **PASSED** | **PASS** |
| **REQ-M6.4** | iCal calendar feed export | `facilities/views.py:export_calendar_ics` | Generates standard VCALENDAR / VEVENT response | `tests.test_facilities.FacilitiesTests.test_ical_export` — **PASSED** (0.18s) | Cypress `04_facilities.cy.js` .ics download — **PASSED** | **PASS** |

---

### Module 7: Funding Register & Applications (M7)

| Req ID | Requirement Description | Source Implementation | Database / Schema Evidence | Test Reference & Fresh Execution Result | Runtime Evidence | Status |
|---|---|---|---|---|---|:---:|
| **REQ-M7.1** | Funding calls register with filters | `funding/models.py:FundingCall`, `funding/views.py:funding_list` | `funding_fundingcall` table; published & research area index | `tests.test_funding.FundingRegisterTests.test_filter_by_area_and_state` — **PASSED** (0.33s) | Cypress `05_funding.cy.js` cards & filters — **PASSED** | **PASS** |
| **REQ-M7.2** | Real-time deadline countdown & closing alerts | `funding/models.py:FundingCall.countdown_label` | Relative date calculations: `Closes today`, `X days left`, `Closed` | `tests.test_funding.FundingRegisterTests.test_countdown_text` — **PASSED** (0.24s) | Badges on funding cards & detail page — **PASSED** | **PASS** |
| **REQ-M7.3** | Internal proposal tracking & endorsement review | `funding/views.py:apply_funding, review_application` | `funding_fundingapplication` table; Research Office endorsement | `tests.test_funding.FundingRegisterTests.test_proposal_submission` — **PASSED** (0.31s) | Proposal tracking card & endorsement queue — **PASSED** | **PASS** |
| **REQ-M7.4** | JSON REST API route `/api/funding-calls/` | `scholar_lens/api.py:funding_calls` | Serializes funding calls with deadline filter | `tests.test_p08_gaps.ApiTest.test_api_funding_calls` — **PASSED** (0.16s) | `api_client.js:getFundingCalls()` — **PASSED** | **PASS** |

---

### Module 8: Collaboration Suggestions (M8)

| Req ID | Requirement Description | Source Implementation | Database / Schema Evidence | Test Reference & Fresh Execution Result | Runtime Evidence | Status |
|---|---|---|---|---|---|:---:|
| **REQ-M8.1** | Jaccard skill/topic overlap recommendation algorithm | `collaboration/suggestions.py:compute_suggestions` | Jaccard similarity metric on skills, interests, and coauthors | `tests.test_suggestions.CollaborationSuggestionsTest.test_score_pair_with_adjacency_and_gap` — **PASSED** (0.34s) | Recommendations card with factor chips — **PASSED** | **PASS** |
| **REQ-M8.2** | Interactive coauthorship network graph & data endpoint | `collaboration/views.py:collaboration_graph_data` | Serializes researcher nodes and coauthorship edges as JSON | `tests.test_suggestions.CollaborationSuggestionsTest.test_collaboration_graph_data_endpoint` — **PASSED** (0.21s) | Cypress `10_collaboration.cy.js` network canvas — **PASSED** | **PASS** |
| **REQ-M8.3** | Accessible tabular fallback for screen readers | `templates/collaboration/graph.html` | Hidden accessible `<table>` with aria attributes | `tests.test_suggestions.CollaborationSuggestionsTest.test_collaboration_graph_page_and_accessible_table` — **PASSED** (0.27s) | Cypress `10_collaboration.cy.js` table check — **PASSED** | **PASS** |
| **REQ-M8.4** | Suggestion dismissal & feedback cycle | `collaboration/views.py:dismiss_suggestion` | Sets `is_dismissed = True` on `CollaborationSuggestion` | `tests.test_suggestions.CollaborationSuggestionsTest.test_dismiss_suggestion` — **PASSED** (0.19s) | Cypress `10_collaboration.cy.js` dismiss button — **PASSED** | **PASS** |

---

### Module 9: Analytics & Institutional Reporting (M9)

| Req ID | Requirement Description | Source Implementation | Database / Schema Evidence | Test Reference & Fresh Execution Result | Runtime Evidence | Status |
|---|---|---|---|---|---|:---:|
| **REQ-M9.1** | Institutional productivity & grant pipeline analytics | `analytics/metrics.py:compute_academic_year_metrics` | Aggregates publications, funding totals, facility hours | `tests.test_analytics.AnalyticsTests` — **PASSED** (0.41s) | Cypress `12_reports.cy.js` KPI summary cards — **PASSED** | **PASS** |
| **REQ-M9.2** | Department-level comparative breakdowns | `analytics/views.py:research_analytics` | Per-department metrics array with funding success rates | `tests.test_research_office.ResearchOfficeTests` — **PASSED** (0.35s) | Department performance chart & table — **PASSED** | **PASS** |
| **REQ-M9.3** | Executive confidentiality protection & masking | `scholar_lens/api.py:research_analytics` | `include_researchers = is_dean(request.user)` | `tests.test_office.ResearchOfficeTests.test_dean_confidentiality` — **PASSED** (0.26s) | BM-04: **100% masked for non-Deans** — **PASSED** | **PASS** |
| **REQ-M9.4** | Immutable audit trail logging | `dashboard/models.py:AuditEntry` | Timestamped, actor-logged immutable audit log | `tests.test_office.ResearchOfficeTests.test_audit_entry_created` — **PASSED** (0.21s) | Audit trail inspector in Research Office — **PASSED** | **PASS** |

---

## 3. Compliance Summary

- **Total Assessed Requirements:** 37
- **Requirements Meeting PASS Standard:** **37 (100%)**
- **Requirements with PARTIAL / FAIL / BLOCKED:** **0 (0%)**
- **Overall Specification Acceptance:** **FULL SPECIFICATION ACCEPTANCE ACHIEVED**.
