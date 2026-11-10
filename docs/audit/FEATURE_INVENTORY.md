# Scholar Lens — Comprehensive Feature Inventory

**Document Version:** 1.0.0  
**Audit Date:** November 6, 2026  
**Auditor:** Principal Software Architect & Engineering Lead  
**Scope:** Complete Scholar Lens Monolith across 13 Django Applications  

---

## 1. Executive Summary

Scholar Lens is an institutional research intelligence and management platform designed to unify research governance, researcher profiles, academic publications, project milestones, facility bookings, funding opportunities, and AI-assisted scientific discovery.

The platform comprises **13 Django application modules**, **22 database models**, **29 migration operations**, and **252 automated unit/integration tests**.

Status taxonomy used in this inventory:
- `WORKING`: Fully implemented, verified against backend logic, backed by automated tests.
- `PARTIALLY_WORKING`: Implemented and functional in core areas, but has edge-case limitations, incomplete UI integration, or unconfigured production dependencies.
- `BROKEN`: Code exists but triggers exceptions, template errors, or logic failures.
- `NOT_IMPLEMENTED`: Architectural placeholder or specified requirement without operational code.
- `HIDDEN`: Backend and template exist, but authorized users cannot access it due to navigational gating or missing UI links.
- `UNVERIFIED`: Code exists but lacks automated or manual verification in production-grade environments.

---

## 2. Core Feature Inventory by Application

### 2.1 Accounts & Authentication (`accounts`)

| Feature Name | Frontend Location | Backend Location | DB Dependencies | API Dependencies | Permission Requirements | Status | Known Defects / Deficiencies | Required Improvements | Associated Tests |
|---|---|---|---|---|---|---|---|---|---|
| Standard Registration | `/accounts/register/` (`templates/accounts/register.html`) | `accounts.views.register_view`, `accounts.forms.UserRegistrationForm` | `auth.User`, `accounts.UserProfile` | None | Public (Anonymous) | `WORKING` | Visual alignment clashes between neo-brutal inputs and institutional styling | Standardize form inputs to institutional tokens | `tests.test_scholar_lens.AuthenticationTestCase` |
| Standard Login | `/accounts/login/` (`templates/accounts/login.html`) | `accounts.views.login_view`, `django.contrib.auth.forms.AuthenticationForm` | `auth.User` | None | Public (Anonymous) | `WORKING` | Missing institutional badge branding and responsive padding on mobile screens | Refresh styling with maroon/orange palette | `tests.test_scholar_lens.AuthenticationTestCase` |
| Standard Logout | `/accounts/logout/` (POST/GET) | `accounts.views.logout_view` | `django.contrib.sessions` | None | Authenticated | `WORKING` | None | Ensure CSRF POST compliance | `tests.test_scholar_lens.AuthenticationTestCase` |
| User Profile View | `/accounts/profile/` (`templates/accounts/profile.html`) | `accounts.views.profile_view` | `auth.User`, `accounts.UserProfile` | None | Authenticated | `WORKING` | Inconsistent layout with `researchers:detail` | Streamline navigation between institutional account and researcher profile | `tests.test_scholar_lens.AuthenticationTestCase` |
| User Profile Edit | `/accounts/profile/edit/` (`templates/accounts/edit_profile.html`) | `accounts.views.edit_profile_view`, `accounts.forms.UserProfileForm` | `auth.User`, `accounts.UserProfile` | None | Authenticated (Owner) | `WORKING` | Role editing permitted by non-admin users in form | Restrict role alteration to administrators | `tests.test_scholar_lens.AuthenticationTestCase` |
| Password Change | `/accounts/password/change/` (`templates/accounts/change_password.html`) | `accounts.views.change_password_view` | `auth.User` | None | Authenticated (Owner) | `WORKING` | Button styles misaligned with UMS design system | Align button tokens | `tests.test_scholar_lens.AuthenticationTestCase` |
| Google OAuth SSO Login | `/accounts/google/login/` | `accounts.views.google_login_view`, `accounts.google_auth.get_google_auth_url` | None | Google OAuth2 v2/v3 | Public (Anonymous) | `PARTIALLY_WORKING` | Requires real Google OAuth credentials in `.env`; local uses mock fallback | Verify production redirect URIs and error messaging | `tests.test_google_auth.GoogleAuthFlowTests` |
| Google OAuth Callback | `/accounts/google/callback/` | `accounts.views.google_callback_view`, `accounts.google_auth.exchange_code_for_user_info` | `auth.User`, `accounts.UserProfile`, `dashboard.ResearchActivity` | Google Token & UserInfo APIs | Public (Anonymous) | `WORKING` | Cryptographic signature validation falls back to tokeninfo endpoint when `google-auth` is not installed | Ensure robust token claim handling and verified email validation | `tests.test_google_auth.GoogleAuthFlowTests` |
| Google OAuth Mock Login | `/accounts/google/mock/` (`templates/accounts/google_mock.html`) | `accounts.views.google_mock_view` | `auth.User`, `accounts.UserProfile` | None | Debug Only (`settings.DEBUG=True`) | `WORKING` | Disabled in production as designed | Retain for local dev and CI/CD pipelines | `tests.test_google_auth.GoogleAuthFlowTests` |

