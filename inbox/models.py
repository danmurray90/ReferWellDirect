"""
Inbox models for ReferWell Direct.
"""
from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Notification(models.Model):
    """
    Notification model for in-app notifications.
    """
    class NotificationType(models.TextChoices):
        REFERRAL_UPDATE = 'referral_update', 'Referral Update'
        MATCHING_COMPLETE = 'matching_complete', 'Matching Complete'
        INVITATION = 'invitation', 'Invitation'
        RESPONSE = 'response', 'Response'
        APPOINTMENT = 'appointment', 'Appointment'
        SYSTEM = 'system', 'System'
        REMINDER = 'reminder', 'Reminder'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    # Content
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    
    # Related objects
    referral = models.ForeignKey('referrals.Referral', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    candidate = models.ForeignKey('referrals.Candidate', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    appointment = models.ForeignKey('referrals.Appointment', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    # Status
    is_read = models.BooleanField(default=False)
    is_important = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'inbox_notification'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['priority']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Notification for {self.user.get_full_name()}: {self.title}"

    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            from django.utils import timezone
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class NotificationTemplate(models.Model):
    """
    Template model for notification messages.
    """
    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    notification_type = models.CharField(max_length=20, choices=Notification.NotificationType.choices)
    
    # Template content
    title_template = models.CharField(max_length=200)
    message_template = models.TextField()
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inbox_notification_template'
        verbose_name = 'Notification Template'
        verbose_name_plural = 'Notification Templates'
        indexes = [
            models.Index(fields=['notification_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name
