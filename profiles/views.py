from django.http import JsonResponse
from .models import Profile


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

        # ---------------- SORTING ----------------
        sort_by = request.GET.get("sort_by", "created_at")
        order = request.GET.get("order", "asc")

        allowed = ["age", "created_at", "gender_probability"]
        if sort_by not in allowed:
            return JsonResponse(
                {"status": "error", "message": "Invalid query parameters"},
                status=422
            )

        if order == "desc":
            sort_by = "-" + sort_by

        qs = qs.order_by(sort_by)

        # ---------------- PAGINATION ----------------
        page = int(request.GET.get("page", 1))
        limit = min(int(request.GET.get("limit", 10)), 50)

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

    except Exception:
        return JsonResponse(
            {"status": "error", "message": "Server failure"},
            status=500
        )