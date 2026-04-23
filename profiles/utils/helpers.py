def clean_str(v):
    if v is None:
        return ""
    return str(v).strip().lower()


def safe_int(v):
    try:
        return int(v)
    except:
        return None


def safe_float(v):
    try:
        return float(v)
    except:
        return None