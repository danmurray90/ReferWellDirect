"""
Inbox models for ReferWell Direct.
"""
import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Notification(models.Model):
    """
    Notification model for in-app notifications.
    """

    class NotificationType(models.TextChoices):
        REFERRAL_UPDATE = "referral_update", "Referral Update"
        MATCHING_COMPLETE = "matching_complete", "Matching Complete"
        INVITATION = "invitation", "Invitation"
        RESPONSE = "response", "Response"
        APPOINTMENT = "appointment", "Appointment"
        SYSTEM = "system", "System"
        REMINDER = "reminder", "Reminder"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )

    # Content
    notification_type = models.CharField(
        max_length=20, choices=NotificationType.choices
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )

    # Related objects
    referral = models.ForeignKey(
        "referrals.Referral",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    candidate = models.ForeignKey(
        "referrals.Candidate",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    appointment = models.ForeignKey(
        "referrals.Appointment",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    # Status
    is_read = models.BooleanField(default=False)
    is_important = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "inbox_notification"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["notification_type"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Notification for {self.user.get_full_name()}: {self.title}"

    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            from django.utils import timezone

            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])


class NotificationTemplate(models.Model):
    """
    Template model for notification messages.
    """

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    notification_type = models.CharField(
        max_length=20, choices=Notification.NotificationType.choices
    )

    # Template content
    title_template = models.CharField(max_length=200)
    message_template = models.TextField()
    email_subject_template = models.CharField(max_length=200, blank=True)
    email_body_template = models.TextField(blank=True)

    # Status
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inbox_notification_template"
        verbose_name = "Notification Template"
        verbose_name_plural = "Notification Templates"
        indexes = [
            models.Index(fields=["notification_type"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name


class NotificationPreference(models.Model):
    """
    User notification preferences for different notification types.
    """

    class DeliveryMethod(models.TextChoices):
        IN_APP = "in_app", "In-App Only"
        EMAIL = "email", "Email Only"
        PUSH = "push", "Push Notification"
        ALL = "all", "All Methods"
        NONE = "none", "Disabled"

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="notification_preferences"
    )

    # Preferences by notification type
    referral_update_method = models.CharField(
        max_length=10, choices=DeliveryMethod.choices, default=DeliveryMethod.IN_APP
    )
    matching_complete_method = models.CharField(
        max_length=10, choices=DeliveryMethod.choices, default=DeliveryMethod.IN_APP
    )
    invitation_method = models.CharField(
        max_length=10, choices=DeliveryMethod.choices, default=DeliveryMethod.ALL
    )
    response_method = models.CharField(
        max_length=10, choices=DeliveryMethod.choices, default=DeliveryMethod.IN_APP
    )
    appointment_method = models.CharField(
        max_length=10, choices=DeliveryMethod.choices, default=DeliveryMethod.ALL
    )
    system_method = models.CharField(
        max_length=10, choices=DeliveryMethod.choices, default=DeliveryMethod.IN_APP
    )
    reminder_method = models.CharField(
        max_length=10, choices=DeliveryMethod.choices, default=DeliveryMethod.EMAIL
    )

    # Global settings
    email_notifications_enabled = models.BooleanField(default=True)
    push_notifications_enabled = models.BooleanField(default=True)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inbox_notification_preference"
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"

    def __str__(self):
        return f"Notification preferences for {self.user.get_full_name()}"

    def get_delivery_method(self, notification_type):
        """Get delivery method for a specific notification type."""
        method_map = {
            Notification.NotificationType.REFERRAL_UPDATE: self.referral_update_method,
            Notification.NotificationType.MATCHING_COMPLETE: self.matching_complete_method,
            Notification.NotificationType.INVITATION: self.invitation_method,
            Notification.NotificationType.RESPONSE: self.response_method,
            Notification.NotificationType.APPOINTMENT: self.appointment_method,
            Notification.NotificationType.SYSTEM: self.system_method,
            Notification.NotificationType.REMINDER: self.reminder_method,
        }
        return method_map.get(notification_type, self.DeliveryMethod.IN_APP)

    def is_quiet_hours(self):
        """Check if current time is within quiet hours."""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False

        from django.utils import timezone

        now = timezone.now().time()

        if self.quiet_hours_start <= self.quiet_hours_end:
            return self.quiet_hours_start <= now <= self.quiet_hours_end
        else:  # Quiet hours span midnight
            return now >= self.quiet_hours_start or now <= self.quiet_hours_end


class NotificationChannel(models.Model):
    """
    WebSocket channels for real-time notifications.
    """

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notification_channels"
    )
    channel_name = models.CharField(max_length=100, unique=True)

    # Status
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inbox_notification_channel"
        verbose_name = "Notification Channel"
        verbose_name_plural = "Notification Channels"
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["channel_name"]),
        ]

    def __str__(self):
        return f"Channel {self.channel_name} for {self.user.get_full_name()}"
