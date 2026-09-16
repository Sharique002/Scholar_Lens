"""
Management command to synchronize latest academic research and emerging technologies
from Google Scholar and scholarly sources into Scholar Lens.
Safe to execute repeatedly (100% idempotent).
"""

from django.core.management.base import BaseCommand
from papers.scholar_service import GoogleScholarService


class Command(BaseCommand):
    help = "Synchronize latest academic research and emerging technologies from Google Scholar"

    def add_arguments(self, parser):
        parser.add_argument(
            '--areas',
            nargs='+',
            type=str,
            help='Specific research areas to synchronize (e.g., AI_ML NLP COMPUTER_VISION)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=3,
            help='Maximum number of papers to retrieve per research area (default: 3)',
        )

    def handle(self, *args, **options):
        areas = options.get('areas')
        limit = options.get('limit', 3)

        self.stdout.write(self.style.NOTICE("Initiating Google Scholar research synchronization..."))

        service = GoogleScholarService()
        result = service.sync_latest_research(areas=areas, limit_per_area=limit)

        self.stdout.write(
            self.style.SUCCESS(
                f"Synchronization completed successfully!\n"
                f" - Total papers processed/verified: {result.get('total_synced', 0)}\n"
                f" - Newly indexed records: {result.get('newly_added', 0)}\n"
                f" - Timestamp: {result.get('timestamp')}"
            )
        )
