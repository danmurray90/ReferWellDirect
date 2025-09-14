"""
Ops models for ReferWell Direct.
"""
from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class AuditEvent(models.Model):
    """
    Audit event model for tracking all state changes.
    """
    class EventType(models.TextChoices):
        CREATE = 'create', 'Create'
        UPDATE = 'update', 'Update'
        DELETE = 'delete', 'Delete'
        LOGIN = 'login', 'Login'
        LOGOUT = 'logout', 'Logout'
        REFERRAL_SUBMIT = 'referral_submit', 'Referral Submit'
        MATCHING_START = 'matching_start', 'Matching Start'
        MATCHING_COMPLETE = 'matching_complete', 'Matching Complete'
        INVITATION_SENT = 'invitation_sent', 'Invitation Sent'
        INVITATION_RESPONSE = 'invitation_response', 'Invitation Response'
        APPOINTMENT_BOOKED = 'appointment_booked', 'Appointment Booked'
        PAYMENT_PROCESSED = 'payment_processed', 'Payment Processed'
        OTHER = 'other', 'Other'

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    
    # User and session
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_events')
    session_key = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Object details
    object_type = models.CharField(max_length=100, blank=True, help_text="Type of object affected")
    object_id = models.CharField(max_length=100, blank=True, help_text="ID of object affected")
    
    # Event details
    description = models.TextField(help_text="Human-readable description of the event")
    details = models.JSONField(default=dict, blank=True, help_text="Additional event details")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ops_audit_event'
        verbose_name = 'Audit Event'
        verbose_name_plural = 'Audit Events'
        indexes = [
            models.Index(fields=['event_type']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['object_type', 'object_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.description}"


class Metric(models.Model):
    """
    Metric model for tracking system metrics.
    """
    class MetricType(models.TextChoices):
        COUNTER = 'counter', 'Counter'
        GAUGE = 'gauge', 'Gauge'
        HISTOGRAM = 'histogram', 'Histogram'
        SUMMARY = 'summary', 'Summary'

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    metric_type = models.CharField(max_length=20, choices=MetricType.choices)
    description = models.TextField(blank=True)
    
    # Value
    value = models.FloatField(help_text="Current value of the metric")
    
    # Labels
    labels = models.JSONField(default=dict, blank=True, help_text="Metric labels")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ops_metric'
        verbose_name = 'Metric'
        verbose_name_plural = 'Metrics'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['metric_type']),
            models.Index(fields=['updated_at']),
        ]

    def __str__(self):
        return f"{self.name}: {self.value}"


class SystemLog(models.Model):
    """
    System log model for application logs.
    """
    class LogLevel(models.TextChoices):
        DEBUG = 'debug', 'Debug'
        INFO = 'info', 'Info'
        WARNING = 'warning', 'Warning'
        ERROR = 'error', 'Error'
        CRITICAL = 'critical', 'Critical'

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    level = models.CharField(max_length=20, choices=LogLevel.choices)
    logger_name = models.CharField(max_length=100, help_text="Name of the logger")
    
    # Message
    message = models.TextField(help_text="Log message")
    details = models.JSONField(default=dict, blank=True, help_text="Additional log details")
    
    # Context
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='system_logs')
    request_id = models.CharField(max_length=100, blank=True, help_text="Request ID for tracing")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ops_system_log'
        verbose_name = 'System Log'
        verbose_name_plural = 'System Logs'
        indexes = [
            models.Index(fields=['level']),
            models.Index(fields=['logger_name']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.level.upper()} - {self.logger_name}: {self.message[:50]}"
