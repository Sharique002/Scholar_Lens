"""Management command to import publications from ORCID, Crossref or Scopus."""
from django.core.management.base import BaseCommand, CommandError
from papers.models import ImportRun
from papers.importers import fetch_orcid_works, fetch_crossref, fetch_scopus, import_records


class Command(BaseCommand):
    help = "Import publications from ORCID, Crossref or Scopus (Scopus needs SCOPUS_API_KEY)."

    def add_arguments(self, parser):
        parser.add_argument('--source', type=str, required=True, choices=['orcid', 'crossref', 'scopus'], help="Source API")
        parser.add_argument('--orcid', type=str, help="ORCID iD (e.g. 0000-0002-1825-0097)")
        parser.add_argument('--query', type=str, help="Search query for Crossref")
        parser.add_argument('--scopus-author', type=str, help="Scopus author ID")
        parser.add_argument('--rows', type=int, default=20, help="Max records to fetch (default: 20)")

    def handle(self, *args, **options):
        source = options['source'].lower()

        if source == 'orcid':
            orcid_id = options.get('orcid')
            if not orcid_id:
                raise CommandError("--orcid is required when --source=orcid")
            query_str = orcid_id
            self.stdout.write(f"Fetching ORCID works for {orcid_id}...")
            raw_items = fetch_orcid_works(orcid_id)

        elif source == 'crossref':
            query_str = options.get('query')
            if not query_str:
                raise CommandError("--query is required when --source=crossref")
            rows = options.get('rows', 20)
            self.stdout.write(f"Searching Crossref for '{query_str}' (rows={rows})...")
            raw_items = fetch_crossref(query_str, rows=rows)

        elif source == 'scopus':
            query_str = options.get('scopus_author')
            if not query_str:
                raise CommandError("--scopus-author is required when --source=scopus")
            self.stdout.write(f"Fetching Scopus works for author {query_str}...")
            try:
                raw_items = fetch_scopus(query_str, rows=options.get('rows', 20))
            except ValueError as e:
                raise CommandError(str(e))

        self.stdout.write(f"Fetched {len(raw_items)} raw items. Importing...")

        run = ImportRun.objects.create(
            source=source.upper(),
            query=query_str
        )

        res = import_records(raw_items, source=source.upper(), import_run=run)

        self.stdout.write(
            self.style.SUCCESS(
                f"Import completed successfully!\n"
                f" - Imported: {res['imported']}\n"
                f" - Duplicates avoided: {res['duplicates']}\n"
                f" - Skipped/malformed: {res['skipped']}"
            )
        )
