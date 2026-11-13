"""Management command to reset and seed the deterministic E2E database."""
import os
from datetime import time, date, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.utils import timezone

from accounts.models import UserProfile
from researchers.models import ResearcherProfile, ResearchInterest, Skill, Department
from papers.models import ResearchPaper, PaperAuthor, DuplicateCandidate
from papers.text import normalise_title
from projects.models import ResearchProject, ProjectMember, Milestone
from facilities.models import Facility, FacilitySlot
from funding.models import FundingCall
from opportunities.models import ResearchOpening
from evaluation.models import EvaluationReport, ResearchScore
from researchers.search_index import refresh_search_document
from collaboration.suggestions import compute_suggestions


class Command(BaseCommand):
    help = 'Reset and seed the deterministic E2E database for Cypress tests'

    def handle(self, *args, **options):
        # 1. Multi-layered fail-closed safety checks
        if not getattr(settings, 'E2E', False):
            raise CommandError("CRITICAL SECURITY: e2e_reset can only run when settings.E2E is True (set E2E=1).")

        # Refuse to run if running with production settings (DEBUG=False and not testing)
        if not getattr(settings, 'DEBUG', True) and not getattr(settings, 'TESTING', False):
            raise CommandError("CRITICAL SECURITY: e2e_reset is permanently disabled in production (DEBUG=False).")

        db_config = settings.DATABASES.get('default', {})
        db_name = str(db_config.get('NAME', ''))
        db_host = str(db_config.get('HOST', ''))

        # Database name validation: must explicitly end with _e2e
        if not db_name.endswith('_e2e'):
            raise CommandError(
                f"CRITICAL SECURITY: e2e_reset refuses to run against '{db_name}'. Database name must explicitly end with '_e2e'."
            )

        # Database host validation: reject known cloud/production database domains
        prohibited_hosts = ['.render.com', 'neon.tech', 'supabase.co', 'rds.amazonaws.com', 'cloudsql', 'azure.com']
        for bad_host in prohibited_hosts:
            if bad_host in db_host.lower():
                raise CommandError(
                    f"CRITICAL SECURITY: e2e_reset refuses to run against remote cloud database host '{db_host}'."
                )

        self.stdout.write(
            self.style.WARNING(
                f"AUDIT LOG [{timezone.now().isoformat()}]: Initiating deterministic E2E database reset on '{db_name}' (host: {db_host or 'localhost'})."
            )
        )
        self.stdout.write(f"Flushing database '{db_name}'...")
        call_command('flush', interactive=False)

        self.stdout.write("Seeding deterministic E2E test data...")
        password = os.environ.get('E2E_PASSWORD', 'TestPassword123!')

        # 2. Departments
        cse = Department.objects.create(code='CSE', name='Computer Science & Engineering')
        btb = Department.objects.create(code='BTB', name='Biotechnology & Bioinformatics')

        # 3. Interests
        cat_ai = ResearchInterest.objects.create(name='Artificial Intelligence', category='AI')
        cat_bio = ResearchInterest.objects.create(name='Biological Sciences', category='BIO')
        cat_sys = ResearchInterest.objects.create(name='Systems & Architecture', category='SYSTEMS')

        int_ml = ResearchInterest.objects.create(name='Machine Learning', category='AI', parent=cat_ai)
        int_nlp = ResearchInterest.objects.create(name='Natural Language Processing', category='AI', parent=cat_ai)
        int_cv = ResearchInterest.objects.create(name='Computer Vision', category='AI', parent=cat_ai)
        int_bio = ResearchInterest.objects.create(name='Bioinformatics', category='BIO', parent=cat_bio)
        int_gen = ResearchInterest.objects.create(name='Genomic Analysis', category='BIO', parent=cat_bio)
        int_dist = ResearchInterest.objects.create(name='Distributed Systems', category='SYSTEMS', parent=cat_sys)

        # 4. Skills
        sk_py = Skill.objects.create(name='Python', category='PROGRAMMING')
        sk_torch = Skill.objects.create(name='PyTorch', category='FRAMEWORK')
        sk_dock = Skill.objects.create(name='Docker', category='TOOL')
        sk_r = Skill.objects.create(name='R', category='PROGRAMMING')

        # 5. Groups
        dean_group, _ = Group.objects.get_or_create(name='Dean of Research')

        # 6. Users
        # Student: Asha Rao
        u_student = User.objects.create_user(
            username='e2e_student',
            email='asha.rao@university.edu',
            password=password,
            first_name='Asha',
            last_name='Rao',
        )
        u_student.profile.role = 'STUDENT'
        u_student.profile.institution = 'University Research Campus'
        u_student.profile.bio = 'Undergraduate researcher exploring deep learning and edge AI.'
        u_student.profile.save()

        prof_student, _ = ResearcherProfile.objects.get_or_create(user=u_student)
        prof_student.department = cse
        prof_student.headline = 'Student Researcher in CSE'
        prof_student.expertise_summary = 'Machine learning architectures, computer vision, and neural network compression.'
        prof_student.verification_status = 'UNVERIFIED'
        prof_student.save()
        prof_student.interests.add(int_ml, int_cv)
        prof_student.skills.add(sk_py, sk_torch)

        # Faculty: Vikram Singh
        u_faculty = User.objects.create_user(
            username='e2e_faculty',
            email='vikram.singh@university.edu',
            password=password,
            first_name='Vikram',
            last_name='Singh',
        )
        u_faculty.profile.role = 'FACULTY'
        u_faculty.profile.institution = 'University Research Campus'
        u_faculty.profile.bio = 'Professor of Computer Science specializing in Distributed AI.'
        u_faculty.profile.save()

        prof_faculty, _ = ResearcherProfile.objects.get_or_create(user=u_faculty)
        prof_faculty.department = cse
        prof_faculty.headline = 'Professor in Computer Science & Engineering'
        prof_faculty.expertise_summary = 'Distributed deep learning, edge intelligence, and edge-native neural systems.'
        prof_faculty.verification_status = 'VERIFIED'
        prof_faculty.orcid_id = '0000-0002-1825-0097'
        prof_faculty.save()
        prof_faculty.interests.add(int_ml, int_dist)
        prof_faculty.skills.add(sk_py, sk_dock)

        # Custodian: Priya Sharma
        u_custodian = User.objects.create_user(
            username='e2e_custodian',
            email='priya.sharma@university.edu',
            password=password,
            first_name='Priya',
            last_name='Sharma',
        )
        u_custodian.profile.role = 'FACULTY'
        u_custodian.profile.institution = 'University Research Campus'
        u_custodian.profile.bio = 'Facility custodian and hardware systems specialist.'
        u_custodian.profile.save()

        prof_custodian, _ = ResearcherProfile.objects.get_or_create(user=u_custodian)
        prof_custodian.department = cse
        prof_custodian.headline = 'Facility Custodian in Computer Science'
        prof_custodian.expertise_summary = 'HPC infrastructure, GPU clusters, and cluster scheduling.'
        prof_custodian.verification_status = 'VERIFIED'
        prof_custodian.save()

        # Office: Research Office Staff
        u_office = User.objects.create_user(
            username='e2e_office',
            email='office@university.edu',
            password=password,
            first_name='Office',
            last_name='Staff',
            is_staff=True,
            is_superuser=False,
        )
        u_office.profile.role = 'ADMIN'
        u_office.profile.institution = 'University Research Campus'
        u_office.profile.bio = 'Research administration officer.'
        u_office.profile.save()

        prof_office, _ = ResearcherProfile.objects.get_or_create(user=u_office)
        prof_office.department = cse
        prof_office.headline = 'Research Office Administrator'
        prof_office.expertise_summary = 'Research ethics, grant compliance, and publication registry.'
        prof_office.verification_status = 'VERIFIED'
        prof_office.save()

        # Dean: Rajesh Kumar
        u_dean = User.objects.create_user(
            username='e2e_dean',
            email='dean.research@university.edu',
            password=password,
            first_name='Rajesh',
            last_name='Kumar',
            is_staff=True,
        )
        u_dean.groups.add(dean_group)
        u_dean.profile.role = 'ADMIN'
        u_dean.profile.institution = 'University Research Campus'
        u_dean.profile.bio = 'Dean of Research and Institutional Innovation.'
        u_dean.profile.save()

        prof_dean, _ = ResearcherProfile.objects.get_or_create(user=u_dean)
        prof_dean.department = cse
        prof_dean.headline = 'Dean of Research'
        prof_dean.expertise_summary = 'Institutional research policy and strategic innovation.'
        prof_dean.verification_status = 'VERIFIED'
        prof_dean.save()

        # Biotech: Meera Iyer
        u_biotech = User.objects.create_user(
            username='e2e_biotech',
            email='meera.iyer@university.edu',
            password=password,
            first_name='Meera',
            last_name='Iyer',
        )
        u_biotech.profile.role = 'FACULTY'
        u_biotech.profile.institution = 'University Research Campus'
        u_biotech.profile.bio = 'Associate Professor in Biotechnology specializing in genomics.'
        u_biotech.profile.save()

        prof_biotech, _ = ResearcherProfile.objects.get_or_create(user=u_biotech)
        prof_biotech.department = btb
        prof_biotech.headline = 'Associate Professor in Biotechnology'
        prof_biotech.expertise_summary = 'Computational genomics, bioinformatics pipelines, machine learning, and CRISPR screening.'
        prof_biotech.verification_status = 'VERIFIED'
        prof_biotech.orcid_id = '0000-0001-5000-0007'
        prof_biotech.save()
        prof_biotech.interests.add(int_bio, int_gen, int_ml)
        prof_biotech.skills.add(sk_py, sk_r)

        # 7. Facilities
        gpu_cluster = Facility.objects.create(
            name='GPU Compute Cluster',
            kind='COMPUTE',
            department='Computer Science & Engineering',
            location='Lab Block B, Room 204',
            custodian=u_custodian,
            capacity=16,
            requires_approval=True,
            description='High-performance NVIDIA A100 GPU cluster for deep learning experiments.',
            is_active=True,
        )
        cleanroom = Facility.objects.create(
            name='Biotech Cleanroom',
            kind='LAB',
            department='Biotechnology & Bioinformatics',
            location='Bio Block C, Room 101',
            custodian=u_custodian,
            capacity=8,
            requires_approval=False,
            description='Class 10,000 cleanroom for biological sample preparation.',
            is_active=True,
        )

        # Mon-Fri 09:00 - 17:00 slots for both facilities (0=Mon .. 4=Fri)
        for fac in [gpu_cluster, cleanroom]:
            for weekday in range(0, 5):
                FacilitySlot.objects.create(
                    facility=fac,
                    weekday=weekday,
                    opens=time(9, 0),
                    closes=time(17, 0),
                )

        # 8. Funding Calls (+3, +10, +25, -5 days)
        now = timezone.now()
        call_3d = FundingCall.objects.create(
            title='AI for Healthcare Initiative',
            sponsor='National Science Foundation',
            amount='₹50,00,000',
            deadline=now + timedelta(days=3),
            description='Targeted grants for deploying machine learning diagnostics in clinical workflows.',
            eligibility='Faculty and student researchers.',
            research_area='AI',
            is_published=True,
            created_by=u_office,
        )
        call_3d.watchers.add(u_student)

        call_10d = FundingCall.objects.create(
            title='Quantum Computing Seed Grant',
            sponsor='Ministry of Information Technology',
            amount='₹30,00,000',
            deadline=now + timedelta(days=10),
            description='Seed funding for quantum algorithm exploration and hybrid solvers.',
            eligibility='Faculty researchers.',
            research_area='OTHER',
            is_published=True,
            created_by=u_office,
        )
        call_10d.watchers.add(u_student)

        call_25d = FundingCall.objects.create(
            title='Clean Energy Innovation Fund',
            sponsor='Department of Renewable Energy',
            amount='₹80,00,000',
            deadline=now + timedelta(days=25),
            description='Accelerating next-generation sustainable grid intelligence.',
            eligibility='Open to all university departments.',
            research_area='OTHER',
            is_published=True,
            created_by=u_office,
        )
        # Note: unwatched so student toggles Watch in spec 05_funding

        call_past = FundingCall.objects.create(
            title='Past Robotics Challenge',
            sponsor='Industry Innovation Council',
            amount='₹20,00,000',
            deadline=now - timedelta(days=5),
            description='Closed call for autonomous robotic manipulation.',
            eligibility='All researchers.',
            research_area='SE',
            is_published=True,
            created_by=u_office,
        )

        # 9. Project & Milestones
        today = timezone.localdate()
        proj_edge = ResearchProject.objects.create(
            title='Edge AI Lab',
            leader=u_faculty,
            research_area='AI',
            description='Developing resource-efficient neural network architectures for resource-constrained edge devices.',
            status='ACTIVE',
            start_date=today - timedelta(days=60),
            end_date=today + timedelta(days=120),
        )
        ProjectMember.objects.create(project=proj_edge, user=u_faculty, role='LEAD')

        # Milestones:
        # 1 overdue: Hardware Architecture Design (due -5d, 20%)
        m_overdue = Milestone.objects.create(
            project=proj_edge,
            title='Hardware Architecture Design',
            due_date=today - timedelta(days=5),
            progress=20,
            status='IN_PROGRESS',
            risk='OVERDUE',
            risk_reason='Past due date and progress < 100%',
        )

        # 1 due in 3 days at 10%: Dataset Collection
        m_at_risk = Milestone.objects.create(
            project=proj_edge,
            title='Dataset Collection',
            due_date=today + timedelta(days=3),
            progress=10,
            status='IN_PROGRESS',
            risk='AT_RISK',
            risk_reason='Due within 7 days and progress < 50%',
        )

        # 1 waiting on another: Model Training Pipeline (depends_on Dataset Collection)
        m_dep = Milestone.objects.create(
            project=proj_edge,
            title='Model Training Pipeline',
            due_date=today + timedelta(days=20),
            progress=0,
            status='NOT_STARTED',
            risk='ON_TRACK',
        )
        m_dep.depends_on.add(m_at_risk)

        # 1 done: Literature Review
        m_done = Milestone.objects.create(
            project=proj_edge,
            title='Literature Review',
            due_date=today - timedelta(days=15),
            progress=100,
            status='COMPLETED',
            risk='ON_TRACK',
        )

        # 10. Openings
        op = ResearchOpening.objects.create(
            project=proj_edge,
            department=cse,
            title='Undergraduate ML Researcher',
            description='Looking for a motivated undergraduate student in CSE to work on edge machine learning models.',
            status='OPEN',
            spots_available=1,
            deadline=today + timedelta(days=30),
            created_by=u_faculty,
        )
        op.required_skills.add(sk_py, sk_torch)

        # Second opening for testing withdrawal
        op2 = ResearchOpening.objects.create(
            department=cse,
            title='Junior Systems Assistant',
            description='Assistantship for lab infrastructure maintenance.',
            status='OPEN',
            spots_available=2,
            deadline=today + timedelta(days=45),
            created_by=u_faculty,
        )
        from opportunities.models import OpportunityApplication
        OpportunityApplication.objects.create(
            opening=op2,
            applicant=u_student,
            statement='Interested in supporting system administration.',
        )

        from dashboard.models import ResearchActivity
        ResearchActivity.objects.create(
            user=u_student,
            activity_type='OPENING',
            description="Recommended research opening: 'Undergraduate ML Researcher' (You match 100%)"
        )

        # 11. Publications
        # Baseline publications
        p1 = ResearchPaper.objects.create(
            title='Edge-Native Neural Networks for IoT Devices',
            normalised_title=normalise_title('Edge-Native Neural Networks for IoT Devices'),
            uploader=u_faculty,
            doi='10.1145/3343031.3351001',
            venue='ACM Conference on Embedded Systems',
            pub_type='CONFERENCE',
            year=2024,
            publication_date=date(2024, 5, 10),
            abstract='A lightweight neural network architecture optimized for microcontrollers and edge gateways.',
            source='CROSSREF',
            status='PROCESSED',
        )
        PaperAuthor.objects.create(
            paper=p1,
            name='Vikram Singh',
            order=1,
            researcher=prof_faculty,
            match_status=PaperAuthor.MatchStatus.CONFIRMED,
            match_score=100.0,
        )

        # Pre-seed canonical 7-dimension evaluation report for p1
        eval_report = EvaluationReport.objects.create(
            paper=p1,
            overall_score=84.5,
            summary="Strong edge-native neural architecture addressing constrained memory overhead with novel quantized pruning techniques.",
            strengths=["Low memory footprint", "High inference speed on ARM Cortex-M"],
            weaknesses=["Limited evaluation on non-vision tasks"],
            recommendations=["ACCEPT with minor revisions"],
            confidence="High",
        )
        dimensions = [
            ('NOVELTY', 88.0, 0.20, "Novel quantized pruning technique specifically tailored for edge devices."),
            ('RESEARCH_GAP', 82.0, 0.15, "Addresses critical memory constraint gap in microcontrollers."),
            ('METHODOLOGY', 86.0, 0.15, "Sound empirical benchmarking across multiple hardware platforms."),
            ('CONTRIBUTION', 85.0, 0.15, "Substantial open-source artifact and benchmark contribution."),
            ('EVIDENCE_QUALITY', 83.0, 0.15, "High quality experimental measurements with repeated trials."),
            ('TECHNICAL_STRENGTH', 87.0, 0.10, "Mathematically rigorous quantization analysis."),
            ('CLARITY', 80.0, 0.10, "Well-structured paper with clear architectural schematics."),
        ]
        for dim, score_val, weight, expl in dimensions:
            ResearchScore.objects.create(
                report=eval_report,
                dimension=dim,
                score=score_val,
                weight=weight,
                explanation=expl,
                confidence='High',
            )

        p2 = ResearchPaper.objects.create(
            title='Genomic Variant Interpretation via Graph Transformers',
            normalised_title=normalise_title('Genomic Variant Interpretation via Graph Transformers'),
            uploader=u_biotech,
            doi='10.1093/bioinformatics/btab500',
            venue='Bioinformatics',
            pub_type='JOURNAL',
            year=2023,
            publication_date=date(2023, 8, 15),
            abstract='Leveraging graph neural networks to predict clinical pathogenicity of non-coding mutations.',
            source='CROSSREF',
            status='PROCESSED',
        )
        PaperAuthor.objects.create(
            paper=p2,
            name='Meera Iyer',
            order=1,
            researcher=prof_biotech,
            match_status=PaperAuthor.MatchStatus.CONFIRMED,
            match_score=100.0,
        )

        # Duplicate pair at review level (for spec 08_publications)
        dup1 = ResearchPaper.objects.create(
            title='Scalable Distributed Machine Learning Systems',
            normalised_title=normalise_title('Scalable Distributed Machine Learning Systems'),
            uploader=u_faculty,
            venue='IEEE Transactions on Cloud Computing',
            pub_type='JOURNAL',
            year=2023,
            publication_date=date(2023, 4, 1),
            abstract='Principles of distributed deep learning across heterogeneous clusters.',
            source='USER_UPLOAD',
            status='PROCESSED',
        )
        dup2 = ResearchPaper.objects.create(
            title='Scalable Distributed Machine Learning System',
            normalised_title=normalise_title('Scalable Distributed Machine Learning System'),
            uploader=u_faculty,
            venue='IEEE Trans. Cloud Comput.',
            pub_type='JOURNAL',
            year=2023,
            publication_date=date(2023, 4, 1),
            abstract='Principles of distributed deep learning across heterogeneous compute clusters.',
            source='USER_UPLOAD',
            status='PROCESSED',
        )
        DuplicateCandidate.objects.create(
            incoming_paper=dup2,
            existing_paper=dup1,
            similarity_score=94.5,
            status=DuplicateCandidate.Status.PENDING,
        )

        # Ambiguous author match at review level for e2e_biotech (spec 08_publications / author review)
        p_bio = ResearchPaper.objects.create(
            title='CRISPR Genome Editing in Plant Biotechnology',
            normalised_title=normalise_title('CRISPR Genome Editing in Plant Biotechnology'),
            uploader=u_biotech,
            doi='10.1038/s41587-022-01450-x',
            venue='Nature Biotechnology',
            pub_type='JOURNAL',
            year=2024,
            publication_date=date(2024, 2, 20),
            abstract='Targeted mutations and gene replacement strategies in cereal crops.',
            source='ORCID',
            status='PROCESSED',
        )
        PaperAuthor.objects.create(
            paper=p_bio,
            name='M. Iyer',
            order=1,
            researcher=prof_biotech,
            match_status=PaperAuthor.MatchStatus.PENDING_REVIEW,
            match_score=85.0,
        )

        # 12. Search & Collaboration Suggestions
        refresh_search_document()
        compute_suggestions()

        self.stdout.write(self.style.SUCCESS("E2E database seeded successfully!"))
