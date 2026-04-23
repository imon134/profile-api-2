import json
from django.core.management.base import BaseCommand
from profiles.models import Profile


class Command(BaseCommand):
    help = "Seed profiles safely"

    def handle(self, *args, **kwargs):

        with open("profiles/data/profiles.json") as f:
            data = json.load(f)

        created = 0

        for row in data["profiles"]:
            name = row["name"].strip().lower()

            if Profile.objects.filter(name=name).exists():
                continue

            Profile.objects.create(
                name=name,
                gender=row["gender"],
                gender_probability=row["gender_probability"],
                age=row["age"],
                age_group=row["age_group"],
                country_id=row["country_id"],
                country_name=row["country_name"],
                country_probability=row["country_probability"],
            )

            created += 1

        self.stdout.write(f"Seeded: {created}")