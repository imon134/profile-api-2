import os
import json
import gdown
from django.core.management.base import BaseCommand
from profiles.models import Profile
from profiles.utils import uuid7

FILE_ID = "1Up06dcS9OfUEnDj_u6OV_xTRntupFhPH"
URL = f"https://drive.google.com/uc?id={FILE_ID}"
LOCAL_FILE = "profiles_seed.json"


class Command(BaseCommand):
    help = "Seed profiles database from Google Drive file"

    def handle(self, *args, **kwargs):

        # ✅ Only download if file does NOT exist
        if not os.path.exists(LOCAL_FILE):
            self.stdout.write("Downloading dataset...")
            gdown.download(URL, LOCAL_FILE, quiet=False)
        else:
            self.stdout.write("Using cached dataset...")

        self.stdout.write("Loading dataset...")

        with open(LOCAL_FILE, "r") as f:
            data = json.load(f)

        profiles = data["profiles"]

        created = 0
        skipped = 0

        for row in profiles:
            name = str(row["name"]).strip().lower()

            # ✅ prevent duplicates
            if Profile.objects.filter(name=name).exists():
                skipped += 1
                continue

            Profile.objects.create(
                id=uuid7(),
                name=name,
                gender=row["gender"],
                gender_probability=float(row["gender_probability"]),
                age=int(row["age"]),
                age_group=row["age_group"],
                country_id=row["country_id"],
                country_name=row["country_name"],
                country_probability=float(row["country_probability"]),
            )

            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done → Created: {created}, Skipped: {skipped}"
        ))