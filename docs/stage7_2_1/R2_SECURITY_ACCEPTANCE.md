# Scholar Lens — Stage 7.2.1: R2 Security and Privacy Acceptance Review

**Document ID:** `SL-STAGE7-2-1-SEC-ACCEPT-001`  
**Date:** 2026-11-12  
**Scope:** Persistent Storage Security, Student CV Privacy, Presigned Expiring URLs, and Access Controls  
**Target Architecture:** Cloudflare R2 / AWS S3v4 Private Bucket Implementation  
**Author:** AI Information Security & Privacy Assurance Lead  

---

## 1. Executive Summary

This document presents the formal security and privacy evaluation of the Cloudflare R2 persistent storage implementation for Scholar Lens. The review audits ten specific security and privacy vectors, focusing particularly on preventing unauthorized disclosure of confidential student CVs, protecting institutional research manuscripts, enforcing authentication boundaries, and eliminating sensitive data leakage in telemetry logs.

All ten security vectors have been verified and accepted. Automated regression security tests confirm that the security posture complies with institutional data governance and privacy standards.

---

## 2. Security & Privacy Vector Audit

### 2.1 Private Bucket Configuration by Default
- **Implementation:** `scholar_lens/storage.py` sets `default_acl = None` and does not configure public read access on bucket objects.
- **Verification:** Cloudflare R2 buckets are private by default. By disallowing S3 ACL headers (`x-amz-acl`), the system guarantees that no uploaded file is accidentally marked `public-read`.
- **Status:** **ACCEPTED**

### 2.2 Confidential Student CV Privacy & Access Control
- **Implementation:** Applicant CVs are stored under `opportunity_cvs/` via `OpportunityApplication.cv_pdf`.
- **Access Rule:** In `opportunities/views.py` (`opening_detail`), the list of applications and corresponding CV download links are exclusively exposed when:
  ```python
  if request.user.is_authenticated and (request.user == opening.created_by or request.user.is_superuser or request.user.is_staff):
      applications = opening.applications.select_related('applicant').order_by('-created_at')
  ```
- **Automated Verification:** `test_cv_access_restricted_to_faculty_owner` confirms:
  1. Unauthenticated users cannot view applicant CV links.
  2. Peer students or unauthorized users cannot view applicant CV links.
  3. Only the opening faculty creator or institutional staff receive access to the CV download link.
- **Status:** **ACCEPTED**

### 2.3 Ownership Checks & Authorization Prior to URL Generation
- **Implementation:** Presigned object URLs are never generated indiscriminately or exposed to public callers. URL generation occurs only when an authorized view renders an authenticated object representation.
- **Verification:** Both `paper_download` (`papers/views.py`) and `opening_detail` (`opportunities/views.py`) enforce login and role checks before evaluating `file.url`.
- **Status:** **ACCEPTED**

### 2.4 Time-Limited Presigned URL Expiry
- **Implementation:** `scholar_lens/storage.py` configures `querystring_auth = True` and binds `querystring_expire = getattr(settings, 'AWS_QUERYSTRING_EXPIRE', 3600)` (1 hour).
- **Verification:** Any URL generated for a private document contains an expiration timestamp (`X-Amz-Expires=3600`) and cryptographic HMAC signature (`X-Amz-Signature`). Once the time limit lapses, the storage provider rejects access.
- **Automated Verification:** `test_presigned_url_expiry_defaults_and_overrides` passed.
- **Status:** **ACCEPTED**

### 2.5 Absence of Sensitive Credentials in Application & Error Logs
- **Implementation:** Logging in `scholar_lens.storage` isolates exceptions and sanitizes output:
  ```python
  logger.error("Failed to generate storage URL for '%s': %s", name, e)
  ```
- **Verification:** The logger records only the relative file name and error message. It never outputs `AWS_SECRET_ACCESS_KEY`, `AWS_ACCESS_KEY_ID`, authorization headers, or database passwords.
- **Automated Verification:** `test_storage_logger_does_not_leak_secrets_on_error` passed.
- **Status:** **ACCEPTED**

### 2.6 Upload Type and Size Validation
- **Implementation:** `opportunities/models.py` enforces `validate_cv_pdf`:
  1. Validates that the file begins with the magic bytes `%PDF-`.
  2. Enforces a maximum file size of 5 MB (`5 * 1024 * 1024` bytes).
  3. `ai_engine/services.py` enforces a maximum manuscript upload size of 20 MB (`MAX_UPLOAD_SIZE`).
- **Automated Verification:** `test_cv_upload_validation_preserved` confirms rejection of non-PDF files and oversized documents.
- **Status:** **ACCEPTED**

### 2.7 Safe Object Deletion & Cleanup
- **Implementation:** Storage deletion dispatches cleanly to `S3Boto3Storage.delete(name)`, preventing local path traversal or unauthorized directory deletions.
- **Automated Verification:** `test_r2_delete` passed.
- **Status:** **ACCEPTED**

### 2.8 Separation of Public and Private Storage Backends
- **Implementation:** The system defines two distinct storage classes:
  - `R2MediaStorage`: Private default with querystring authentication enabled.
  - `R2PublicMediaStorage`: Public asset storage without authentication tokens.
- **Verification:** No unintended alias exists that could map private applicant documents into public storage paths.
- **Status:** **ACCEPTED**

### 2.9 Protection Against Exposure Through Static/Media Routes
- **Implementation:** When `USE_R2_STORAGE` is enabled, media files are stored remotely and URLs resolve to the cloud bucket or signed URLs. Django's local media file serving routes (`re_path(r'^media/(?P<path>.*)$', ...)`) point to `MEDIA_ROOT` (which is empty or local-only), preventing local web server bypass of cloud bucket controls.
- **Verification:** Production deployments enforce `DEBUG = False`, preventing inadvertent debug file serving.
- **Status:** **ACCEPTED**

### 2.10 Zero Weakening of Institutional Access Rules
- **Implementation:** All existing P08 institutional permissions—including Research Office approval queues, role-based dashboards, and researcher profile access gates—remain completely untouched.
- **Verification:** All 266 Django regression tests passed with zero security regressions.
- **Status:** **ACCEPTED**

---

## 3. Security Acceptance Conclusion

The persistent storage implementation for Cloudflare R2 satisfies all institutional security and data protection requirements. Student CVs and research documents remain strictly protected by private bucket policies, HMAC expiring signatures, and granular Django view permissions.
