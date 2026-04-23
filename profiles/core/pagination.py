def paginate(qs, page, limit):
    try:
        page = int(page)
        limit = int(limit)
    except:
        return None, "Invalid query parameters"

    if page < 1 or limit < 1:
        return None, "Invalid query parameters"

    if limit > 50:
        limit = 50

    total = qs.count()

    start = (page - 1) * limit
    end = start + limit

    return qs[start:end], {
        "page": page,
        "limit": limit,
        "total": total
    }