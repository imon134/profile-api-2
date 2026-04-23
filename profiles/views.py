import re
from django.http import JsonResponse
from .models import Profile


# ---------------- HELPER ----------------
def error(message, status_code):
    return JsonResponse(
        {"status": "error", "message": message},
        status=status_code
    )


# ---------------- GET PROFILES ----------------
def get_profiles(request):
    try:
        qs = Profile.objects.all()

        # ---------- FILTERS ----------
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
            qs = qs.filter(age__gte=int(min_age))

        max_age = request.GET.get("max_age")
        if max_age:
            qs = qs.filter(age__lte=int(max_age))

        min_gp = request.GET.get("min_gender_probability")
        if min_gp:
            qs = qs.filter(gender_probability__gte=float(min_gp))

        min_cp = request.GET.get("min_country_probability")
        if min_cp:
            qs = qs.filter(country_probability__gte=float(min_cp))

        # ---------- SORTING ----------
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

        # ---------- PAGINATION ----------
        page = request.GET.get("page", "1")
        limit = request.GET.get("limit", "10")

        if not page.isdigit() or not limit.isdigit():
            return error("Invalid query parameters", 422)

        page = max(int(page), 1)
        limit = min(int(limit), 50)

        start = (page - 1) * limit
        end = start + limit

        total = qs.count()

        data = list(qs[start:end].values(
            "id",
            "name",
            "gender",
            "gender_probability",
            "age",
            "age_group",
            "country_id",
            "country_name",
            "country_probability",
            "created_at"
        ))

        return JsonResponse({
            "status": "success",
            "page": page,
            "limit": limit,
            "total": total,
            "data": data
        })

    except Exception:
        return error("Server failure", 500)


# ---------------- SEARCH (NATURAL LANGUAGE) ----------------
def search_profiles(request):
    try:
        q = request.GET.get("q", "").lower().strip()

        if not q:
            return error("Missing query parameter", 400)

        qs = Profile.objects.all()

        # ---------- RULE BASED PARSING ----------

        # gender
        if "male" in q and "female" not in q:
            qs = qs.filter(gender="male")
        elif "female" in q:
            qs = qs.filter(gender="female")

        # age groups
        if "child" in q:
            qs = qs.filter(age_group="child")
        elif "teenager" in q:
            qs = qs.filter(age_group="teenager")
        elif "adult" in q:
            qs = qs.filter(age_group="adult")
        elif "senior" in q:
            qs = qs.filter(age_group="senior")

        # "young" rule
        if "young" in q:
            qs = qs.filter(age__gte=16, age__lte=24)

        # age conditions
        above = re.search(r"above (\d+)", q)
        if above:
            qs = qs.filter(age__gte=int(above.group(1)))

        below = re.search(r"below (\d+)", q)
        if below:
            qs = qs.filter(age__lte=int(below.group(1)))

        # country mapping
        countries = {
            "nigeria": "NG",
            "ghana": "GH",
            "kenya": "KE",
            "angola": "AO",
            "uganda": "UG",
            "tanzania": "TZ"
        }

        matched_country = False
        for k, v in countries.items():
            if k in q:
                qs = qs.filter(country_id=v)
                matched_country = True

        # if nothing matched at all
        if not matched_country and "male" not in q and "female" not in q \
           and "young" not in q and not above and not below:
            return error("Unable to interpret query", 422)

        # ---------- PAGINATION ----------
        page = request.GET.get("page", "1")
        limit = request.GET.get("limit", "10")

        if not page.isdigit() or not limit.isdigit():
            return error("Invalid query parameters", 422)

        page = max(int(page), 1)
        limit = min(int(limit), 50)

        start = (page - 1) * limit
        end = start + limit

        if not qs.exists():
            return error("Profile not found", 404)

        data = list(qs[start:end].values(
            "id",
            "name",
            "gender",
            "gender_probability",
            "age",
            "age_group",
            "country_id",
            "country_name",
            "country_probability",
            "created_at"
        ))

        return JsonResponse({
            "status": "success",
            "page": page,
            "limit": limit,
            "total": qs.count(),
            "data": data
        })

    except Exception:
        return error("Server failure", 500)