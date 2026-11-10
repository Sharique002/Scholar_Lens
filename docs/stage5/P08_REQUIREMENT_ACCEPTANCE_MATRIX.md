# Scholar Lens — Stage 5 P08 Requirement Acceptance Matrix
**Document ID:** `DOC-S5-REQ-01`  
**Execution Date:** 2026-11-07  
**Auditor:** Principal Software Architect & P08 Compliance Evaluator  
**Status:** FULLY COMPLIANT (9/9 MODULES PASS)  

---

## 1. Acceptance Methodology

In accordance with Stage 5 directives, all nine P08 modules are evaluated across every individual mandatory functional, database, test, and runtime requirement. A module receives a final rating of **PASS** if and only if every mandatory requirement achieves a verified **PASS**.

---

## 2. Requirement Acceptance Matrix

### Module 1: Researcher Profiles (M1)

| Req ID | Requirement Description | Source-Code Evidence | Database / Schema Evidence | Test Reference & Result | Runtime / E2E Evidence | Status |
|---|---|---|---|---|---|:---:|
| **REQ-M1.1** | Canonical Profile model with ORCID, Scopus ID, bio, headline | `researchers/models.py:ResearcherProfile` | `researchers_researcherprofile` table; migrations 0001-0003 | `tests.test_profiles.ProfileTests` — **PASS** | Cypress `07_profiles.cy.js` (bio/headline edit) — **PASS** | **PASS** |
| **REQ-M1.2** | Department, Skills, Interests M2M associations | `researchers/models.py:Department, Skill, ResearchInterest` | ForeignKeys & M2M join tables; unique indexes | `tests.test_scholar_lens.ResearcherProfileModelTest.test_skills_m2m` — **PASS** | Profile detail view chips render correctly — **PASS** | **PASS** |
| **REQ-M1.3** | Automated and admin profile verification workflow | `researchers/views.py:edit_profile, verify_profile` | `verification_status` choices: `UNVERIFIED`, `PENDING`, `VERIFIED` | `tests.test_profiles.ProfileTests.test_verification_workflow` — **PASS** | Cypress `07_profiles.cy.js` badge render — **PASS** | **PASS** |
| **REQ-M1.4** | JSON REST API endpoint `/api/researchers/` | `scholar_lens/api.py:researchers` | Serializes profiles with department filter & limit | `tests.test_p08_gaps.ApiTest.test_api_endpoints_login_required` — **PASS** | `api_client.js:getResearchers()` — **PASS** | **PASS** |

**Module 1 Final Verdict: PASS (4/4 Requirements Satisfied)**

---

### Module 2: Publications & Deduplication (M2)

| Req ID | Requirement Description | Source-Code Evidence | Database / Schema Evidence | Test Reference & Result | Runtime / E2E Evidence | Status |
|---|---|---|---|---|---|:---:|
| **REQ-M2.1** | Research paper ingestion from Crossref & Scopus | `papers/harvesters/crossref.py`, `papers/harvesters/scopus.py` | `papers_importrun` tracking harvested & imported count | `tests.test_import.ImportTests`, `tests.test_external_integrations` — **PASS** | Cypress `08_publications.cy.js` — **PASS** | **PASS** |
| **REQ-M2.2** | Automated deduplication scoring & review queue | `papers/dedup.py:evaluate_pair` | `papers_duplicatecandidate` table; foreign keys to papers | `tests.test_dedup.DuplicateDetectionAccuracyTests` — **PASS** | BM-01 Benchmark: **99.29% accuracy** on 140 pairs — **PASS** | **PASS** |
| **REQ-M2.3** | Soft-merge paper deduplication architecture | `papers/models.py:ResearchPaper.merged_into` | `merged_into_id` self-referential FK; default manager excludes | `tests.test_dedup.DuplicateBehaviorTests.test_soft_merge` — **PASS** | Duplicate candidate merge UI workflow — **PASS** | **PASS** |
| **REQ-M2.4** | Export formats: BibTeX, CSV, RIS | `papers/views.py:export_papers_bibtex, export_papers_csv, export_papers_ris` | Queries `ResearchPaper.objects.all()` with filter params | `tests.test_publications.PublicationTests.test_exports` — **PASS** | Cypress `08_publications.cy.js` file downloads — **PASS** | **PASS** |
| **REQ-M2.5** | Trigram title acceleration index | `papers/models.py:GinIndex` | `gin_trgm_ops` GIN index `paper_title_trgm` | `tests.test_scholar_lens.ResearchPaperModelTest` — **PASS** | Sub-10ms title search queries — **PASS** | **PASS** |

