import re
from django.http import JsonResponse
from profiles.models import Profile
from profiles.core.seed import ensure_seed
from profiles.core.serializers import serialize_profile
from profiles.core.pagination import paginate
from profiles.core.validators import clean_str, safe_int


def error(code, message, status=400):
    return JsonResponse({
        "error": {
            "code": code,
            "message": message
        }
    }, status=status)


def success(data, pagination=None):
    payload = {"data": data}
    if pagination:
        payload["pagination"] = pagination
    return JsonResponse(payload)


# =========================
# GET /profiles
# =========================
def get_profiles(request):
    ensure_seed()

    qs = Profile.objects.all()

    gender = clean_str(request.GET.get("gender"))
    if gender:
        qs = qs.filter(gender=gender)

    country = clean_str(request.GET.get("country_id")).upper()
    if country:
        qs = qs.filter(country_id=country)

    min_age = safe_int(request.GET.get("min_age"))
    max_age = safe_int(request.GET.get("max_age"))

    if min_age is not None:
        qs = qs.filter(age__gte=min_age)

    if max_age is not None:
        qs = qs.filter(age__lte=max_age)

    # SORT
    allowed = ["age", "created_at", "gender_probability"]
    sort_by = clean_str(request.GET.get("sort_by", "created_at"))
    order = clean_str(request.GET.get("order", "asc"))

    if sort_by and sort_by not in allowed:
        return error("INVALID_SORT", "Invalid sort_by value", 400)

    if order == "desc":
        sort_by = "-" + sort_by

    qs = qs.order_by(sort_by)

    # PAGINATION
    page = request.GET.get("page", 1)
    limit = request.GET.get("limit", 10)

    data, pagination = paginate(qs, page, limit)
    data = [serialize_profile(p) for p in data]

    return success(data, pagination)


# =========================
# SEARCH /profiles/search
# =========================
def search_profiles(request):
    ensure_seed()

    q = clean_str(request.GET.get("q"))

    if not q:
        return error("MISSING_QUERY", "Missing or empty parameter", 400)

    qs = Profile.objects.all()
    parsed = False

    if "male" in q:
        qs = qs.filter(gender="male")
        parsed = True

    if "female" in q:
        qs = qs.filter(gender="female")
        parsed = True

    if "young" in q:
        qs = qs.filter(age__gte=16, age__lte=24)
        parsed = True

    country_map = {
        "nigeria": "NG",
        "kenya": "KE",
        "ghana": "GH",
        "uganda": "UG",
        "tanzania": "TZ",
    }

    for k, v in country_map.items():
        if k in q:
            qs = qs.filter(country_id=v)
            parsed = True

    match = re.search(r"above (\d+)", q)
    if match:
        qs = qs.filter(age__gte=int(match.group(1)))
        parsed = True

    if not parsed:
        return error("UNINTERPRETABLE_QUERY", "Unable to interpret query", 422)

    page = request.GET.get("page", 1)
    limit = request.GET.get("limit", 10)

    data, pagination = paginate(qs, page, limit)
    data = [serialize_profile(p) for p in data]

    return success(data, pagination)