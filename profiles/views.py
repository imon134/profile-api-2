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

    if request.method != "GET":
        return cors(error("Method not allowed", 405))

    try:
        gender = request.GET.get("gender")
        age_group = request.GET.get("age_group")
        country_id = request.GET.get("country_id")

        min_age = request.GET.get("min_age")
        max_age = request.GET.get("max_age")

        min_gender_probability = request.GET.get("min_gender_probability")
        min_country_probability = request.GET.get("min_country_probability")

        sort_by = request.GET.get("sort_by", "created_at")
        order = request.GET.get("order", "asc")

        page = int(request.GET.get("page", 1))
        limit = min(int(request.GET.get("limit", 10)), 50)

    except:
        return cors(error("Invalid query parameters", 422))

    qs = Profile.objects.all()

    # FILTERS (ALL COMBINABLE)
    if gender:
        qs = qs.filter(gender=gender)

    if age_group:
        qs = qs.filter(age_group=age_group)

    if country_id:
        qs = qs.filter(country_id=country_id)

    if min_age:
        qs = qs.filter(age__gte=min_age)

    if max_age:
        qs = qs.filter(age__lte=max_age)

    if min_gender_probability:
        qs = qs.filter(gender_probability__gte=min_gender_probability)

    if min_country_probability:
        qs = qs.filter(country_probability__gte=min_country_probability)

    # SORTING
    allowed = ["age", "created_at", "gender_probability"]
    if sort_by not in allowed:
        sort_by = "created_at"

    if order == "desc":
        sort_by = "-" + sort_by

    qs = qs.order_by(sort_by)

    # PAGINATION (NO FULL SCAN)
    total = qs.count()
    start = (page - 1) * limit
    end = start + limit

    data = qs[start:end]

    return cors(JsonResponse({
        "status": "success",
        "page": page,
        "limit": limit,
        "total": total,
        "data": [
            {
                "id": str(p.id),
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
            for p in data
        ]
    }))

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

    q = request.GET.get("q")

    if not q:
        return cors(error("Missing or empty parameter", 400))

    parsed = parse_query(q)

    if not parsed:
        return cors(error("Unable to interpret query", 400))

    qs = Profile.objects.all()

    if "gender" in parsed:
        qs = qs.filter(gender=parsed["gender"])

    if "country_id" in parsed:
        qs = qs.filter(country_id=parsed["country_id"])

    if "age_group" in parsed:
        qs = qs.filter(age_group=parsed["age_group"])

    if "min_age" in parsed:
        qs = qs.filter(age__gte=parsed["min_age"])

    if "max_age" in parsed:
        qs = qs.filter(age__lte=parsed["max_age"])

    return cors(JsonResponse({
        "status": "success",
        "data": [
            {
                "id": str(p.id),
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
            for p in qs
        ]
    }))