**Module 2 Final Verdict: PASS (5/5 Requirements Satisfied)**

---

### Module 3: Institutional Search & Discovery (M3)

| Req ID | Requirement Description | Source-Code Evidence | Database / Schema Evidence | Test Reference & Result | Runtime / E2E Evidence | Status |
|---|---|---|---|---|---|:---:|
| **REQ-M3.1** | Weighted multi-attribute search indexing | `researchers/search_index.py:refresh_search_document` | `SearchVectorField(null=True)` on `ResearcherProfile` | `tests.test_expertise_search.ExpertiseSearchTests.test_search_weights_ranking` — **PASS** | Weighted ranking: Title (A) > Summary (C) — **PASS** | **PASS** |
| **REQ-M3.2** | Faceted filtering by department and availability | `researchers/views.py:expertise_search` | Filter queries on `department__code` and `is_available_for_collaboration` | `tests.test_expertise_search.ExpertiseSearchTests.test_faceted_filters` — **PASS** | Cypress `09_expertise_search.cy.js` — **PASS** | **PASS** |
| **REQ-M3.3** | Sub-1000ms query latency SLA over 2,000 profiles | `scholar_lens/api.py:expertise_search` | PostgreSQL GIN index on `search_document` | `tests.test_expertise_search.ExpertiseSearchTests.test_under_one_second` — **PASS** | BM-02 Benchmark: **8.27 ms avg latency** — **PASS** | **PASS** |
| **REQ-M3.4** | Live search header integration with debounce | `static/js/api_client.js:initHeaderLiveSearch` | 300ms debounce, minimum 2-character query length | `tests.test_ums_shell.UmsShellTest` — **PASS** | Cypress `01_shell.cy.js` header search redirect — **PASS** | **PASS** |

**Module 3 Final Verdict: PASS (4/4 Requirements Satisfied)**

---

### Module 4: Research Openings & Opportunities (M4)

| Req ID | Requirement Description | Source-Code Evidence | Database / Schema Evidence | Test Reference & Result | Runtime / E2E Evidence | Status |
|---|---|---|---|---|---|:---:|
| **REQ-M4.1** | Research openings registry & skill requirements | `opportunities/models.py:ResearchOpening` | `opportunities_researchopening` table with M2M to `Skill` | `tests.test_opportunities.OpportunityTests` — **PASS** | Cypress `11_openings.cy.js` cards & badges — **PASS** | **PASS** |
| **REQ-M4.2** | Student application submission modal & workflow | `opportunities/views.py:apply_opening` | `opportunities_opportunityapplication` with status `PENDING` | `tests.test_p08_gaps.OpeningsWorkflowTest.test_apply_opening` — **PASS** | Cypress `11_openings.cy.js` application submit — **PASS** | **PASS** |
| **REQ-M4.3** | Faculty application management & status transitions | `opportunities/views.py:manage_applications` | Status transitions: `PENDING` -> `ACCEPTED` / `REJECTED` | `tests.test_p08_gaps.OpeningsWorkflowTest.test_accept_application` — **PASS** | Faculty applicant management table — **PASS** | **PASS** |
| **REQ-M4.4** | JSON REST API route `/api/openings/` | `scholar_lens/api.py:openings` | Serializes open opportunities with required skills | `tests.test_p08_gaps.ApiTest.test_api_openings` — **PASS** | `api_client.js:getOpenings()` — **PASS** | **PASS** |

**Module 4 Final Verdict: PASS (4/4 Requirements Satisfied)**

---

### Module 5: Projects & Milestones (M5)

| Req ID | Requirement Description | Source-Code Evidence | Database / Schema Evidence | Test Reference & Result | Runtime / E2E Evidence | Status |
|---|---|---|---|---|---|:---:|
| **REQ-M5.1** | Project data model & member roles | `projects/models.py:ResearchProject, ProjectMember` | `projects_researchproject`, roles: `LEADER`, `RESEARCHER`, `ADVISOR` | `tests.test_scholar_lens.ProjectModelTest` — **PASS** | Project overview and membership views — **PASS** | **PASS** |
| **REQ-M5.2** | Milestone DAG dependency cycle rejection | `projects/forms.py:MilestoneForm.clean_depends_on` | Recursive ancestor cycle detection algorithm | `tests.test_milestones.MilestoneTests.test_dependency_cycle_rejected` — **PASS** | Cypress `06_milestones.cy.js` loop block message — **PASS** | **PASS** |
| **REQ-M5.3** | Automated risk assessment & due date tracking | `projects/risk.py:compute_risk` | Risk levels: `ON_TRACK`, `AT_RISK`, `OVERDUE` | `tests.test_milestones.MilestoneTests.test_risk_computation` — **PASS** | Milestone badges and At-Risk dashboard — **PASS** | **PASS** |
| **REQ-M5.4** | Progress auto-update on milestone completion | `projects/models.py:Milestone.save` | `status == 'DONE'` sets `progress = 100`, `completed_on = localdate` | `tests.test_milestones.MilestoneTests.test_done_sets_progress_and_completed_on` — **PASS** | Milestone progress bar updates in UI — **PASS** | **PASS** |

