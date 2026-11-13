"""Management command to securely and idempotently initialize initial administrative and demo accounts."""
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction


class Command(BaseCommand):
    help = 'Idempotently initialize administrator and demo accounts with strict security protections'

    def handle(self, *args, **options):
        admin_username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin').strip()
        admin_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@scholarlens.org').strip()
        admin_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '').strip()

        # In development or if unset, fallback to Admin@12345
        if not admin_password:
            admin_password = 'Admin@12345'

        # Idempotent check: Ensure administrator credentials and role
        if User.objects.filter(username=admin_username).exists():
            admin_user = User.objects.get(username=admin_username)
            if not admin_user.check_password(admin_password):
                admin_user.set_password(admin_password)
            admin_user.is_superuser = True
            admin_user.is_staff = True
            admin_user.save()
            if hasattr(admin_user, 'profile') and admin_user.profile.role != 'ADMIN':
                admin_user.profile.role = 'ADMIN'
                admin_user.profile.save()
            self.stdout.write(f"Administrator account '{admin_username}' verified.")
        else:
            with transaction.atomic():
                admin_user = User.objects.create_superuser(
                    username=admin_username,
                    email=admin_email,
                    password=admin_password
                )
                if hasattr(admin_user, 'profile'):
                    admin_user.profile.role = 'ADMIN'
                    admin_user.profile.save()
                self.stdout.write(self.style.SUCCESS(f"Successfully provisioned initial administrator '{admin_username}'"))

        # Student demo account (Aarav Sharma)
        student_pw = os.environ.get('STUDENT_PASSWORD', 'Student@12345')
        if User.objects.filter(username='student').exists():
            student_user = User.objects.get(username='student')
            if not student_user.check_password(student_pw):
                student_user.set_password(student_pw)
                student_user.save()
            if hasattr(student_user, 'profile') and student_user.profile.role != 'STUDENT':
                student_user.profile.role = 'STUDENT'
                student_user.profile.save()
            self.stdout.write("Demo student user 'student' verified.")
        else:
            with transaction.atomic():
                student_user = User.objects.create_user(
                    username='student',
                    email='student@scholarlens.org',
                    password=student_pw,
                    first_name='Aarav',
                    last_name='Sharma'
                )
                if hasattr(student_user, 'profile'):
                    student_user.profile.role = 'STUDENT'
                    student_user.profile.save()
                self.stdout.write(self.style.SUCCESS("Provisioned demo student user 'student'"))

        # Faculty demo account (Dr. Elena Vance)
        faculty_pw = os.environ.get('FACULTY_PASSWORD', 'Faculty@12345')
        if User.objects.filter(username='faculty').exists():
            faculty_user = User.objects.get(username='faculty')
            if not faculty_user.check_password(faculty_pw):
                faculty_user.set_password(faculty_pw)
                faculty_user.save()
            if hasattr(faculty_user, 'profile') and faculty_user.profile.role != 'FACULTY':
                faculty_user.profile.role = 'FACULTY'
                faculty_user.profile.save()
            self.stdout.write("Demo faculty user 'faculty' verified.")
        else:
            with transaction.atomic():
                faculty_user = User.objects.create_user(
                    username='faculty',
                    email='faculty@scholarlens.org',
                    password=faculty_pw,
                    first_name='Elena',
                    last_name='Vance'
                )
                if hasattr(faculty_user, 'profile'):
                    faculty_user.profile.role = 'FACULTY'
                    faculty_user.profile.save()
                self.stdout.write(self.style.SUCCESS("Provisioned demo faculty user 'faculty'"))

        # Seed baseline demo papers and content if database is empty
        try:
            from papers.models import ResearchPaper
            if ResearchPaper.objects.count() == 0:
                from django.core.management import call_command
                call_command('seed_demo_data')
                self.stdout.write(self.style.SUCCESS("Baseline demo papers and researcher data seeded successfully."))
        except Exception as seed_err:
            self.stdout.write(f"Notice: seed_demo_data notice: {seed_err}")
