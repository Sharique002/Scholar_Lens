"""Scholar Lens Cloudflare R2 / S3 Persistent Storage Backend.

This module provides production-ready, additive storage backends for
Cloudflare R2 (and AWS S3-compatible APIs) using django-storages and boto3.

Key Capabilities:
- Scale-to-Zero Compatibility: Preserves uploaded files (CVs, manuscripts, avatars)
  beyond container ephemeral lifecycles.
- Private by Default: Objects are private without public bucket listing.
- Presigned Expiring URLs: Generates time-limited signed URLs for confidential documents.
- Cloudflare R2 Tuning: Sets default_acl=None (R2 does not support S3 ACLs) and
  forces signature_version='s3v4' with region_name='auto'.
- Graceful Local Fallback: When USE_R2_STORAGE is False, Django falls back to
  standard FileSystemStorage without requiring network access or cloud credentials.
"""

import logging
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage

logger = logging.getLogger('scholar_lens.storage')


class R2MediaStorage(S3Boto3Storage):
    """Additive persistent storage backend tuned specifically for Cloudflare R2.
    
    Cloudflare R2 provides an S3-compatible API with zero egress fees and a 10 GB
    free tier. This class enforces private object semantics and presigned URLs.
    """
    default_acl = None
    file_overwrite = False
    signature_version = 's3v4'
    location = getattr(settings, 'AWS_LOCATION', 'media')

    def __init__(self, **settings_dict):
        # Allow runtime override or read from Django settings
        super().__init__(**settings_dict)
        # Cloudflare R2 requires region_name='auto' and default_acl=None
        if not self.region_name:
            self.region_name = getattr(settings, 'AWS_S3_REGION_NAME', 'auto')
        self.default_acl = None
        self.querystring_auth = getattr(settings, 'AWS_QUERYSTRING_AUTH', True)
        self.querystring_expire = getattr(settings, 'AWS_QUERYSTRING_EXPIRE', 3600)

    def url(self, name, parameters=None, expire=None, http_method=None):
        """Generate presigned expiring URL for private files or custom domain URL."""
        try:
            return super().url(name, parameters=parameters, expire=expire, http_method=http_method)
        except Exception as e:
            logger.error("Failed to generate storage URL for '%s': %s", name, e)
            raise


class R2PublicMediaStorage(S3Boto3Storage):
    """Storage backend for public assets (e.g. public avatars) without querystring tokens."""
    default_acl = None
    file_overwrite = False
    signature_version = 's3v4'
    querystring_auth = False
    location = getattr(settings, 'AWS_LOCATION', 'media')

    def __init__(self, **settings_dict):
        super().__init__(**settings_dict)
        self.default_acl = None
        self.querystring_auth = False


def get_active_storage():
    """Return the active storage backend instance based on environment configuration."""
    use_r2 = getattr(settings, 'USE_R2_STORAGE', False) or getattr(settings, 'USE_S3_STORAGE', False)
    if use_r2:
        return R2MediaStorage()
    return FileSystemStorage()