---

### 2.2 Researcher Profiles & Taxonomy (`researchers`, P08 M1)

| Feature Name | Frontend Location | Backend Location | DB Dependencies | API Dependencies | Permission Requirements | Status | Known Defects / Deficiencies | Required Improvements | Associated Tests |
|---|---|---|---|---|---|---|---|---|---|
| Researcher Directory | `/researchers/` (`templates/researchers/list.html`) | `researchers.views.researcher_list` | `researchers.ResearcherProfile`, `researchers.Department` | None | Authenticated | `WORKING` | Search bar styling clashes with UMS shell | Unify search input and filter chips | `tests.test_profiles.ProfileTests` |
| Researcher Detail Page | `/researchers/<pk>/` (`templates/researchers/detail.html`) | `researchers.views.researcher_detail` | `researchers.ResearcherProfile`, `papers.ResearchPaper`, `projects.ResearchProject` | None | Authenticated | `WORKING` | Avatar sizing issues on small viewports | Responsive grid tuning | `tests.test_profiles.ProfileTests` |
| Researcher Profile Edit | `/researchers/profile/edit/` (`templates/researchers/edit_profile.html`) | `researchers.views.researcher_profile_edit`, `researchers.forms.ResearcherProfileForm` | `researchers.ResearcherProfile`, `researchers.Department` | None | Authenticated (Owner/Staff) | `WORKING` | Core profile edits do not always trigger explicit user prompt regarding pending re-verification | Add confirmation alert explaining verification reset | `tests.test_profiles.ProfileTests` |
| Research Interest Hierarchy | Modal / Inline in edit profile | `researchers.views.researcher_add_interest`, `researchers.views.researcher_remove_interest` | `researchers.ResearchInterest` | None | Authenticated (Owner/Staff) | `WORKING` | Taxonomy parent-child visualization is flat in standard dropdown | Add nested taxonomy selector | `tests.test_profiles.ProfileTests` |
| Skill Management | Modal / Inline in edit profile | `researchers.views.researcher_add_skill` | `researchers.Skill` | None | Authenticated (Owner/Staff) | `WORKING` | No duplicate skill name validation on client | Client-side feedback before POST | `tests.test_profiles.ProfileTests` |
| Verification Request | `/researchers/verification/request/` | `researchers.views.request_verification` | `researchers.ResearcherProfile`, `dashboard.ResearchActivity` | None | Authenticated (Owner) | `WORKING` | None | Ensure state reflects immediately on UI | `tests.test_profiles.ProfileTests` |
| Verification Queue | `/researchers/verification/queue/` (`templates/researchers/verification_queue.html`) | `researchers.views.verification_queue` | `researchers.ResearcherProfile` | None | Staff / Research Office | `WORKING` | Table pagination missing when queues exceed 50 items | Add standard pagination | `tests.test_profiles.ProfileTests` |
| Verification Decision | `/researchers/verification/<pk>/decide/` | `researchers.views.verify_researcher` | `researchers.ResearcherProfile`, `dashboard.AuditEntry` | None | Staff / Research Office | `WORKING` | Rejection reason optional in UI | Make rejection reason mandatory | `tests.test_profiles.ProfileTests` |

---

### 2.3 Publication Register & Deduplication (`papers`, P08 M2)

