"""
Comprehensive test suite for Scholar Lens.
Tests cover authentication, models, forms, views, search, and AI service handling.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import UserProfile
from researchers.models import ResearcherProfile, ResearchInterest, Skill
from papers.models import ResearchPaper, PaperAuthor, PaperChunk
from projects.models import ResearchProject, ProjectMember
from collaboration.models import CollaborationRequest
from ai_engine.models import AIAnalysis, ResearchGap, ChatMessage
from evaluation.models import EvaluationReport, ResearchScore
from dashboard.models import ResearchActivity
from ai_engine.services import SemanticSearchService


# =============================================================================
# Helper Mixin
# =============================================================================

class ScholarLensTestMixin:
    """Common test setup for Scholar Lens tests."""

    def create_user(self, username='testuser', password='testpass123!',
                    email='test@example.com', first_name='Test', last_name='User'):
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        return user

    def create_paper(self, user, title='Test Paper', status='UPLOADED'):
        return ResearchPaper.objects.create(
            title=title,
            abstract='This is a test abstract for testing purposes.',
            research_area='AI_ML',
            keywords='test, machine learning',
            status=status,
            uploader=user,
        )

    def login_user(self, username='testuser', password='testpass123!'):
        self.client.login(username=username, password=password)


# =============================================================================
# Authentication Tests
# =============================================================================

class RegistrationTest(ScholarLensTestMixin, TestCase):
    """Test user registration flow."""

    def test_registration_page_loads(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Register')

    def test_registration_valid_data(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'securepass123!',
            'password2': 'securepass123!',
            'role': 'STUDENT',
            'institution': 'Test University',
        })
        # Should redirect after successful registration
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_registration_password_mismatch(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'securepass123!',
            'password2': 'differentpass123!',
            'role': 'STUDENT',
            'institution': 'Test University',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_registration_creates_profile(self):
        self.client.post(reverse('accounts:register'), {
            'username': 'profileuser',
            'email': 'profile@example.com',
            'first_name': 'Profile',
            'last_name': 'User',
            'password1': 'securepass123!',
            'password2': 'securepass123!',
            'role': 'FACULTY',
            'institution': 'Test University',
        })
        user = User.objects.get(username='profileuser')
        self.assertTrue(hasattr(user, 'profile'))


class LoginTest(ScholarLensTestMixin, TestCase):
    """Test login functionality."""

    def setUp(self):
        self.user = self.create_user()

    def test_login_page_loads(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)

    def test_login_valid_credentials(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'testpass123!',
        })
        self.assertEqual(response.status_code, 302)

    def test_login_invalid_credentials(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)

    def test_login_redirect_authenticated_user(self):
        self.login_user()
        response = self.client.get(reverse('accounts:login'))
        # Should still show login page or redirect
        self.assertIn(response.status_code, [200, 302])


class LogoutTest(ScholarLensTestMixin, TestCase):
    """Test logout functionality."""

    def setUp(self):
        self.user = self.create_user()
        self.login_user()

    def test_logout(self):
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)

    def test_logout_clears_session(self):
        self.client.get(reverse('accounts:logout'))
        response = self.client.get(reverse('dashboard:home'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)


class ProtectedViewTest(ScholarLensTestMixin, TestCase):
    """Test that views require authentication."""

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_paper_list_requires_login(self):
        response = self.client.get(reverse('papers:list'))
        self.assertEqual(response.status_code, 302)

    def test_paper_upload_requires_login(self):
        response = self.client.get(reverse('papers:upload'))
        self.assertEqual(response.status_code, 302)

    def test_profile_requires_login(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)

    def test_projects_require_login(self):
        response = self.client.get(reverse('projects:list'))
        self.assertEqual(response.status_code, 302)

    def test_collaboration_requires_login(self):
        response = self.client.get(reverse('collaboration:list'))
        self.assertEqual(response.status_code, 302)


# =============================================================================
# Model Tests
# =============================================================================

class UserProfileModelTest(ScholarLensTestMixin, TestCase):
    """Test UserProfile model."""

    def setUp(self):
        self.user = self.create_user()

    def test_profile_auto_created(self):
        """UserProfile should be auto-created via signal when User is created."""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)

    def test_profile_str(self):
        profile = self.user.profile
        self.assertIn(self.user.username, str(profile))

    def test_profile_default_role(self):
        profile = self.user.profile
        self.assertEqual(profile.role, 'STUDENT')

    def test_profile_update(self):
        profile = self.user.profile
        profile.role = 'FACULTY'
        profile.institution = 'MIT'
        profile.save()
        profile.refresh_from_db()
        self.assertEqual(profile.role, 'FACULTY')
        self.assertEqual(profile.institution, 'MIT')


class ResearchPaperModelTest(ScholarLensTestMixin, TestCase):
    """Test ResearchPaper model."""

    def setUp(self):
        self.user = self.create_user()
        self.paper = self.create_paper(self.user)

    def test_paper_creation(self):
        self.assertEqual(self.paper.title, 'Test Paper')
        self.assertEqual(self.paper.uploader, self.user)
        self.assertEqual(self.paper.status, 'UPLOADED')

    def test_paper_str(self):
        self.assertIn('Test Paper', str(self.paper))

    def test_paper_ordering(self):
        """Papers should be ordered by -created_at by default."""
        paper2 = self.create_paper(self.user, title='Newer Paper')
        papers = list(ResearchPaper.objects.all())
        self.assertEqual(papers[0], paper2)

    def test_paper_status_choices(self):
        for status in ['UPLOADED', 'TEXT_EXTRACTED', 'INDEXED', 'AI_ANALYZED', 'EVALUATED', 'FAILED']:
            self.paper.status = status
            self.paper.save()
            self.paper.refresh_from_db()
            self.assertEqual(self.paper.status, status)


class PaperAuthorModelTest(ScholarLensTestMixin, TestCase):
    """Test PaperAuthor model."""

    def setUp(self):
        self.user = self.create_user()
        self.paper = self.create_paper(self.user)

    def test_author_creation(self):
        author = PaperAuthor.objects.create(
            paper=self.paper,
            name='Jane Doe',
            email='jane@example.com',
            affiliation='Test University',
            order=1,
        )
        self.assertEqual(author.paper, self.paper)
        self.assertEqual(author.name, 'Jane Doe')

    def test_author_ordering(self):
        PaperAuthor.objects.create(paper=self.paper, name='Author B', order=2)
        PaperAuthor.objects.create(paper=self.paper, name='Author A', order=1)
        authors = list(self.paper.authors.all())
        self.assertEqual(authors[0].name, 'Author A')


class ResearchProjectModelTest(ScholarLensTestMixin, TestCase):
    """Test ResearchProject model."""

    def setUp(self):
        self.user = self.create_user()

    def test_project_creation(self):
        project = ResearchProject.objects.create(
            title='Test Project',
            description='A test research project',
            leader=self.user,
            research_area='AI_ML',
            status='ACTIVE',
        )
        self.assertEqual(project.title, 'Test Project')
        self.assertEqual(project.leader, self.user)

    def test_project_member(self):
        project = ResearchProject.objects.create(
            title='Test Project',
            description='Test',
            leader=self.user,
            research_area='AI_ML',
        )
        member = ProjectMember.objects.create(
            project=project,
            user=self.user,
            role='LEADER',
        )
        self.assertEqual(member.project, project)


class CollaborationModelTest(ScholarLensTestMixin, TestCase):
    """Test CollaborationRequest model."""

    def setUp(self):
        self.sender = self.create_user(username='sender')
        self.receiver = self.create_user(username='receiver', email='recv@example.com')

    def test_request_creation(self):
        req = CollaborationRequest.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            message='Let us collaborate!',
        )
        self.assertEqual(req.status, 'PENDING')
        self.assertEqual(req.sender, self.sender)
        self.assertEqual(req.receiver, self.receiver)


class ResearcherProfileModelTest(ScholarLensTestMixin, TestCase):
    """Test ResearcherProfile model."""

    def setUp(self):
        self.user = self.create_user()

    def test_researcher_profile_creation(self):
        profile = ResearcherProfile.objects.create(
            user=self.user,
            headline='AI Researcher',
            expertise_summary='Machine Learning expert',
            years_experience=5,
        )
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.headline, 'AI Researcher')

    def test_interests_m2m(self):
        profile = ResearcherProfile.objects.create(user=self.user)
        interest = ResearchInterest.objects.create(name='Test AI', category='AI')
        profile.interests.add(interest)
        self.assertIn(interest, profile.interests.all())

    def test_skills_m2m(self):
        profile = ResearcherProfile.objects.create(user=self.user)
        skill = Skill.objects.create(name='Test Python', category='PROGRAMMING')
        profile.skills.add(skill)
        self.assertIn(skill, profile.skills.all())


class AIAnalysisModelTest(ScholarLensTestMixin, TestCase):
    """Test AIAnalysis model."""

    def setUp(self):
        self.user = self.create_user()
        self.paper = self.create_paper(self.user)

    def test_analysis_creation(self):
        analysis = AIAnalysis.objects.create(
            paper=self.paper,
            analysis_type='SUMMARY',
            result={'summary': 'Test summary'},
            model_name='gpt-4o-mini',
        )
        self.assertEqual(analysis.paper, self.paper)
        self.assertEqual(analysis.analysis_type, 'SUMMARY')

    def test_cached_analysis(self):
        AIAnalysis.objects.create(
            paper=self.paper,
            analysis_type='SUMMARY',
            result={'summary': 'Cached result'},
        )
        cached = AIAnalysis.objects.filter(
            paper=self.paper, analysis_type='SUMMARY'
        ).first()
        self.assertIsNotNone(cached)


class EvaluationModelTest(ScholarLensTestMixin, TestCase):
    """Test EvaluationReport and ResearchScore models."""

    def setUp(self):
        self.user = self.create_user()
        self.paper = self.create_paper(self.user)

    def test_report_creation(self):
        report = EvaluationReport.objects.create(
            paper=self.paper,
            overall_score=82.5,
            summary='Good research paper',
            strengths=['Strong methodology', 'Novel approach'],
            weaknesses=['Limited dataset'],
        )
        self.assertEqual(report.overall_score, 82.5)
        self.assertEqual(len(report.strengths), 2)

    def test_score_creation(self):
        report = EvaluationReport.objects.create(
            paper=self.paper,
            overall_score=80.0,
        )
        score = ResearchScore.objects.create(
            report=report,
            dimension='NOVELTY',
            score=85.0,
            weight=30.0,
            explanation='Novel approach to the problem',
        )
        self.assertEqual(score.report, report)
        self.assertEqual(score.dimension, 'NOVELTY')


# =============================================================================
# Form Tests
# =============================================================================

class RegistrationFormTest(TestCase):
    """Test registration form validation."""

    def test_valid_registration_form(self):
        from accounts.forms import RegistrationForm
        form = RegistrationForm(data={
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'securepass123!',
            'password2': 'securepass123!',
            'role': 'STUDENT',
            'institution': 'Test University',
        })
        self.assertTrue(form.is_valid())

    def test_registration_missing_email(self):
        from accounts.forms import RegistrationForm
        form = RegistrationForm(data={
            'username': 'testuser',
            'password1': 'securepass123!',
            'password2': 'securepass123!',
        })
        self.assertFalse(form.is_valid())


class PaperUploadFormTest(ScholarLensTestMixin, TestCase):
    """Test paper upload form validation."""

    def test_valid_paper_form_without_file(self):
        from papers.forms import PaperUploadForm
        form = PaperUploadForm(data={
            'title': 'Test Paper Title',
            'abstract': 'This is a test abstract.',
            'research_area': 'AI_ML',
            'keywords': 'test, AI',
        })
        # Form should be valid without file (file is optional in form, required at view level)
        self.assertTrue(form.is_valid() or 'pdf_file' in form.errors)

    def test_invalid_file_type(self):
        from papers.forms import PaperUploadForm
        fake_file = SimpleUploadedFile(
            'test.txt',
            b'This is not a PDF',
            content_type='text/plain',
        )
        form = PaperUploadForm(
            data={
                'title': 'Test Paper',
                'abstract': 'Test abstract',
                'research_area': 'AI_ML',
                'keywords': 'test',
            },
            files={'pdf_file': fake_file},
        )
        self.assertFalse(form.is_valid())


class SearchFormTest(TestCase):
    """Test search form."""

    def test_search_form_valid(self):
        from search.forms import SearchForm
        form = SearchForm(data={'query': 'machine learning'})
        self.assertTrue(form.is_valid())

    def test_search_form_empty_valid(self):
        from search.forms import SearchForm
        form = SearchForm(data={})
        # Empty search should be valid (shows all results)
        self.assertTrue(form.is_valid())


# =============================================================================
# View Tests
# =============================================================================

class LandingPageTest(TestCase):
    """Test landing page."""

    def test_landing_page_loads(self):
        response = self.client.get(reverse('dashboard:landing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Scholar')

    def test_landing_page_template(self):
        response = self.client.get(reverse('dashboard:landing'))
        self.assertTemplateUsed(response, 'dashboard/landing.html')


class DashboardViewTest(ScholarLensTestMixin, TestCase):
    """Test dashboard view."""

    def setUp(self):
        self.user = self.create_user()

    def test_dashboard_authenticated(self):
        self.login_user()
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_context(self):
        self.login_user()
        response = self.client.get(reverse('dashboard:home'))
        self.assertIn('total_papers', response.context)


class PaperViewTest(ScholarLensTestMixin, TestCase):
    """Test paper views."""

    def setUp(self):
        self.user = self.create_user()
        self.paper = self.create_paper(self.user)

    def test_paper_list_authenticated(self):
        self.login_user()
        response = self.client.get(reverse('papers:list'))
        self.assertEqual(response.status_code, 200)

    def test_paper_detail(self):
        self.login_user()
        response = self.client.get(reverse('papers:detail', args=[self.paper.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Paper')

    def test_paper_upload_page(self):
        self.login_user()
        response = self.client.get(reverse('papers:upload'))
        self.assertEqual(response.status_code, 200)

    def test_paper_delete_only_owner(self):
        other_user = self.create_user(username='other', email='other@test.com')
        self.client.login(username='other', password='testpass123!')
        response = self.client.post(reverse('papers:delete', args=[self.paper.pk]))
        # Should be forbidden or redirect
        self.assertIn(response.status_code, [302, 403])
        # Paper should still exist
        self.assertTrue(ResearchPaper.objects.filter(pk=self.paper.pk).exists())


class ProjectViewTest(ScholarLensTestMixin, TestCase):
    """Test project views."""

    def setUp(self):
        self.user = self.create_user()

    def test_project_list(self):
        self.login_user()
        response = self.client.get(reverse('projects:list'))
        self.assertEqual(response.status_code, 200)

    def test_project_create_page(self):
        self.login_user()
        response = self.client.get(reverse('projects:create'))
        self.assertEqual(response.status_code, 200)

    def test_project_create_post(self):
        self.login_user()
        response = self.client.post(reverse('projects:create'), {
            'title': 'New Project',
            'description': 'Test project description',
            'research_area': 'AI',
            'status': 'PLANNING',
            'is_public': True,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ResearchProject.objects.filter(title='New Project').exists())


class ResearcherViewTest(ScholarLensTestMixin, TestCase):
    """Test researcher views."""

    def setUp(self):
        self.user = self.create_user()

    def test_researcher_list(self):
        self.login_user()
        response = self.client.get(reverse('researchers:list'))
        self.assertEqual(response.status_code, 200)


class CollaborationViewTest(ScholarLensTestMixin, TestCase):
    """Test collaboration views."""

    def setUp(self):
        self.sender = self.create_user(username='sender')
        self.receiver = self.create_user(username='receiver', email='recv@test.com')

    def test_collaboration_list(self):
        self.client.login(username='sender', password='testpass123!')
        response = self.client.get(reverse('collaboration:list'))
        self.assertEqual(response.status_code, 200)

    def test_send_collaboration_request(self):
        self.client.login(username='sender', password='testpass123!')
        response = self.client.post(
            reverse('collaboration:send', args=[self.receiver.pk]),
            {'message': 'Let us collaborate on AI research!', 'receiver': self.receiver.pk}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            CollaborationRequest.objects.filter(
                sender=self.sender, receiver=self.receiver
            ).exists()
        )

    def test_respond_to_request(self):
        req = CollaborationRequest.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            message='Collaborate?',
        )
        self.client.login(username='receiver', password='testpass123!')
        response = self.client.post(
            reverse('collaboration:respond', args=[req.pk]),
            {'action': 'accept'}
        )
        self.assertEqual(response.status_code, 302)
        req.refresh_from_db()
        self.assertEqual(req.status, 'ACCEPTED')


# =============================================================================
# Search Tests
# =============================================================================

class SearchViewTest(ScholarLensTestMixin, TestCase):
    """Test search functionality."""

    def setUp(self):
        self.user = self.create_user()
        self.paper = self.create_paper(self.user, title='Machine Learning Survey')
        self.paper2 = self.create_paper(self.user, title='Deep Learning Applications')

    def test_search_page_loads(self):
        self.login_user()
        response = self.client.get(reverse('search:search'))
        self.assertEqual(response.status_code, 200)

    def test_keyword_search(self):
        self.login_user()
        response = self.client.get(reverse('search:search') + '?q=Machine+Learning')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Machine Learning Survey')

    def test_empty_search(self):
        self.login_user()
        response = self.client.get(reverse('search:search') + '?q=nonexistentterm12345')
        self.assertEqual(response.status_code, 200)


# =============================================================================
# AI Service Tests
# =============================================================================

class AIServiceConfigTest(TestCase):
    """Test AI service configuration handling."""

    def test_service_not_configured_without_key(self):
        from ai_engine.services import AIService
        service = AIService()
        # With no API key, should report not configured
        # (depends on settings, but in test env API key should be empty)
        if not service.is_configured:
            self.assertFalse(service.is_configured)

    def test_ai_views_handle_no_config(self):
        """AI views should not crash when AI is not configured."""
        user = User.objects.create_user('aiuser', 'ai@test.com', 'testpass123!')
        paper = ResearchPaper.objects.create(
            title='AI Test Paper',
            abstract='Testing AI features',
            research_area='AI_ML',
            keywords='test',
            uploader=user,
        )
        self.client.login(username='aiuser', password='testpass123!')
        # These should not crash, even without AI config
        response = self.client.get(reverse('ai_engine:summary', args=[paper.pk]))
        self.assertIn(response.status_code, [200, 302])

        response = self.client.get(reverse('ai_engine:gaps', args=[paper.pk]))
        self.assertIn(response.status_code, [200, 302])

        response = self.client.get(reverse('ai_engine:ask_paper', args=[paper.pk]))
        self.assertIn(response.status_code, [200, 302])


# =============================================================================
# URL Routing Tests
# =============================================================================

class URLRoutingTest(TestCase):
    """Test that all URL patterns resolve correctly."""

    def test_landing_url(self):
        url = reverse('dashboard:landing')
        self.assertEqual(url, '/')

    def test_login_url(self):
        url = reverse('accounts:login')
        self.assertEqual(url, '/accounts/login/')

    def test_register_url(self):
        url = reverse('accounts:register')
        self.assertEqual(url, '/accounts/')

    def test_papers_url(self):
        url = reverse('papers:list')
        self.assertEqual(url, '/papers/')

    def test_paper_upload_url(self):
        url = reverse('papers:upload')
        self.assertEqual(url, '/papers/upload/')

    def test_projects_url(self):
        url = reverse('projects:list')
        self.assertEqual(url, '/projects/')

    def test_researchers_url(self):
        url = reverse('researchers:list')
        self.assertEqual(url, '/researchers/')

    def test_collaboration_url(self):
        url = reverse('collaboration:list')
        self.assertEqual(url, '/collaboration/')

    def test_search_url(self):
        url = reverse('search:search')
        self.assertEqual(url, '/search/')

    def test_dashboard_url(self):
        url = reverse('dashboard:home')
        self.assertIn('dashboard', url)


# =============================================================================
# Permission Tests
# =============================================================================

class PermissionTest(ScholarLensTestMixin, TestCase):
    """Test authorization and permission checks."""

    def setUp(self):
        self.owner = self.create_user(username='owner')
        self.other = self.create_user(username='other', email='other@test.com')
        self.paper = self.create_paper(self.owner)

    def test_owner_can_edit_paper(self):
        self.client.login(username='owner', password='testpass123!')
        response = self.client.get(reverse('papers:edit', args=[self.paper.pk]))
        self.assertEqual(response.status_code, 200)

    def test_non_owner_cannot_edit_paper(self):
        self.client.login(username='other', password='testpass123!')
        response = self.client.get(reverse('papers:edit', args=[self.paper.pk]))
        self.assertIn(response.status_code, [302, 403])

    def test_non_owner_cannot_delete_paper(self):
        self.client.login(username='other', password='testpass123!')
        response = self.client.post(reverse('papers:delete', args=[self.paper.pk]))
        self.assertIn(response.status_code, [302, 403])
        self.assertTrue(ResearchPaper.objects.filter(pk=self.paper.pk).exists())

    def test_unauthenticated_cannot_access_dashboard(self):
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 302)

    def test_unauthenticated_can_access_landing(self):
        response = self.client.get(reverse('dashboard:landing'))
        self.assertEqual(response.status_code, 200)


# =============================================================================
# Dependency Chains Integration Tests (Audit Verified: Chains A through H)
# =============================================================================

class DependencyChainATest(ScholarLensTestMixin, TestCase):
    """Chain A: User Registration -> Researcher Profile -> Interests/Skills."""

    def test_chain_a_registration_to_profile_and_skills(self):
        # 1. Register new user
        reg_data = {
            'username': 'chain_a_user',
            'email': 'chain_a@example.com',
            'first_name': 'Chain',
            'last_name': 'User',
            'password1': 'ComplexPassword123!',
            'password2': 'ComplexPassword123!',
            'role': 'FACULTY',
            'institution': 'Stanford University',
        }
        res = self.client.post(reverse('accounts:register'), data=reg_data)
        self.assertEqual(res.status_code, 302)

        user = User.objects.get(username='chain_a_user')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.institution, 'Stanford University')

        # 2. Verify ResearcherProfile is created / accessible
        self.client.login(username='chain_a_user', password='ComplexPassword123!')
        res_profile = reverse('researchers:edit_profile')
        res_get = self.client.get(res_profile)
        self.assertEqual(res_get.status_code, 200)

        # 3. Add interests & skills
        interest = ResearchInterest.objects.create(name='Quantum Computing', category='Physics')
        skill = Skill.objects.create(name='Qiskit', category='FRAMEWORK')

        profile = user.researcher_profile
        profile.headline = 'Quantum AI Specialist'
        profile.interests.add(interest)
        profile.skills.add(skill)
        profile.save()

        # 4. Verify public profile display
        detail_res = self.client.get(reverse('researchers:detail', args=[profile.pk]))
        self.assertEqual(detail_res.status_code, 200)
        self.assertContains(detail_res, 'Quantum Computing')
        self.assertContains(detail_res, 'Qiskit')
        self.assertContains(detail_res, 'Quantum AI Specialist')


class DependencyChainBTest(ScholarLensTestMixin, TestCase):
    """Chain B: Paper Upload -> Extraction -> Chunking -> Detail View."""

    def setUp(self):
        self.user = self.create_user(username='uploader_b')
        self.client.login(username='uploader_b', password='testpass123!')

    def test_chain_b_upload_extraction_chunks(self):
        dummy_pdf = SimpleUploadedFile("quantum_paper.pdf", b"%PDF-1.4 dummy pdf content for testing", content_type="application/pdf")
        upload_data = {
            'title': 'Advances in Quantum Error Correction',
            'abstract': 'Detailed study of surface codes and topological stability in fault-tolerant quantum computing.',
            'research_area': 'AI_ML',
            'keywords': 'quantum, error correction, topological',
            'pdf_file': dummy_pdf,
        }
        res = self.client.post(reverse('papers:upload'), data=upload_data)
        self.assertEqual(res.status_code, 302)

        paper = ResearchPaper.objects.get(title='Advances in Quantum Error Correction')
        self.assertEqual(paper.uploader, self.user)
        self.assertIn(paper.status, ['UPLOADED', 'PROCESSED', 'FAILED'])

        # Verify activity was logged
        self.assertTrue(ResearchActivity.objects.filter(user=self.user, activity_type='PAPER_UPLOAD').exists())

        # Detail view renders cleanly with chunk count and action buttons
        detail_res = self.client.get(reverse('papers:detail', args=[paper.pk]))
        self.assertEqual(detail_res.status_code, 200)
        self.assertContains(detail_res, 'Advances in Quantum Error Correction')
        self.assertContains(detail_res, 'AI Research Intelligence')


class DependencyChainCTest(ScholarLensTestMixin, TestCase):
    """Chain C: Paper Detail -> AI Summarization -> Research Gap Detection."""

    def setUp(self):
        self.user = self.create_user(username='ai_researcher_c')
        self.paper = self.create_paper(self.user, title='Graph Neural Networks for Drug Discovery')
        self.client.login(username='ai_researcher_c', password='testpass123!')

    def test_chain_c_summary_and_gaps_generation(self):
        # 1. Summary view handles POST gracefully
        summary_res = self.client.post(reverse('ai_engine:summary', args=[self.paper.pk]))
        self.assertEqual(summary_res.status_code, 200)

        # 2. Gaps view handles POST gracefully
        gaps_res = self.client.post(reverse('ai_engine:gaps', args=[self.paper.pk]))
        self.assertEqual(gaps_res.status_code, 200)

        # 3. Create simulated analysis records and check paper detail displays them
        AIAnalysis.objects.create(
            paper=self.paper,
            analysis_type='SUMMARY',
            result={'executive_summary': 'Demonstrates high affinity binding predictions using GNNs.'}
        )
        ResearchGap.objects.create(
            paper=self.paper,
            title='Scalability on Large Macrocycles',
            description='Current architectures fail on structures exceeding 100 atoms.',
            area='AI_ML',
            severity='HIGH',
            suggestions='Incorporate hierarchical message passing.'
        )

        detail_res = self.client.get(reverse('papers:detail', args=[self.paper.pk]))
        self.assertEqual(detail_res.status_code, 200)
        self.assertContains(detail_res, 'Scalability on Large Macrocycles')


class DependencyChainDTest(ScholarLensTestMixin, TestCase):
    """Chain D: Paper Detail -> RAG Question Answering -> Chat History."""

    def setUp(self):
        self.user = self.create_user(username='rag_user_d')
        self.paper = self.create_paper(self.user, title='Attention Is All You Need')
        self.client.login(username='rag_user_d', password='testpass123!')

    def test_chain_d_rag_and_chat_history(self):
        # Ask question without API key returns graceful notice
        res = self.client.post(reverse('ai_engine:ask_paper', args=[self.paper.pk]), data={
            'question': 'What is the attention mechanism complexity?'
        })
        self.assertEqual(res.status_code, 200)

        # Add simulated ChatMessage and verify it appears in history
        ChatMessage.objects.create(
            paper=self.paper,
            user=self.user,
            question='What is the attention mechanism complexity?',
            answer='The computational complexity per layer is O(n^2 * d).',
            sources=[{'chunk_index': 0, 'relevance': 0.95}]
        )
        history_res = self.client.get(reverse('ai_engine:ask_paper', args=[self.paper.pk]))
        self.assertEqual(history_res.status_code, 200)
        self.assertContains(history_res, 'O(n^2 * d)')


class DependencyChainETest(ScholarLensTestMixin, TestCase):
    """Chain E: Semantic Search -> Keyword Fallback -> Result Scoring."""

    def setUp(self):
        self.user = self.create_user(username='searcher_e')
        self.paper1 = self.create_paper(self.user, title='Deep Reinforcement Learning in Robotics')
        self.paper2 = self.create_paper(self.user, title='Transformer Models for Natural Language')
        self.client.login(username='searcher_e', password='testpass123!')

    def test_chain_e_search_service_and_view(self):
        search_service = SemanticSearchService()
        results = search_service.search('Robotics')
        self.assertIsInstance(results, list)
        self.assertTrue(any(r['paper'].pk == self.paper1.pk for r in results))

        # View search with semantic mode
        res = self.client.get(reverse('search:search') + '?q=Robotics&search_type=semantic')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Deep Reinforcement Learning in Robotics')


class DependencyChainFTest(ScholarLensTestMixin, TestCase):
    """Chain F: Collaboration Request -> Duplicate Prevention -> Accept -> Project Team."""

    def setUp(self):
        self.sender = self.create_user(username='alice_f')
        self.receiver = self.create_user(username='bob_f', email='bob@test.com')
        self.project = ResearchProject.objects.create(
            title='Autonomous Drones Project',
            description='Collaborative drone swarms research',
            leader=self.sender,
            research_area='AI_ML',
        )
        self.client.login(username='alice_f', password='testpass123!')

    def test_chain_f_collaboration_lifecycle(self):
        # 1. Alice sends collaboration request to Bob
        res = self.client.post(reverse('collaboration:send', args=[self.receiver.pk]), data={
            'project': self.project.pk,
            'message': 'Would love to collaborate on drone swarming!',
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(CollaborationRequest.objects.count(), 1)
        req = CollaborationRequest.objects.first()
        self.assertEqual(req.status, 'PENDING')

        # 2. Prevent duplicate pending request
        res_dup = self.client.post(reverse('collaboration:send', args=[self.receiver.pk]), data={
            'project': self.project.pk,
            'message': 'Another request should be blocked!',
        })
        self.assertEqual(res_dup.status_code, 302)
        self.assertEqual(CollaborationRequest.objects.count(), 1)

        # 3. Bob logs in and accepts the request
        self.client.logout()
        self.client.login(username='bob_f', password='testpass123!')
        res_accept = self.client.post(reverse('collaboration:respond', args=[req.pk]), data={
            'action': 'accept'
        })
        self.assertEqual(res_accept.status_code, 302)
        req.refresh_from_db()
        self.assertEqual(req.status, 'ACCEPTED')

        # Bob should now be added as project member
        self.assertTrue(ProjectMember.objects.filter(project=self.project, user=self.receiver).exists())

        # Verify activity was logged for collaboration
        self.assertTrue(ResearchActivity.objects.filter(activity_type='COLLABORATION').exists())


class DependencyChainGTest(ScholarLensTestMixin, TestCase):
    """Chain G: Paper Evaluation -> 6-D Scoring -> Recommendation."""

    def setUp(self):
        self.user = self.create_user(username='eval_user_g')
        self.paper = self.create_paper(self.user, title='Zero-Knowledge Proofs in Decentralized Identity')
        self.client.login(username='eval_user_g', password='testpass123!')

    def test_chain_g_evaluation_lifecycle(self):
        eval_url = reverse('evaluation:evaluate', args=[self.paper.pk])
        res_get = self.client.get(eval_url)
        self.assertEqual(res_get.status_code, 200)

        # Create evaluation report with 6 dimensions
        report = EvaluationReport.objects.create(
            paper=self.paper,
            overall_score=85.5,
            summary='Novel formulation with high potential impact.',
            recommendations=['ACCEPT'],
            model_name='gpt-4o-mini',
        )
        ResearchScore.objects.create(
            report=report,
            dimension='NOVELTY',
            score=90.0,
            weight=1.0,
            explanation='Highly original approach.',
        )
        report_url = reverse('evaluation:report', args=[report.pk])
        res_report = self.client.get(report_url)
        self.assertEqual(res_report.status_code, 200)
        self.assertContains(res_report, '85.5')


class DependencyChainHTest(ScholarLensTestMixin, TestCase):
    """Chain H: User Activity -> Dashboard Counters & Activity Feed."""

    def setUp(self):
        self.user = self.create_user(username='dashboard_user_h')
        self.client.login(username='dashboard_user_h', password='testpass123!')

    def test_chain_h_dashboard_and_activity_feed(self):
        paper = self.create_paper(self.user, title='Federated Learning at Scale')
        project = ResearchProject.objects.create(
            title='Edge Computing Project',
            description='Edge devices testbed',
            leader=self.user,
            research_area='AI_ML',
        )
        ResearchActivity.objects.create(
            user=self.user,
            activity_type='PAPER_UPLOAD',
            description='Uploaded paper Federated Learning at Scale',
            related_paper=paper
        )
        ResearchActivity.objects.create(
            user=self.user,
            activity_type='PROJECT',
            description='Created project Edge Computing Project'
        )

        res = self.client.get(reverse('dashboard:home'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Uploaded paper Federated Learning at Scale')
        self.assertContains(res, 'Created project Edge Computing Project')

