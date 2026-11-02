"""Tests for M2 ORCID and Crossref import resilience, idempotency, and management command."""
import json
import os
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings
from django.core.management import call_command

from papers.models import ResearchPaper, ImportRun, PaperAuthor
from papers.importers import import_records, fetch_orcid_works, fetch_crossref, to_record
from dashboard.models import ResearchActivity


class ImportResilienceTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('office_staff', password='password123', is_staff=True)
        self.student = User.objects.create_user('student_user', password='password123')

        with open(os.path.join(settings.BASE_DIR, 'tests', 'fixtures', 'orcid_sample.json'), 'r', encoding='utf-8') as f:
            self.orcid_data = json.load(f)

        with open(os.path.join(settings.BASE_DIR, 'tests', 'fixtures', 'crossref_sample.json'), 'r', encoding='utf-8') as f:
            self.crossref_data = json.load(f)

    def test_import_resilient_to_malformed(self):
        # 1. ORCID Import
        run_orcid = ImportRun.objects.create(
            source='ORCID',
            query='0000-0002-1825-0097',
            initiated_by=self.staff
        )
        # 5 items in fixture:
        # - Item 1: Valid
        # - Item 2: Missing title -> skipped_malformed
        # - Item 3: Year '2021a' -> parsed as 2021
        # - Item 4: HTML in title -> stripped
        # - Item 5: Giant abstract -> truncated
        raw_orcid_items = [g['work-summary'][0] for g in self.orcid_data['group']]
        import_records(raw_orcid_items, source='ORCID', import_run=run_orcid, actor=self.staff)

        run_orcid.refresh_from_db()
        self.assertEqual(run_orcid.status, 'SUCCESS')
        self.assertEqual(run_orcid.skipped_malformed, 1)
        self.assertEqual(run_orcid.imported_count, 4)

        # Check year '2021a' was parsed to 2021
        p_acl = ResearchPaper.objects.filter(doi='10.18653/v1/2021.acl-long.999').first()
        self.assertIsNotNone(p_acl)
        self.assertEqual(p_acl.year, 2021)

        # Check HTML in title was stripped
        p_html = ResearchPaper.objects.filter(title__icontains='Quantum Error Correction').first()
        self.assertIsNotNone(p_html)
        self.assertEqual(p_html.title, 'Quantum Error Correction Protocols')

        # 2. Crossref Import
        run_crossref = ImportRun.objects.create(
            source='CROSSREF',
            query='Graph Representation Learning',
            initiated_by=self.staff
        )
        # 4 items in fixture:
        # - Item 1: Valid with authors + ORCID
        # - Item 2: Empty title -> skipped_malformed
        # - Item 3: Null authors -> imported with 0 authors
        # - Item 4: String year '2020a' -> imported
        raw_cr_items = self.crossref_data['message']['items']
        import_records(raw_cr_items, source='CROSSREF', import_run=run_crossref, actor=self.staff)

        run_crossref.refresh_from_db()
        self.assertEqual(run_crossref.status, 'SUCCESS')
        self.assertEqual(run_crossref.skipped_malformed, 1)
        self.assertEqual(run_crossref.imported_count, 3)

        # Check null authors item saved without error
        p_null_authors = ResearchPaper.objects.filter(doi='10.1145/malformed.null.author').first()
        self.assertIsNotNone(p_null_authors)
        self.assertEqual(p_null_authors.authors.count(), 0)

        # Check ResearchActivity was logged
        self.assertTrue(ResearchActivity.objects.filter(activity_type='IMPORT').exists())

    def test_import_idempotent_duplicate_prevention(self):
        raw_cr_items = self.crossref_data['message']['items']
        run1 = ImportRun.objects.create(source='CROSSREF', query='run1', initiated_by=self.staff)
        import_records(raw_cr_items, source='CROSSREF', import_run=run1, actor=self.staff)

        run2 = ImportRun.objects.create(source='CROSSREF', query='run2', initiated_by=self.staff)
        import_records(raw_cr_items, source='CROSSREF', import_run=run2, actor=self.staff)

        run2.refresh_from_db()
        self.assertEqual(run2.imported_count, 0)
        self.assertEqual(run2.duplicate_count, 3)

    @patch('papers.importers.requests.get')
    def test_management_command_import_publications(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = self.crossref_data
        mock_get.return_value = mock_resp

        call_command('import_publications', source='crossref', query='Graph Neural Networks', rows=5)

        run = ImportRun.objects.latest('created_at')
        self.assertEqual(run.source, 'CROSSREF')
        self.assertEqual(run.status, 'SUCCESS')

    def test_import_view_authorization(self):
        # Student cannot access import page
        self.client.force_login(self.student)
        res_forbidden = self.client.get(reverse('papers:import_publications'))
        self.assertEqual(res_forbidden.status_code, 403)

        # Staff can access import page
        self.client.force_login(self.staff)
        res_ok = self.client.get(reverse('papers:import_publications'))
        self.assertEqual(res_ok.status_code, 200)
        self.assertContains(res_ok, "Import Publications")
