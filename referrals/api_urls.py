"""
API URL configuration for referrals app.
"""
from django.urls import path

from . import views

app_name = "referrals_api"

urlpatterns = [
    # Referral API endpoints
    path("referrals/", views.ReferralListAPIView.as_view(), name="referral-list"),
    path(
        "referrals/<uuid:id>/",
        views.ReferralDetailAPIView.as_view(),
        name="referral-detail",
    ),
    path(
        "referrals/<uuid:referral_id>/submit/",
        views.submit_referral,
        name="submit-referral",
    ),
    # Candidate API endpoints
    path(
        "referrals/<uuid:referral_id>/candidates/",
        views.CandidateListAPIView.as_view(),
        name="candidate-list",
    ),
    path(
        "candidates/<uuid:id>/",
        views.CandidateDetailAPIView.as_view(),
        name="candidate-detail",
    ),
    path(
        "candidates/<uuid:candidate_id>/respond/",
        views.respond_to_invitation,
        name="respond-to-invitation",
    ),
    # Advanced Search API endpoints
    path("search/suggestions/", views.search_suggestions, name="search-suggestions"),
    path("search/facets/", views.search_facets, name="search-facets"),
    path("search/analytics/", views.search_analytics, name="search-analytics"),
    # Bulk Operations API endpoints
    path("bulk/update-status/", views.bulk_update_status, name="bulk-update-status"),
    path(
        "bulk/assign-referrer/", views.bulk_assign_referrer, name="bulk-assign-referrer"
    ),
    path("bulk/export/", views.bulk_export, name="bulk-export"),
    # Appointment Bulk Operations API endpoints
    path(
        "bulk/appointments/update-status/",
        views.bulk_update_appointment_status,
        name="bulk-update-appointment-status",
    ),
    path(
        "bulk/appointments/reschedule/",
        views.bulk_reschedule_appointments,
        name="bulk-reschedule-appointments",
    ),
    path(
        "bulk/appointments/assign-psychologist/",
        views.bulk_assign_psychologist,
        name="bulk-assign-psychologist",
    ),
    path(
        "bulk/appointments/export/",
        views.bulk_export_appointments,
        name="bulk-export-appointments",
    ),
    # Task Bulk Operations API endpoints
    path(
        "bulk/tasks/update-status/",
        views.bulk_update_task_status,
        name="bulk-update-task-status",
    ),
    path(
        "bulk/tasks/assign-user/",
        views.bulk_assign_task_user,
        name="bulk-assign-task-user",
    ),
]
