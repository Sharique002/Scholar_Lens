from django.core.management.base import BaseCommand
from django.utils import timezone
from funding.alerts import send_due_alerts


class Command(BaseCommand):
    help = 'Send scheduled deadline alerts for watched funding calls.'

    def handle(self, *args, **options):
        today = timezone.localdate()
        count = send_due_alerts(today)
        self.stdout.write(f"Sent {count} funding alerts.")
