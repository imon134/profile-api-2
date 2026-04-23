from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def home(request):
    return JsonResponse({"status": "API is live"})

urlpatterns = [
    path("", home),
    path("api/", include("profiles.urls")),
]