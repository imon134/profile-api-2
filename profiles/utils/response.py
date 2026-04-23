from django.http import JsonResponse


def success(data, pagination=None):
    res = {"data": data}
    if pagination:
        res["pagination"] = pagination
    return JsonResponse(res)


def error(code, message, status=400):
    return JsonResponse(
        {
            "error": {
                "code": code,
                "message": message
            }
        },
        status=status
    )