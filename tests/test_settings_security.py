"""
Tests for Scholar Lens production settings security validation.
Verifies fail-closed constraints for SECRET_KEY, ALLOWED_HOSTS, and DATABASE_URL.
"""
import os
import runpy
from pathlib import Path
from unittest import TestCase, mock
from django.core.exceptions import ImproperlyConfigured

SETTINGS_PATH = str(Path(__file__).resolve().parent.parent / 'scholar_lens' / 'settings.py')

class SettingsSecurityTests(TestCase):
    """
    Test that scholar_lens/settings.py enforces strict production security invariants
    when DEBUG is False or in production environments.
    """

    def _eval_settings(self, env_overrides):
        """Helper to execute settings.py with an isolated environment."""
        # Clean environment without any .env leakage for critical variables
        clean_env = {
            'PATH': os.environ.get('PATH', ''),
            'SYSTEMROOT': os.environ.get('SYSTEMROOT', ''),
        }
        clean_env.update(env_overrides)
        with mock.patch.dict(os.environ, clean_env, clear=True):
            return runpy.run_path(SETTINGS_PATH)

    def test_debug_true_allows_insecure_defaults(self):
        """In development (DEBUG=True), default dev secret key and SQLite are permitted."""
        settings = self._eval_settings({
            'DEBUG': 'True',
            'SECRET_KEY': '',
            'ALLOWED_HOSTS': 'localhost',
        })
        self.assertTrue(settings['DEBUG'])
        self.assertIn('django-insecure', settings['SECRET_KEY'])
        self.assertEqual(settings['DATABASES']['default']['ENGINE'], 'django.db.backends.sqlite3')

    def test_debug_false_missing_secret_key_raises(self):
        """In production (DEBUG=False), missing SECRET_KEY must raise ImproperlyConfigured."""
        with self.assertRaises(ImproperlyConfigured) as ctx:
            self._eval_settings({
                'DEBUG': 'False',
                'SECRET_KEY': '',
            })
        self.assertIn("SECRET_KEY must be configured", str(ctx.exception))

    def test_debug_false_insecure_prefix_raises(self):
        """In production (DEBUG=False), SECRET_KEY starting with django-insecure must raise ImproperlyConfigured."""
        with self.assertRaises(ImproperlyConfigured) as ctx:
            self._eval_settings({
                'DEBUG': 'False',
                'SECRET_KEY': 'django-insecure-this-is-a-development-key-that-is-too-weak',
            })
        self.assertIn("cryptographically secure key", str(ctx.exception))

    def test_debug_false_short_secret_key_raises(self):
        """In production (DEBUG=False), SECRET_KEY shorter than 32 characters must raise ImproperlyConfigured."""
        with self.assertRaises(ImproperlyConfigured) as ctx:
            self._eval_settings({
                'DEBUG': 'False',
                'SECRET_KEY': 'too-short-production-key',
            })
        self.assertIn("at least 32 characters", str(ctx.exception))

    def test_debug_false_wildcard_allowed_hosts_raises(self):
        """In production (DEBUG=False), '*' in ALLOWED_HOSTS must raise ImproperlyConfigured."""
        with self.assertRaises(ImproperlyConfigured) as ctx:
            self._eval_settings({
                'DEBUG': 'False',
                'SECRET_KEY': 'a' * 50,
                'ALLOWED_HOSTS': '*',
                'DATABASE_URL': 'postgres://user:pass@localhost:5432/db',
            })
        self.assertIn("Wildcard '*' in ALLOWED_HOSTS is strictly forbidden", str(ctx.exception))

    def test_debug_false_empty_allowed_hosts_raises(self):
        """In production (DEBUG=False), empty ALLOWED_HOSTS must raise ImproperlyConfigured."""
        with self.assertRaises(ImproperlyConfigured) as ctx:
            self._eval_settings({
                'DEBUG': 'False',
                'SECRET_KEY': 'a' * 50,
                'ALLOWED_HOSTS': '',
                'DATABASE_URL': 'postgres://user:pass@localhost:5432/db',
            })
        self.assertIn("ALLOWED_HOSTS must be explicitly defined", str(ctx.exception))

    def test_debug_false_sqlite_fallback_raises(self):
        """In production (DEBUG=False), attempting to fall back to SQLite must raise ImproperlyConfigured."""
        with self.assertRaises(ImproperlyConfigured) as ctx:
            self._eval_settings({
                'DEBUG': 'False',
                'SECRET_KEY': 'a' * 50,
                'ALLOWED_HOSTS': 'example.com',
                'DATABASE_URL': '',
                'USE_POSTGRES': 'False',
            })
        self.assertIn("SQLite fallback is strictly forbidden in production", str(ctx.exception))

    def test_debug_false_valid_production_passes(self):
        """With DEBUG=False and proper production env vars, settings evaluate successfully."""
        settings = self._eval_settings({
            'DEBUG': 'False',
            'SECRET_KEY': 'p' * 50,
            'ALLOWED_HOSTS': 'scholarlens.example.com, api.scholarlens.example.com',
            'DATABASE_URL': 'postgres://user:pass@localhost:5432/scholar_lens_prod',
            'RENDER_EXTERNAL_HOSTNAME': 'scholar-lens.onrender.com',
        })
        self.assertFalse(settings['DEBUG'])
        self.assertIn('scholarlens.example.com', settings['ALLOWED_HOSTS'])
        self.assertIn('scholar-lens.onrender.com', settings['ALLOWED_HOSTS'])
        self.assertIn('https://scholar-lens.onrender.com', settings['CSRF_TRUSTED_ORIGINS'])
        self.assertEqual(settings['DATABASES']['default']['ENGINE'], 'django.db.backends.postgresql')

    def test_allowed_hosts_wildcard_subdomain_normalization(self):
        """Wildcard subdomain '*.example.com' is normalized to '.example.com' per Django conventions."""
        settings = self._eval_settings({
            'DEBUG': 'True',
            'ALLOWED_HOSTS': '*.scholarlens.org, example.com',
        })
        self.assertIn('.scholarlens.org', settings['ALLOWED_HOSTS'])
        self.assertIn('example.com', settings['ALLOWED_HOSTS'])
        self.assertNotIn('*.scholarlens.org', settings['ALLOWED_HOSTS'])

    def test_is_serverless_flag(self):
        """VERCEL environment variable activates IS_SERVERLESS."""
        settings = self._eval_settings({
            'DEBUG': 'True',
            'VERCEL': '1',
        })
        self.assertTrue(settings['IS_SERVERLESS'])
