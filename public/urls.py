"""
URL configuration for public app.
"""
from django.urls import path

from . import views

app_name = "public"

urlpatterns = [
    # Public landing pages
    path("", views.landing_page, name="landing"),
    path("for-gps/", views.for_gps, name="for_gps"),
    path("for-psychologists/", views.for_psychologists, name="for_psychologists"),
    path("for-patients/", views.for_patients, name="for_patients"),
]
