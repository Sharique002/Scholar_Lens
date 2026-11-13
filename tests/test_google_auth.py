"""Comprehensive Automated Test Suite for Google OAuth2 / OpenID Connect Authentication.

Covers all Phase 9 verification requirements:
  - First-time login and user account provisioning
  - Existing user recognized by google_sub
  - Existing user linked by email
  - Duplicate account prevention
  - ID token verification (issuer, audience, expiry)
  - State mismatch / CSRF defense
  - User cancellation handling
  - Open redirect prevention
  - Session preservation across requests
  - Logout session invalidation
  - Dynamic redirect URI resolution
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import UserProfile
from accounts.google_auth import (
    is_google_auth_configured,
    get_redirect_uri,
    get_google_auth_url,
    get_or_create_google_user,
    verify_id_token_server_side,
)
from dashboard.models import ResearchActivity


class GoogleAuthUnitTests(TestCase):
    def test_is_google_auth_configured(self):
        with override_settings(GOOGLE_CLIENT_ID='', GOOGLE_CLIENT_SECRET=''):
            self.assertFalse(is_google_auth_configured())
        with override_settings(GOOGLE_CLIENT_ID='my-client-id', GOOGLE_CLIENT_SECRET=''):
            self.assertFalse(is_google_auth_configured())
        with override_settings(GOOGLE_CLIENT_ID='my-client-id', GOOGLE_CLIENT_SECRET='my-secret'):
            self.assertTrue(is_google_auth_configured())

    def test_first_login_creates_user_with_google_sub(self):
        user_info = {
            'sub': 'google_unique_sub_101',
            'email': 'dr_new@scholar.edu',
            'name': 'Dr. New Scholar',
            'given_name': 'New',
            'family_name': 'Scholar',
            'picture': 'https://lh3.googleusercontent.com/photo.jpg',
        }
        user, created = get_or_create_google_user(user_info)
        self.assertTrue(created)
        self.assertEqual(user.email, 'dr_new@scholar.edu')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'Scholar')
        self.assertFalse(user.has_usable_password())
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.google_sub, 'google_unique_sub_101')
        self.assertEqual(user.profile.role, 'STUDENT')
        self.assertTrue(hasattr(user, 'researcher_profile'))

    def test_returning_login_recognized_by_google_sub(self):
        # Create user with existing google_sub
        existing = User.objects.create_user(
            username='returning_scholar',
            email='returning@scholar.edu',
            first_name='Returning',
            last_name='User'
        )
        existing.profile.google_sub = 'google_unique_sub_202'
        existing.profile.save()

        user_info = {
            'sub': 'google_unique_sub_202',
            'email': 'returning_new_email@scholar.edu',  # Even if email changed
            'name': 'Returning User',
            'given_name': 'Returning',
            'family_name': 'User',
        }
        user, created = get_or_create_google_user(user_info)
        self.assertFalse(created)
        self.assertEqual(user.id, existing.id)
        self.assertEqual(User.objects.filter(username__startswith='returning').count(), 1)

    def test_returning_login_by_email_links_google_sub(self):
        # Existing user registered via email without Google sub
        existing = User.objects.create_user(
            username='email_user',
            email='preexisting@scholar.edu',
            first_name='Pre',
            last_name='Existing'
        )
        self.assertIsNone(existing.profile.google_sub)

        user_info = {
            'sub': 'google_unique_sub_303',
            'email': 'preexisting@scholar.edu',
            'name': 'Pre Existing',
            'given_name': 'Pre',
            'family_name': 'Existing',
        }
        user, created = get_or_create_google_user(user_info)
        self.assertFalse(created)
        self.assertEqual(user.id, existing.id)
        existing.profile.refresh_from_db()
        self.assertEqual(existing.profile.google_sub, 'google_unique_sub_303')

    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_verify_id_token_google_auth_success(self, mock_verify):
        mock_verify.return_value = {
            'iss': 'https://accounts.google.com',
            'aud': 'expected-client-id',
            'sub': 'google_sub_verified_lib',
            'email': 'lib_verified@google.com',
            'email_verified': True,
            'exp': 9999999999,
        }
        claims = verify_id_token_server_side('real_jwt_token', 'expected-client-id')
        self.assertEqual(claims['sub'], 'google_sub_verified_lib')
        self.assertEqual(claims['email'], 'lib_verified@google.com')
        self.assertTrue(mock_verify.called)

    @patch('accounts.google_auth.requests.get')
    def test_verify_id_token_server_side_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'iss': 'https://accounts.google.com',
            'aud': 'expected-client-id',
            'sub': 'google_sub_valid',
            'email': 'valid@google.com',
            'email_verified': 'true',
            'exp': '9999999999',  # Far future
        }
        mock_get.return_value = mock_resp

        claims = verify_id_token_server_side('dummy_id_token', 'expected-client-id')
        self.assertEqual(claims['sub'], 'google_sub_valid')
        self.assertEqual(claims['email'], 'valid@google.com')

    @patch('accounts.google_auth.requests.get')
    def test_verify_id_token_audience_mismatch_rejected(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'iss': 'https://accounts.google.com',
            'aud': 'attacker-client-id',
            'sub': 'google_sub_valid',
            'email': 'valid@google.com',
            'email_verified': 'true',
        }
        mock_get.return_value = mock_resp

        with self.assertRaises(ValueError) as ctx:
            verify_id_token_server_side('dummy_id_token', 'expected-client-id')
        self.assertIn("audience mismatch", str(ctx.exception))

    @patch('accounts.google_auth.requests.get')
    def test_verify_id_token_unverified_email_rejected(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'iss': 'https://accounts.google.com',
            'aud': 'expected-client-id',
            'sub': 'google_sub_valid',
            'email': 'unverified@google.com',
            'email_verified': 'false',
            'exp': 9999999999,
        }
        mock_get.return_value = mock_resp

        with self.assertRaises(ValueError) as ctx:
            verify_id_token_server_side('dummy_id_token', 'expected-client-id')
        self.assertIn("not verified", str(ctx.exception))

    @patch('accounts.google_auth.requests.get')
    def test_verify_id_token_invalid_issuer_rejected(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'iss': 'https://attacker-identity-provider.com',
            'aud': 'expected-client-id',
            'sub': 'google_sub_valid',
            'email': 'user@example.com',
            'email_verified': True,
            'exp': 9999999999,
        }
        mock_get.return_value = mock_resp

        with self.assertRaises(ValueError) as ctx:
            verify_id_token_server_side('dummy_id_token', 'expected-client-id')
        self.assertIn("Invalid ID token issuer", str(ctx.exception))

    @patch('accounts.google_auth.requests.get')
    def test_verify_id_token_expired_rejected(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'iss': 'https://accounts.google.com',
            'aud': 'expected-client-id',
            'sub': 'google_sub_valid',
            'email': 'user@example.com',
            'email_verified': True,
            'exp': 1000000000,  # Far past timestamp
        }
        mock_get.return_value = mock_resp

        with self.assertRaises(ValueError) as ctx:
            verify_id_token_server_side('dummy_id_token', 'expected-client-id')
        self.assertIn("expired", str(ctx.exception))

    @patch('accounts.google_auth.requests.get')
    def test_verify_id_token_missing_exp_rejected(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'iss': 'https://accounts.google.com',
            'aud': 'expected-client-id',
            'sub': 'google_sub_valid',
            'email': 'user@example.com',
            'email_verified': True,
        }
        mock_get.return_value = mock_resp

        with self.assertRaises(ValueError) as ctx:
            verify_id_token_server_side('dummy_id_token', 'expected-client-id')
        self.assertIn("missing required 'exp'", str(ctx.exception))

    def test_conflicting_google_subject_rejected(self):
        # Create user already linked to sub A
        user = User.objects.create_user('conflict_user', email='conflict@example.com')
        user.profile.google_sub = 'google_sub_A'
        user.profile.save()

        # Attempt to link user to sub B with same email
        with self.assertRaises(ValueError) as ctx:
            get_or_create_google_user({
                'sub': 'google_sub_B',
                'email': 'conflict@example.com',
                'name': 'Conflict User'
            })
        self.assertIn("already linked to a different Google identity", str(ctx.exception))

    @patch('accounts.google_auth.requests.post')
    def test_failed_token_exchange_handled(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = "invalid_grant"
        mock_post.return_value = mock_resp

        from accounts.google_auth import exchange_code_for_user_info
        with self.assertRaises(ValueError) as ctx:
            exchange_code_for_user_info('bad_code', 'http://localhost:8000/callback/')
        self.assertIn("Failed to exchange authorization code", str(ctx.exception))

    @patch('accounts.google_auth.verify_id_token_server_side', side_effect=ValueError("Invalid signature"))
    @patch('accounts.google_auth.requests.post')
    def test_invalid_id_token_with_access_token_fails_fast(self, mock_post, mock_verify):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'id_token': 'tampered_id_token',
            'access_token': 'valid_access_token',
        }
        mock_post.return_value = mock_resp

        from accounts.google_auth import exchange_code_for_user_info
        with self.assertRaises(ValueError) as ctx:
            exchange_code_for_user_info('test_code', 'http://localhost:8000/callback/')
        self.assertIn("Invalid signature", str(ctx.exception))


class GoogleAuthViewTests(TestCase):
    def setUp(self):
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')
        self.google_login_url = reverse('accounts:google_login')
        self.google_callback_url = reverse('accounts:google_callback')
        self.google_mock_url = reverse('accounts:google_mock')

    def test_login_and_register_pages_render_google_buttons(self):
        resp = self.client.get(self.login_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Sign In with Google')

        resp2 = self.client.get(reverse('accounts:register'))
        self.assertEqual(resp2.status_code, 200)
        self.assertContains(resp2, 'Sign Up with Google')

    @override_settings(GOOGLE_CLIENT_ID='test-client-id', GOOGLE_CLIENT_SECRET='test-secret')
    def test_google_login_redirects_to_google_with_state(self):
        resp = self.client.get(self.google_login_url)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('https://accounts.google.com/o/oauth2/v2/auth'))
        self.assertIn('client_id=test-client-id', resp.url)
        self.assertIn('google_oauth_state', self.client.session)
        self.assertIn('google_oauth_redirect_uri', self.client.session)

    def test_user_cancelled_login(self):
        resp = self.client.get(f"{self.google_callback_url}?error=access_denied")
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, self.login_url)

    def test_csrf_state_mismatch_rejected(self):
        session = self.client.session
        session['google_oauth_state'] = 'genuine_state_abc'
        session.save()

        resp = self.client.get(f"{self.google_callback_url}?code=fake_code&state=forged_state_xyz")
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, self.login_url)

    @override_settings(GOOGLE_CLIENT_ID='test-client-id', GOOGLE_CLIENT_SECRET='test-secret')
    @patch('accounts.views.exchange_code_for_user_info')
    def test_state_replay_rejected(self, mock_exchange):
        mock_exchange.return_value = {
            'sub': 'google_replay_sub',
            'email': 'replay@gmail.com',
            'name': 'Replay User',
        }

        session = self.client.session
        session['google_oauth_state'] = 'single_use_state_999'
        session.save()

        # First use succeeds
        resp1 = self.client.get(f"{self.google_callback_url}?code=code1&state=single_use_state_999")
        self.assertEqual(resp1.status_code, 302)
        self.assertRedirects(resp1, reverse('dashboard:home'))

        self.client.logout()

        # Second use (replay with same state) must be rejected because state was popped
        resp2 = self.client.get(f"{self.google_callback_url}?code=code2&state=single_use_state_999")
        self.assertEqual(resp2.status_code, 302)
        self.assertRedirects(resp2, self.login_url)

    @override_settings(GOOGLE_CLIENT_ID='test-client-id', GOOGLE_CLIENT_SECRET='test-secret')
    @patch('accounts.views.exchange_code_for_user_info')
    def test_google_callback_success_and_session_persistence(self, mock_exchange):
        mock_exchange.return_value = {
            'sub': 'google_1234567890',
            'email': 'shariquehussain03@gmail.com',
            'name': 'Sharique Hussain',
            'given_name': 'Sharique',
            'family_name': 'Hussain',
        }

        session = self.client.session
        session['google_oauth_state'] = 'valid_state_123'
        session['google_oauth_redirect_uri'] = 'http://testserver/accounts/google/callback/'
        session.save()

        resp = self.client.get(f"{self.google_callback_url}?code=valid_auth_code&state=valid_state_123")
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('dashboard:home'))

        # Verify user is authenticated in session
        user = User.objects.get(email='shariquehussain03@gmail.com')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)
        self.assertEqual(user.profile.google_sub, 'google_1234567890')

        # Verify session persists across subsequent request (refresh)
        dashboard_resp = self.client.get(reverse('dashboard:home'))
        self.assertEqual(dashboard_resp.status_code, 200)

        # Verify logout invalidates the session
        logout_resp = self.client.get(self.logout_url)
        self.assertEqual(logout_resp.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)

    @override_settings(GOOGLE_CLIENT_ID='test-client-id', GOOGLE_CLIENT_SECRET='test-secret')
    @patch('accounts.views.exchange_code_for_user_info')
    def test_open_redirect_attack_neutralized(self, mock_exchange):
        mock_exchange.return_value = {
            'sub': 'google_open_red_sub',
            'email': 'test_redirect@gmail.com',
            'name': 'Test User',
        }

        session = self.client.session
        session['google_oauth_state'] = 'state_open_red'
        session['google_oauth_next'] = 'https://malicious-phishing-site.com/steal'
        session.save()

        resp = self.client.get(f"{self.google_callback_url}?code=valid_code&state=state_open_red")
        self.assertEqual(resp.status_code, 302)
        # Sanitized: redirects to safe internal dashboard instead of external attacker site
        self.assertRedirects(resp, reverse('dashboard:home'))
