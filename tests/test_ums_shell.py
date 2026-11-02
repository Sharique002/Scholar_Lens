"""Tests for LPU UMS-style institutional shell."""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

SIDEBAR = [
    'dashboard:home',
    'papers:list',
    'projects:list',
    'researchers:list',
    'collaboration:list',
    'search:search',
]  # Task 4 appends 'facilities:list'


class UmsShellTest(TestCase):
    def setUp(self):
        self.student = User.objects.create_user('stu', password='x')
        self.staff = User.objects.create_user('boss', password='x', is_staff=True)

    def test_sidebar_links(self):
        self.client.force_login(self.student)
        r = self.client.get(reverse('dashboard:home'))
        self.assertContains(r, 'class="ums-sidebar"')
        self.assertContains(r, 'class="ums-nav-link', count=len(SIDEBAR))
        for name in SIDEBAR:
            self.assertContains(r, f'href="{reverse(name)}"')
        self.assertContains(r, 'top-marquee-strip')

    def test_active_section_highlighted(self):
        self.client.force_login(self.student)
        r = self.client.get(reverse('papers:upload'))  # a sub-page still lights up "Papers"
        self.assertContains(r, f'href="{reverse("papers:list")}" class="ums-nav-link is-active"')

    def test_account_menu_and_bell(self):
        self.client.force_login(self.student)
        r = self.client.get(reverse('dashboard:home'))
        for name in [
            'accounts:profile',
            'researchers:edit_profile',
            'dashboard:settings',
            'accounts:change_password',
            'accounts:logout',
            'dashboard:notifications',
        ]:
            self.assertContains(r, f'href="{reverse(name)}"')

    def test_guest_pages_have_no_sidebar(self):
        for name in ['dashboard:landing', 'accounts:login', 'accounts:register']:
            self.assertNotContains(self.client.get(reverse(name)), 'class="ums-sidebar"')

    def test_admin_link_only_for_staff(self):
        self.client.force_login(self.student)
        self.assertNotContains(self.client.get(reverse('dashboard:home')), 'Admin Panel')
        self.client.force_login(self.staff)
        self.assertContains(self.client.get(reverse('dashboard:home')), 'Admin Panel')

    def test_fake_ratings_footer_removed(self):
        self.assertNotContains(self.client.get(reverse('dashboard:landing')), 'PUBLIC RATINGS')

    def test_dashboard_quick_actions(self):
        self.client.force_login(self.student)
        r = self.client.get(reverse('dashboard:home'))
        self.assertContains(r, 'class="ums-quick-actions"')
        for name in [
            'papers:upload',
            'projects:create',
            'collaboration:recommendations',
            'search:search',
        ]:  # Task 4 adds 'facilities:list'
            self.assertContains(r, f'href="{reverse(name)}" class="ums-quick-action"')
        self.assertContains(r, 'Latest Research &amp; Emerging Technologies')
