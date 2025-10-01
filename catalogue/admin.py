"""
Admin configuration for catalogue app.
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import Availability, Psychologist, Qualification, Review, Specialism


@admin.register(Psychologist)
class PsychologistAdmin(admin.ModelAdmin):
    """
    Psychologist admin with comprehensive filtering and display.
    """

    list_display = (
        "user",
        "service_type",
        "modality",
        "availability_status",
        "is_verified",
        "is_active",
        "created_at",
    )
    list_filter = (
        "service_type",
        "modality",
        "availability_status",
        "is_verified",
        "is_active",
        "created_at",
    )
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "registration_number",
        "specialisms",
    )
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Basic Info",
            {
                "fields": (
                    "user",
                    "title",
                    "is_verified",
                    "is_active",
                    "is_accepting_referrals",
                )
            },
        ),
        (
            "Professional Info",
            {
                "fields": (
                    "qualifications",
                    "specialisms",
                    "languages",
                    "registration_number",
                    "registration_body",
                    "years_experience",
                )
            },
        ),
        (
            "Service Info",
            {"fields": ("service_type", "modality", "hourly_rate", "session_duration")},
        ),
        (
            "Location",
            {
                "fields": (
                    "location",
                    "address_line_1",
                    "address_line_2",
                    "city",
                    "postcode",
                    "country",
                )
            },
        ),
        (
            "Availability",
            {
                "fields": (
                    "availability_status",
                    "max_patients",
                    "current_patients",
                    "max_distance_km",
                )
            },
        ),
        ("Preferences", {"fields": ("preferred_age_groups", "preferred_conditions")}),
        ("Matching", {"fields": ("embedding", "last_updated_embedding")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
        ("Audit", {"fields": ("created_by",)}),
    )

    readonly_fields = ("created_at", "updated_at", "last_updated_embedding")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "created_by")


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    """
    Availability admin for managing psychologist schedules.
    """

    list_display = (
        "psychologist",
        "day_of_week",
        "start_time",
        "end_time",
        "modality",
        "is_active",
    )
    list_filter = ("day_of_week", "modality", "is_active", "created_at")
    search_fields = ("psychologist__user__first_name", "psychologist__user__last_name")
    ordering = ("psychologist", "day_of_week", "start_time")

    fieldsets = (
        (
            "Basic Info",
            {
                "fields": (
                    "psychologist",
                    "day_of_week",
                    "start_time",
                    "end_time",
                    "modality",
                )
            },
        ),
        ("Status", {"fields": ("is_active",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("psychologist__user")


@admin.register(Specialism)
class SpecialismAdmin(admin.ModelAdmin):
    """
    Specialism admin for managing psychologist specialisms.
    """

    list_display = ("name", "category", "is_active", "created_at")
    list_filter = ("category", "is_active", "created_at")
    search_fields = ("name", "description", "category")
    ordering = ("name",)

    fieldsets = (
        ("Basic Info", {"fields": ("name", "description", "category")}),
        ("Status", {"fields": ("is_active",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")


@admin.register(Qualification)
class QualificationAdmin(admin.ModelAdmin):
    """
    Qualification admin for managing psychologist qualifications.
    """

    list_display = ("name", "abbreviation", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description", "abbreviation")
    ordering = ("name",)

    fieldsets = (
        ("Basic Info", {"fields": ("name", "description", "abbreviation")}),
        ("Status", {"fields": ("is_active",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Review admin for managing psychologist reviews.
    """

    list_display = (
        "psychologist",
        "patient",
        "rating",
        "title",
        "is_verified",
        "is_public",
        "created_at",
    )
    list_filter = ("rating", "is_verified", "is_public", "created_at")
    search_fields = (
        "psychologist__user__first_name",
        "psychologist__user__last_name",
        "patient__first_name",
        "patient__last_name",
        "title",
    )
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Basic Info",
            {"fields": ("psychologist", "patient", "rating", "title", "content")},
        ),
        ("Status", {"fields": ("is_verified", "is_public")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("psychologist__user", "patient")
        )
