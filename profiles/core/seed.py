from profiles.models import Profile
from data.seed import PROFILES


def ensure_seed():
    if Profile.objects.exists():
        return

    objs = []

    for p in PROFILES:
        try:
            objs.append(Profile(
                name=str(p["name"]).strip().lower(),
                gender=str(p["gender"]).lower(),
                gender_probability=float(p["gender_probability"]),
                age=int(p["age"]),
                age_group=str(p["age_group"]).lower(),
                country_id=str(p["country_id"]).upper(),
                country_name=str(p["country_name"]),
                country_probability=float(p["country_probability"]),
            ))
        except:
            continue

    if objs:
        Profile.objects.bulk_create(objs)