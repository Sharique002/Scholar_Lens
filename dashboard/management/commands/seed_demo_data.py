"""Management command to create demo/seed data for Scholar Lens."""
import random
from datetime import time, date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.utils import timezone

from accounts.models import UserProfile
from researchers.models import ResearcherProfile, ResearchInterest, Skill, Department
from papers.models import ResearchPaper, PaperAuthor, DuplicateCandidate
from projects.models import ResearchProject, ProjectMember, Milestone
from facilities.models import Facility, FacilitySlot
from funding.models import FundingCall, FundingApplication
from opportunities.models import ResearchOpening, OpportunityApplication
from researchers.search_index import refresh_search_document
from collaboration.suggestions import compute_suggestions


class Command(BaseCommand):
    help = 'Seed the database with baseline demo data for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing demo data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing demo data...')
            FundingApplication.objects.filter(title__startswith='[DEMO]').delete()
            FundingCall.objects.filter(title__startswith='[DEMO]').delete()
            OpportunityApplication.objects.filter(statement__startswith='[DEMO]').delete()
            ResearchOpening.objects.filter(title__startswith='[DEMO]').delete()
            Milestone.objects.filter(title__startswith='[DEMO]').delete()
            Facility.objects.filter(name__in=[
                'GPU Compute Cluster',
                'IoT Lab',
                'Confocal Microscope',
                'PCR Room'
            ]).delete()
            DuplicateCandidate.objects.all().delete()
            ResearchPaper.objects.filter(title__startswith='[DEMO]').delete()
            ResearchProject.objects.filter(title__startswith='[DEMO]').delete()
            User.objects.filter(username__startswith='demo_').delete()
            ResearchInterest.objects.filter(name__startswith='[DEMO]').delete()
            Skill.objects.filter(name__startswith='[DEMO]').delete()

        self.stdout.write('Creating institutional baseline demo data for Scholar Lens...')

        # 1. Departments
        dept_cse, _ = Department.objects.get_or_create(
            code='CSE',
            defaults={'name': 'Computer Science & Engineering'}
        )
        dept_btb, _ = Department.objects.get_or_create(
            code='BTB',
            defaults={'name': 'Biotechnology & Bioinformatics'}
        )

        # 2. Research Interests Taxonomy (with hierarchy)
        cat_ai, _ = ResearchInterest.objects.get_or_create(name='[DEMO] Artificial Intelligence', defaults={'category': 'AI'})
        cat_systems, _ = ResearchInterest.objects.get_or_create(name='[DEMO] Computer Systems', defaults={'category': 'SYSTEMS'})
        cat_bio, _ = ResearchInterest.objects.get_or_create(name='[DEMO] Biological Sciences', defaults={'category': 'BIO'})

        interests_data = [
            ('[DEMO] Machine Learning', 'Artificial Intelligence', cat_ai),
            ('[DEMO] Natural Language Processing', 'Artificial Intelligence', cat_ai),
            ('[DEMO] Computer Vision', 'Artificial Intelligence', cat_ai),
            ('[DEMO] Deep Learning', 'Artificial Intelligence', cat_ai),
            ('[DEMO] Cloud Computing', 'Systems', cat_systems),
            ('[DEMO] Distributed Systems', 'Systems', cat_systems),
            ('[DEMO] Bioinformatics', 'Interdisciplinary', cat_bio),
            ('[DEMO] Structural Biology', 'Biology', cat_bio),
            ('[DEMO] Genomic Analysis', 'Interdisciplinary', cat_bio),
        ]
        interests = []
        for name, category, parent in interests_data:
            interest, _ = ResearchInterest.objects.get_or_create(
                name=name, defaults={'category': category, 'parent': parent}
            )
            interests.append(interest)

        # 3. Skills
        skills_data = [
            ('[DEMO] Python', 'PROGRAMMING'),
            ('[DEMO] TensorFlow', 'FRAMEWORK'),
            ('[DEMO] PyTorch', 'FRAMEWORK'),
            ('[DEMO] Docker', 'TOOL'),
            ('[DEMO] R Stats', 'PROGRAMMING'),
            ('[DEMO] Cryo-EM', 'METHOD'),
            ('[DEMO] Nextflow', 'TOOL'),
        ]
        skills = []
        for name, category in skills_data:
            skill, _ = Skill.objects.get_or_create(
                name=name, defaults={'category': category}
            )
            skills.append(skill)

        # 4. Demo Users & Roles
        dean_grp, _ = Group.objects.get_or_create(name='Dean of Research')

        demo_users_data = [
            {
                'username': 'demo_alice',
                'email': 'alice@demo.scholarlens.test',
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'role': 'FACULTY',
                'department_obj': dept_cse,
                'institution': 'LPU Research Division',
                'bio': 'AI researcher focusing on NLP, foundation models, and deep learning architectures.',
                'interests': [interests[0], interests[1], interests[3]],
                'skills': [skills[0], skills[1], skills[2]],
                'is_staff': False,
                'verification_status': 'VERIFIED',
            },
            {
                'username': 'demo_bob',
                'email': 'bob@demo.scholarlens.test',
                'first_name': 'Bob',
                'last_name': 'Patel',
                'role': 'FACULTY',
                'department_obj': dept_btb,
                'institution': 'LPU Biotechnology Division',
                'bio': 'Biotechnology researcher focusing on genomic data pipelines, cryo-EM, and computational biology.',
                'interests': [interests[4], interests[6], interests[7], interests[8]],
                'skills': [skills[0], skills[3], skills[4], skills[5]],
                'is_staff': False,
                'verification_status': 'VERIFIED',
            },
            {
                'username': 'demo_carol',
                'email': 'carol@demo.scholarlens.test',
                'first_name': 'Carol',
                'last_name': 'Williams',
                'role': 'STUDENT',
                'department_obj': dept_cse,
                'institution': 'LPU Postgraduate Studies',
                'bio': 'Graduate student exploring machine learning applications in genomics.',
                'interests': [interests[0], interests[6]],
                'skills': [skills[0], skills[4]],
                'is_staff': False,
                'verification_status': 'PENDING',  # Generates 1 pending verification for review queue!
            },
            {
                'username': 'demo_custodian',
                'email': 'custodian@demo.scholarlens.test',
                'first_name': 'Facility',
                'last_name': 'Custodian',
                'role': 'FACULTY',
                'department_obj': dept_cse,
                'institution': 'LPU Central Research Facility',
                'bio': 'Central instrumentation custodian and research operations manager.',
                'interests': [interests[0]],
                'skills': [skills[0], skills[3]],
                'is_staff': True,
                'verification_status': 'VERIFIED',
            },
            {
                'username': 'demo_dean',
                'email': 'dean@demo.scholarlens.test',
                'first_name': 'David',
                'last_name': 'Dean',
                'role': 'FACULTY',
                'department_obj': dept_cse,
                'institution': 'LPU Executive Office',
                'bio': 'Dean of Research and Institutional Innovation.',
                'interests': [interests[0], interests[4]],
                'skills': [skills[0]],
                'is_staff': True,
                'is_dean': True,
                'verification_status': 'VERIFIED',
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
            if created or not user.has_usable_password():
                user.set_password('demo_password_123')
                user.save()

            if user_data.get('is_dean'):
                user.groups.add(dean_grp)

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = user_data['role']
            profile.institution = user_data['institution']
            profile.bio = user_data['bio']
            profile.save()

            r_prof, _ = ResearcherProfile.objects.get_or_create(user=user)
            r_prof.department = user_data['department_obj']
            r_prof.verification_status = user_data['verification_status']
            r_prof.headline = f"{user_data['role'].capitalize()} in {user_data['department_obj'].name}"
            r_prof.expertise_summary = user_data['bio']
            r_prof.is_available_for_collaboration = True
            r_prof.save()
            r_prof.interests.set(user_data['interests'])
            r_prof.skills.set(user_data['skills'])

            created_users.append(user)
            self.stdout.write(f'  Created user: {user.username} ({user_data["department_obj"].code})')

        # Refresh all search documents after papers and interests are assigned


        alice_prof = created_users[0].researcher_profile
        bob_prof = created_users[1].researcher_profile
        staff_custodian = created_users[3]

        # 5. Facilities & Weekly Slots
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
                'department': 'Biotechnology & Bioinformatics',
                'location': 'BioScience Block 102',
                'description': 'High-resolution spectral confocal laser scanning microscope for cellular and tissue imaging.',
                'capacity': 2,
            },
            {
                'name': 'PCR Room',
                'kind': 'LAB',
                'department': 'Biotechnology & Bioinformatics',
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
                for w in range(5):
                    FacilitySlot.objects.get_or_create(
                        facility=facility,
                        weekday=w,
                        opens=time(9, 0),
                        closes=time(17, 0)
                    )

        # 6. Seed Publications (≥10 per Department)
        cse_papers_data = [
            ("Attention-Based Neural Architectures for Scientific Text Mining", "AI_ML", "attention, nlp, transformers", 2024),
            ("Federated Learning on Edge Devices: Latency and Privacy Tradeoffs", "AI_ML", "federated learning, edge computing", 2025),
            ("High-Throughput Approximate Nearest Neighbor Search on Sparse Vectors", "DATA_SCIENCE", "vector search, indexing", 2024),
            ("Graph Neural Networks for Chemical Molecule Property Prediction", "AI_ML", "gnn, molecular biology", 2025),
            ("Robust Distributed Consensus in Byzantine Fault-Tolerant Systems", "NETWORKING", "consensus, distributed systems", 2024),
            ("Zero-Shot Domain Adaptation for Cross-Lingual Information Retrieval", "NLP", "zero-shot, cross-lingual", 2025),
            ("Optimizing Compiler Pipelines for Heterogeneous Accelerated Hardware", "SOFTWARE_ENGINEERING", "compilers, gpu, llvm", 2024),
            ("Provably Secure Multi-Party Computation over Untrusted Clouds", "CYBERSECURITY", "mpc, cryptography, security", 2025),
            ("Autonomous Path Planning for Agile UAV Navigation in Obstacle Fields", "ROBOTICS", "robotics, slam, navigation", 2024),
            ("Quantum Circuit Synthesis via Deep Reinforcement Learning", "QUANTUM_COMPUTING", "quantum, reinforcement learning", 2025),
        ]

        btb_papers_data = [
            ("Scalable Distributed Systems for Large-Scale Genomic Data Processing", "BIOINFORMATICS", "genomics, cloud, pipelines", 2024),
            ("Cryo-EM Reconstruction of Ribosomal Subunits at Atomic Resolution", "BIOINFORMATICS", "cryo-em, structural biology", 2025),
            ("Deep Structural Prediction of Novel Microbial Proteomes", "BIOINFORMATICS", "alphafold, proteome, prediction", 2025),
            ("CRISPR-Cas12a Target Specificity and Off-Target Genome Dynamics", "BIOINFORMATICS", "crispr, cas12a, genome editing", 2024),
            ("Single-Cell Transcriptomic Atlas of Immune Cell Subpopulations", "BIOINFORMATICS", "single-cell, rna-seq, immunology", 2025),
            ("High-Throughput Metabolic Flux Analysis in Engineered Yeast Strains", "BIOINFORMATICS", "metabolic engineering, flux", 2024),
            ("Metagenomic Profiling of Extremophilic Soil Microorganisms", "BIOINFORMATICS", "metagenomics, microbiomes", 2025),
            ("Computational Design of De Novo Protein Binders for Viral Antigens", "BIOINFORMATICS", "protein design, de novo", 2024),
            ("Epigenetic Modulations in Neurodegenerative Disease Progression", "BIOINFORMATICS", "epigenetics, methylation", 2025),
            ("Nanopore Long-Read Sequencing for Variant Detection in Rare Diseases", "BIOINFORMATICS", "nanopore, long-read, variants", 2025),
        ]

        cse_papers = []
        for i, (title, area, kw, year) in enumerate(cse_papers_data):
            p, _ = ResearchPaper.objects.get_or_create(
                title=f"[DEMO] {title}",
                defaults={
                    'abstract': f"[DEMO ABSTRACT] Research on {title} exploring computational efficiency and institutional impact.",
                    'uploader': created_users[0],
                    'research_area': area,
                    'keywords': kw,
                    'year': year,
                    'publication_date': date(year, 3 + (i % 8), 15),
                    'status': 'PROCESSED',
                }
            )
            PaperAuthor.objects.get_or_create(
                paper=p,
                order=1,
                defaults={
                    'name': 'Alice Johnson',
                    'researcher': alice_prof,
                    'match_status': 'CONFIRMED',
                    'match_score': 100.0,
                }
            )
            cse_papers.append(p)

        btb_papers = []
        for i, (title, area, kw, year) in enumerate(btb_papers_data):
            p, _ = ResearchPaper.objects.get_or_create(
                title=f"[DEMO] {title}",
                defaults={
                    'abstract': f"[DEMO ABSTRACT] Research on {title} applying advanced biotechnological pipelines.",
                    'uploader': created_users[1],
                    'research_area': area,
                    'keywords': kw,
                    'year': year,
                    'publication_date': date(year, 2 + (i % 9), 10),
                    'status': 'PROCESSED',
                }
            )
            PaperAuthor.objects.get_or_create(
                paper=p,
                order=1,
                defaults={
                    'name': 'Bob Patel',
                    'researcher': bob_prof,
                    'match_status': 'CONFIRMED',
                    'match_score': 100.0,
                }
            )
            btb_papers.append(p)

        self.stdout.write(f'  Created {len(cse_papers)} CSE publications and {len(btb_papers)} BTB publications.')

        # 7. Seed Sample Duplicate Candidate for Review Queue
        dup_copy, _ = ResearchPaper.objects.get_or_create(
            title="[DEMO] Attention Based Neural Architectures for Scientific Literature Mining",
            defaults={
                'abstract': "Duplicate variant of the paper for deduplication queue benchmark.",
                'uploader': created_users[2],
                'research_area': 'AI_ML',
                'year': 2024,
                'status': 'INDEXED',
            }
        )
        DuplicateCandidate.objects.get_or_create(
            incoming_paper=dup_copy,
            existing_paper=cse_papers[0],
            defaults={
                'similarity_score': 91.5,
                'status': DuplicateCandidate.Status.PENDING,
            }
        )

        # 8. Seed Sample Ambiguous Author Match for Author Review Queue
        PaperAuthor.objects.get_or_create(
            paper=btb_papers[0],
            name='R. Patel',
            defaults={
                'researcher': bob_prof,
                'match_status': PaperAuthor.MatchStatus.PENDING_REVIEW,
                'match_score': 84.0,
                'order': 2,
            }
        )

        # 9. Seed Projects & Milestones
        proj_cse, _ = ResearchProject.objects.get_or_create(
            title='[DEMO] AI-Powered Academic Research Assistant',
            defaults={
                'description': 'Developing an intelligent assistant to help researchers identify literature and collaborate.',
                'leader': created_users[0],
                'research_area': 'AI',
                'status': 'ACTIVE',
                'is_public': True,
            }
        )
        ProjectMember.objects.get_or_create(project=proj_cse, user=created_users[0], defaults={'role': 'LEADER'})
        ProjectMember.objects.get_or_create(project=proj_cse, user=created_users[2], defaults={'role': 'RESEARCHER'})

        proj_btb, _ = ResearchProject.objects.get_or_create(
            title='[DEMO] High-Throughput Genomic Sequence Assembly',
            defaults={
                'description': 'Building next-generation distributed sequencing analysis pipelines.',
                'leader': created_users[1],
                'research_area': 'BIO',
                'status': 'ACTIVE',
                'is_public': True,
            }
        )
        ProjectMember.objects.get_or_create(project=proj_btb, user=created_users[1], defaults={'role': 'LEADER'})

        today = timezone.localdate()
        Milestone.objects.get_or_create(
            project=proj_cse,
            title='[DEMO] Literature Corpus Assembly',
            defaults={
                'is_deliverable': True,
                'owner': created_users[0],
                'start_date': today - timedelta(days=25),
                'due_date': today - timedelta(days=12),
                'status': 'DONE',
                'progress': 100,
                'risk': 'ON_TRACK',
            }
        )
        Milestone.objects.get_or_create(
            project=proj_cse,
            title='[DEMO] Fine-Tuning Multi-Task Evaluator',
            defaults={
                'is_deliverable': True,
                'owner': created_users[2],
                'start_date': today - timedelta(days=10),
                'due_date': today + timedelta(days=2),
                'status': 'IN_PROGRESS',
                'progress': 25,
                'risk': 'AT_RISK',
                'risk_reason': 'Behind schedule; only 25% completed with 2 days remaining.',
            }
        )

        # 10. Seed Funding Calls & Proposals
        call, _ = FundingCall.objects.get_or_create(
            title='[DEMO] SERB Core Research Grant in AI',
            defaults={
                'sponsor': 'Science & Engineering Research Board',
                'description': 'Competitive grant for faculty researching foundation models.',
                'eligibility': 'Faculty researchers.',
                'research_area': 'AI',
                'amount': 'Up to ₹40 Lakhs',
                'deadline': timezone.now() + timedelta(days=20),
                'is_published': True,
                'created_by': staff_custodian,
            }
        )
        FundingApplication.objects.get_or_create(
            call=call,
            applicant=created_users[0],
            title='[DEMO] Scalable Text Intelligence System',
            defaults={
                'project': proj_cse,
                'amount_requested': 3000000.00,
                'amount_awarded': 2800000.00,
                'status': 'AWARDED',
                'decision_date': today - timedelta(days=10),
            }
        )

        # 11. Seed Opportunities Board
        opening, _ = ResearchOpening.objects.get_or_create(
            title='[DEMO] Research Assistant in Deep NLP',
            defaults={
                'project': proj_cse,
                'department': dept_cse,
                'description': 'Graduate assistantship focusing on transformer fine-tuning.',
                'spots_available': 2,
                'deadline': today + timedelta(days=28),
                'status': 'OPEN',
                'created_by': created_users[0],
            }
        )
        opening.required_skills.set([skills[0], skills[2]])

        # 12. Refresh Search Document Index & Pre-compute Suggestions
        refresh_search_document()
        self.stdout.write('  Refreshed full-text expertise search index.')
        compute_suggestions(top_k=5)
        self.stdout.write('  Pre-computed explainable collaboration suggestions.')

        self.stdout.write(self.style.SUCCESS('\nInstitutional baseline demo data seeded successfully!'))
        self.stdout.write(self.style.WARNING(
            '\nDemo accounts:\n'
            '  demo_alice     / demo_password_123 (CSE Faculty)\n'
            '  demo_bob       / demo_password_123 (BTB Faculty)\n'
            '  demo_carol     / demo_password_123 (CSE Student - Pending Verification)\n'
            '  demo_custodian / demo_password_123 (Staff / Facility Custodian)\n'
            '  demo_dean      / demo_password_123 (Dean of Research / Executive)\n'
        ))