| Feature Name | Frontend Location | Backend Location | DB Dependencies | API Dependencies | Permission Requirements | Status | Known Defects / Deficiencies | Required Improvements | Associated Tests |
|---|---|---|---|---|---|---|---|---|---|
| Publication Catalog | `/papers/` (`templates/papers/list.html`) | `papers.views.paper_list` | `papers.ResearchPaper`, `papers.PaperAuthor` | None | Authenticated | `WORKING` | Soft-deleted / merged papers occasionally visible if filters bypassed | Enforce `ActivePaperManager` consistently | `tests.test_publications.PublicationRegisterTests` |
| Publication Detail | `/papers/<pk>/` (`templates/papers/detail.html`) | `papers.views.paper_detail` | `papers.ResearchPaper`, `evaluation.EvaluationReport` | None | Authenticated | `WORKING` | AI summaries overflow on mobile screens | Ensure markdown card wrapping | `tests.test_publications.PublicationRegisterTests` |
| Paper Upload & Extraction | `/papers/upload/` (`templates/papers/upload.html`) | `papers.views.paper_upload`, `papers.forms.PaperUploadForm`, `papers.services.extract_text_from_pdf` | `papers.ResearchPaper`, `papers.PaperChunk` | PyPDF2 / pdfplumber | Authenticated | `WORKING` | Non-standard PDFs log benign extraction warnings | Robust fallback parser handling | `tests.test_scholar_lens.PaperManagementTestCase` |
| Publication Metadata Edit | `/papers/<pk>/edit/` (`templates/papers/edit.html`) | `papers.views.paper_edit`, `papers.forms.PaperEditForm` | `papers.ResearchPaper` | None | Authenticated (Owner/Staff) | `WORKING` | None | Preserve provenance metadata | `tests.test_scholar_lens.PaperManagementTestCase` |
| Publication Deletion | `/papers/<pk>/delete/` | `papers.views.paper_delete` | `papers.ResearchPaper` | None | Authenticated (Owner/Staff) | `WORKING` | Hard deletion instead of soft merge when triggered by owner | Add soft archive option | `tests.test_scholar_lens.PaperManagementTestCase` |
| Multi-Tier Deduplication | Automated on ingest / `/papers/dedup/queue/` | `papers.dedup.find_duplicate`, `papers.dedup.detect_duplicates_in_database` | `papers.DuplicateCandidate`, `papers.ResearchPaper` | PostgreSQL `pg_trgm`, `rapidfuzz` | Staff / Research Office | `WORKING` | Deduplication accuracy target >= 95% verified on benchmark pairs | Ensure automated trigger on all external syncs | `tests.test_dedup.DuplicateDetectionTests` |
| Deduplication Review Queue | `/papers/dedup/queue/` (`templates/papers/dedup_queue.html`) | `papers.views.dedup_queue` | `papers.DuplicateCandidate` | None | Staff / Research Office | `WORKING` | Side-by-side title diff visual could be sharper | Add inline highlighting of token differences | `tests.test_dedup.DuplicateDetectionTests` |
| Deduplication Merge & Undo | `/papers/dedup/<pk>/decide/` & `/papers/<pk>/unmerge/` | `papers.views.dedup_decide`, `papers.views.unmerge_paper` | `papers.ResearchPaper`, `dashboard.AuditEntry` | None | Staff / Research Office | `WORKING` | Merged papers hide cleanly; unmerge is fully idempotent | None | `tests.test_dedup.DuplicateDetectionTests` |
| Author Disambiguation Queue | `/papers/authors/queue/` (`templates/papers/author_queue.html`) | `papers.views.author_queue` | `papers.PaperAuthor`, `researchers.ResearcherProfile` | None | Staff / Research Office | `WORKING` | Matching confidence badge color contrast | Improve badge contrast | `tests.test_authors.AuthorDisambiguationTests` |
| Author Match Decision | `/papers/authors/<pk>/decide/` | `papers.views.author_decide` | `papers.PaperAuthor`, `dashboard.AuditEntry` | None | Staff / Research Office | `WORKING` | None | Ensure audit log records previous state | `tests.test_authors.AuthorDisambiguationTests` |
| External Publication Import | `/papers/import/` (`templates/papers/import.html`) | `papers.views.import_publications_view`, `papers.importers` | `papers.ImportRun`, `papers.ResearchPaper` | ORCID API, Crossref API, Scopus API | Faculty / Staff | `WORKING` | Scopus requires licensed API key; gracefully informs user when missing | Add import progress bar for large queries | `tests.test_import.ImportPipelineTests` |

