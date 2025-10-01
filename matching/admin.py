"""
Admin configuration for matching app.
"""
from typing import Any

from django.contrib import admin

from .models import CalibrationModel, MatchingAlgorithm, MatchingRun, MatchingThreshold


@admin.register(MatchingRun)
class MatchingRunAdmin(admin.ModelAdmin):
    """
    Matching run admin.
    """

    list_display = (
        "referral",
        "status",
        "candidates_found",
        "candidates_shortlisted",
        "candidates_invited",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("referral__referral_id",)
    ordering = ("-created_at",)

    fieldsets = (
        ("Basic Info", {"fields": ("referral", "status")}),
        ("Timing", {"fields": ("started_at", "completed_at")}),
        (
            "Results",
            {
                "fields": (
                    "candidates_found",
                    "candidates_shortlisted",
                    "candidates_invited",
                )
            },
        ),
        ("Configuration", {"fields": ("config",)}),
        ("Error Handling", {"fields": ("error_message",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request: Any) -> Any:
        return super().get_queryset(request).select_related("referral")


@admin.register(MatchingAlgorithm)
class MatchingAlgorithmAdmin(admin.ModelAdmin):
    """
    Matching algorithm admin.
    """

    list_display = (
        "name",
        "algorithm_type",
        "version",
        "accuracy",
        "is_active",
        "is_default",
        "created_at",
    )
    list_filter = ("algorithm_type", "is_active", "is_default", "created_at")
    search_fields = ("name", "version")
    ordering = ("-created_at",)

    fieldsets = (
        ("Basic Info", {"fields": ("name", "algorithm_type", "version")}),
        ("Configuration", {"fields": ("config",)}),
        ("Performance", {"fields": ("accuracy", "precision", "recall", "f1_score")}),
        ("Status", {"fields": ("is_active", "is_default")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")


@admin.register(CalibrationModel)
class CalibrationModelAdmin(admin.ModelAdmin):
    """
    Calibration model admin.
    """

    list_display = (
        "name",
        "calibration_type",
        "version",
        "brier_score",
        "is_active",
        "is_default",
        "created_at",
    )
    list_filter = ("calibration_type", "is_active", "is_default", "created_at")
    search_fields = ("name", "version")
    ordering = ("-created_at",)

    fieldsets = (
        ("Basic Info", {"fields": ("name", "calibration_type", "version")}),
        ("Model Data", {"fields": ("model_data",)}),
        ("Performance", {"fields": ("brier_score", "reliability_score")}),
        ("Training", {"fields": ("training_samples", "training_date")}),
        ("Status", {"fields": ("is_active", "is_default")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")


@admin.register(MatchingThreshold)
class MatchingThresholdAdmin(admin.ModelAdmin):
    """
    Matching threshold admin.
    """

    list_display = (
        "user_type",
        "auto_threshold",
        "high_touch_threshold",
        "is_active",
        "created_at",
    )
    list_filter = ("user_type", "is_active", "created_at")
    ordering = ("user_type",)

    fieldsets = (
        (
            "Basic Info",
            {"fields": ("user_type", "auto_threshold", "high_touch_threshold")},
        ),
        ("Status", {"fields": ("is_active",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")
