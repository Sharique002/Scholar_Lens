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

        # Ensure a demo researcher account exists for immediate testing
        if not User.objects.filter(username='demo_researcher').exists():
            researcher_user = User.objects.create_user(
                username='demo_researcher',
                email='researcher@scholarlens.org',
                password=os.environ.get('RESEARCHER_PASSWORD', 'Researcher@12345')
            )
            researcher_user.profile.role = 'RESEARCHER'
            researcher_user.profile.save()
            self.stdout.write(self.style.SUCCESS("Successfully created researcher user 'demo_researcher'"))
        else:
            self.stdout.write("Researcher user 'demo_researcher' already exists.")

        # Ensure demo student account exists matching the 1-click Quick Demo Credentials button
        student_username = os.environ.get('STUDENT_USERNAME', 'student')
        student_password = os.environ.get('STUDENT_PASSWORD', 'Student@12345')
        if not User.objects.filter(username=student_username).exists():
            student_user = User.objects.create_user(
                username=student_username,
                email=os.environ.get('STUDENT_EMAIL', 'student@scholarlens.org'),
                password=student_password,
                first_name='Aarav',
                last_name='Sharma'
            )
            student_user.profile.role = 'STUDENT'
            student_user.profile.institution = 'University of Science & Technology'
            student_user.profile.save()
            self.stdout.write(self.style.SUCCESS(f"Successfully created student user '{student_username}'"))
        else:
            self.stdout.write(f"Student user '{student_username}' already exists.")
