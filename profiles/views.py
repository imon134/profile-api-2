import re
from django.http import JsonResponse
from profiles.models import Profile
from profiles.core.seed import ensure_seed
from profiles.core.pagination import paginate
from profiles.core.serializers import serialize
from profiles.core.validators import to_int, to_float


def error(msg, status):
    return JsonResponse({"status": "error", "message": msg}, status=status)


def success(data, meta):
    return JsonResponse({
        "status": "success",
        "page": meta["page"],
        "limit": meta["limit"],
        "total": meta["total"],
        "data": data
    })


# =========================
# GET /api/profiles
# =========================
def get_profiles(request):
    ensure_seed()

    qs = Profile.objects.all()

    # FILTERS
    if request.GET.get("gender"):
        qs = qs.filter(gender=request.GET["gender"])

    if request.GET.get("age_group"):
        qs = qs.filter(age_group=request.GET["age_group"])

    if request.GET.get("country_id"):
        qs = qs.filter(country_id=request.GET["country_id"])

    min_age = to_int(request.GET.get("min_age"))
    if request.GET.get("min_age") and min_age is None:
        return error("Invalid query parameters", 422)
    if min_age is not None:
        qs = qs.filter(age__gte=min_age)

    max_age = to_int(request.GET.get("max_age"))
    if request.GET.get("max_age") and max_age is None:
        return error("Invalid query parameters", 422)
    if max_age is not None:
        qs = qs.filter(age__lte=max_age)

    min_gp = to_float(request.GET.get("min_gender_probability"))
    if request.GET.get("min_gender_probability") and min_gp is None:
        return error("Invalid query parameters", 422)
    if min_gp is not None:
        qs = qs.filter(gender_probability__gte=min_gp)

    min_cp = to_float(request.GET.get("min_country_probability"))
    if request.GET.get("min_country_probability") and min_cp is None:
        return error("Invalid query parameters", 422)
    if min_cp is not None:
        qs = qs.filter(country_probability__gte=min_cp)

    # SORT
    sort_by = request.GET.get("sort_by", "created_at")
    order = request.GET.get("order", "asc")

    allowed = ["age", "created_at", "gender_probability"]

    if sort_by not in allowed:
        return error("Invalid query parameters", 422)

    if order not in ["asc", "desc"]:
        return error("Invalid query parameters", 422)

    if order == "desc":
        sort_by = "-" + sort_by

    qs = qs.order_by(sort_by)

    # PAGINATION
    page = request.GET.get("page", 1)
    limit = request.GET.get("limit", 10)

    result, meta = paginate(qs, page, limit)
    if result is None:
        return error(meta, 422)

    data = [serialize(p) for p in result]

    return success(data, meta)


# =========================
# GET /api/profiles/search
# =========================
def search_profiles(request):
    ensure_seed()

    q = request.GET.get("q", "").lower()

    if not q:
        return error("Missing or empty parameter", 400)

    qs = Profile.objects.all()
    parsed = False

    if "male" in q:
        qs = qs.filter(gender="male")
        parsed = True

    if "female" in q:
        qs = qs.filter(gender="female")
        parsed = True

    if "teenager" in q:
        qs = qs.filter(age_group="teenager")
        parsed = True

    if "adult" in q:
        qs = qs.filter(age_group="adult")
        parsed = True

    if "child" in q:
        qs = qs.filter(age_group="child")
        parsed = True

    if "senior" in q:
        qs = qs.filter(age_group="senior")
        parsed = True

    if "young" in q:
        qs = qs.filter(age__gte=16, age__lte=24)
        parsed = True

    countries = {
        "nigeria": "NG",
        "kenya": "KE",
        "ghana": "GH",
        "uganda": "UG",
        "tanzania": "TZ",
        "angola": "AO",
        "benin": "BJ",
    }

    for k, v in countries.items():
        if k in q:
            qs = qs.filter(country_id=v)
            parsed = True

    match = re.search(r"above (\d+)", q)
    if match:
        qs = qs.filter(age__gte=int(match.group(1)))
        parsed = True

    if not parsed:
        return error("Unable to interpret query", 422)

    page = request.GET.get("page", 1)
    limit = request.GET.get("limit", 10)

    result, meta = paginate(qs, page, limit)
    if result is None:
        return error(meta, 422)

    data = [serialize(p) for p in result]

    return success(data, meta)