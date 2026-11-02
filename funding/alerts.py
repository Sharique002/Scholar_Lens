from datetime import date
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from dashboard.models import ResearchActivity
from .models import FundingCall, FundingAlert


def send_due_alerts(today: date = None) -> int:
    """
    Checks all published funding calls for upcoming deadlines at configured intervals.
    Creates ResearchActivity notifications for watchers and logs FundingAlert records.
    Returns the total number of notifications created.
    """
    if today is None:
        today = timezone.localdate()

    alert_days = getattr(settings, 'FUNDING_ALERT_DAYS', [30, 14, 7, 1])
    alerts_count = 0

    calls = FundingCall.objects.filter(is_published=True).prefetch_related('watchers')

    with transaction.atomic():
        for call in calls:
            days_left = call.days_left(today)
            if days_left < 0:
                continue

            passed = [d for d in alert_days if days_left <= d]
            if not passed:
                continue

            target = min(passed)
            watchers = call.watchers.all()
            if not watchers:
                continue

            deadline_local = timezone.localtime(call.deadline) if timezone.is_aware(call.deadline) else call.deadline
            deadline_str = deadline_local.strftime('%d %b %Y')

            for watcher in watchers:
                already_fired = FundingAlert.objects.filter(
                    call=call,
                    user=watcher,
                    days_before=target
                ).exists()

                if not already_fired:
                    desc = f"{call.title}: {days_left} day(s) left to apply (deadline {deadline_str})."
                    ResearchActivity.objects.create(
                        user=watcher,
                        activity_type='FUNDING',
                        description=desc
                    )
                    alerts_count += 1

                    for d in passed:
                        FundingAlert.objects.get_or_create(
                            call=call,
                            user=watcher,
                            days_before=d
                        )

    return alerts_count
