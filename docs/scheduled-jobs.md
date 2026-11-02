# Scheduled Jobs & Automated Management Tasks

## 1. Overview
Scholar Lens relies on lightweight, idempotent Django management commands rather than heavyweight asynchronous message brokers (e.g., Celery). These jobs run on a daily schedule via external schedulers (Linux cron, Windows Task Scheduler, or cloud cron jobs like Render Cron).

| Management Command | Purpose | Frequency |
|---|---|---|
| `python manage.py send_funding_alerts` | Evaluates active, published funding calls against deadline alert intervals (`FUNDING_ALERT_DAYS = [30, 14, 7, 1]`). Sends `ResearchActivity` notifications to watchers. Catches up missed days without duplicate alerts. | Once daily (e.g., 06:00 AM) |
| `python manage.py check_milestone_risk` | Evaluates all active project milestones against at-risk thresholds (`MILESTONE_AT_RISK_DAYS = 7`, `MILESTONE_AT_RISK_PROGRESS = 50%`) and dependency blockers. Emits notifications when a milestone becomes `AT_RISK` or `OVERDUE`. | Once daily (e.g., 06:15 AM) |

---

## 2. Idempotency & Fault Tolerance
Both commands are designed to be completely idempotent:
- **`send_funding_alerts`**: Tracks fired alerts in the `FundingAlert` table (`unique_together = ('call', 'user', 'days_before')`). Running multiple times in the same day or missing a day produces exactly the required notifications without duplicates.
- **`check_milestone_risk`**: Evaluates in two passes so overdue dependency states propagate immediately. Notifications are dispatched only when a milestone's risk state transitions into `AT_RISK` or `OVERDUE`. A one-off "due on..." notification is dispatched once when a deliverable enters the active warning window.

---

## 3. Configuration & Overrides
Environment variables or CLI arguments can adjust thresholds:
- `FUNDING_ALERT_DAYS`: Comma-separated alert intervals in days (default: `30,14,7,1`).
- `MILESTONE_AT_RISK_DAYS`: Days before deadline threshold (default: `7`). Override via CLI: `--days 10`.
- `MILESTONE_AT_RISK_PROGRESS`: Minimum progress percentage threshold (default: `50`). Override via CLI: `--min-progress 60`.

---

## 4. Scheduling Setup Examples

### 4.1 Linux Cron
Edit the crontab using `crontab -e`:
```bash
# Run funding deadline alerts daily at 06:00 AM
0 6 * * * cd /path/to/scholar_lens && /path/to/scholar_lens/.venv/bin/python manage.py send_funding_alerts >> /var/log/scholar_lens_funding.log 2>&1

# Run milestone risk assessment daily at 06:15 AM
15 6 * * * cd /path/to/scholar_lens && /path/to/scholar_lens/.venv/bin/python manage.py check_milestone_risk >> /var/log/scholar_lens_milestones.log 2>&1
```

### 4.2 Windows Task Scheduler (PowerShell)
Register a daily scheduled task in PowerShell (run as Administrator):
```powershell
$Action1 = New-ScheduledTaskAction -Execute "C:\path\to\.venv\Scripts\python.exe" `
    -Argument "manage.py send_funding_alerts" `
    -WorkingDirectory "C:\path\to\scholar_lens_research_hub"

$Action2 = New-ScheduledTaskAction -Execute "C:\path\to\.venv\Scripts\python.exe" `
    -Argument "manage.py check_milestone_risk" `
    -WorkingDirectory "C:\path\to\scholar_lens_research_hub"

$Trigger = New-ScheduledTaskTrigger -Daily -At 6am

Register-ScheduledTask -Action $Action1 -Trigger $Trigger -TaskName "ScholarLens_FundingAlerts" -Description "Daily funding alert dispatcher"
Register-ScheduledTask -Action $Action2 -Trigger $Trigger -TaskName "ScholarLens_MilestoneRisk" -Description "Daily milestone risk auditor"
```

### 4.3 Cloud Cron (Render `render.yaml` Snippet)
*(Reference documentation only)*:
```yaml
services:
  - type: cron
    name: scholar-lens-funding-alerts
    env: python
    schedule: "0 6 * * *"
    buildCommand: "poetry install || pip install -r requirements.txt"
    startCommand: "python manage.py send_funding_alerts"
    envVars:
      - key: USE_POSTGRES
        value: "1"
      - key: DATABASE_URL
        fromDatabase:
          name: scholar-lens-db
          property: connectionString

  - type: cron
    name: scholar-lens-milestone-risk
    env: python
    schedule: "15 6 * * *"
    buildCommand: "poetry install || pip install -r requirements.txt"
    startCommand: "python manage.py check_milestone_risk"
    envVars:
      - key: USE_POSTGRES
        value: "1"
      - key: DATABASE_URL
        fromDatabase:
          name: scholar-lens-db
          property: connectionString
```
