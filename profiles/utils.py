import time
import random
from datetime import datetime, timezone
import httpx

def uuid7():
    ts = int(time.time() * 1000)
    rand = random.getrandbits(80)
    return f"{ts:012x}-{rand:020x}"

def now_iso():
    return datetime.now(timezone.utc)

def age_group(age):
    if age <= 12:
        return "child"
    elif age <= 19:
        return "teenager"
    elif age <= 59:
        return "adult"
    return "senior"

def fetch_external(name):
    try:
        g = httpx.get("https://api.genderize.io", params={"name": name}).json()
        a = httpx.get("https://api.agify.io", params={"name": name}).json()
        n = httpx.get("https://api.nationalize.io", params={"name": name}).json()
    except:
        return None, ("External API failure", 502)

    if g.get("gender") is None or g.get("count", 0) == 0:
        return None, ("Genderize invalid", 502)

    if a.get("age") is None:
        return None, ("Agify invalid", 502)

    countries = n.get("country", [])
    if not countries:
        return None, ("Nationalize invalid", 502)

    top = max(countries, key=lambda x: x["probability"])

    return {
        "gender": g["gender"],
        "gender_probability": g["probability"],
        "sample_size": g["count"],
        "age": a["age"],
        "age_group": age_group(a["age"]),
        "country_id": top["country_id"],
        "country_probability": top["probability"]
    }, None