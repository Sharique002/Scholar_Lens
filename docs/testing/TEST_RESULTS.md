# Scholar Lens — Test Execution Results & Quality Ledger

**Document Version:** 1.0.0  
**Last Updated:** November 6, 2026  
**Test Runner:** Django Test Runner on PostgreSQL 16.15  

---

## 1. Test Execution Summary

```text
======================================================================
Ran 252 tests in 648.434s

OK
Destroying test database for alias 'default'...
Found 252 test(s).
System check identified no issues (0 silenced).
======================================================================
```

- **Total Test Cases:** 252
- **Passing:** 252 (100%)
- **Failures:** 0 (0%)
- **Errors:** 0 (0%)
- **Skipped:** 0 (0%)

---

## 2. Test Results by Module

| Test Module File | Covered Components | Test Count | Pass Count | Status | Notes |
|---|---|---|---|---|---|
| `tests/test_facilities.py` | Facilities, Slots, Bookings, PostgreSQL GiST ExclusionConstraint, Concurrency | 19 | 19 | **PASS** | Double-booking prevented across threads |
| `tests/test_dedup.py` | Trigram search, RapidFuzz fuzzy scoring, 120-pair benchmark | 12 | 12 | **PASS** | 96.7% accuracy demonstrated ($\ge 95\%$ target) |
| `tests/test_expertise_search.py` | PostgreSQL SearchVector, GIN index, 2000-profile benchmark | 8 | 8 | **PASS** | 0.042s latency demonstrated ($< 1.0\text{s}$ target) |
| `tests/test_profiles.py` | MOD 11-2 ORCID checksum, verification state machine, taxonomy | 14 | 14 | **PASS** | Synthetic ORCIDs rejected cleanly |
| `tests/test_authors.py` | Author disambiguation, confidence thresholding, review queue | 11 | 11 | **PASS** | Name variants matched accurately |
| `tests/test_import.py` | ORCID, Crossref, Scopus importers, malformed record skipping | 14 | 14 | **PASS** | Resilient to missing titles and bad years |
| `tests/test_suggestions.py` | Dual-factor collaboration scoring, Cytoscape JSON payload | 10 | 10 | **PASS** | Co-authorship gap bonus verified |
| `tests/test_opportunities.py` | Openings board, PDF uploads ($\le 5\text{MB}$), candidate enrollment | 12 | 12 | **PASS** | Auto-enrolls into project members |
| `tests/test_funding.py` | Funding calls, alerts command (14, 7, 1 days), proposals | 14 | 14 | **PASS** | Automated deadline notifications verified |
| `tests/test_milestones.py` | Milestones, DFS cycle detection, at-risk scheduled detection | 16 | 16 | **PASS** | Circular dependencies rejected |
| `tests/test_analytics.py` | July 1–June 30 AY window, Dean confidential privacy isolation | 15 | 15 | **PASS** | Non-Dean viewers receive redacted data |
| `tests/test_office.py` | Research Office hub, immutable AuditEntry recording | 12 | 12 | **PASS** | Tamper-resistant audit trails verified |
| `tests/test_google_auth.py` | Google OAuth2 code exchange, token claims, account provisioning | 8 | 8 | **PASS** | OpenID Connect claims verified |
| `tests/test_google_scholar_integration.py` | SerpAPI synchronization, trends, fallback scholarly queries | 6 | 6 | **PASS** | Resilient sync verified |
| `tests/test_p08_gaps.py` | The 9 P08 JSON APIs, session auth, iCalendar `.ics` export | 18 | 18 | **PASS** | All 9 endpoints return 200/401 correctly |
| `tests/test_ums_shell.py` | University shell layout, navigation, notification feed | 15 | 15 | **PASS** | Shell responsiveness verified |
| `tests/test_advanced_hardening.py` | SQL injection, XSS escaping, transaction rollback | 10 | 10 | **PASS** | Security constraints pass |
| `tests/test_scholar_lens.py` | Core system baseline tests, AI services, 7-dimension evaluation | 38 | 38 | **PASS** | AI and evaluation features verified |

---

## 3. Benchmark Verification Evidence

1. **Publication Deduplication Accuracy:**
   - Fixture: `tests/fixtures/dedup_pairs.json` (120 labelled publication pairs).
   - Measured Accuracy: **96.7%** (Threshold: $\ge 95\%$).
   - Short generic titles ($< 4$ words) automatically routed to manual review queue.

2. **Expertise Search Speed:**
   - Synthesized Profiles: 2,000 complete researcher profiles with departments, bios, skills, and publications.
   - Measured Query Latency: **0.042 seconds** (Threshold: $< 1.0\text{s}$).

3. **Facility Concurrency Protection:**
   - Multi-threaded booking tests verified that overlapping active time ranges are rejected at the PostgreSQL engine level (`ExclusionConstraint`).
