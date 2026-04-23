def paginate(qs, page, limit):
    try:
        page = int(page)
    except:
        page = 1

    try:
        limit = int(limit)
    except:
        limit = 10

    if page < 1:
        page = 1

    if limit < 1:
        limit = 1

    if limit > 50:
        limit = 50

    total = qs.count()

    start = (page - 1) * limit
    end = start + limit

    return qs[start:end], {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit if total else 1
    }