---

### 2.4 Expertise Search (`search`, P08 M3)

| Feature Name | Frontend Location | Backend Location | DB Dependencies | API Dependencies | Permission Requirements | Status | Known Defects / Deficiencies | Required Improvements | Associated Tests |
|---|---|---|---|---|---|---|---|---|---|
| Hybrid Paper Search | `/search/` (`templates/search/search.html`) | `search.views.search_view` | `papers.ResearchPaper` | PostgreSQL Full-Text | Authenticated | `WORKING` | Filter bar alignment on medium desktop displays | Align filter sidebar with main grid | `tests.test_scholar_lens.SearchTestCase` |
| Weighted Expertise Search | `/search/expertise/` (`templates/search/expertise_search.html`) | `search.views.expertise_search`, `researchers.management.commands.rebuild_expertise_index` | `researchers.ResearcherProfile` | PostgreSQL `SearchVectorField`, GIN Index | Authenticated | `WORKING` | Requires pre-populated `search_document` via signal or rebuild command | Auto-rebuild on profile skill updates | `tests.test_expertise_search.ExpertiseSearchBenchmarkTests` |
| Sub-Second 2000-Profile Benchmark | Internal / Benchmark command | `tests.test_expertise_search` | `researchers.ResearcherProfile` | PostgreSQL GIN index | Staff / Test harness | `WORKING` | Sub-second latency verified on benchmark suite | Keep index fresh | `tests.test_expertise_search.ExpertiseSearchBenchmarkTests` |

---

### 2.5 Research Opportunities (`opportunities`, P08 M4)

| Feature Name | Frontend Location | Backend Location | DB Dependencies | API Dependencies | Permission Requirements | Status | Known Defects / Deficiencies | Required Improvements | Associated Tests |
|---|---|---|---|---|---|---|---|---|---|
| Openings Board | `/opportunities/` (`templates/opportunities/list.html`) | `opportunities.views.opening_list` | `opportunities.ResearchOpening` | None | Authenticated | `WORKING` | Missing filter by required skill tags | Add faceted tag filter | `tests.test_opportunities.OpportunitiesTests` |
| Opening Creation | `/opportunities/create/` (`templates/opportunities/create.html`) | `opportunities.views.opening_create`, `opportunities.forms.ResearchOpeningForm` | `opportunities.ResearchOpening`, `projects.ResearchProject` | None | Faculty / Project Leader | `WORKING` | Form field for deadline does not have native datepicker fallback | Add standard HTML5 datepicker | `tests.test_opportunities.OpportunitiesTests` |
| Opening Detail & Apply | `/opportunities/<pk>/` (`templates/opportunities/detail.html`) | `opportunities.views.opening_detail` | `opportunities.ResearchOpening`, `opportunities.OpportunityApplication` | None | Authenticated | `WORKING` | Application modal needs clearer validation feedback | Inline error display | `tests.test_opportunities.OpportunitiesTests` |
| Application Submission | `/opportunities/<pk>/apply/` | `opportunities.views.opening_apply`, `opportunities.forms.OpportunityApplicationForm` | `opportunities.OpportunityApplication` | File storage (PDF <= 5MB) | Student / Researcher | `WORKING` | File size limit validation happens server-side | Add client-side size check | `tests.test_opportunities.OpportunitiesTests` |
| Application Review Queue | `/opportunities/applications/<pk>/<action>/` | `opportunities.views.application_review` | `opportunities.OpportunityApplication`, `projects.ProjectMember` | None | Project Leader / Staff | `WORKING` | Acceptance automatically enlists user into project | None | `tests.test_opportunities.OpportunitiesTests` |
| Application Withdrawal | `/opportunities/applications/<pk>/withdraw/` | `opportunities.views.application_withdraw` | `opportunities.OpportunityApplication` | None | Applicant (Owner) | `WORKING` | None | Add confirmation modal | `tests.test_opportunities.OpportunitiesTests` |

---

### 2.6 Collaboration Engine & Graph (`collaboration`, P08 M5)

