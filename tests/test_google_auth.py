"""Tests for Google OAuth2 / SSO Authentication."""
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.google_auth import (
    is_google_auth_configured,
    get_google_auth_url,
    get_or_create_google_user,
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

    def test_get_or_create_google_user_new_user(self):
        user_info = {
            'email': 'new_scholar@example.edu',
            'name': 'Dr. Scholar Test',
            'given_name': 'Scholar',
            'family_name': 'Test',
            'sub': 'google_sub_123',
        }
        user, created = get_or_create_google_user(user_info)
        self.assertTrue(created)
        self.assertEqual(user.email, 'new_scholar@example.edu')
        self.assertEqual(user.first_name, 'Scholar')
        self.assertEqual(user.last_name, 'Test')
        self.assertFalse(user.has_usable_password())
        self.assertTrue(hasattr(user, 'profile'))
        self.assertTrue(hasattr(user, 'researcher_profile'))

    def test_get_or_create_google_user_existing_user(self):
        existing = User.objects.create_user(
            username='existing_scholar',
            email='existing@example.edu',
            first_name='Existing',
            last_name='User'
        )
        user_info = {
            'email': 'existing@example.edu',
            'name': 'Existing User Updated',
            'given_name': 'Existing',
            'family_name': 'User',
            'sub': 'google_sub_456',
        }
        user, created = get_or_create_google_user(user_info)
        self.assertFalse(created)
        self.assertEqual(user.id, existing.id)


class GoogleAuthViewTests(TestCase):
    def setUp(self):
        self.login_url = reverse('accounts:login')
        self.google_login_url = reverse('accounts:google_login')
        self.google_callback_url = reverse('accounts:google_callback')
        self.google_mock_url = reverse('accounts:google_mock')

    def test_login_page_renders_google_button(self):
        resp = self.client.get(self.login_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Sign In with Google')
        self.assertContains(resp, self.google_login_url)

    def test_register_page_renders_google_button(self):
        resp = self.client.get(reverse('accounts:register'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Sign Up with Google')
        self.assertContains(resp, self.google_login_url)

    @override_settings(GOOGLE_CLIENT_ID='test-client-id', GOOGLE_CLIENT_SECRET='test-secret')
    def test_google_login_redirects_to_google(self):
        resp = self.client.get(self.google_login_url)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('https://accounts.google.com/o/oauth2/v2/auth'))
        self.assertIn('client_id=test-client-id', resp.url)
        self.assertIn('google_oauth_state', self.client.session)

    @override_settings(GOOGLE_CLIENT_ID='', GOOGLE_CLIENT_SECRET='', DEBUG=True)
    def test_google_login_unconfigured_redirects_to_mock_in_debug(self):
        resp = self.client.get(self.google_login_url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/accounts/google/mock/', resp.url)

    def test_google_callback_with_error(self):
        resp = self.client.get(f"{self.google_callback_url}?error=access_denied")
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, self.login_url)

    def test_google_callback_state_mismatch(self):
        session = self.client.session
        session['google_oauth_state'] = 'correct_state'
        session.save()

        resp = self.client.get(f"{self.google_callback_url}?code=sample_code&state=wrong_state")
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, self.login_url)

    @override_settings(GOOGLE_CLIENT_ID='test-client-id', GOOGLE_CLIENT_SECRET='test-secret')
    @patch('accounts.views.exchange_code_for_user_info')
    def test_google_callback_success_login(self, mock_exchange):
        mock_exchange.return_value = {
            'email': 'shariquehussain03@gmail.com',
            'name': 'Sharique Hussain',
            'given_name': 'Sharique',
            'family_name': 'Hussain',
            'sub': '10987654321',
        }

        session = self.client.session
        session['google_oauth_state'] = 'valid_state_123'
        session.save()

        resp = self.client.get(f"{self.google_callback_url}?code=valid_code&state=valid_state_123")
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('dashboard:home'))

        # Verify user is logged in
        user = User.objects.get(email='shariquehussain03@gmail.com')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)
        # Verify login activity recorded
        self.assertTrue(ResearchActivity.objects.filter(user=user, activity_type='LOGIN').exists())

    @override_settings(DEBUG=True)
    def test_google_mock_login_flow(self):
        resp = self.client.post(self.google_mock_url, {
            'email': 'mock_faculty@google.com',
            'name': 'Prof. Mock Researcher',
            'role': 'FACULTY',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('dashboard:home'))

        user = User.objects.get(email='mock_faculty@google.com')
        self.assertEqual(user.profile.role, 'FACULTY')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)
