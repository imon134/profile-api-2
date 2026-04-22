import uuid
from django.db import models
from uuid_extensions import uuid7  # recommended

class Profile(models.Model):

    # UUID v7 PRIMARY KEY
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

    def __str__(self):
        return self.name