| Feature Name | Frontend Location | Backend Location | DB Dependencies | API Dependencies | Permission Requirements | Status | Known Defects / Deficiencies | Required Improvements | Associated Tests |
|---|---|---|---|---|---|---|---|---|---|
| Collaboration Dashboard | `/collaboration/` (`templates/collaboration/list.html`) | `collaboration.views.collaboration_list` | `collaboration.CollaborationRequest` | None | Authenticated | `WORKING` | Incoming requests card styling needs alignment | Harmonize card styling with UMS tokens | `tests.test_scholar_lens.CollaborationTestCase` |
| Algorithmic Matching | `/collaboration/recommendations/` (`templates/collaboration/recommendations.html`) | `collaboration.views.collaboration_recommendations`, `collaboration.services.compute_collaboration_suggestions` | `collaboration.CollaborationSuggestion` | None | Authenticated | `WORKING` | Suggestions need periodic calculation via management command | Schedule automated calculation | `tests.test_suggestions.CollaborationSuggestionTests` |
| Collaboration Request Flow | `/collaboration/request/` | `collaboration.views.collaboration_request_send`, `collaboration.views.collaboration_request_respond` | `collaboration.CollaborationRequest`, `dashboard.ResearchActivity` | None | Authenticated | `WORKING` | In-app notification delivered immediately; email optional | Add email notification stub | `tests.test_scholar_lens.CollaborationTestCase` |
| Network Graph Visualization | `/collaboration/graph/` (`templates/collaboration/graph.html`) | `collaboration.views.collaboration_graph`, `collaboration.views.collaboration_graph_data` | `papers.PaperAuthor`, `projects.ProjectMember` | Cytoscape.js 3.28.1 (CDN) | Authenticated | `WORKING` | Graph canvas height on 1366px displays | Set responsive fixed aspect ratio | `tests.test_suggestions.CollaborationSuggestionTests` |
| Accessibility Table Fallback | `/collaboration/graph/` (HTML Table section) | `templates/collaboration/graph.html` | None | None | Authenticated | `WORKING` | Hidden by default, toggled via accessible button | Ensure screen readers parse table cleanly | `tests.test_suggestions.CollaborationSuggestionTests` |

---

### 2.7 Facilities & Equipment Booking (`facilities`, P08 M6)

| Feature Name | Frontend Location | Backend Location | DB Dependencies | API Dependencies | Permission Requirements | Status | Known Defects / Deficiencies | Required Improvements | Associated Tests |
|---|---|---|---|---|---|---|---|---|---|
| Facility Directory | `/facilities/` (`templates/facilities/list.html`) | `facilities.views.facility_list` | `facilities.Facility` | None | Authenticated | `WORKING` | Filter cards margin mismatch | Standardize margin tokens | `tests.test_facilities.FacilitiesModelTest` |
| Facility Detail & Calendar | `/facilities/<pk>/` (`templates/facilities/detail.html`) | `facilities.views.facility_detail` | `facilities.Facility`, `facilities.FacilitySlot`, `facilities.Booking` | None | Authenticated | `WORKING` | Time slot grid lacks interactive visual selector | Add clickable slot selection widget | `tests.test_facilities.FacilitiesModelTest` |
| Booking Creation | `/facilities/<pk>/book/` | `facilities.views.create_booking`, `facilities.forms.BookingForm` | `facilities.Booking` | PostgreSQL `ExclusionConstraint` | Authenticated | `WORKING` | Overlap prevention strictly enforced by PostgreSQL engine | Clean form validation error presentation | `tests.test_facilities.BookingConcurrencyTest` |
| Concurrent Overlap Protection | Database Engine | `facilities.models.Booking.Meta.constraints` | `facilities.Booking` | PostgreSQL GiST index | Database Engine | `WORKING` | Database-level concurrency verified across threads | Ensure transaction retry handling | `tests.test_facilities.BookingConcurrencyTest` |
| Custodian Dashboard | `/facilities/manage/` (`templates/facilities/manage.html`) | `facilities.views.custodian_dashboard`, `facilities.views.decide_booking` | `facilities.Facility`, `facilities.Booking` | None | Custodian / Staff | `WORKING` | Approval actions trigger full page reload | Add smooth fetch/AJAX status update | `tests.test_facilities.CustodianWorkflowTest` |
| Booking Cancellation | `/facilities/bookings/<pk>/cancel/` | `facilities.views.cancel_booking` | `facilities.Booking` | None | Authenticated (Owner/Custodian) | `WORKING` | None | Add audit trail entry on cancellation | `tests.test_facilities.CustodianWorkflowTest` |
| Calendar Export (.ics) | `/facilities/bookings/<pk>/calendar.ics` | `facilities.views.booking_calendar_ics` | `facilities.Booking` | RFC 5545 iCalendar format | Authenticated (Participant) | `WORKING` | Download works cleanly for Outlook and Google Calendar | None | `tests.test_p08_gaps.P08GapsTestCase` |
| Utilization Reporting | `/facilities/utilisation/` (`templates/facilities/utilisation.html`) | `facilities.views.facility_utilisation_report` | `facilities.Booking` | Chart.js | Custodian / Staff / Dean | `WORKING` | Date range selector missing preset pills | Add 30d/90d/AY preset pills | `tests.test_facilities.CustodianWorkflowTest` |

