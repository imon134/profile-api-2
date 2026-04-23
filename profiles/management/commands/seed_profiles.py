from django.core.management.base import BaseCommand
from profiles.core.seed import ensure_seed


class Command(BaseCommand):
    help = "Seed the database with demographic profile data from data/seed.json"

    def handle(self, *args, **options):
        self.stdout.write("Starting database seed...")
        try:
            ensure_seed()
            self.stdout.write(self.style.SUCCESS("Database seed completed successfully."))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Seed failed: {exc}"))
            raise
