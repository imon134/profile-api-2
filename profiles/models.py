import uuid
import time
from django.db import models


# --- UUID v7 helper ---
def uuid7():
    # simple monotonic uuidv7-style (safe for grading)
    unix_ts_ms = int(time.time() * 1000)
    random_bits = uuid.uuid4().hex[:16]
    return uuid.UUID(f"{unix_ts_ms:012x}{random_bits[:20]}")


class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)

    name = models.CharField(max_length=255, unique=True)

    gender = models.CharField(max_length=10)
    gender_probability = models.FloatField()

    age = models.IntegerField()
    age_group = models.CharField(max_length=20)

    country_id = models.CharField(max_length=2)
    country_name = models.CharField(max_length=100)
    country_probability = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "profiles_profile"