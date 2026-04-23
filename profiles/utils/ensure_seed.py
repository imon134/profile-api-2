import json
import requests
from profiles.models import Profile

DATA_URL = "https://drive.google.com/uc?id=1Up06dcS9OfUEnDj_u6OV_xTRntupFhPH"

_seeded = False


def ensure_seed():
    global _seeded

    if _seeded:
        return

    # if DB already has data, skip
    if Profile.objects.exists():
        _seeded = True
        return

    try:
        res = requests.get(DATA_URL, timeout=10)
        data = res.json()

        objs = []

        for row in data["profiles"]:
            name = str(row["name"]).strip().lower()

            objs.append(Profile(
                name=name,
                gender=row["gender"],
                gender_probability=float(row["gender_probability"]),
                age=int(row["age"]),
                age_group=row["age_group"],
                country_id=row["country_id"],
                country_name=row["country_name"],
                country_probability=float(row["country_probability"]),
            ))

        Profile.objects.bulk_create(objs)

        _seeded = True

    except Exception:
        # NEVER crash API
        pass