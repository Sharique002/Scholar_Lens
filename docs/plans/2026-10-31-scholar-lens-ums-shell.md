# Scholar Lens — Simple UMS Shell + P08 M8/M6/M7 Implementation Plan (rev 3)

For agentic workers: REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox ( - [ ] ) syntax for tracking.

Goal: Give Scholar Lens a simple maroon/white LPU-UMS-style shell (header + short collapsible sidebar + dashboard quick actions) and add three P08 modules:
- M8 Facility & Asset Management: a catalogue, open hours, booking with approval, double-booking made impossible, and utilisation.
- M6 Funding Call Register: calls, eligibility, deadline countdown, and alerts at configured intervals.
- M7 Project & Milestone Management: milestones, dependencies, a timeline view, and a scheduled at-risk check with configurable thresholds.

Architecture: Part A is templates + CSS + ~15 lines added to `main.js`; no Python changes outside one new test file. Part B is one new Django app `facilities` (models, forms, function-based views, templates), following the existing apps' style. Part C is a new `funding` app. Part D extends the existing `projects` app with a `Milestone` model. Scheduled work (funding alerts, at-risk check) is plain Django management commands run once a day by cron, Render Cron or Windows Task Scheduler. The project has no Celery, and the plan doesn't add it. Double-booking is blocked by a PostgreSQL `ExclusionConstraint` instead of application code. PostgreSQL becomes the required database.

Tech Stack: Django 4.2, PostgreSQL 15 (`docker-compose.yml` db service), `django.contrib.postgres` (`DateTimeRangeField`, `ExclusionConstraint`, `BtreeGistExtension`), `psycopg2` (already in requirements), plain CSS, existing `main.js`.

Spec: the pasted "Scholar Lens — UMS-inspired frontend update" note; the user's asks ("use simple UI so the user can easily use every function and understand it", simpler sidebar, dashboard quick actions, a softer maroon, an orange accent, a collapsible sidebar); `Details.pdf` P08 §5 M8, §6 (Facility Custodian role), §7 Track P (ExclusionConstraint), §8 (booking calendar with conflict prevention, booking conflict prevention under concurrency), §11 (booking approved/rejected notification), §15 (concurrent booking test), and §22 ("Facility double-booking impossible under concurrent requests – proven by test"). For M6/M7, the plan also follows §5, §8 (milestone or Gantt view; at-risk computation as a scheduled job), §11 (funding deadline countdown; milestone due and overdue), and §22 ("Project milestones flagged at-risk automatically with configurable thresholds" and "Funding deadline alerts fire at configured intervals").

Findings from checking the zip
1. The zip has the original project. `static/css/ums.css` doesn't exist, and `base.html` is still the old pink navbar with the fake "PUBLIC RATINGS" footer.
2. The zip includes `venv/`, `staticfiles/`, `__pycache__/`, `db.sqlite3` and `debug.log`. Exclude them.
3. `tests/test_google_scholar_integration.py:365-367` checks for the marquee on `dashboard:home`. Keep the marquee markup.
4. `main.js` already binds `#mobileMenuBtn`, which toggles `.active` on `#navLinks`, plus `.nav-dropdown .dropdown-toggle` and `.alert-dismissible .close-alert`. Reuse these.
5. `style.css` hard-codes 46 offset shadows and 23 thick black borders without using variables. These need explicit overrides.
6. The request context processor is on, and search reads GET `q`.
7. List pages already have their own Upload/Create buttons (`papers/list.html:115`, `projects/list.html:115`, `researchers/list.html:115` → recommendations). Removing those links from the sidebar loses nothing.
8. The notifications page lists `ResearchActivity` rows (`dashboard/views.py:102`), so booking decisions can show up there with no new notification system.
9. `docker-compose.yml` already defines `postgres:15-alpine`, and `settings.py:166` already supports `USE_POSTGRES=1` / `DATABASE_URL`.
10. Making Postgres required breaks two things that use SQLite today: the plain `python manage.py test` run, and the Vercel config (`vercel.json`, `/tmp/db.sqlite3`). After Part B, both need `DATABASE_URL` / `USE_POSTGRES`. The facilities migration cannot run on SQLite.

Global Constraints
- Keep every existing named route working, plus the blocks `title`, `extra_css`, `content` and `extra_js`, the messages markup, the marquee markup, and the `main.js` / `charts.js` / `Chart.js` tags.
- Colours: maroon `#9B2335` (header bar, active nav, links), dark maroon `#7A1B29` (hover), maroon tint `#FBEFF1` (active background), orange `#F37021` (primary buttons only), button text on orange `#1F2328` (white on `#F37021` is only about 2.9:1 and fails AA), white `#FFFFFF`, page background `#F5F5F7`, text `#1F2328`, muted text `#5B6270`, borders `#E2E4E8`.
- Simple UI:
  - The sidebar has 8 flat items, no groups: Dashboard, Papers, Projects, Researchers, Collaboration, Facilities, Funding, Search. Milestones live inside each project, with no sidebar item of their own.
  - Account things (Profile, Researcher Profile, Settings, Change Password, Admin Panel for staff, Logout) live only in the header account menu.
  - Notifications are the header bell.
  - Tap targets are at least 44px, body text at least 15px, and the app shell uses no script font.
