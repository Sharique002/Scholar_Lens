"""Management command to rebuild the PostgreSQL SearchVector for all researcher profiles."""
from django.core.management.base import BaseCommand
from researchers.search_index import refresh_search_document


class Command(BaseCommand):
    help = "Rebuild the full-text search_document index across all researcher profiles."

    def handle(self, *args, **options):
        self.stdout.write("Rebuilding expertise search index...")
        count = refresh_search_document()
        self.stdout.write(self.style.SUCCESS(f"Successfully indexed {count} researcher profiles."))
