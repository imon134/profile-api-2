import json
from django.http import JsonResponse
from django.db.models import Q
from .models import Profile

# ---------------- ERROR FORMAT ----------------

def error(message, code=400):
    return JsonResponse({
        "status": "error",
        "message": message
    }, status=code)


# ---------------- CORS WRAPPER ----------------
def cors(response):
    response["Access-Control-Allow-Origin"] = "*"
    return response


# ---------------- GET ALL PROFILES ----------------
def get_profiles(request):
    try:
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
        if min_age is not None:
            try:
                qs = qs.filter(age__gte=int(min_age))
            except ValueError:
                return JsonResponse(
                    {"status": "error", "message": "Invalid query parameters"},
                    status=422
                )

        max_age = request.GET.get("max_age")
        if max_age is not None:
            try:
                qs = qs.filter(age__lte=int(max_age))
            except ValueError:
                return JsonResponse(
                    {"status": "error", "message": "Invalid query parameters"},
                    status=422
                )

        min_gender_prob = request.GET.get("min_gender_probability")
        if min_gender_prob is not None:
            try:
                qs = qs.filter(gender_probability__gte=float(min_gender_prob))
            except ValueError:
                return JsonResponse(
                    {"status": "error", "message": "Invalid query parameters"},
                    status=422
                )

        min_country_prob = request.GET.get("min_country_probability")
        if min_country_prob is not None:
            try:
                qs = qs.filter(country_probability__gte=float(min_country_prob))
            except ValueError:
                return JsonResponse(
                    {"status": "error", "message": "Invalid query parameters"},
                    status=422
                )

        # ---------------- SORTING ----------------
        sort_by = request.GET.get("sort_by", "created_at")
        order = request.GET.get("order", "asc")

        allowed_sort_fields = ["age", "created_at", "gender_probability"]

        if sort_by not in allowed_sort_fields:
            sort_by = "created_at"

        if order == "desc":
            sort_by = "-" + sort_by

        qs = qs.order_by(sort_by)

        # ---------------- PAGINATION ----------------
        try:
            page = int(request.GET.get("page", 1))
            limit = int(request.GET.get("limit", 10))
        except ValueError:
            return JsonResponse(
                {"status": "error", "message": "Invalid query parameters"},
                status=422
            )

        limit = min(limit, 50)
        start = (page - 1) * limit
        end = start + limit

        total = qs.count()
        data = list(qs[start:end].values())

        # ---------------- RESPONSE ----------------
        return JsonResponse({
            "status": "success",
            "page": page,
            "limit": limit,
            "total": total,
            "data": data
        })

    except Exception:
        return JsonResponse(
            {"status": "error", "message": "Server failure"},
            status=500
        )

def parse_query(q):

    q = q.lower()

    f = {}

    # COUNTRY MAP
    countries = {
        "nigeria": "NG",
        "kenya": "KE",
        "angola": "AO",
        "benin": "BJ"
    }

    for k, v in countries.items():
        if k in q:
            f["country_id"] = v

    # GENDER
    if "male" in q:
        f["gender"] = "male"

    if "female" in q:
        f["gender"] = "female"

    # AGE GROUP
    if "adult" in q:
        f["age_group"] = "adult"

    if "teenager" in q:
        f["age_group"] = "teenager"

    if "child" in q:
        f["age_group"] = "child"

    if "senior" in q:
        f["age_group"] = "senior"

    # NATURAL AGE RULES
    if "young" in q:
        f["min_age"] = 16
        f["max_age"] = 24

    if "above 30" in q:
        f["min_age"] = 30

    if "above 17" in q:
        f["min_age"] = 17

    return f


def search_profiles(request):
    q = request.GET.get("q", "").lower().strip()

    if not q:
        return JsonResponse({"status": "error", "message": "Missing or empty parameter"}, status=400)

    qs = Profile.objects.all()

    # RULES
    if "young" in q:
        qs = qs.filter(age__gte=16, age__lte=24)

    if "male" in q:
        qs = qs.filter(gender="male")

    if "female" in q:
        qs = qs.filter(gender="female")

    if "angola" in q:
        qs = qs.filter(country_id="AO")

    if "nigeria" in q:
        qs = qs.filter(country_id="NG")

    if "adult" in q:
        qs = qs.filter(age_group="adult")

    if "teen" in q:
        qs = qs.filter(age_group="teenager")

    # pagination
    page = int(request.GET.get("page", 1))
    limit = min(int(request.GET.get("limit", 10)), 50)

    start = (page - 1) * limit
    end = start + limit

    return JsonResponse({
        "status": "success",
        "page": page,
        "limit": limit,
        "total": qs.count(),
        "data": list(qs[start:end].values())
    })