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

        # Idempotent check: Never overwrite or reset existing administrator credentials or roles
        if User.objects.filter(username=admin_username).exists():
            admin_user = User.objects.get(username=admin_username)
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
        if not User.objects.filter(username='student').exists():
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
        else:
            self.stdout.write("Demo student user 'student' verified.")

        # Faculty demo account (Dr. Elena Vance)
        faculty_pw = os.environ.get('FACULTY_PASSWORD', 'Faculty@12345')
        if not User.objects.filter(username='faculty').exists():
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
        else:
            self.stdout.write("Demo faculty user 'faculty' verified.")
