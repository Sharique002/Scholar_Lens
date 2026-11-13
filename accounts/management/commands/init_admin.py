"""Management command to securely and idempotently initialize initial administrative accounts."""
import os
import secrets
from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction


class Command(BaseCommand):
    help = 'Idempotently initialize administrator account with strict security protections'

    def handle(self, *args, **options):
        admin_username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin').strip()
        admin_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@scholarlens.org').strip()
        admin_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '').strip()

        # In production (DEBUG=False), require an explicit environment-provided password
        if not settings.DEBUG and not admin_password:
            self.stdout.write(
                self.style.WARNING(
                    "DJANGO_SUPERUSER_PASSWORD is not set in production. "
                    "Skipping automated administrator provisioning for security."
                )
            )
            return

        # In development, provide a fallback if unset
        if settings.DEBUG and not admin_password:
            admin_password = 'Admin@12345'

        # Idempotent check: Never overwrite or reset existing administrator credentials or roles
        if User.objects.filter(username=admin_username).exists():
            self.stdout.write(f"Administrator account '{admin_username}' already exists. Preserving existing credentials and roles.")
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

        # Demo accounts: Strictly permitted ONLY in DEBUG or when CREATE_DEMO_ACCOUNTS is explicitly enabled
        allow_demo = settings.DEBUG or os.environ.get('CREATE_DEMO_ACCOUNTS', '').lower() in ('true', '1', 'yes')
        if not allow_demo:
            self.stdout.write("Skipping demo accounts provisioning in production.")
            return

        # Faculty account for testing evaluation workflows
        faculty_pw = os.environ.get('FACULTY_PASSWORD', 'Faculty@12345')
        if not User.objects.filter(username='faculty').exists():
            with transaction.atomic():
                faculty_user = User.objects.create_user(
                    username='faculty',
                    email='faculty@scholarlens.org',
                    password=faculty_pw
                )
                faculty_user.profile.role = 'FACULTY'
                faculty_user.profile.save()
                self.stdout.write(self.style.SUCCESS("Provisioned demo faculty user 'faculty'"))
        else:
            self.stdout.write("Demo faculty user 'faculty' already exists.")

        # Researcher account for testing collaboration workflows
        researcher_pw = os.environ.get('RESEARCHER_PASSWORD', 'Researcher@12345')
        if not User.objects.filter(username='demo_researcher').exists():
            with transaction.atomic():
                researcher_user = User.objects.create_user(
                    username='demo_researcher',
                    email='researcher@scholarlens.org',
                    password=researcher_pw
                )
                researcher_user.profile.role = 'RESEARCHER'
                researcher_user.profile.save()
                self.stdout.write(self.style.SUCCESS("Provisioned demo researcher user 'demo_researcher'"))
        else:
            self.stdout.write("Demo researcher user 'demo_researcher' already exists.")
