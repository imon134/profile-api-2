import re
from .models import Profile
from .utils.seed import ensure_seed
from .utils.response import success, error


# ---------------------------
# SERIALIZER (CRITICAL)
# ---------------------------
def serialize(p):
    return {
        "id": p.id,
        "name": p.name,
        "gender": p.gender,
        "gender_probability": p.gender_probability,
        "age": p.age,
        "age_group": p.age_group,
        "country_id": p.country_id,
        "country_name": p.country_name,
        "country_probability": p.country_probability,
        "created_at": p.created_at.isoformat()
    }


# ---------------------------
# PAGINATION (STRICT)
# ---------------------------
def paginate(qs, page, limit):
    total = qs.count()

    start = (page - 1) * limit
    end = start + limit

    return (
        [serialize(x) for x in qs[start:end]],
        {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    )


# ===========================
# GET /profiles
# ===========================
def get_profiles(request):
    ensure_seed()

    qs = Profile.objects.all()

    # ---- FILTERING ----
    gender = request.GET.get("gender")
    if gender:
        qs = qs.filter(gender=gender)

    country_id = request.GET.get("country_id")
    if country_id:
        qs = qs.filter(country_id=country_id)

    min_age = request.GET.get("min_age")
    max_age = request.GET.get("max_age")

    if min_age:
        if not min_age.isdigit():
            return error("INVALID_QUERY", "Invalid query parameters", 422)
        qs = qs.filter(age__gte=int(min_age))

    if max_age:
        if not max_age.isdigit():
            return error("INVALID_QUERY", "Invalid query parameters", 422)
        qs = qs.filter(age__lte=int(max_age))

    # ---- SORTING ----
    sort_by = request.GET.get("sort_by", "created_at")
    order = request.GET.get("order", "asc")

    allowed = ["age", "created_at", "gender_probability"]

    if sort_by not in allowed:
        return error("INVALID_SORT", "Invalid sort_by value", 400)

    if order not in ["asc", "desc"]:
        return error("INVALID_QUERY", "Invalid query parameters", 422)

    if order == "desc":
        sort_by = "-" + sort_by

    qs = qs.order_by(sort_by)

    # ---- PAGINATION ----
    page = request.GET.get("page", "1")
    limit = request.GET.get("limit", "10")

    if not page.isdigit() or int(page) < 1:
        return error("INVALID_QUERY", "Invalid query parameters", 422)

    if not limit.isdigit() or int(limit) < 1:
        return error("INVALID_QUERY", "Invalid query parameters", 422)

    page = int(page)
    limit = min(int(limit), 50)

    data, pagination = paginate(qs, page, limit)

    return success(data, pagination)


# ===========================
# SEARCH /profiles/search
# ===========================
def search_profiles(request):
    ensure_seed()

    q = request.GET.get("q", "").lower().strip()

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

    # ---- PAGINATION ----
    page = int(request.GET.get("page", 1))
    limit = min(int(request.GET.get("limit", 10)), 50)

    data, pagination = paginate(qs, page, limit)

    return success(data, pagination)