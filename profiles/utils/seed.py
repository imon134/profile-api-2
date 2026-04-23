from ..models import Profile
from ..data_seed import PROFILES_DATA


def ensure_seed():
    if Profile.objects.exists():
        return

    objs = []

    for p in PROFILES_DATA["profiles"]:
        try:
            objs.append(Profile(
                name=str(p["name"]).strip().lower(),
                gender=p["gender"],
                gender_probability=float(p["gender_probability"]),
                age=int(p["age"]),
                age_group=p["age_group"],
                country_id=p["country_id"],
                country_name=p["country_name"],
                country_probability=float(p["country_probability"]),
            ))
        except:
            continue

    Profile.objects.bulk_create(objs)