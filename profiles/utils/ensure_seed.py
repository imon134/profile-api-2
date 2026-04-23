from profiles.models import Profile
from profiles.data_seed import PROFILES_DATA

_seeded = False


def ensure_seed():
    global _seeded

    if _seeded or Profile.objects.exists():
        return

    objs = []

    for row in PROFILES_DATA["profiles"]:
        objs.append(Profile(
            name=str(row["name"]).strip().lower(),
            gender=row["gender"],
            gender_probability=row["gender_probability"],
            age=row["age"],
            age_group=row["age_group"],
            country_id=row["country_id"],
            country_name=row["country_name"],
            country_probability=row["country_probability"],
        ))

    Profile.objects.bulk_create(objs)
    _seeded = True