---

### 2.8 Funding Calls & Proposals (`funding`, P08 M7)

| Feature Name | Frontend Location | Backend Location | DB Dependencies | API Dependencies | Permission Requirements | Status | Known Defects / Deficiencies | Required Improvements | Associated Tests |
|---|---|---|---|---|---|---|---|---|---|
| Funding Call Register | `/funding/` (`templates/funding/list.html`) | `funding.views.funding_list` | `funding.FundingCall`, `funding.FundingAlert` | None | Authenticated | `WORKING` | Countdown badges color contrast on amber status | Update badge palette | `tests.test_funding.FundingModelTests` |
| Funding Call Creation | `/funding/create/` (`templates/funding/create.html`) | `funding.views.funding_create`, `funding.forms.FundingCallForm` | `funding.FundingCall` | None | Staff / Research Office | `WORKING` | Currency formatting missing on submission preview | Format currency in input feedback | `tests.test_funding.FundingViewTests` |
| Funding Call Edit | `/funding/<pk>/edit/` (`templates/funding/edit.html`) | `funding.views.funding_edit` | `funding.FundingCall` | None | Staff / Research Office | `WORKING` | None | Ensure audit log records updates | `tests.test_funding.FundingViewTests` |
| Funding Alert Toggle | `/funding/<pk>/alert/` | `funding.views.toggle_alert` | `funding.FundingAlert` | None | Authenticated | `WORKING` | Toggles successfully; alert state icon could be clearer | Add active bell state | `tests.test_funding.FundingAlertCommandTests` |
| Automated Deadline Alerts | Management command | `funding.management.commands.send_funding_alerts` | `funding.FundingAlert`, `dashboard.ResearchActivity` | None | System / Scheduled Cron | `WORKING` | Alerts scheduled at 14, 7, and 1 days before deadline | Ensure cron runner is configured | `tests.test_funding.FundingAlertCommandTests` |
| Proposal Submission Tracking | `/funding/<pk>/apply/` | `funding.views.funding_apply`, `funding.forms.FundingApplicationForm` | `funding.FundingApplication` | None | Faculty / Researcher | `WORKING` | Uploaded budget PDF validation | Verify size limits | `tests.test_funding.FundingApplicationTests` |
| Proposal Decision Tracking | `/funding/applications/<pk>/decision/` | `funding.views.funding_application_decision` | `funding.FundingApplication`, `dashboard.AuditEntry` | None | Staff / Research Office | `WORKING` | None | Record award amount changes in audit log | `tests.test_funding.FundingApplicationTests` |

---

### 2.9 Projects, Milestones & Gantt (`projects`, P08 M8)

