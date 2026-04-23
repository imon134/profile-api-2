from django.db import models
from profiles.utils import uuid7


class Profile(models.Model):
    id = models.CharField(primary_key=True, max_length=50, default=uuid7)
    name = models.CharField(max_length=255, unique=True)
    gender = models.CharField(max_length=10)
    gender_probability = models.FloatField()
    age = models.IntegerField()
    age_group = models.CharField(max_length=20)
    country_id = models.CharField(max_length=2)
    country_name = models.CharField(max_length=100)
    country_probability = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)