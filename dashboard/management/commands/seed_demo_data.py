"""Management command to create demo/seed data for Scholar Lens."""
import random
from datetime import time
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile
from researchers.models import ResearcherProfile, ResearchInterest, Skill
from papers.models import ResearchPaper
from projects.models import ResearchProject, ProjectMember
from facilities.models import Facility, FacilitySlot


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
            Facility.objects.filter(name__in=[
                'GPU Compute Cluster',
                'IoT Lab',
                'Confocal Microscope',
                'PCR Room'
            ]).delete()
            ResearchPaper.objects.filter(title__startswith='[DEMO]').delete()
            ResearchProject.objects.filter(title__startswith='[DEMO]').delete()
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
                'department': 'Computer Science',
                'interests': [interests[0], interests[1], interests[3]],
                'skills': [skills[0], skills[1], skills[2]],
            },
            {
                'username': 'demo_bob',
                'email': 'bob@demo.scholarlens.test',
                'first_name': 'Bob',
                'last_name': 'Smith',
                'role': 'FACULTY',
                'institution': 'Demo University',
                'bio': '[DEMO USER] Systems researcher focusing on cloud and distributed computing.',
                'department': 'Computer Science',
                'interests': [interests[6], interests[7]],
                'skills': [skills[0], skills[3], skills[4]],
            },
            {
                'username': 'demo_carol',
                'email': 'carol@demo.scholarlens.test',
                'first_name': 'Carol',
                'last_name': 'Williams',
                'role': 'STUDENT',
                'institution': 'Demo University',
                'bio': '[DEMO USER] Graduate student working on machine learning applications in bioinformatics.',
                'department': 'Biotechnology',
                'interests': [interests[0], interests[9]],
                'skills': [skills[0], skills[5], skills[6]],
            },
            {
                'username': 'demo_custodian',
                'email': 'custodian@demo.scholarlens.test',
                'first_name': 'Facility',
                'last_name': 'Custodian',
                'role': 'FACULTY',
                'institution': 'Demo University',
                'bio': '[DEMO USER] Facility custodian and laboratory manager.',
                'department': 'Research Operations',
                'interests': [interests[0], interests[6]],
                'skills': [skills[0], skills[4]],
                'is_staff': True,
            },
        ]

        created_users = []
        for user_data in demo_users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'is_staff': user_data.get('is_staff', False),
                }
            )
            if created:
                user.set_password('demo_password_123')
                user.save()
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.role = user_data['role']
                profile.institution = user_data['institution']
                profile.bio = user_data['bio']
                profile.save()

                researcher_profile, _ = ResearcherProfile.objects.get_or_create(user=user)
                researcher_profile.headline = f"{user_data['role'].capitalize()} in {user_data['department']}"
                researcher_profile.expertise_summary = user_data['bio']
                researcher_profile.save()
                researcher_profile.interests.set(user_data['interests'])
                researcher_profile.skills.set(user_data['skills'])
                self.stdout.write(f'  Created demo user: {user.username}')
            created_users.append(user)

        # Create demo facilities
        staff_custodian = created_users[3]
        facilities_seed = [
            {
                'name': 'GPU Compute Cluster',
                'kind': 'COMPUTE',
                'department': 'Computer Science & Engineering',
                'location': 'Tech Tower 401',
                'description': 'High-performance computing cluster equipped with 8x NVIDIA H100 GPUs for deep learning models.',
                'capacity': 4,
            },
            {
                'name': 'IoT Lab',
                'kind': 'LAB',
                'department': 'Computer Science & Engineering',
                'location': 'Innovation Block 202',
                'description': 'Smart sensor networks, FPGA boards, and edge embedded experimentation workbenches.',
                'capacity': 12,
            },
            {
                'name': 'Confocal Microscope',
                'kind': 'EQUIPMENT',
                'department': 'Biotechnology',
                'location': 'BioScience Block 102',
                'description': 'High-resolution spectral confocal laser scanning microscope for cellular and tissue imaging.',
                'capacity': 2,
            },
            {
                'name': 'PCR Room',
                'kind': 'LAB',
                'department': 'Biotechnology',
                'location': 'Genomics Wing 305',
                'description': 'Sterile real-time quantitative PCR suite for gene expression analysis and nucleic acid amplification.',
                'capacity': 6,
            },
        ]

        for f_data in facilities_seed:
            facility, created = Facility.objects.get_or_create(
                name=f_data['name'],
                defaults={
                    'kind': f_data['kind'],
                    'department': f_data['department'],
                    'location': f_data['location'],
                    'description': f_data['description'],
                    'capacity': f_data['capacity'],
                    'custodian': staff_custodian,
                    'requires_approval': True,
                    'is_active': True,
                }
            )
            if created:
                # Mon-Fri 09:00 - 17:00
                for w in range(5):
                    FacilitySlot.objects.get_or_create(
                        facility=facility,
                        weekday=w,
                        opens=time(9, 0),
                        closes=time(17, 0)
                    )
                self.stdout.write(f'  Created facility: {facility.name} (Mon-Fri 09:00-17:00)')

        # Create demo papers
        papers_data = [
            {
                'title': '[DEMO] Attention-Based Neural Architectures for Scientific Text Mining',
                'abstract': '[DEMO ABSTRACT] This paper explores novel attention mechanisms applied to extracting '
                            'semantic relationships from scientific literature. Evaluated on benchmark NLP datasets. '
                            'This is demonstration content for development and testing purposes only.',
                'uploader': created_users[0],
                'research_area': 'AI_ML',
                'keywords': 'machine learning, nlp, attention, transformers',
            },
            {
                'title': '[DEMO] Scalable Distributed Systems for Large-Scale Genomic Data Processing',
                'abstract': '[DEMO ABSTRACT] We propose an architecture for distributing genomic sequence alignment '
                            'across heterogeneous cloud compute nodes. Results demonstrate significant throughput '
                            'improvements. Demonstration content only.',
                'uploader': created_users[1],
                'research_area': 'BIOINFORMATICS',
                'keywords': 'distributed systems, genomics, cloud, bioinformatics',
            },
        ]

        for p_data in papers_data:
            paper, created = ResearchPaper.objects.get_or_create(
                title=p_data['title'],
                defaults={
                    'abstract': p_data['abstract'],
                    'uploader': p_data['uploader'],
                    'research_area': p_data['research_area'],
                    'keywords': p_data['keywords'],
                    'status': 'INDEXED',
                }
            )
            if created:
                self.stdout.write(f'  Created paper: {paper.title}')

        # Create demo projects
        projects_data = [
            {
                'title': '[DEMO] AI-Powered Academic Research Assistant',
                'description': '[DEMO PROJECT] Developing an intelligent assistant to help researchers identify '
                              'relevant literature, summarize papers, and find collaborators across disciplines. '
                              'This is demo content for development purposes.',
                'leader': created_users[0],
                'research_area': 'AI',
                'status': 'ACTIVE',
                'is_public': True,
            },
            {
                'title': '[DEMO] Genomic Analysis at Scale',
                'description': '[DEMO PROJECT] Building computational infrastructure for high-throughput genomic data. '
                              'This is demo content for development purposes.',
                'leader': created_users[1],
                'research_area': 'BIO',
                'status': 'ACTIVE',
                'is_public': True,
            },
        ]

        for proj_data in projects_data:
            project, created = ResearchProject.objects.get_or_create(
                title=proj_data['title'],
                defaults={
                    'description': proj_data['description'],
                    'leader': proj_data['leader'],
                    'research_area': proj_data['research_area'],
                    'status': proj_data['status'],
                    'is_public': proj_data['is_public'],
                }
            )
            if created:
                ProjectMember.objects.get_or_create(
                    project=project,
                    user=proj_data['leader'],
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
            '  Username: demo_alice     | Password: demo_password_123\n'
            '  Username: demo_bob       | Password: demo_password_123\n'
            '  Username: demo_carol     | Password: demo_password_123\n'
            '  Username: demo_custodian | Password: demo_password_123 (Staff/Custodian)\n'
        ))
