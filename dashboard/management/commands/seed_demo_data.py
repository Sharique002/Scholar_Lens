"""Management command to create demo/seed data for Scholar Lens."""
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile
from researchers.models import ResearcherProfile, ResearchInterest, Skill
from papers.models import ResearchPaper
from projects.models import ResearchProject, ProjectMember


class Command(BaseCommand):
    help = 'Seed the database with demo data for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing demo data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing demo data...')
            User.objects.filter(username__startswith='demo_').delete()
            ResearchInterest.objects.filter(name__startswith='[DEMO]').delete()
            Skill.objects.filter(name__startswith='[DEMO]').delete()

        self.stdout.write('Creating demo data for Scholar Lens...')
        self.stdout.write(self.style.WARNING(
            'NOTE: All demo data is clearly labeled and is NOT real published research.'
        ))

        # Create demo interests
        interests_data = [
            ('[DEMO] Machine Learning', 'Artificial Intelligence'),
            ('[DEMO] Natural Language Processing', 'Artificial Intelligence'),
            ('[DEMO] Computer Vision', 'Artificial Intelligence'),
            ('[DEMO] Deep Learning', 'Artificial Intelligence'),
            ('[DEMO] Data Mining', 'Data Science'),
            ('[DEMO] Cybersecurity', 'Security'),
            ('[DEMO] Cloud Computing', 'Systems'),
            ('[DEMO] Blockchain', 'Distributed Systems'),
            ('[DEMO] Quantum Computing', 'Emerging Tech'),
            ('[DEMO] Bioinformatics', 'Interdisciplinary'),
        ]
        interests = []
        for name, category in interests_data:
            interest, _ = ResearchInterest.objects.get_or_create(
                name=name, defaults={'category': category}
            )
            interests.append(interest)

        # Create demo skills
        skills_data = [
            ('[DEMO] Python', 'PROGRAMMING'),
            ('[DEMO] TensorFlow', 'FRAMEWORK'),
            ('[DEMO] PyTorch', 'FRAMEWORK'),
            ('[DEMO] SQL', 'PROGRAMMING'),
            ('[DEMO] Docker', 'TOOL'),
            ('[DEMO] Statistics', 'METHOD'),
            ('[DEMO] R', 'PROGRAMMING'),
            ('[DEMO] MATLAB', 'TOOL'),
        ]
        skills = []
        for name, category in skills_data:
            skill, _ = Skill.objects.get_or_create(
                name=name, defaults={'category': category}
            )
            skills.append(skill)

        # Create demo users
        demo_users_data = [
            {
                'username': 'demo_alice',
                'email': 'alice@demo.scholarlens.test',
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'role': 'FACULTY',
                'institution': 'Demo University',
                'bio': '[DEMO USER] AI researcher focusing on NLP and deep learning.',
                'headline': '[DEMO] NLP & Deep Learning Researcher',
            },
            {
                'username': 'demo_bob',
                'email': 'bob@demo.scholarlens.test',
                'first_name': 'Bob',
                'last_name': 'Smith',
                'role': 'STUDENT',
                'institution': 'Demo Institute of Technology',
                'bio': '[DEMO USER] PhD student working on computer vision.',
                'headline': '[DEMO] Computer Vision PhD Student',
            },
            {
                'username': 'demo_carol',
                'email': 'carol@demo.scholarlens.test',
                'first_name': 'Carol',
                'last_name': 'Williams',
                'role': 'FACULTY',
                'institution': 'Demo Research Lab',
                'bio': '[DEMO USER] Professor specializing in cybersecurity and data privacy.',
                'headline': '[DEMO] Cybersecurity Professor',
            },
        ]

        created_users = []
        for user_data in demo_users_data:
            username = user_data['username']
            if User.objects.filter(username=username).exists():
                self.stdout.write(f'  User {username} already exists, skipping.')
                created_users.append(User.objects.get(username=username))
                continue

            user = User.objects.create_user(
                username=username,
                email=user_data['email'],
                password='demo_password_123',
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
            )

            # Update profile
            profile = user.profile
            profile.role = user_data['role']
            profile.institution = user_data['institution']
            profile.bio = user_data['bio']
            profile.save()

            # Create researcher profile
            researcher_profile, _ = ResearcherProfile.objects.get_or_create(
                user=user,
                defaults={
                    'headline': user_data['headline'],
                    'expertise_summary': user_data['bio'],
                    'years_experience': random.randint(2, 15),
                }
            )

            # Add random interests and skills
            selected_interests = random.sample(interests, min(4, len(interests)))
            researcher_profile.interests.set(selected_interests)
            selected_skills = random.sample(skills, min(3, len(skills)))
            researcher_profile.skills.set(selected_skills)

            created_users.append(user)
            self.stdout.write(f'  Created user: {username}')

        # Create demo papers (without PDFs - metadata only)
        papers_data = [
            {
                'title': '[DEMO] A Survey of Transformer-Based Models in NLP',
                'abstract': '[DEMO PAPER - NOT REAL RESEARCH] This demo paper surveys transformer architectures. '
                           'It covers attention mechanisms, pre-training strategies, and fine-tuning approaches. '
                           'This is demo content for Scholar Lens development purposes only.',
                'research_area': 'NLP',
                'keywords': 'demo, transformers, NLP, attention, survey',
                'status': 'UPLOADED',
            },
            {
                'title': '[DEMO] Deep Learning for Medical Image Classification',
                'abstract': '[DEMO PAPER - NOT REAL RESEARCH] This demo paper explores CNN-based approaches '
                           'for classifying medical imaging data. This is demo content for Scholar Lens '
                           'development purposes only.',
                'research_area': 'COMPUTER_VISION',
                'keywords': 'demo, deep learning, medical imaging, CNN, classification',
                'status': 'UPLOADED',
            },
            {
                'title': '[DEMO] Federated Learning for Privacy-Preserving Analytics',
                'abstract': '[DEMO PAPER - NOT REAL RESEARCH] This demo paper discusses federated learning '
                           'techniques that enable privacy-preserving model training across distributed '
                           'data sources. This is demo content for Scholar Lens development purposes only.',
                'research_area': 'AI_ML',
                'keywords': 'demo, federated learning, privacy, distributed systems',
                'status': 'UPLOADED',
            },
        ]

        for i, paper_data in enumerate(papers_data):
            user = created_users[i % len(created_users)]
            paper, created = ResearchPaper.objects.get_or_create(
                title=paper_data['title'],
                defaults={
                    'abstract': paper_data['abstract'],
                    'research_area': paper_data['research_area'],
                    'keywords': paper_data['keywords'],
                    'status': paper_data['status'],
                    'uploader': user,
                }
            )
            if created:
                self.stdout.write(f'  Created paper: {paper_data["title"][:50]}...')

        # Create demo project
        if created_users:
            project, created = ResearchProject.objects.get_or_create(
                title='[DEMO] AI in Healthcare Research Project',
                defaults={
                    'description': '[DEMO PROJECT] Exploring applications of artificial intelligence '
                                  'in healthcare diagnostics and treatment planning. '
                                  'This is demo content for development purposes.',
                    'leader': created_users[0],
                    'research_area': 'AI_ML',
                    'status': 'ACTIVE',
                    'is_public': True,
                }
            )
            if created:
                ProjectMember.objects.get_or_create(
                    project=project,
                    user=created_users[0],
                    defaults={'role': 'LEADER'}
                )
                if len(created_users) > 1:
                    ProjectMember.objects.get_or_create(
                        project=project,
                        user=created_users[1],
                        defaults={'role': 'RESEARCHER'}
                    )
                self.stdout.write(f'  Created project: {project.title}')

        self.stdout.write(self.style.SUCCESS('\nDemo data seeded successfully!'))
        self.stdout.write(self.style.WARNING(
            '\nDemo user credentials:\n'
            '  Username: demo_alice | Password: demo_password_123\n'
            '  Username: demo_bob   | Password: demo_password_123\n'
            '  Username: demo_carol | Password: demo_password_123\n'
        ))
