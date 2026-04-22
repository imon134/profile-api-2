import gdown
import pandas as pd
import os
from django.core.management.base import BaseCommand
from profiles.models import Profile
from profiles.utils import uuid7  # if using UUIDv7 helper


FILE_ID = "1Up06dcS9OfUEnDj_u6OV_xTRntupFhPH"
URL = f"https://drive.google.com/uc?id={FILE_ID}"
LOCAL_FILE = "profiles_seed.csv"


class Command(BaseCommand):
    help = "Seed profiles database from Google Drive file"

    def handle(self, *args, **kwargs):

        # ---------------- DOWNLOAD FILE ----------------
        self.stdout.write("Downloading dataset...")

        gdown.download(URL, LOCAL_FILE, quiet=False)

        # ---------------- LOAD FILE ----------------
        self.stdout.write("Reading dataset...")

        # Try CSV first
        try:
            df = pd.read_csv(LOCAL_FILE)
        except Exception:
            df = pd.read_excel(LOCAL_FILE)

        created = 0
        updated = 0

        # ---------------- PROCESS ROWS ----------------
        for _, row in df.iterrows():

            name = str(row["name"]).strip().lower()

            obj, was_created = Profile.objects.update_or_create(
                name=name,  # UNIQUE constraint ensures no duplicates

                defaults={
                    "gender": row["gender"],
                    "gender_probability": float(row["gender_probability"]),
                    "age": int(row["age"]),
                    "age_group": row["age_group"],
                    "country_id": row["country_id"],
                    "country_name": row["country_name"],
                    "country_probability": float(row["country_probability"]),
                }
            )

            if was_created:
                obj.id = uuid7()  # assign UUID v7 once
                obj.save()
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seeding complete → Created: {created}, Updated: {updated}"
        ))

        # cleanup
        os.remove(LOCAL_FILE)