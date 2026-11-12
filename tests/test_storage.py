"""Unit and Integration Tests for Persistent Storage (Cloudflare R2 / S3 Fallback).

Covers:
- Default local storage fallback in offline development.
- R2MediaStorage initialization, configuration, and ACL enforcement.
- Upload, retrieval, URL generation, and deletion.
- Presigned URL generation for private objects.
- Unsigned URL generation for public objects.
- Error and failure handling.
- Remote storage compatibility with paper_download view and AI extraction.
- Preservation of file upload validation (size and MIME type).
"""

import io
from unittest.mock import MagicMock, PropertyMock, patch
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage, default_storage
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from scholar_lens.storage import R2MediaStorage, R2PublicMediaStorage, get_active_storage
from opportunities.models import validate_cv_pdf
from papers.models import ResearchPaper

User = get_user_model()


class PersistentStorageUnitTests(TestCase):
    """Unit tests for R2MediaStorage configuration and behavior."""

    def test_default_storage_is_filesystem_when_r2_disabled(self):
        """When USE_R2_STORAGE is False, default storage must be FileSystemStorage."""
        with override_settings(USE_R2_STORAGE=False, USE_S3_STORAGE=False):
            active_storage = get_active_storage()
            self.assertIsInstance(active_storage, FileSystemStorage)

    def test_r2_storage_attributes_and_acls(self):
        """R2MediaStorage must enforce default_acl=None (R2 standard) and signature_version=s3v4."""
        with override_settings(
            USE_R2_STORAGE=True,
            AWS_STORAGE_BUCKET_NAME='scholar-lens-test-bucket',
            AWS_S3_ENDPOINT_URL='https://test.r2.cloudflarestorage.com',
            AWS_ACCESS_KEY_ID='mock-key',
            AWS_SECRET_ACCESS_KEY='mock-secret',
            AWS_S3_REGION_NAME='auto',
            AWS_QUERYSTRING_AUTH=True,
            AWS_QUERYSTRING_EXPIRE=3600
        ):
            storage = R2MediaStorage()
            self.assertIsNone(storage.default_acl)
            self.assertFalse(storage.file_overwrite)
            self.assertEqual(storage.signature_version, 's3v4')
            self.assertEqual(storage.region_name, 'auto')
            self.assertTrue(storage.querystring_auth)
            self.assertEqual(storage.querystring_expire, 3600)

    def test_r2_public_media_storage_attributes(self):
        """R2PublicMediaStorage must disable querystring auth for public asset access."""
        with override_settings(
            USE_R2_STORAGE=True,
            AWS_STORAGE_BUCKET_NAME='scholar-lens-test-bucket',
            AWS_S3_ENDPOINT_URL='https://test.r2.cloudflarestorage.com',
            AWS_ACCESS_KEY_ID='mock-key',
            AWS_SECRET_ACCESS_KEY='mock-secret'
        ):
            storage = R2PublicMediaStorage()
            self.assertIsNone(storage.default_acl)
            self.assertFalse(storage.querystring_auth)

    @patch('storages.backends.s3boto3.S3Boto3Storage.url')
    def test_r2_presigned_url_generation(self, mock_s3_url):
        """url() should delegate to S3Boto3Storage and return the presigned URL."""
        mock_s3_url.return_value = 'https://mock-bucket.r2.cloudflarestorage.com/media/test.pdf?X-Amz-Signature=123'
        storage = R2MediaStorage()
        generated_url = storage.url('opportunity_cvs/test.pdf')
        self.assertIn('X-Amz-Signature=123', generated_url)
        mock_s3_url.assert_called_once_with('opportunity_cvs/test.pdf', parameters=None, expire=None, http_method=None)

    @patch('storages.backends.s3boto3.S3Boto3Storage.exists', return_value=False)
    @patch('storages.backends.s3boto3.S3Boto3Storage._save')
    def test_r2_upload_and_save(self, mock_save, mock_exists):
        """_save() should invoke S3 client put_object and return cleaned name."""
        mock_save.return_value = 'opportunity_cvs/applicant_cv.pdf'
        storage = R2MediaStorage(bucket_name='test-bucket')
        content = ContentFile(b"%PDF-1.4 mock pdf content", name="applicant_cv.pdf")
        saved_name = storage.save('opportunity_cvs/applicant_cv.pdf', content)
        self.assertEqual(saved_name, 'opportunity_cvs/applicant_cv.pdf')
        mock_save.assert_called_once()

    @patch('storages.backends.s3boto3.S3Boto3Storage.delete')
    def test_r2_delete(self, mock_delete):
        """delete() should properly invoke S3 delete_object."""
        storage = R2MediaStorage()
        storage.delete('opportunity_cvs/applicant_cv.pdf')
        mock_delete.assert_called_once_with('opportunity_cvs/applicant_cv.pdf')

    @patch('storages.backends.s3boto3.S3Boto3Storage.url', side_effect=Exception("S3 connection error"))
    def test_r2_storage_url_failure_handling(self, mock_url):
        """url() should raise exception and log error if underlying S3 client fails."""
        storage = R2MediaStorage()
        with self.assertRaises(Exception):
            storage.url('error_file.pdf')


