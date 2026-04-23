import os
import json
import gdown
from django.db import transaction
from django.core.management.base import BaseCommand
from profiles.models import Profile
from profiles.utils import uuid7

FILE_ID = "1Up06dcS9OfUEnDj_u6OV_xTRntupFhPH"
URL = f"https://drive.google.com/uc?id={FILE_ID}"
LOCAL_FILE = "profiles_seed.json"


class Command(BaseCommand):
    help = "Fast seed profiles"

    def handle(self, *args, **kwargs):

        # ---------------- DOWNLOAD ONCE ----------------
        if not os.path.exists(LOCAL_FILE):
            self.stdout.write("Downloading dataset...")
            gdown.download(URL, LOCAL_FILE, quiet=False)
        else:
            self.stdout.write("Using cached dataset...")

        # ---------------- FAST JSON LOAD ----------------
        self.stdout.write("Loading dataset into memory...")
        with open(LOCAL_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        profiles = data.get("profiles", [])

        # ---------------- PRELOAD EXISTING NAMES (VERY IMPORTANT) ----------------
        existing_names = set(
            Profile.objects.values_list("name", flat=True)
        )

        new_objects = []
        updated = 0

        # ---------------- BUILD OBJECTS IN MEMORY ----------------
        for row in profiles:
            name = str(row["name"]).strip().lower()

            if name in existing_names:
                updated += 1
                continue

            obj = Profile(
                id=uuid7(),
                name=name,
                gender=row["gender"],
                gender_probability=row["gender_probability"],
                age=row["age"],
                age_group=row["age_group"],
                country_id=row["country_id"],
                country_name=row["country_name"],
                country_probability=row["country_probability"],
            )

            new_objects.append(obj)

        # ---------------- BULK INSERT (FASTEST PART) ----------------
        with transaction.atomic():
            Profile.objects.bulk_create(new_objects, batch_size=1000)

        self.stdout.write(self.style.SUCCESS(
            f"Done → Created: {len(new_objects)}, Skipped existing: {updated}"
        ))