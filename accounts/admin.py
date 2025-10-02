"""
Admin configuration for accounts app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone

from .models import (
    Organisation,
    PatientClaimInvite,
    User,
    UserOrganisation,
    VerificationStatus,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom user admin with role-based fields.
    """

    list_display = (
        "email",
        "first_name",
        "last_name",
        "user_type",
        "is_active",
        "is_verified",
        "created_at",
    )
    list_filter = ("user_type", "is_active", "is_verified", "created_at")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "date_of_birth",
                    "phone",
                    "profile_picture",
                )
            },
        ),
        (
            "Account info",
            {"fields": ("user_type", "is_active", "is_verified", "last_login")},
        ),
        ("Preferences", {"fields": ("preferred_language", "timezone")}),
        (
            "Permissions",
            {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("created_at", "updated_at")}),
        ("Audit", {"fields": ("created_by",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "user_type",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at", "last_login")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("created_by")


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    """
    Organisation admin with geographic and NHS-specific fields.
    """

    list_display = (
        "name",
        "organisation_type",
        "city",
        "postcode",
        "is_active",
        "is_verified",
        "created_at",
    )
    list_filter = ("organisation_type", "is_active", "is_verified", "created_at")
    search_fields = ("name", "email", "postcode", "ods_code", "ccg_code")
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Basic info",
            {"fields": ("name", "organisation_type", "is_active", "is_verified")},
        ),
        ("Contact", {"fields": ("email", "phone", "website")}),
        (
            "Address",
            {
                "fields": (
                    "address_line_1",
                    "address_line_2",
                    "city",
                    "postcode",
                    "country",
                    "location",
                )
            },
        ),
        ("NHS info", {"fields": ("ods_code", "ccg_code")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
        ("Audit", {"fields": ("created_by",)}),
    )

    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("created_by")


@admin.register(UserOrganisation)
class UserOrganisationAdmin(admin.ModelAdmin):
    """
    User-Organisation relationship admin.
    """

    list_display = ("user", "organisation", "role", "is_active", "created_at")
    list_filter = ("role", "is_active", "created_at")
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "organisation__name",
    )
    ordering = ("-created_at",)

    fieldsets = (
        ("Relationship", {"fields": ("user", "organisation", "role")}),
        ("Status", {"fields": ("is_active",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
        ("Audit", {"fields": ("created_by",)}),
    )

    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("user", "organisation", "created_by")
        )


@admin.register(VerificationStatus)
class VerificationStatusAdmin(admin.ModelAdmin):
    """
    Verification status admin for GP and Psychologist verification.
    """

    list_display = ("user", "status", "vetted_at", "vetted_by", "created_at")
    list_filter = ("status", "vetted_at", "created_at")
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "vetted_by__email",
    )
    ordering = ("-created_at",)

    fieldsets = (
        ("User", {"fields": ("user",)}),
        ("Verification", {"fields": ("status", "notes")}),
        ("Vetting", {"fields": ("vetted_by", "vetted_at")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at", "vetted_at")

    actions = ["verify_users", "reject_users"]

    def verify_users(self, request, queryset):
        """Bulk verify selected users."""
        updated = queryset.filter(status=VerificationStatus.Status.PENDING).update(
            status=VerificationStatus.Status.VERIFIED,
            vetted_by=request.user,
            vetted_at=timezone.now(),
        )
        self.message_user(request, f"{updated} users verified successfully.")

    verify_users.short_description = "Verify selected users"

    def reject_users(self, request, queryset):
        """Bulk reject selected users."""
        updated = queryset.filter(status=VerificationStatus.Status.PENDING).update(
            status=VerificationStatus.Status.REJECTED,
            vetted_by=request.user,
            vetted_at=timezone.now(),
        )
        self.message_user(request, f"{updated} users rejected successfully.")

    reject_users.short_description = "Reject selected users"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "vetted_by")


@admin.register(PatientClaimInvite)
class PatientClaimInviteAdmin(admin.ModelAdmin):
    """
    Patient claim invite admin.
    """

    list_display = (
        "patient_profile",
        "email",
        "expires_at",
        "used_at",
        "is_valid",
        "created_at",
    )
    list_filter = ("expires_at", "used_at", "created_at")
    search_fields = (
        "email",
        "patient_profile__first_name",
        "patient_profile__last_name",
        "token",
    )
    ordering = ("-created_at",)

    fieldsets = (
        ("Invite Details", {"fields": ("patient_profile", "email", "token")}),
        ("Status", {"fields": ("expires_at", "used_at")}),
        ("Timestamps", {"fields": ("created_at",)}),
        ("Audit", {"fields": ("created_by",)}),
    )

    readonly_fields = ("created_at", "token")

    def is_valid(self, obj):
        """Check if invite is valid."""
        return obj.is_valid

    is_valid.boolean = True
    is_valid.short_description = "Valid"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("patient_profile", "created_by")
        )
