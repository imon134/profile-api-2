import os
import dj_database_url

DEBUG = False

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get("DATABASE_URL")
    )
}

USE_TZ = True
TIME_ZONE = "UTC"