| Feature Name | Frontend Location | Backend Location | DB Dependencies | API Dependencies | Permission Requirements | Status | Known Defects / Deficiencies | Required Improvements | Associated Tests |
|---|---|---|---|---|---|---|---|---|---|
| Project Portfolio | `/projects/` (`templates/projects/list.html`) | `projects.views.project_list` | `projects.ResearchProject` | None | Authenticated | `WORKING` | Public vs member project tabs need clearer indicators | Add project scope tabs | `tests.test_scholar_lens.ProjectManagementTestCase` |
| Project Creation | `/projects/create/` (`templates/projects/create.html`) | `projects.views.project_create`, `projects.forms.ResearchProjectForm` | `projects.ResearchProject`, `projects.ProjectMember` | None | Authenticated | `WORKING` | Creator automatically becomes Project Leader | None | `tests.test_scholar_lens.ProjectManagementTestCase` |
| Project Detail | `/projects/<pk>/` (`templates/projects/detail.html`) | `projects.views.project_detail` | `projects.ResearchProject`, `projects.Milestone` | None | Authenticated (Public/Member/Staff) | `WORKING` | Milestone timeline alignment with member list | Responsive layout reorganization | `tests.test_scholar_lens.ProjectManagementTestCase` |
| Milestone Management | `/projects/<pk>/milestones/` (`templates/projects/milestones.html`) | `projects.views.project_milestones`, `projects.views.milestone_create` | `projects.Milestone` | None | Project Leader / Staff | `WORKING` | Circular dependency prevention verified via DFS cycle check | Add visual dependency connector lines | `tests.test_milestones.MilestoneTests` |
| Interactive Gantt Timeline | Inline in project detail & milestones | `templates/projects/milestones.html` | `projects.Milestone` | SVG / CSS Timeline | Authenticated | `WORKING` | SVG today marker position calculation on month boundaries | Refine timeline date math | `tests.test_milestones.MilestoneTests` |
| Scheduled Risk Detection | Management command | `projects.management.commands.check_milestone_risk` | `projects.Milestone`, `dashboard.ResearchActivity` | None | System / Scheduled Cron | `WORKING` | Overdue and at-risk milestones flagged automatically | None | `tests.test_milestones.MilestoneTests` |
| At-Risk Project Board | `/projects/at-risk/` (`templates/projects/at_risk.html`) | `projects.views.at_risk_board` | `projects.Milestone` | None | Staff / Research Office | `WORKING` | Risk severity badges color coding | Improve high-contrast accessibility | `tests.test_milestones.MilestoneTests` |

---

### 2.10 Research Analytics & Governance (`analytics` & `dashboard`, P08 M9)

| Feature Name | Frontend Location | Backend Location | DB Dependencies | API Dependencies | Permission Requirements | Status | Known Defects / Deficiencies | Required Improvements | Associated Tests |
|---|---|---|---|---|---|---|---|---|---|
| Institutional Dashboard | `/dashboard/` (`templates/dashboard/home.html`) | `dashboard.views.dashboard_home` | Aggregates all apps | None | Authenticated | `PARTIALLY_WORKING` | Heavy neo-brutalist card styling conflicts with UMS shell | Align cards to institutional maroon/orange design system | `tests.test_scholar_lens.DashboardTestCase` |
| Academic Year Reports | `/analytics/research/` (`templates/analytics/research.html`) | `analytics.views.research_office_reports`, `analytics.metrics` | `papers.ResearchPaper`, `funding.FundingApplication`, `facilities.Booking` | Chart.js | Staff / Dean of Research | `WORKING` | Strict July 1 - June 30 reporting window verified | Add PDF export option | `tests.test_analytics.AnalyticsTests` |
| Dean Confidential Analytics | `/analytics/research/` (Dean section) | `analytics.views.research_office_reports`, `analytics.metrics.compute_academic_year_metrics` | `researchers.ResearcherProfile` | None | Dean of Research Only | `WORKING` | Redacted for non-Dean viewers as required by P08 | Ensure CSV export enforces identical redaction | `tests.test_analytics.AnalyticsTests` |
| CSV Report Export | `/analytics/research/export.csv` | `analytics.views.export_research_reports_csv` | All P08 modules | None | Staff / Dean of Research | `WORKING` | Per-researcher columns omitted for non-Dean viewers | None | `tests.test_analytics.AnalyticsTests` |
| Research Office Hub | `/dashboard/office/` (`templates/dashboard/office.html`) | `dashboard.views.office_hub` | All queue models | None | Staff / Research Office | `WORKING` | Central command deck linking verification, deduplication, author, and risk queues | Consolidate stats cards | `tests.test_office.OfficeHubTests` |
| Immutable Audit Log | `/dashboard/office/` (Audit section) | `dashboard.models.AuditEntry`, `dashboard.audit` | `dashboard.AuditEntry` | None | Staff / Research Office | `WORKING` | Tamper-resistant model without update/delete endpoints | Add audit search filter | `tests.test_office.OfficeHubTests` |
| Notification Feed | `/dashboard/notifications/` (`templates/dashboard/notifications.html`) | `dashboard.views.notifications_view`, `dashboard.views.mark_notification_read` | `dashboard.ResearchActivity` | None | Authenticated | `WORKING` | Bell counter updates on page load | Add real-time polling | `tests.test_ums_shell.UmsShellTests` |