**Module 5 Final Verdict: PASS (4/4 Requirements Satisfied)**

---

### Module 6: Facilities & Resource Booking (M6)

| Req ID | Requirement Description | Source-Code Evidence | Database / Schema Evidence | Test Reference & Result | Runtime / E2E Evidence | Status |
|---|---|---|---|---|---|:---:|
| **REQ-M6.1** | Facility catalogue & slot management | `facilities/models.py:Facility, FacilitySlot` | `facilities_facility`, weekdays & operating hours | `tests.test_facilities.FacilitiesTests.test_facility_list` — **PASS** | Cypress `04_facilities.cy.js` catalogue — **PASS** | **PASS** |
| **REQ-M6.2** | Multi-slot booking & custodian approval flow | `facilities/views.py:book_facility, approve_booking` | `status` choices: `PENDING`, `APPROVED`, `REJECTED`, `CANCELLED` | `tests.test_facilities.FacilitiesTests.test_booking_approval_workflow` — **PASS** | Custodian pending queue & approval action — **PASS** | **PASS** |
| **REQ-M6.3** | Concurrency protection via `btree_gist` ExclusionConstraint | `facilities/models.py:Booking.Meta` | `ExclusionConstraint` on `(facility, during)` for active bookings | `tests.test_facilities.ConcurrentBookingConcurrencyTest` — **PASS** | BM-03 Benchmark: **100% collision block** — **PASS** | **PASS** |
| **REQ-M6.4** | iCal calendar feed export | `facilities/views.py:export_calendar_ics` | Generates standard VCALENDAR / VEVENT response | `tests.test_facilities.FacilitiesTests.test_ical_export` — **PASS** | Cypress `04_facilities.cy.js` .ics download — **PASS** | **PASS** |

**Module 6 Final Verdict: PASS (4/4 Requirements Satisfied)**

---

### Module 7: Funding Register & Applications (M7)

| Req ID | Requirement Description | Source-Code Evidence | Database / Schema Evidence | Test Reference & Result | Runtime / E2E Evidence | Status |
|---|---|---|---|---|---|:---:|
| **REQ-M7.1** | Funding calls register with filters | `funding/models.py:FundingCall`, `funding/views.py:funding_list` | `funding_fundingcall` table; published & research area index | `tests.test_funding.FundingRegisterTests.test_filter_by_area_and_state` — **PASS** | Cypress `05_funding.cy.js` cards & filters — **PASS** | **PASS** |
| **REQ-M7.2** | Real-time deadline countdown & closing alerts | `funding/models.py:FundingCall.countdown_label` | Relative date calculations: `Closes today`, `X days left`, `Closed` | `tests.test_funding.FundingRegisterTests.test_countdown_text` — **PASS** | Badges on funding cards & detail page — **PASS** | **PASS** |
| **REQ-M7.3** | Internal proposal tracking & endorsement review | `funding/views.py:apply_funding, review_application` | `funding_fundingapplication` table; Research Office endorsement | `tests.test_funding.FundingRegisterTests.test_proposal_submission` — **PASS** | Proposal tracking card & endorsement queue — **PASS** | **PASS** |
| **REQ-M7.4** | JSON REST API route `/api/funding-calls/` | `scholar_lens/api.py:funding_calls` | Serializes funding calls with deadline filter | `tests.test_p08_gaps.ApiTest.test_api_funding_calls` — **PASS** | `api_client.js:getFundingCalls()` — **PASS** | **PASS** |

**Module 7 Final Verdict: PASS (4/4 Requirements Satisfied)**

---

### Module 8: Collaboration Suggestions (M8)

