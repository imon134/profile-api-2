from ..models import Profile
from ..data_seed import PROFILES_DATA


def ensure_seed():
    try:
        if Profile.objects.exists():
            return

        objs = []

        for p in PROFILES_DATA.get("profiles", []):
            if not isinstance(p, dict):
                continue

            try:
                objs.append(Profile(
                    name=str(p.get("name", "")).strip().lower(),
                    gender=str(p.get("gender", "")).lower(),
                    gender_probability=float(p.get("gender_probability", 0)),
                    age=int(p.get("age", 0)),
                    age_group=str(p.get("age_group", "")).lower(),
                    country_id=str(p.get("country_id", "")).upper(),
                    country_name=str(p.get("country_name", "")),
                    country_probability=float(p.get("country_probability", 0)),
                ))
            except:
                continue

        if objs:
            Profile.objects.bulk_create(objs)

    except Exception:
        # NEVER break request pipeline
        pass