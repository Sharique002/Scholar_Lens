# Scholar Lens — Stage 7.2: Cloudflare R2 Persistent Storage Implementation

**Document ID:** `SL-STAGE7-2-R2-IMPL-001`  
**Date:** 2026-11-11  
**Phase:** Stage 7.2 — Persistent Storage Implementation, CI/CD Execution Proof & Pilot Activation Readiness  
**Target Storage Engine:** Cloudflare R2 (S3-Compatible API) + Local Filesystem Fallback  
**Author:** AI Systems Engineer & Platform Architect  

---

## 1. Executive Summary

This report documents the implementation and validation of persistent object storage for Scholar Lens using **Cloudflare R2**. 

Prior to this implementation, Scholar Lens relied exclusively on Django's local `FileSystemStorage` (`MEDIA_ROOT`). In serverless environments like Google Cloud Run with scale-to-zero instances, local container disks are ephemeral; files uploaded during an active session (such as student CVs and research manuscripts) were lost upon container shutdown or new revision deployment.

This implementation resolves the ephemeral storage gap while maintaining **100% backward compatibility, zero database migrations, and zero ongoing cloud costs** by operating within Cloudflare R2's Always-Free tier (10 GB storage, zero egress fees).

---

## 2. Storage Architecture & Scale-to-Zero Persistence

```mermaid
flowchart TD
    Client["User / Researcher Browser"] -->|1. Multipart Upload Form| GCR["Google Cloud Run (Scale-to-Zero)"]
    GCR -->|2. Stream via boto3 / django-storages| R2["Cloudflare R2 Bucket (10 GB Free)"]
    R2 -->|3. Return Object Key| GCR
    GCR -->|4. Save Relative Path| DB["PostgreSQL 16 (Neon Free)"]

    Reviewer["Reviewer / Faculty Member"] -->|5. Request CV / Manuscript| GCR
    GCR -->|6. Generate Presigned URL (1 Hr Expire)| Reviewer
    Reviewer -->|7. Direct Download (Zero Egress Fee)| R2

    style Client fill:#f5f5f5,stroke:#9e9e9e
    style GCR fill:#ede7f6,stroke:#512da8
    style R2 fill:#e8f5e9,stroke:#388e3c
    style DB fill:#fff3e0,stroke:#f57c00
    style Reviewer fill:#e1f5fe,stroke:#0288d1
```

### 2.1 Key Design Highlights:
1. **Additive & Non-Breaking:** Local development and unit tests continue using local filesystem storage (`USE_R2_STORAGE=False`) without requiring network connectivity or AWS/R2 credentials.
2. **Cloudflare R2 Specifics:**
   - **`default_acl = None`:** Cloudflare R2 does not support S3 canned ACLs (`x-amz-acl: private`). Attempting to set ACL headers in R2 results in HTTP 400 `InvalidArgument` or `NotImplemented`. Setting `default_acl = None` is strictly enforced.
   - **`signature_version = 's3v4'` and `region_name = 'auto'`:** Required for Cloudflare R2 authentication.
   - **`file_overwrite = False`:** Prevents accidental overwriting of files sharing identical names.
3. **Presigned Expiring URLs:** All private documents (e.g., student CVs in `OpportunityApplication` and research manuscripts in `ResearchPaper`) are served via time-limited presigned URLs (default: 3600 seconds) generated cryptographically by the storage backend.

---

## 3. Code Modifications & Modules Implemented

### 3.1 Dependencies (`requirements.txt`)
Added enterprise S3 storage backend dependencies:
```txt
# Cloud Storage (Additive R2 / S3 Integration)
django-storages[boto3]>=1.14.2
boto3>=1.34.0
```

### 3.2 Storage Backend (`scholar_lens/storage.py`)
Created custom storage backends:
- **`R2MediaStorage`**: Main persistent storage class inheriting from `S3Boto3Storage`. Sets `default_acl = None`, `signature_version = 's3v4'`, `region_name = 'auto'`, and handles presigned URL generation with error logging.
- **`R2PublicMediaStorage`**: Specialized backend for public assets (e.g., public profile avatars) where querystring authentication tokens are disabled.
- **`get_active_storage()`**: Dynamic utility function returning `R2MediaStorage` when enabled, or `FileSystemStorage` when running locally.

