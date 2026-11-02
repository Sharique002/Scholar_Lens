from datetime import date
from django.conf import settings
from django.utils import timezone
from dashboard.models import ResearchActivity
from .models import Milestone


def compute_risk(m: Milestone, today: date, days: int, min_progress: int) -> tuple[str, str]:
    """
    Computes (risk, reason) for a milestone.
    Evaluates rules in order:
    1. status == DONE -> ('ON_TRACK', '')
    2. due_date < today -> ('OVERDUE', f'Was due {due:%d %b}')
    3. due_date - today <= days and progress < min_progress -> ('AT_RISK', f'Due in {n} days, only {progress}% done')
    4. Any dependency not DONE, with that dependency's due_date >= m.due_date or its risk == 'OVERDUE' -> ('AT_RISK', f'Waiting on "{dep.title}"')
    5. Otherwise -> ('ON_TRACK', '')
    """
    if m.status == 'DONE':
        return ('ON_TRACK', '')

    if m.due_date < today:
        return ('OVERDUE', f'Was due {m.due_date.strftime("%d %b")}')

    diff_days = (m.due_date - today).days
    if diff_days <= days and m.progress < min_progress:
        return ('AT_RISK', f'Due in {diff_days} days, only {m.progress}% done')

    if m.pk:
        for dep in m.depends_on.all():
            if dep.status != 'DONE':
                if dep.due_date >= m.due_date or dep.risk == 'OVERDUE':
                    return ('AT_RISK', f'Waiting on "{dep.title}"')

    return ('ON_TRACK', '')


def run_risk_check(today: date = None, days: int = None, min_progress: int = None) -> dict:
    if today is None:
        today = timezone.localdate()
    if days is None:
        days = getattr(settings, 'MILESTONE_AT_RISK_DAYS', 7)
    if min_progress is None:
        min_progress = getattr(settings, 'MILESTONE_AT_RISK_PROGRESS', 50)

    milestones = list(
        Milestone.objects.exclude(status='DONE')
        .select_related('project', 'project__leader', 'owner')
        .prefetch_related('depends_on')
    )

    checked_count = len(milestones)
    at_risk_count = 0
    overdue_count = 0
    notified_count = 0

    now_ts = timezone.now()

    # Pass 1: compute rules 1-3
    pass1_risks = {}
    for m in milestones:
        if m.due_date < today:
            new_risk = 'OVERDUE'
            reason = f'Was due {m.due_date.strftime("%d %b")}'
        else:
            diff_days = (m.due_date - today).days
            if diff_days <= days and m.progress < min_progress:
                new_risk = 'AT_RISK'
                reason = f'Due in {diff_days} days, only {m.progress}% done'
            else:
                new_risk = 'ON_TRACK'
                reason = ''

        m._pass1_risk = new_risk
        m._pass1_reason = reason
        pass1_risks[m.pk] = new_risk

    # Pass 2: rule 4 for dependencies
    for m in milestones:
        old_risk = m.risk
        new_risk = m._pass1_risk
        reason = m._pass1_reason

        if new_risk == 'ON_TRACK':
            for dep in m.depends_on.all():
                if dep.status != 'DONE':
                    dep_risk = pass1_risks.get(dep.pk, dep.risk)
                    if dep.due_date >= m.due_date or dep_risk == 'OVERDUE':
                        new_risk = 'AT_RISK'
                        reason = f'Waiting on "{dep.title}"'
                        break

        if new_risk == 'AT_RISK':
            at_risk_count += 1
        elif new_risk == 'OVERDUE':
            overdue_count += 1

        # Check if risk transitioned into AT_RISK or OVERDUE
        if new_risk in ('AT_RISK', 'OVERDUE') and old_risk != new_risk:
            label = 'At Risk' if new_risk == 'AT_RISK' else 'Overdue'
            msg = f'"{m.title}" in {m.project.title} is now {label}: {reason}'
            recipients = set()
            if m.owner:
                recipients.add(m.owner)
            if m.project.leader:
                recipients.add(m.project.leader)

            for user in recipients:
                ResearchActivity.objects.create(
                    user=user,
                    activity_type='MILESTONE',
                    description=msg
                )

        # One-off due notice
        diff_days = (m.due_date - today).days
        if diff_days <= days and not m.due_notified and m.status != 'DONE':
            due_str = m.due_date.strftime('%d %b %Y')
            notice = f'"{m.title}" in {m.project.title} is due on {due_str}'
            recipients = set()
            if m.owner:
                recipients.add(m.owner)
            if m.project.leader:
                recipients.add(m.project.leader)

            for user in recipients:
                ResearchActivity.objects.create(
                    user=user,
                    activity_type='MILESTONE',
                    description=notice
                )
            m.due_notified = True
            notified_count += 1

        m.risk = new_risk
        m.risk_reason = reason
        m.risk_checked_at = now_ts
        m.save(update_fields=['risk', 'risk_reason', 'risk_checked_at', 'due_notified'])

    return {
        'checked': checked_count,
        'at_risk': at_risk_count,
        'overdue': overdue_count,
        'notified': notified_count,
    }
