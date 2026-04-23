import os
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "profile_project.settings")
application = get_wsgi_application()

try:
    call_command("seed_profiles")
except Exception:
    pass