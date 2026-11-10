# Scholar Lens — Stage 4 Django Test Verification Report
**Document ID:** `DOC-S4-DJT-01`  
**Execution Date:** 2026-11-07  
**Auditor:** Independent Software Auditor & Principal QA Architect  
**Status:** VERIFIED & PASSED (252/252)  

---

## 1. Executive Summary

During Phase 2 of the Stage 4 Independent Final Verification and Production Acceptance Audit, the entire backend Django test suite was independently re-executed against the live PostgreSQL 16 database.

The audit verified that:
- The 252-test figure represents **252 unique, individually discovered and executed unit, integration, security, and concurrency test methods**, and NOT accumulated duplicates from repeated runs.
- Initial forensic execution identified three subtle date/time boundary edge cases in test assertions (caused by OS vs UTC timezone divergence and midnight boundary crossings).
- Following precise, targeted corrections to test assertions (without weakening any test logic or changing production database schemas), the test suite was re-run in its entirety.
- **100% of the 252 tests executed cleanly, passing with Process Exit Code 0.**

---

## 2. Test Execution Environment & Exact Metrics

| Metric / Parameter | Observed Value | Specification Requirement | Verification Status |
|---|---|---|---|
| **Test Runner** | Django `DiscoverRunner` | Django standard runner | **VERIFIED** |
| **Command** | `python manage.py test tests -v 2` | Full test package | **VERIFIED** |
| **Database Backend** | PostgreSQL 16.3 (`test_scholar_lens`) on port 5433 | Dedicated PostgreSQL runner | **VERIFIED** |
| **Discovered Tests** | **252** | $\ge 250$ tests | **VERIFIED** |
| **Executed Tests** | **252** | Exactly 252 | **VERIFIED** |
| **Passed Tests** | **252** | Exactly 252 | **VERIFIED** |
| **Failed Tests** | **0** | 0 failures | **VERIFIED** |
| **Error Count** | **0** | 0 errors | **VERIFIED** |
| **Skipped Tests** | **0** | 0 skipped | **VERIFIED** |
| **Suite Run Time** | **384.79 seconds** (~6.4 minutes) | Reproducible | **VERIFIED** |
| **Total Duration** | **391.52 seconds** (including setup/teardown) | Monitored | **VERIFIED** |
| **Final Exit Code** | **0** | `0` (Success) | **VERIFIED** |

---

## 3. Discovered Test Distribution by Test Suite Module

The 252 tests span all 15 core architectural and P08 functional modules:

| Test Module File | Focus / Capabilities Verified | Unique Test Count | Result |
|---|---|:---:|:---:|
| `tests.test_advanced_hardening` | Canonical 7-dimension scoring, versioning, provenance, explainable recommendations | 16 | **16/16 PASSED** |
| `tests.test_duplicate_detection` | Trigram similarity, soft merge, candidate review, dedup benchmark accuracy | 18 | **18/18 PASSED** |
| `tests.test_external_integrations` | Crossref / Scopus ingestion, arXiv / PubMed harvesting, fallback resilience | 14 | **14/14 PASSED** |
| `tests.test_facilities` | Multi-slot bookings, PostgreSQL `btree_gist` ExclusionConstraint concurrency | 16 | **16/16 PASSED** |
| `tests.test_funding` | Institutional proposal tracking, deadline countdowns, closing alerts, staff review | 15 | **15/15 PASSED** |
| `tests.test_google_auth` | OAuth2/OIDC nonce/state, id_token verification, google_sub linking, account merge | 14 | **14/14 PASSED** |
| `tests.test_institutional_search` | Dean analytics, field-weighted search rank, sub-100ms latency, confidentiality | 16 | **16/16 PASSED** |
| `tests.test_milestones` | Milestone DAG dependency cycle prevention, risk computation, progress tracking | 17 | **17/17 PASSED** |
| `tests.test_p08_gaps` | 9 canonical REST API routes, CSV/BibTeX/RIS/iCal export endpoints | 18 | **18/18 PASSED** |
| `tests.test_research_office` | Research Office portal, dean role gate, audit trail immutability, project risk | 14 | **14/14 PASSED** |
| `tests.test_suggestions` | Jaccard skill/topic graph, coauthorship adjacency, gap bonus, suggestion alerts | 14 | **14/14 PASSED** |
| `tests.test_ums_shell` | LPU design tokens, navigation links, bell notifications, role-based visibility | 12 | **12/12 PASSED** |
| `tests.test_scholar_lens` | Auth registration/login, user profiles, paper CRUD, search forms, URL routing | 68 | **68/68 PASSED** |
| **TOTAL** | **Comprehensive Full System Coverage** | **252** | **252/252 PASSED** |

---

## 4. Forensic Analysis of Discovered Test Edge Cases

During the initial audit run, three time-boundary edge cases were isolated and remediated in accordance with Rule 10 ("Only make a correction if a concrete defect is established and the correction is necessary; document and test that correction separately"):

### 4.1 Timezone Divergence in Milestone Completion (`test_milestones.py`)
- **Root Cause:** In `projects/models.py:121`, `Milestone.save()` sets `self.completed_on = timezone.localdate()`, which resolves using Django's configured `TIME_ZONE = 'UTC'`. The test assertion on line 106 used Python's un-timezone-aware `datetime.date.today()`, which resolves against the host OS timezone (India Standard Time, UTC+05:30). When tests executed after midnight local time (e.g. 02:30 IST) while UTC was still the previous day (21:00 UTC), `date.today()` evaluated to tomorrow relative to UTC, yielding an assertion mismatch (`2026-11-06 != 2026-11-07`).
- **Remediation:** Updated `test_milestones.py` line 106 to assert `self.assertEqual(m.completed_on, timezone.localdate())`, perfectly aligning the test assertion with Django's timezone runtime.
- **Verification:** Verified in isolation (`1/1 PASSED`) and in the full suite.

### 4.2 Midnight Boundary in Funding Countdown (`test_funding.py`)
- **Root Cause:** In `tests/test_funding.py:54`, `self.call_today` was initialized with `deadline = now + timedelta(hours=3)`. When the test ran at 21:19 UTC, adding 3 hours pushed the deadline to 00:19 UTC the following day, causing `days_left` to evaluate to `1` ("1 day left") instead of `0` ("Closes today").
- **Remediation:** Updated line 54 to `deadline = timezone.localtime().replace(hour=23, minute=59, second=0)`, guaranteeing that the deadline remains on the current calendar day regardless of the hour of test execution.
- **Verification:** Verified in isolation (`1/1 PASSED`) and in the full suite.

### 4.3 Deterministic Tie-Breaker in Paper Ordering (`test_scholar_lens.py`)
- **Root Cause:** In PostgreSQL within a rapid test transaction, `self.paper` (created in `setUp`) and `paper2` (created in `test_paper_ordering`) could receive identical timestamp values under certain clock resolutions. Because `ordering = ['-created_at']` had equal keys, the database returned rows in indeterminate heap order.
- **Remediation:** Updated `test_paper_ordering` to explicitly ensure `paper2`'s `created_at` timestamp is strictly newer (`self.paper.created_at + timedelta(seconds=1)`), guaranteeing deterministic descending sort evaluation.
- **Verification:** Verified in isolation (`1/1 PASSED`) and in the full suite.

---

## 5. Phase 2 Verification Conclusion

The Django test suite was independently executed with all 252 tests discovered and executed against PostgreSQL 16.

**Phase 2 Django Test Verification Verdict: PASSED — 252/252 TESTS PASSING (100% SUCCESS, EXIT CODE 0).**
