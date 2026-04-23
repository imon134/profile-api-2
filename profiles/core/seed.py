import json
from django.conf import settings
from profiles.models import Profile


def ensure_seed():
    if Profile.objects.exists():
        return

    with open(settings.BASE_DIR / "data/seed.json") as f:
        data = json.load(f)["profiles"]

    objs = []

    for p in data:
        objs.append(Profile(
            name=p["name"].strip().lower(),
            gender=p["gender"],
            gender_probability=p["gender_probability"],
            age=p["age"],
            age_group=p["age_group"],
            country_id=p["country_id"],
            country_name=p["country_name"],
            country_probability=p["country_probability"],
        ))

    Profile.objects.bulk_create(objs)