- Mobile: at 900px and narrower, the sidebar is off-canvas and the ☰ button opens it. At 375px there's no horizontal scroll.
- Desktop collapse: the collapse button shrinks the sidebar to 64px showing icons only. Each link keeps `title` + `aria-label`. The state is saved in `localStorage['ums-sidebar']`, with every access wrapped in try/catch.
- Cache versions: `style.css?v=1.7`, `ums.css?v=1.0`, `main.js?v=1.1`.
- Booking times: stored as timezone-aware [start, end) ranges (`DateTimeRangeField`, default bounds `[)`), so back-to-back bookings (10–11, then 11–12) are allowed.
- New settings (in `settings.py`, overridable by environment variables using the file's existing `get_*_env` helpers):
  - `FUNDING_ALERT_DAYS = [30, 14, 7, 1]`
  - `MILESTONE_AT_RISK_DAYS = 7`
  - `MILESTONE_AT_RISK_PROGRESS = 50`
- Curation: funding calls are curated by staff (`is_staff` = Research Office). There are no new roles.
- Booking status values: `PENDING`, `APPROVED`, `REJECTED`, `CANCELLED`, `COMPLETED`, `NO_SHOW`. Only `PENDING` and `APPROVED` block a time slot.

Review Focus
1. Two users book the same slot at the same moment: exactly one booking is saved, and the other gets a friendly "That time was just taken" message, not a 500 error. Test: `test_concurrent_booking_only_one_wins` (Task 6).
2. A booking that partly overlaps an existing one (10:00–11:00 vs 10:30–11:30) is rejected, while back-to-back bookings are allowed. Tests: `test_partial_overlap_rejected` and `test_back_to_back_allowed` (Task 4).
3. A rejected or cancelled booking frees its slot. Test: `test_rejected_booking_frees_slot` (Task 4).
4. A non-custodian tries to approve a booking: gets 403. Test: `test_only_custodian_or_staff_can_decide` (Task 7).
5. Bookings outside open hours, in the past, or with end ≤ start are form errors, not database errors. Test: `test_booking_form_validation` (Task 6).
6. The daily alert job runs twice in one day, or misses a day: no duplicate funding alerts. A missed day still sends the alert for the most recent threshold passed. Tests: `test_alerts_idempotent` and `test_missed_day_catches_up` (Task 10).
7. A milestone made to depend on itself or on a later milestone that depends back on it gives a form error, not an infinite loop in the risk check. Test: `test_dependency_cycle_rejected` (Task 11).

Part A — Simple shell

Task 0: Baseline
- [x] Copy the project into the target repo without venv/ staticfiles/ __pycache__/ *.pyc db.sqlite3 debug.log media/* (keep media/.gitkeep ), and add these to .gitignore .
- [x] python -m venv .venv , then .venv\Scripts\pip install -r requirements.txt .
- [x] docker compose up -d db , then set USE_POSTGRES=1 , then python manage.py migrate , then python manage.py test . Record the pass count. Any failures here already existed before this work.

Task 1: Shell in base.html
Files: Modify `templates/base.html`. Test: `tests/test_ums_shell.py` (new).
Interfaces:
- Produces these hooks: `body.ums-body`, `.ums-header`, `.ums-brand`, `.ums-header-search`, `.ums-bell`, `#mobileMenuBtn.mobile-menu-btn > .hamburger`, `#sidebarCollapse`, `.ums-layout`, `aside.ums-sidebar#navLinks`, `a.ums-nav-link` (+ `.is-active`) containing `.ums-nav-icon` and `.ums-nav-label`, `.ums-main` (+ `.ums-main--full` for guests), `.ums-breadcrumb`, `.ums-footer`.
- Produces the template block `{% block breadcrumb %}`.
- [ ] Step 1: Write failing tests (`tests/test_ums_shell.py`).
- [x] Step 2: Run the tests and confirm they fail.
- [ ] Step 3: Rewrite `base.html`.
- [ ] Step 4: Add the collapse handler to `static/js/main.js`.
- [x] Step 5: Run the tests and confirm they pass. Run full suite.
- [ ] Step 6: Commit. `feat(ui): simple UMS header + 7-item sidebar shell`

Task 2: Theme in ums.css
Files: Create `static/css/ums.css`.
- [ ] Step 1: Token overrides on `:root`.
- [x] Step 2: Primary buttons.
- [x] Step 3: Remove brutalist shadows and borders.
- [x] Step 4: Shell layout.
- [x] Step 5: Mobile and motion.
- [x] Step 6: Accessibility.
- [ ] Step 7: Commit. `feat(ui): maroon/white UMS theme with orange actions`

Task 3: Dashboard quick actions
Files: Modify `templates/dashboard/home.html`. Test: add to `tests/test_ums_shell.py`.
- [x] Step 1: Write a failing test.
- [x] Step 2: Confirm the test fails.
- [x] Step 3: Add the quick actions at top of `{% block content %}`.
- [x] Step 4: Style quick actions in `ums.css`.
- [x] Step 5: Confirm test passes, then commit with `feat(ui): dashboard quick actions`.

Part B — M8 Facility & Asset Management

Task 4: facilities app, models and migration
Files: Create `facilities/` (`__init__.py`, `apps.py`, `models.py`, `admin.py`, `urls.py`, `views.py`, `forms.py`, `migrations/0001_initial.py`).
- [x] Step 1: Write failing tests (`tests/test_facilities.py`).
- [x] Step 2: Confirm tests fail.
- [x] Step 3: Implement models, migrations with `BtreeGistExtension()`, register admin.
- [x] Step 4: Wire up UI (Facilities link in `base.html`, "Book a Facility" card in `home.html`).
- [x] Step 5: Confirm tests pass on Postgres and full suite maintains baseline.
- [x] Step 6: Commit. `feat(facilities): models with DB-level double-booking prevention`

Task 5: Catalogue and weekly calendar (read-only pages)
Files: `facilities/views.py`, `facilities/urls.py`, `templates/facilities/list.html`, `templates/facilities/detail.html`.
- [x] Step 1: Write failing tests.
- [x] Step 2: Implement `facility_list` and `facility_detail`.
- [x] Step 3: Confirm tests pass, then commit with `feat(facilities): catalogue and weekly availability view`.

Task 6: Booking form and concurrency proof
Files: `facilities/forms.py`, `facilities/views.py`, `templates/facilities/book.html`, `templates/facilities/my_bookings.html`.
- [x] Step 1: Write failing tests (`test_booking_form_validation`, `test_book_creates_pending_and_redirects`, `test_book_conflict_shows_friendly_error`, `test_concurrent_booking_only_one_wins`).
- [x] Step 2: Implement `create_booking()`, `book` view, `my_bookings` view, cancel action.
- [x] Step 3: Confirm tests pass, then commit with `feat(facilities): booking with conflict-safe create and concurrency test`.

Task 7: Custodian approval, usage log, utilisation
Files: `facilities/views.py`, `templates/facilities/manage.html`, `templates/facilities/utilisation.html`.
- [x] Step 1: Write failing tests.
- [x] Step 2: Implement `manage`, `log_use`, `utilisation`, and header bell indicator.
- [x] Step 3: Confirm tests pass, then commit with `feat(facilities): custodian approvals, usage log, utilisation report`.

Task 8: Seed data, docs, browser check
- [x] Extend `seed_demo_data` with 4 facilities across CSE and Biotech.
- [x] Add `docs/facilities.md`.
- [x] Browser check at 1366px and 375px.
- [x] Commit `docs+seed: facilities baseline`.

Part C — M6 Funding Call Register

Task 9: funding app — register, countdown, watch
Files: Create `funding/` app, views, models, forms, templates.
- [ ] Step 1: Write failing tests (`tests/test_funding.py`).
- [x] Step 2: Implement models, views, countdown logic.
- [x] Step 3: Confirm tests pass, then commit with `feat(funding): funding call register with countdown and watch`.

Task 10: Deadline alerts job
Files: Create `funding/alerts.py` and `send_funding_alerts` management command.
- [ ] Step 1: Write failing tests.
- [x] Step 2: Implement `send_due_alerts()` and management command.
- [x] Step 3: Confirm tests pass, then commit with `feat(funding): deadline alerts at configured intervals`.

Part D — M7 Project milestones and at-risk detection

Task 11: Milestone model, CRUD and dependency rules
Files: Modify `projects/`, add `Milestone` model and form with cycle check.
- [ ] Step 1: Write failing tests (`tests/test_milestones.py`).
- [ ] Step 2: Implement model, clean() cycle check, views, and migrations.
- [ ] Step 3: Confirm tests pass, then commit with `feat(projects): milestones with dependencies`.

Task 12: Timeline (Gantt-style) view
Files: `projects/views.py`, `templates/projects/milestones.html`, `ums.css`.
- [ ] Step 1: Write failing test (`test_timeline_bar_positions`).
- [ ] Step 2: Implement timeline view with status badges and today marker.
- [ ] Step 3: Confirm test passes, then commit with `feat(projects): milestone timeline view`.

Task 13: Scheduled at-risk detection and board
Files: Create `projects/risk.py` and `check_milestone_risk` management command. Modify `projects/views.py` (`at_risk_board`).
- [ ] Step 1: Write failing tests.
- [ ] Step 2: Implement risk checking logic, command, and board view.
- [ ] Step 3: Confirm tests pass, then commit with `feat(projects): scheduled milestone at-risk detection and board`.

Task 14: Seed, docs, scheduling, browser check (all parts)
- [ ] Extend `seed_demo_data` with funding calls and milestones.
- [ ] Add `docs/scheduled-jobs.md`.
- [ ] Browser check at 1366px and 375px.
- [ ] Commit `docs+seed: scheduled jobs and demo data for M6/M7`.
