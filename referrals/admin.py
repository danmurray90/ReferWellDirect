"""
Admin configuration for referrals app.
"""
from typing import Any

from django.contrib import admin

from .models import Appointment, Candidate, Message, Referral, Task


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    """
    Referral admin with comprehensive filtering and display.
    """

    list_display = (
        "referral_id",
        "patient",
        "referrer",
        "status",
        "priority",
        "service_type",
        "created_at",
    )
    list_filter = ("status", "priority", "service_type", "modality", "created_at")
    search_fields = (
        "referral_id",
        "patient__first_name",
        "patient__last_name",
        "referrer__first_name",
        "referrer__last_name",
    )
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Basic Info",
            {"fields": ("referral_id", "referrer", "patient", "status", "priority")},
        ),
        (
            "Service Preferences",
            {"fields": ("service_type", "modality", "preferred_language")},
        ),
        (
            "Clinical Information",
            {"fields": ("presenting_problem", "clinical_notes", "urgency_notes")},
        ),
        (
            "Patient Preferences",
            {
                "fields": (
                    "patient_preferences",
                    "preferred_location",
                    "max_distance_km",
                    "required_specialisms",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at", "submitted_at", "completed_at")},
        ),
        ("Audit", {"fields": ("created_by",)}),
    )

    readonly_fields = (
        "referral_id",
        "created_at",
        "updated_at",
        "submitted_at",
        "completed_at",
    )

    def get_queryset(self, request: Any) -> Any:
        return (
            super()
            .get_queryset(request)
            .select_related("referrer", "patient", "created_by")
        )


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    """
    Candidate admin for managing referral candidates.
    """

    list_display = (
        "referral",
        "psychologist",
        "status",
        "final_score",
        "confidence_score",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "referral__referral_id",
        "psychologist__first_name",
        "psychologist__last_name",
    )
    ordering = ("-created_at",)

    fieldsets = (
        ("Basic Info", {"fields": ("referral", "psychologist", "status")}),
        (
            "Scores",
            {
                "fields": (
                    "similarity_score",
                    "structured_score",
                    "final_score",
                    "confidence_score",
                )
            },
        ),
        ("Matching Details", {"fields": ("matching_explanation",)}),
        (
            "Invitation",
            {"fields": ("invited_at", "responded_at", "expires_at", "response_notes")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request: Any) -> Any:
        return super().get_queryset(request).select_related("referral", "psychologist")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """
    Appointment admin for managing scheduled appointments.
    """

    list_display = (
        "id",
        "patient",
        "psychologist",
        "scheduled_at",
        "status",
        "modality",
        "duration_minutes",
    )
    list_filter = ("status", "modality", "scheduled_at")
    search_fields = (
        "patient__first_name",
        "patient__last_name",
        "psychologist__first_name",
        "psychologist__last_name",
    )
    ordering = ("-scheduled_at",)

    fieldsets = (
        ("Basic Info", {"fields": ("referral", "patient", "psychologist", "status")}),
        (
            "Appointment Details",
            {"fields": ("scheduled_at", "duration_minutes", "location", "modality")},
        ),
        ("Notes", {"fields": ("notes", "outcome_notes")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at", "confirmed_at", "completed_at")},
        ),
    )

    readonly_fields = ("created_at", "updated_at", "confirmed_at", "completed_at")

    def get_queryset(self, request: Any) -> Any:
        return (
            super()
            .get_queryset(request)
            .select_related("referral", "patient", "psychologist")
        )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Message admin for managing communication messages.
    """

    list_display = (
        "subject",
        "sender",
        "recipient",
        "message_type",
        "is_read",
        "is_important",
        "created_at",
    )
    list_filter = ("message_type", "is_read", "is_important", "created_at")
    search_fields = (
        "subject",
        "sender__first_name",
        "sender__last_name",
        "recipient__first_name",
        "recipient__last_name",
    )
    ordering = ("-created_at",)

    fieldsets = (
        ("Basic Info", {"fields": ("referral", "sender", "recipient", "message_type")}),
        ("Content", {"fields": ("subject", "content")}),
        ("Status", {"fields": ("is_read", "is_important", "read_at")}),
        ("Timestamps", {"fields": ("created_at",)}),
    )

    readonly_fields = ("created_at", "read_at")

    def get_queryset(self, request: Any) -> Any:
        return (
            super()
            .get_queryset(request)
            .select_related("referral", "sender", "recipient")
        )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
    Task admin for managing tasks and reminders.
    """

    list_display = (
        "title",
        "assigned_to",
        "task_type",
        "priority",
        "is_completed",
        "is_overdue",
        "due_at",
    )
    list_filter = ("task_type", "priority", "is_completed", "is_overdue", "created_at")
    search_fields = ("title", "assigned_to__first_name", "assigned_to__last_name")
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Basic Info",
            {"fields": ("referral", "assigned_to", "created_by", "task_type")},
        ),
        ("Task Details", {"fields": ("title", "description", "priority")}),
        ("Status", {"fields": ("is_completed", "is_overdue", "completed_at")}),
        ("Timestamps", {"fields": ("created_at", "updated_at", "due_at")}),
    )

    readonly_fields = ("created_at", "updated_at", "completed_at")

    def get_queryset(self, request: Any) -> Any:
        return (
            super()
            .get_queryset(request)
            .select_related("referral", "assigned_to", "created_by")
        )
