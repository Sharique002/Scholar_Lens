from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from projects.risk import run_risk_check


class Command(BaseCommand):
    help = 'Evaluate project milestones and flag at-risk and overdue deliverables.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=None,
            help='Days threshold before deadline to flag low progress as at-risk.'
        )
        parser.add_argument(
            '--min-progress',
            type=int,
            default=None,
            help='Minimum progress percentage required to be considered on track.'
        )

    def handle(self, *args, **options):
        today = timezone.localdate()
        days = options['days']
        min_progress = options['min_progress']

        res = run_risk_check(today=today, days=days, min_progress=min_progress)
        self.stdout.write(
            f"Checked {res['checked']} milestones: {res['at_risk']} at risk, {res['overdue']} overdue."
        )