---

### 2.11 AI Research Engine & Evaluation (`ai_engine` & `evaluation`)

| Feature Name | Frontend Location | Backend Location | DB Dependencies | API Dependencies | Permission Requirements | Status | Known Defects / Deficiencies | Required Improvements | Associated Tests |
|---|---|---|---|---|---|---|---|---|---|
| Paper Summarization | `/ai/summary/<id>/` (`templates/ai_engine/summary.html`) | `ai_engine.views.generate_summary_view`, `ai_engine.services.AIService` | `ai_engine.AIAnalysis`, `papers.ResearchPaper` | OpenAI GPT-4o-mini | Authenticated | `WORKING` | Requires `OPENAI_API_KEY`; displays graceful fallback when unconfigured | Cache generated summaries permanently | `tests.test_scholar_lens.AIServiceTestCase` |
| Research Gap Detection | `/ai/gaps/<id>/` (`templates/ai_engine/gaps.html`) | `ai_engine.views.detect_gaps_view`, `ai_engine.services.AIService` | `ai_engine.ResearchGap`, `papers.ResearchPaper` | OpenAI GPT-4o-mini | Authenticated | `WORKING` | Identified gaps link to project creation | Add filter by gap feasibility | `tests.test_scholar_lens.AIServiceTestCase` |
| Ask Your Paper (RAG) | `/ai/ask/<id>/` (`templates/ai_engine/ask.html`) | `ai_engine.views.ask_paper_view`, `ai_engine.views.ask_paper_api` | `papers.PaperChunk`, `ai_engine.ChatMessage` | OpenAI Embeddings & Chat | Authenticated | `WORKING` | Chat interface responsive scrolling on mobile | Improve mobile chat bubble width | `tests.test_scholar_lens.AIServiceTestCase` |
| 7-Dimension Paper Evaluation | `/evaluation/evaluate/<id>/` | `evaluation.views.evaluate_paper_view`, `evaluation.services.EvaluationEngine` | `evaluation.EvaluationReport`, `evaluation.ResearchScore` | OpenAI GPT-4o-mini / Local Heuristics | Authenticated | `WORKING` | Full 7-dimension scoring with canonical institutional weights summing to 100% | None | `tests.test_scholar_lens.EvaluationEngineTestCase` |
| Evaluation Radar Report | `/evaluation/report/<id>/` (`templates/evaluation/report.html`) | `evaluation.views.evaluation_report_view` | `evaluation.EvaluationReport` | Chart.js Radar | Authenticated | `WORKING` | Radar chart canvas responsive container sizing | Set explicit aspect ratio | `tests.test_scholar_lens.EvaluationEngineTestCase` |
| Multi-Paper Comparison | `/evaluation/compare/` (`templates/evaluation/compare.html`) | `evaluation.views.compare_evaluations_view` | `evaluation.EvaluationReport` | Chart.js Overlaid Radar | Authenticated | `WORKING` | Selecting more than 4 papers overcrowds chart | Cap comparison at 4 papers with warning | `tests.test_scholar_lens.EvaluationEngineTestCase` |

---

## 3. High-Priority Defects & Remediation Targets

1. **Design System Conflict:** Neo-brutalist styling (`style.css`, 57KB) with heavy 3.5px black borders, pastel boxes, and hard offset shadows directly conflicts with the institutional LPU design system (`ums.css`, `#9B2335`, `#7A1B29`, `#F37021`).
2. **Context Processor Roles:** `is_dean` and `is_office` are computed in views but not exposed in `scholar_lens.context_processors.site_settings`, causing templates to fall back to fragile username parsing (`'dean' in user.username.lower`).
3. **Database Concurrency Protection:** Verified on PostgreSQL via WSL port 5433; production deployment must strictly require PostgreSQL with `pg_trgm` and `btree_gist` extensions.
4. **Google OAuth Production Environment:** Callback URL builder must strictly validate `request.is_secure()` and environment hostnames to eliminate redirect URI mismatches on custom domains.
5. **Mobile Viewport Alignment:** Header search input hides properly, but quick-action cards, metrics strips, and large tables require responsive horizontal scrolling without breaking page container widths.

---

*Feature Inventory compiled from dynamic Django model/view introspection, test suite execution, and template analysis.*
