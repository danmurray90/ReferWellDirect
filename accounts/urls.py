"""
URL configuration for accounts app.
"""
from rest_framework.routers import DefaultRouter

from django.urls import include, path

from . import views

app_name = "accounts"

# Create router for API views
router = DefaultRouter()
router.register(r"users", views.UserViewSet)
router.register(r"organisations", views.OrganisationViewSet)
router.register(r"onboarding-steps", views.OnboardingStepViewSet)
router.register(r"onboarding-progress", views.UserOnboardingProgressViewSet)
router.register(r"onboarding-sessions", views.OnboardingSessionViewSet)

urlpatterns = [
    # Web views
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    # Authentication views
    path("signin/", views.signin, name="signin"),
    path("signout/", views.signout, name="signout"),
    path("signup/", views.signup, name="signup"),
    path("profile/", views.profile, name="profile"),
    # Onboarding views
    path("onboarding/start/", views.onboarding_start, name="onboarding_start"),
    path("onboarding/gp/start/", views.gp_onboarding_start, name="gp_onboarding_start"),
    path(
        "onboarding/psych/start/",
        views.psych_onboarding_start,
        name="psych_onboarding_start",
    ),
    path(
        "onboarding/step/<uuid:step_id>/", views.onboarding_step, name="onboarding_step"
    ),
    path(
        "onboarding/step/<uuid:step_id>/complete/",
        views.onboarding_complete_step,
        name="onboarding_complete_step",
    ),
    path(
        "onboarding/step/<uuid:step_id>/skip/",
        views.onboarding_skip_step,
        name="onboarding_skip_step",
    ),
    path("onboarding/progress/", views.onboarding_progress, name="onboarding_progress"),
    # Patient management views
    path("gp/patients/new/", views.gp_create_patient, name="gp_create_patient"),
    path(
        "gp/patients/<uuid:patient_id>/invite/",
        views.gp_invite_patient,
        name="gp_invite_patient",
    ),
    # Patient claim views
    path("claim/<str:token>/", views.patient_claim, name="patient_claim"),
    # API views
    path("api/", include(router.urls)),
]
