"""
API URL configuration for accounts app.
"""
from rest_framework.routers import DefaultRouter

from django.urls import include, path

from . import views

app_name = "accounts_api"

# Create router for API views
router = DefaultRouter()
router.register(r"users", views.UserViewSet)
router.register(r"organisations", views.OrganisationViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