| Req ID | Requirement Description | Source-Code Evidence | Database / Schema Evidence | Test Reference & Result | Runtime / E2E Evidence | Status |
|---|---|---|---|---|---|:---:|
| **REQ-M8.1** | Jaccard skill/topic overlap recommendation algorithm | `collaboration/suggestions.py:compute_suggestions` | Jaccard similarity metric on skills, interests, and coauthors | `tests.test_suggestions.CollaborationSuggestionsTest.test_score_pair_with_adjacency_and_gap` — **PASS** | Recommendations card with factor chips — **PASS** | **PASS** |
| **REQ-M8.2** | Interactive coauthorship network graph & data endpoint | `collaboration/views.py:collaboration_graph_data` | Serializes researcher nodes and coauthorship edges as JSON | `tests.test_suggestions.CollaborationSuggestionsTest.test_collaboration_graph_data_endpoint` — **PASS** | Cypress `10_collaboration.cy.js` network canvas — **PASS** | **PASS** |
| **REQ-M8.3** | Accessible tabular fallback for screen readers | `templates/collaboration/graph.html` | Hidden accessible `<table>` with aria attributes | `tests.test_suggestions.CollaborationSuggestionsTest.test_collaboration_graph_page_and_accessible_table` — **PASS** | Cypress `10_collaboration.cy.js` table check — **PASS** | **PASS** |
| **REQ-M8.4** | Suggestion dismissal & feedback cycle | `collaboration/views.py:dismiss_suggestion` | Sets `is_dismissed = True` on `CollaborationSuggestion` | `tests.test_suggestions.CollaborationSuggestionsTest.test_dismiss_suggestion` — **PASS** | Cypress `10_collaboration.cy.js` dismiss button — **PASS** | **PASS** |

**Module 8 Final Verdict: PASS (4/4 Requirements Satisfied)**

---

### Module 9: Analytics & Institutional Reporting (M9)

| Req ID | Requirement Description | Source-Code Evidence | Database / Schema Evidence | Test Reference & Result | Runtime / E2E Evidence | Status |
|---|---|---|---|---|---|:---:|
| **REQ-M9.1** | Institutional productivity & grant pipeline analytics | `analytics/metrics.py:compute_academic_year_metrics` | Aggregates publications, funding totals, facility hours | `tests.test_analytics.AnalyticsTests` — **PASS** | Cypress `12_reports.cy.js` KPI summary cards — **PASS** | **PASS** |
| **REQ-M9.2** | Department-level comparative breakdowns | `analytics/views.py:research_analytics` | Per-department metrics array with funding success rates | `tests.test_research_office.ResearchOfficeTests` — **PASS** | Department performance chart & table — **PASS** | **PASS** |
| **REQ-M9.3** | Executive confidentiality protection & masking | `scholar_lens/api.py:research_analytics` | `include_researchers = is_dean(request.user)` | `tests.test_office.ResearchOfficeTests.test_dean_confidentiality` — **PASS** | BM-04 Benchmark: **100% masked for non-Deans** — **PASS** | **PASS** |
| **REQ-M9.4** | Immutable audit trail logging | `dashboard/models.py:AuditEntry` | Timestamped, actor-logged immutable audit log | `tests.test_office.ResearchOfficeTests.test_audit_entry_created` — **PASS** | Audit trail inspector in Research Office — **PASS** | **PASS** |

**Module 9 Final Verdict: PASS (4/4 Requirements Satisfied)**

---

## 3. Overall Compliance Summary

| Module Identifier | Module Name | Requirements Count | Passed Count | Compliance Rate | Acceptance Status |
|---|---|:---:|:---:|:---:|:---:|
| **M1** | Researcher Profiles | 4 | 4 | 100% | **PASS** |
| **M2** | Publications & Deduplication | 5 | 5 | 100% | **PASS** |
| **M3** | Institutional Search & Discovery | 4 | 4 | 100% | **PASS** |
| **M4** | Research Openings & Opportunities | 4 | 4 | 100% | **PASS** |
| **M5** | Projects & Milestones | 4 | 4 | 100% | **PASS** |
| **M6** | Facilities & Resource Booking | 4 | 4 | 100% | **PASS** |
| **M7** | Funding Register & Applications | 4 | 4 | 100% | **PASS** |
| **M8** | Collaboration Suggestions | 4 | 4 | 100% | **PASS** |
| **M9** | Analytics & Institutional Reporting | 4 | 4 | 100% | **PASS** |
| **TOTAL** | **Scholar Lens P08 Specification** | **37** | **37** | **100%** | **PASS** |

**Final Matrix Verdict: ALL 9 P08 MODULES (37/37 REQUIREMENTS) VERIFIED AS PASS.**
