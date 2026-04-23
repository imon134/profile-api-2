from django.http import JsonResponse
from django.db.models import Q
from .models import Profile
from .utils.ensure_seed import ensure_seed


# -------------------------
# Helpers
# -------------------------

def error(message, status=400):
    return JsonResponse(
        {"status": "error", "message": message},
        status=status
    )


def validate_int(value):
    try:
        return int(value)
    except:
        return None


def validate_float(value):
    try:
        return float(value)
    except:
        return None


# -------------------------
# GET /api/profiles
# -------------------------
def get_profiles(request):
    ensure_seed()

    qs = Profile.objects.all()

    # ---------------- FILTERS ----------------
    gender = request.GET.get("gender")
    if gender:
        qs = qs.filter(gender=gender)

    age_group = request.GET.get("age_group")
    if age_group:
        qs = qs.filter(age_group=age_group)

    country_id = request.GET.get("country_id")
    if country_id:
        qs = qs.filter(country_id=country_id)

    min_age = request.GET.get("min_age")
    if min_age:
        min_age = validate_int(min_age)
        if min_age is None:
            return error("Invalid query parameters", 422)
        qs = qs.filter(age__gte=min_age)

    max_age = request.GET.get("max_age")
    if max_age:
        max_age = validate_int(max_age)
        if max_age is None:
            return error("Invalid query parameters", 422)
        qs = qs.filter(age__lte=max_age)

    min_gp = request.GET.get("min_gender_probability")
    if min_gp:
        min_gp = validate_float(min_gp)
        if min_gp is None:
            return error("Invalid query parameters", 422)
        qs = qs.filter(gender_probability__gte=min_gp)

    min_cp = request.GET.get("min_country_probability")
    if min_cp:
        min_cp = validate_float(min_cp)
        if min_cp is None:
            return error("Invalid query parameters", 422)
        qs = qs.filter(country_probability__gte=min_cp)

    # ---------------- SORTING ----------------
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

    # ---------------- PAGINATION ----------------
    page = validate_int(request.GET.get("page", 1))
    limit = validate_int(request.GET.get("limit", 10))

    if page is None or page < 1:
        return error("Invalid query parameters", 422)

    if limit is None or limit < 1:
        return error("Invalid query parameters", 422)

    if limit > 50:
        limit = 50

    start = (page - 1) * limit
    end = start + limit

    total = qs.count()

    return JsonResponse({
        "status": "success",
        "page": page,
        "limit": limit,
        "total": total,
        "data": list(qs[start:end].values())
    })


# -------------------------
# GET /api/profiles/search
# -------------------------
def search_profiles(request):
    ensure_seed()

    q = request.GET.get("q", "").lower().strip()

    if not q:
        return error("Missing or empty parameter", 400)

    qs = Profile.objects.all()

    parsed = False

    # ---------------- RULE-BASED PARSING ----------------

    # gender
    if "male" in q:
        qs = qs.filter(gender="male")
        parsed = True

    if "female" in q:
        qs = qs.filter(gender="female")
        parsed = True

    # age groups
    if "child" in q:
        qs = qs.filter(age_group="child")
        parsed = True

    if "teenager" in q:
        qs = qs.filter(age_group="teenager")
        parsed = True

    if "adult" in q:
        qs = qs.filter(age_group="adult")
        parsed = True

    if "senior" in q:
        qs = qs.filter(age_group="senior")
        parsed = True

    # country mapping (basic ISO examples)
    country_map = {
        "nigeria": "NG",
        "kenya": "KE",
        "ghana": "GH",
        "angola": "AO",
        "uganda": "UG",
        "tanzania": "TZ",
        "benin": "BJ",
    }

    for k, v in country_map.items():
        if k in q:
            qs = qs.filter(country_id=v)
            parsed = True

    # age rules
    if "young" in q:
        qs = qs.filter(age__gte=16, age__lte=24)
        parsed = True

    if "above" in q:
        import re
        match = re.search(r"above (\d+)", q)
        if match:
            qs = qs.filter(age__gte=int(match.group(1)))
            parsed = True

    # ---------------- IF NOTHING MATCHED ----------------
    if not parsed:
        return error("Unable to interpret query", 422)

    # ---------------- PAGINATION ----------------
    page = validate_int(request.GET.get("page", 1))
    limit = validate_int(request.GET.get("limit", 10))

    if page is None or limit is None:
        return error("Invalid query parameters", 422)

    if limit > 50:
        limit = 50

    start = (page - 1) * limit
    end = start + limit

    total = qs.count()

    return JsonResponse({
        "status": "success",
        "page": page,
        "limit": limit,
        "total": total,
        "data": list(qs[start:end].values())
    })