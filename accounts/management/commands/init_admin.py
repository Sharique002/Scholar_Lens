import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Initialize default admin and faculty accounts for deployment'

    def handle(self, *args, **options):
        admin_username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        admin_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@scholarlens.org')
        admin_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin@12345')

        if not User.objects.filter(username=admin_username).exists():
            admin_user = User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password
            )
            admin_user.profile.role = 'ADMIN'
            admin_user.profile.save()
            self.stdout.write(self.style.SUCCESS(f"Successfully created admin user '{admin_username}'"))
        else:
            self.stdout.write(f"Admin user '{admin_username}' already exists.")

        # Also ensure faculty account exists for novelty evaluation testing
        if not User.objects.filter(username='faculty').exists():
            faculty_user = User.objects.create_user(
                username='faculty',
                email='faculty@scholarlens.org',
                password=os.environ.get('FACULTY_PASSWORD', 'Faculty@12345')
            )
            faculty_user.profile.role = 'FACULTY'
            faculty_user.profile.save()
            self.stdout.write(self.style.SUCCESS("Successfully created faculty user 'faculty'"))
        else:
            self.stdout.write("Faculty user 'faculty' already exists.")