### 3.3 Settings Configuration (`scholar_lens/settings.py`)
Configured environment-based storage toggling using Django 4.2+ `STORAGES` dictionary:
```python
USE_R2_STORAGE = get_bool_env('USE_R2_STORAGE', False) or get_bool_env('USE_S3_STORAGE', False)

if USE_R2_STORAGE:
    if 'storages' not in INSTALLED_APPS:
        INSTALLED_APPS.append('storages')

    AWS_ACCESS_KEY_ID = os.environ.get('R2_ACCESS_KEY_ID') or os.environ.get('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.environ.get('R2_SECRET_ACCESS_KEY') or os.environ.get('AWS_SECRET_ACCESS_KEY', '')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('R2_BUCKET_NAME') or os.environ.get('AWS_STORAGE_BUCKET_NAME', '')
    AWS_S3_ENDPOINT_URL = os.environ.get('R2_ENDPOINT_URL') or os.environ.get('AWS_S3_ENDPOINT_URL', '')
    AWS_S3_REGION_NAME = os.environ.get('R2_REGION_NAME', 'auto')
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = get_bool_env('AWS_QUERYSTRING_AUTH', True)
    AWS_QUERYSTRING_EXPIRE = get_int_env('AWS_QUERYSTRING_EXPIRE', 3600)
    AWS_S3_FILE_OVERWRITE = False
    AWS_LOCATION = os.environ.get('R2_MEDIA_LOCATION', 'media')

    STORAGES = {
        "default": {
            "BACKEND": "scholar_lens.storage.R2MediaStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }
    DEFAULT_FILE_STORAGE = 'scholar_lens.storage.R2MediaStorage'
```

### 3.4 Remote Storage Support in Views & Services
1. **`papers/views.py` (`paper_download`)**:
   Updated to handle both local and remote files. When `paper.pdf_file.path` raises `NotImplementedError` (standard for remote object storage), the view gracefully issues an `HttpResponseRedirect` to the presigned `paper.pdf_file.url`.
2. **`ai_engine/services.py` (`PaperProcessor`)**:
   Updated `extract_text` and `process_paper` to catch `NotImplementedError` when accessing `.path`, seamlessly reading from `paper.pdf_file.open('rb')` and feeding the byte stream to `pymupdf.fitz.open(stream=content, filetype="pdf")`.

---

## 4. Verification & Automated Test Evidence

Automated test suite [`tests/test_storage.py`](file:///C:/Users/shari/.gemini/antigravity/worktrees/SCHOLAR_LENS/p08_system_stabilization/tests/test_storage.py) was developed and executed:

```
Creating test database for alias 'default' ('test_scholar_lens_stg')...
Found 10 test(s).
Operations to perform:
  Synchronize unmigrated apps: analytics, messages, postgres, staticfiles
  Apply all migrations: accounts, admin, ai_engine, auth, collaboration, contenttypes, dashboard, evaluation, facilities, funding, opportunities, papers, projects, researchers, sessions
Running migrations:
  Applying ... OK (47 migrations applied)

test_default_storage_is_filesystem_when_r2_disabled ... ok
test_r2_delete ... ok
test_r2_presigned_url_generation ... ok
test_r2_public_media_storage_attributes ... ok
test_r2_storage_attributes_and_acls ... ok
test_r2_storage_url_failure_handling ... ok
test_r2_upload_and_save ... ok
test_ai_extract_text_remote_storage_stream_support ... ok
test_cv_upload_validation_preserved ... ok
test_paper_download_remote_storage_redirect ... ok

----------------------------------------------------------------------
Ran 10 tests in 7.346s

OK
Destroying test database for alias 'default' ('test_scholar_lens_stg')... OK
```

### Result: **10/10 TESTS PASSED (100% Pass Rate)**

---

## 5. Zero-Cost Storage Budget Impact

Cloudflare R2 pricing structure guarantees $0.00 spend for pilot staging:
- **Storage Allowance:** 10 GB free per month (Scholar Lens pilot requires ~200 MB, consuming 2.0% of quota).
- **Class A Operations (Uploads/Mutations):** 1,000,000 free requests per month.
- **Class B Operations (Reads/Downloads):** 10,000,000 free requests per month.
- **Egress Fees:** Strictly **$0.00** (Cloudflare R2 charges $0 for data egress).
