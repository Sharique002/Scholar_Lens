from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from researchers.models import ResearcherProfile
from collaboration.suggestions import compute_suggestions


class Command(BaseCommand):
    help = 'Pre-computes and stores explainable collaboration suggestions (M5).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username of a specific researcher to compute suggestions for.',
        )
        parser.add_argument(
            '--top-k',
            type=int,
            default=10,
            help='Number of suggestions per researcher (default 10).',
        )

    def handle(self, *args, **options):
        username = options.get('user')
        top_k = options.get('top_k', 10)

        if username:
            try:
                user = User.objects.get(username=username)
                target = ResearcherProfile.objects.get(user=user)
                compute_suggestions(target_researcher=target, top_k=top_k)
                self.stdout.write(self.style.SUCCESS(f"Computed top {top_k} suggestions for {username}"))
            except (User.DoesNotExist, ResearcherProfile.DoesNotExist):
                self.stderr.write(f"User/Profile '{username}' not found.")
        else:
            compute_suggestions(target_researcher=None, top_k=top_k)
            self.stdout.write(self.style.SUCCESS(f"Computed top {top_k} suggestions for all researchers."))
