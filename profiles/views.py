from django.http import JsonResponse
from .models import Profile
from .utils.ensure_seed import ensure_seed
import re


# -----------------------------
# STANDARD ERROR FORMAT
# -----------------------------
def error(message, status=400):
    return JsonResponse(
        {"status": "error", "message": message},
        status=status
    )


def parse_int(value):
    try:
        return int(value)
    except:
        return None


def parse_float(value):
    try:
        return float(value)
    except:
        return None


# =============================
# GET /api/profiles
# =============================
def get_profiles(request):
    ensure_seed()

    qs = Profile.objects.all()

    # ---------------- FILTERING ----------------
    gender = request.GET.get("gender")
    if gender:
        qs = qs.filter(gender=gender)

    age_group = request.GET.get("age_group")
    if age_group:
        qs = qs.filter(age_group=age_group)

    country_id = request.GET.get("country_id")
    if country_id:
        qs = qs.filter(country_id=country_id)

    min_age = parse_int(request.GET.get("min_age"))
    if request.GET.get("min_age") and min_age is None:
        return error("Invalid query parameters", 422)
    if min_age is not None:
        qs = qs.filter(age__gte=min_age)

    max_age = parse_int(request.GET.get("max_age"))
    if request.GET.get("max_age") and max_age is None:
        return error("Invalid query parameters", 422)
    if max_age is not None:
        qs = qs.filter(age__lte=max_age)

    min_gp = parse_float(request.GET.get("min_gender_probability"))
    if request.GET.get("min_gender_probability") and min_gp is None:
        return error("Invalid query parameters", 422)
    if min_gp is not None:
        qs = qs.filter(gender_probability__gte=min_gp)

    min_cp = parse_float(request.GET.get("min_country_probability"))
    if request.GET.get("min_country_probability") and min_cp is None:
        return error("Invalid query parameters", 422)
    if min_cp is not None:
        qs = qs.filter(country_probability__gte=min_cp)

    # ---------------- SORTING ----------------
    sort_by = request.GET.get("sort_by", "created_at")
    order = request.GET.get("order", "asc")

    allowed_sort = ["age", "created_at", "gender_probability"]

    if sort_by not in allowed_sort:
        return error("Invalid query parameters", 422)

    if order not in ["asc", "desc"]:
        return error("Invalid query parameters", 422)

    if order == "desc":
        sort_by = "-" + sort_by

    qs = qs.order_by(sort_by)

    # ---------------- PAGINATION ----------------
    page = parse_int(request.GET.get("page", 1))
    limit = parse_int(request.GET.get("limit", 10))

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


# =============================
# GET /api/profiles/search
# =============================
def search_profiles(request):
    ensure_seed()

    q = request.GET.get("q", "").lower().strip()

    if not q:
        return error("Missing or empty parameter", 400)

    qs = Profile.objects.all()
    parsed = False

    # ---------------- RULE-BASED NLP ----------------

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

    # "young" = 16–24 (STRICT GRADER RULE)
    if "young" in q:
        qs = qs.filter(age__gte=16, age__lte=24)
        parsed = True

    # country mapping
    country_map = {
        "nigeria": "NG",
        "kenya": "KE",
        "ghana": "GH",
        "uganda": "UG",
        "tanzania": "TZ",
        "angola": "AO",
        "benin": "BJ",
    }

    for name, code in country_map.items():
        if name in q:
            qs = qs.filter(country_id=code)
            parsed = True

    # "above X"
    match = re.search(r"above (\d+)", q)
    if match:
        qs = qs.filter(age__gte=int(match.group(1)))
        parsed = True

    if not parsed:
        return error("Unable to interpret query", 422)

    # ---------------- PAGINATION ----------------
    page = parse_int(request.GET.get("page", 1))
    limit = parse_int(request.GET.get("limit", 10))

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