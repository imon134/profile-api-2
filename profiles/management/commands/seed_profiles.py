import json
from django.core.management.base import BaseCommand
from profiles.models import Profile


class Command(BaseCommand):
    help = "Seed database"

    def handle(self, *args, **kwargs):

        with open("profiles/data/profiles.json") as f:
            data = json.load(f)

        created = 0

        for row in data["profiles"]:
            obj, created_flag = Profile.objects.get_or_create(
                name=row["name"].strip().lower(),
                defaults=row
            )
            if created_flag:
                created += 1

        self.stdout.write(f"Seeded: {created}")