from django.http import JsonResponse


def success(data, pagination=None):
    payload = {"data": data}

    if pagination:
        payload["pagination"] = {
            "page": int(pagination["page"]),
            "limit": int(pagination["limit"]),
            "total": int(pagination["total"]),
            "pages": int(pagination["pages"]),
        }

    return JsonResponse(payload, json_dumps_params={"ensure_ascii": False})


def error(code, message, status=400):
    return JsonResponse(
        {
            "error": {
                "code": str(code),
                "message": str(message)
            }
        },
        status=status,
        json_dumps_params={"ensure_ascii": False}
    )