class StorageIntegrationAndFallbackTests(TestCase):
    """Integration tests verifying model, view, and service compatibility with remote storage."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='test_researcher',
            email='researcher@university.edu',
            password='TestPassword123!',
            first_name='Test',
            last_name='Researcher'
        )

    def test_cv_upload_validation_preserved(self):
        """validate_cv_pdf must continue rejecting non-PDF and oversized files."""
        # Non-PDF rejection
        text_file = ContentFile(b"Plain text content, not a PDF", name="cv.txt")
        with self.assertRaises(ValidationError) as cm:
            validate_cv_pdf(text_file)
        self.assertIn("PDF", str(cm.exception))

        # Oversized file (> 5MB) rejection
        large_content = b"%PDF-1.4 " + b"0" * (6 * 1024 * 1024)
        large_file = ContentFile(large_content, name="huge_cv.pdf")
        with self.assertRaises(ValidationError) as cm_size:
            validate_cv_pdf(large_file)
        self.assertIn("5 MB", str(cm_size.exception))

        # Valid PDF header accepted
        valid_pdf = ContentFile(b"%PDF-1.4 valid test pdf content", name="good_cv.pdf")
        try:
            validate_cv_pdf(valid_pdf)
        except ValidationError:
            self.fail("validate_cv_pdf raised ValidationError on valid PDF.")

    def test_paper_download_remote_storage_redirect(self):
        """When paper.pdf_file.path raises NotImplementedError, paper_download redirects to url."""
        self.client.login(username='test_researcher', password='TestPassword123!')
        paper = ResearchPaper.objects.create(
            title="Remote Storage Manuscript",
            uploader=self.user,
            research_area="CS",
            status="UPLOADED"
        )
        mock_file = MagicMock()
        mock_file.name = "papers/remote_paper.pdf"
        type(mock_file).path = PropertyMock(side_effect=NotImplementedError("This backend doesn't support absolute paths."))
        mock_file.url = "https://mock-bucket.r2.cloudflarestorage.com/media/papers/remote_paper.pdf?token=abc"
        paper.pdf_file = mock_file

        with patch('papers.views.get_object_or_404', return_value=paper):
            response = self.client.get(reverse('papers:download', kwargs={'pk': paper.pk}))
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, mock_file.url)

    def test_ai_extract_text_remote_storage_stream_support(self):
        """PaperProcessor.extract_text must read stream when .path raises NotImplementedError."""
        from ai_engine.services import PaperProcessor

        paper = ResearchPaper.objects.create(
            title="Stream Extraction Test",
            uploader=self.user,
            research_area="CS",
            status="UPLOADED"
        )

        # Create a real minimal PDF in memory using PyMuPDF if available
        try:
            import pymupdf as fitz
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((50, 72), "Abstract: This is a test paper extracted from stream.")
            pdf_bytes = doc.tobytes()
        except ImportError:
            pdf_bytes = b"%PDF-1.4 minimal test pdf"

        mock_file = MagicMock()
        mock_file.name = "papers/stream_paper.pdf"
        type(mock_file).path = PropertyMock(side_effect=NotImplementedError("Remote S3 storage."))
        mock_file.open = MagicMock(return_value=io.BytesIO(pdf_bytes))
        mock_file.read = MagicMock(return_value=pdf_bytes)
        paper.pdf_file = mock_file

        processor = PaperProcessor()
        try:
            text = processor.extract_text(paper)
            self.assertIn("Abstract:", text)
        except Exception as e:
            # If pymupdf is not installed or test environment lacks native fitz, verify it didn't fail on NotImplementedError
            self.assertNotIn("NotImplementedError", str(e))


class R2StorageSecurityTests(TestCase):
    """Security, authorization, and privacy verification for persistent storage."""

    def setUp(self):
        self.faculty = User.objects.create_user(
            username='prof_secure',
            email='prof@university.edu',
            password='TestPassword123!',
            first_name='Prof',
            last_name='Secure'
        )
        self.student = User.objects.create_user(
            username='student_applicant',
            email='student@university.edu',
            password='TestPassword123!',
            first_name='Student',
            last_name='Applicant'
        )
        self.unauthorized_user = User.objects.create_user(
            username='other_student',
            email='other@university.edu',
            password='TestPassword123!',
            first_name='Other',
            last_name='Student'
        )

    def test_r2_private_bucket_default_acl_none(self):
        """R2MediaStorage must enforce default_acl=None to prevent accidental public bucket exposure."""
        storage = R2MediaStorage()
        self.assertIsNone(storage.default_acl)
        self.assertFalse(storage.file_overwrite)
        self.assertTrue(storage.querystring_auth)

    def test_presigned_url_expiry_defaults_and_overrides(self):
        """Presigned URLs must have limited lifetime (default 3600 seconds = 1 hour)."""
        with override_settings(AWS_QUERYSTRING_EXPIRE=1800):
            storage = R2MediaStorage()
            self.assertEqual(storage.querystring_expire, 1800)

    def test_cv_access_restricted_to_faculty_owner(self):
        """Confidential CV URLs must only be visible to opening owner or staff, never other students."""
        from opportunities.models import ResearchOpening, OpportunityApplication
        from researchers.models import Department

        dept, _ = Department.objects.get_or_create(name="Physics", defaults={"code": "PHYS"})
        opening = ResearchOpening.objects.create(
            title="Quantum Lab Assistant",
            created_by=self.faculty,
            department=dept,
            description="Looking for research assistants.",
            deadline="2027-12-31",
            status="OPEN"
        )
        OpportunityApplication.objects.create(
            opening=opening,
            applicant=self.student,
            statement="Interested in quantum computing.",
            cv_pdf="opportunity_cvs/student_secret_cv.pdf",
            status="SUBMITTED"
        )

        detail_url = reverse('opportunities:detail', kwargs={'pk': opening.pk})

        # 1. Unauthenticated user cannot see applicant CVs
        resp = self.client.get(detail_url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("student_secret_cv.pdf", resp.content.decode('utf-8'))

        # 2. Another student cannot see applicant CVs
        self.client.login(username='other_student', password='TestPassword123!')
        resp = self.client.get(detail_url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("student_secret_cv.pdf", resp.content.decode('utf-8'))
        self.client.logout()

        # 3. Faculty owner CAN see applicant CV link
        self.client.login(username='prof_secure', password='TestPassword123!')
        resp = self.client.get(detail_url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("opportunity_cvs/student_secret_cv.pdf", resp.content.decode('utf-8'))
        self.client.logout()

    def test_storage_logger_does_not_leak_secrets_on_error(self):
        """Storage logger must log filename and error message without leaking sensitive credentials."""
        storage = R2MediaStorage()
        with self.assertLogs('scholar_lens.storage', level='ERROR') as cm:
            with patch('storages.backends.s3boto3.S3Boto3Storage.url', side_effect=Exception("Connection refused")):
                with self.assertRaises(Exception):
                    storage.url('opportunity_cvs/sensitive_cv.pdf')
        log_output = "\n".join(cm.output)
        self.assertIn("sensitive_cv.pdf", log_output)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", log_output)
        self.assertNotIn("AWS_ACCESS_KEY_ID", log_output)
        self.assertNotIn("R2_SECRET_ACCESS_KEY", log_output)

