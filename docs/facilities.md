# Facility & Asset Management (M8)

## 1. Overview
The Facility & Asset Management module (M8) manages high-value research instrumentation, laboratory spaces, and compute clusters across university departments (e.g., Computer Science, Biotechnology). It provides:
- Public catalogue with search and department/kind filtering.
- Monday-aligned 7-day weekly operating availability calendar.
- Time-slot booking workflow with strict validation rules.
- Database-level double-booking prevention under concurrent requests.
- Facility custodian management queue (approval, rejection, logging usage, marking no-shows).
- Utilisation metrics dashboard with CSV export for audit and reporting.

---

## 2. Roles & Permissions

| Role | Permissions |
|---|---|
| **Student / Researcher** | Browse catalogue, view weekly operating availability, create pending booking requests, view personal bookings, cancel own pending/approved bookings prior to start time. |
| **Custodian** | Facility owner/custodian assigned to the facility. Accesses `/facilities/manage/` queue, reviews and approves/rejects pending bookings, logs actual usage (`COMPLETED` or `NO_SHOW`). Notifications sent via `ResearchActivity`. |
| **Research Office / Staff** | All custodian permissions across all facilities, plus access to `/facilities/utilisation/` report and CSV export. |

---

## 3. Database Architecture & Concurrency Safety

### 3.1 ExclusionConstraint on GiST
To guarantee zero double-booking under extreme concurrent requests, double-booking prevention is enforced inside PostgreSQL 15 rather than relying on application-level locks alone.

- **PostgreSQL Extension:** `btree_gist` enabled via `BtreeGistExtension()` in migration `0001_initial.py`.
- **Constraint Definition:**
  ```python
  ExclusionConstraint(
      name='no_overlapping_active_bookings',
      expressions=[
          ('facility', RangeOperators.EQUAL),
          ('during', RangeOperators.OVERLAPS),
      ],
      condition=Q(status__in=['PENDING', 'APPROVED']),
  )
  ```
- **Range Operator:** `during` is stored as a PostgreSQL `tstzrange` (`DateTimeRangeField`) using half-open intervals `[start, end)`.

### 3.2 Handling Conflicts in Code
When a conflicting booking is submitted simultaneously:
1. `create_booking()` wraps the insert in a database transaction.
2. In high-concurrency races, PostgreSQL raises either `IntegrityError` (exclusion violation) or `OperationalError` (`psycopg2.errors.DeadlockDetected` while checking the exclusion constraint).
3. Both exceptions are caught, returning a friendly error: *"The selected time slot has already been booked or has a pending request. Please choose another time."*
4. Zero unhandled 500 errors occur under concurrent write conditions.

---

## 4. Booking Validation Rules

Forms and views validate the following invariant business rules:
1. **Start < End:** The end time must strictly follow the start time.
2. **No Past Bookings:** Booking start time cannot be in the past.
3. **Operating Hours:** The booking must fall completely within the facility's defined `FacilitySlot` operating windows (e.g., Mon–Fri 09:00–17:00).
4. **Max Duration:** A single booking cannot exceed 8 hours.

---

## 5. Running Tests on PostgreSQL

> **Important:** SQLite does not support PostgreSQL range fields (`DateTimeRangeField`) or GiST exclusion constraints (`BtreeGistExtension`). All tests for the `facilities` app must be run on PostgreSQL 15.

1. **Start PostgreSQL in Docker:**
   ```bash
   docker compose up -d db
   ```

2. **Run Facilities Test Suite:**
   ```powershell
   $env:USE_POSTGRES="1"
   $env:DATABASE_URL="postgres://scholar_lens:scholar_lens@localhost:5432/scholar_lens"
   .venv\Scripts\python.exe manage.py test tests.test_facilities
   ```

3. **Run Concurrency Proof Only:**
   ```powershell
   $env:USE_POSTGRES="1"
   $env:DATABASE_URL="postgres://scholar_lens:scholar_lens@localhost:5432/scholar_lens"
   .venv\Scripts\python.exe manage.py test tests.test_facilities.FacilitiesConcurrencyTests.test_concurrent_booking_only_one_wins
   ```

---

## 6. Demo Seed Data
The management command seeds 4 facilities across two departments with `demo_custodian` (password: `demo_password_123`):
- **CSE:** GPU Compute Cluster (LAB), IoT Lab (LAB)
- **Biotech:** Confocal Microscope (EQUIPMENT), PCR Room (ROOM)

```powershell
$env:USE_POSTGRES="1"
$env:DATABASE_URL="postgres://scholar_lens:scholar_lens@localhost:5432/scholar_lens"
.venv\Scripts\python.exe manage.py seed_demo_data --clear
```
