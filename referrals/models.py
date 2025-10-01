"""
Referral models for ReferWell Direct.
"""
import uuid

from django.contrib.auth import get_user_model

# from django.contrib.gis.db import models as gis_models
# from django.contrib.gis.geos import Point
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = get_user_model()


class Referral(models.Model):
    """
    Referral model representing a patient referral to mental health services.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        MATCHING = "matching", "Matching"
        SHORTLISTED = "shortlisted", "Shortlisted"
        HIGH_TOUCH_QUEUE = "high_touch_queue", "High-Touch Queue"
        INVITED = "invited", "Invited"
        RESPONDED = "responded", "Responded"
        APPOINTMENT_BOOKED = "appointment_booked", "Appointment Booked"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        REJECTED = "rejected", "Rejected"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    class ServiceType(models.TextChoices):
        NHS = "nhs", "NHS"
        PRIVATE = "private", "Private"
        MIXED = "mixed", "Mixed"

    class Modality(models.TextChoices):
        IN_PERSON = "in_person", "In-Person"
        REMOTE = "remote", "Remote"
        MIXED = "mixed", "Mixed"

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    referral_id = models.CharField(
        max_length=30, unique=True, help_text="Human-readable referral ID"
    )

    # Relationships
    referrer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="referrals_made"
    )
    patient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="referrals_received"
    )

    # Status and priority
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )

    # Service preferences
    service_type = models.CharField(
        max_length=10, choices=ServiceType.choices, default=ServiceType.NHS
    )
    modality = models.CharField(
        max_length=10, choices=Modality.choices, default=Modality.MIXED
    )

    # Clinical information
    presenting_problem = models.TextField(
        help_text="Description of the patient's presenting problem"
    )
    condition_description = models.TextField(
        blank=True, help_text="Detailed description of the condition"
    )
    clinical_notes = models.TextField(blank=True, help_text="Additional clinical notes")
    urgency_notes = models.TextField(
        blank=True, help_text="Notes about urgency if applicable"
    )

    # Patient preferences
    patient_preferences = models.JSONField(
        default=dict, blank=True, help_text="Patient's preferences and requirements"
    )

    # Geographic preferences (temporarily disabled - requires PostGIS)
    # preferred_location = gis_models.PointField(null=True, blank=True, srid=4326)
    preferred_latitude = models.FloatField(null=True, blank=True)
    preferred_longitude = models.FloatField(null=True, blank=True)
    max_distance_km = models.PositiveIntegerField(
        default=50, help_text="Maximum distance in kilometers"
    )

    # Language preferences
    preferred_language = models.CharField(
        max_length=10, default="en", help_text="Preferred language code"
    )
    language_requirements = models.JSONField(
        default=list, blank=True, help_text="List of language requirements"
    )

    # Patient demographics
    patient_age_group = models.CharField(
        max_length=20, blank=True, help_text="Patient age group"
    )

    # Specialism requirements
    required_specialisms = models.JSONField(
        default=list, blank=True, help_text="List of required specialisms"
    )

    # Routing metadata
    routing_metadata = models.JSONField(
        default=dict, blank=True, help_text="Metadata for routing decisions"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Audit fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_referrals",
    )

    class Meta:
        db_table = "referrals_referral"
        verbose_name = "Referral"
        verbose_name_plural = "Referrals"
        indexes = [
            models.Index(fields=["referral_id"]),
            models.Index(fields=["status"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["service_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"Referral {self.referral_id} - {self.patient.get_full_name()}"

    def save(self, *args, **kwargs) -> None:
        if not self.referral_id:
            # Generate human-readable referral ID
            self.referral_id = self._generate_referral_id()
        super().save(*args, **kwargs)

    def _generate_referral_id(self) -> str:
        """Generate a human-readable referral ID."""
        import datetime
        import random

        now = datetime.datetime.now()
        # Add microseconds and random component to ensure uniqueness
        microsecond = now.microsecond
        random_component = random.randint(10, 99)
        return f"REF{now.strftime('%Y%m%d')}{now.strftime('%H%M%S')}{microsecond:06d}{random_component}"

    @property
    def is_draft(self) -> bool:
        return bool(self.status == self.Status.DRAFT)

    @property
    def is_submitted(self) -> bool:
        return bool(self.status == self.Status.SUBMITTED)

    @property
    def is_matching(self) -> bool:
        return bool(self.status == self.Status.MATCHING)

    @property
    def is_high_touch_queue(self) -> bool:
        return bool(self.status == self.Status.HIGH_TOUCH_QUEUE)

    @property
    def is_completed(self) -> bool:
        return bool(self.status == self.Status.COMPLETED)


class Candidate(models.Model):
    """
    Candidate model representing a psychologist who could potentially match a referral.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SHORTLISTED = "shortlisted", "Shortlisted"
        INVITED = "invited", "Invited"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        EXPIRED = "expired", "Expired"

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    referral = models.ForeignKey(
        Referral, on_delete=models.CASCADE, related_name="candidates"
    )
    psychologist = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="candidate_referrals"
    )

    # Status
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    # Matching scores
    similarity_score = models.FloatField(
        null=True, blank=True, help_text="Similarity score from matching algorithm"
    )
    structured_score = models.FloatField(
        null=True, blank=True, help_text="Score from structured features"
    )
    final_score = models.FloatField(
        null=True, blank=True, help_text="Final combined score"
    )
    confidence_score = models.FloatField(
        null=True, blank=True, help_text="Calibrated confidence score"
    )

    # Matching explanation
    matching_explanation = models.JSONField(
        default=dict,
        blank=True,
        help_text="Explanation of why this candidate was matched",
    )

    # Invitation details
    invited_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    # Response details
    response_notes = models.TextField(
        blank=True, help_text="Notes from psychologist's response"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "referrals_candidate"
        verbose_name = "Candidate"
        verbose_name_plural = "Candidates"
        unique_together = ["referral", "psychologist"]
        indexes = [
            models.Index(fields=["referral", "status"]),
            models.Index(fields=["psychologist", "status"]),
            models.Index(fields=["final_score"]),
            models.Index(fields=["confidence_score"]),
        ]

    def __str__(self) -> str:
        return f"Candidate {self.psychologist.get_full_name()} for {self.referral.referral_id}"

    @property
    def is_pending(self) -> bool:
        return bool(self.status == self.Status.PENDING)

    @property
    def is_shortlisted(self) -> bool:
        return bool(self.status == self.Status.SHORTLISTED)

    @property
    def is_invited(self) -> bool:
        return bool(self.status == self.Status.INVITED)

    @property
    def is_accepted(self) -> bool:
        return bool(self.status == self.Status.ACCEPTED)

    @property
    def is_declined(self) -> bool:
        return bool(self.status == self.Status.DECLINED)

    @property
    def is_expired(self) -> bool:
        return bool(self.status == self.Status.EXPIRED)


class Appointment(models.Model):
    """
    Appointment model representing a scheduled appointment between patient and psychologist.
    """

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        NO_SHOW = "no_show", "No Show"

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    referral = models.ForeignKey(
        Referral, on_delete=models.CASCADE, related_name="appointments"
    )
    patient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="appointments_as_patient"
    )
    psychologist = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="appointments_as_psychologist"
    )

    # Appointment details
    scheduled_at = models.DateTimeField(help_text="Scheduled appointment time")
    duration_minutes = models.PositiveIntegerField(
        default=60, help_text="Appointment duration in minutes"
    )
    location = models.TextField(
        blank=True, help_text="Appointment location or video call details"
    )
    modality = models.CharField(
        max_length=10,
        choices=Referral.Modality.choices,
        default=Referral.Modality.IN_PERSON,
    )

    # Status
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED
    )

    # Notes
    notes = models.TextField(blank=True, help_text="Appointment notes")
    outcome_notes = models.TextField(
        blank=True, help_text="Notes about appointment outcome"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "referrals_appointment"
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"
        indexes = [
            models.Index(fields=["referral", "status"]),
            models.Index(fields=["patient", "scheduled_at"]),
            models.Index(fields=["psychologist", "scheduled_at"]),
            models.Index(fields=["scheduled_at"]),
        ]

    def __str__(self) -> str:
        return f"Appointment {self.id} - {self.patient.get_full_name()} with {self.psychologist.get_full_name()}"

    @property
    def is_scheduled(self) -> bool:
        return bool(self.status == self.Status.SCHEDULED)

    @property
    def is_confirmed(self) -> bool:
        return bool(self.status == self.Status.CONFIRMED)

    @property
    def is_completed(self) -> bool:
        return bool(self.status == self.Status.COMPLETED)

    @property
    def is_cancelled(self) -> bool:
        return bool(self.status == self.Status.CANCELLED)


class Message(models.Model):
    """
    Message model for communication between users about referrals.
    """

    class MessageType(models.TextChoices):
        SYSTEM = "system", "System"
        REFERRAL_UPDATE = "referral_update", "Referral Update"
        INVITATION = "invitation", "Invitation"
        RESPONSE = "response", "Response"
        APPOINTMENT = "appointment", "Appointment"
        GENERAL = "general", "General"

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    referral = models.ForeignKey(
        Referral,
        on_delete=models.CASCADE,
        related_name="messages",
        null=True,
        blank=True,
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="messages_sent"
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="messages_received"
    )

    # Message content
    message_type = models.CharField(
        max_length=20, choices=MessageType.choices, default=MessageType.GENERAL
    )
    subject = models.CharField(max_length=200)
    content = models.TextField()

    # Status
    is_read = models.BooleanField(default=False)
    is_important = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "referrals_message"
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["sender", "created_at"]),
            models.Index(fields=["referral", "created_at"]),
            models.Index(fields=["message_type"]),
        ]

    def __str__(self) -> str:
        return f"Message from {self.sender.get_full_name()} to {self.recipient.get_full_name()}"

    def mark_as_read(self) -> None:
        """Mark message as read."""
        if not self.is_read:
            self.is_read = True
            from django.utils import timezone

            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])


class Task(models.Model):
    """
    Task model for tracking actions and reminders.
    """

    class TaskType(models.TextChoices):
        REVIEW_REFERRAL = "review_referral", "Review Referral"
        SEND_INVITATION = "send_invitation", "Send Invitation"
        FOLLOW_UP = "follow_up", "Follow Up"
        REMINDER = "reminder", "Reminder"
        CALIBRATION = "calibration", "Calibration"
        OTHER = "other", "Other"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    referral = models.ForeignKey(
        Referral, on_delete=models.CASCADE, related_name="tasks", null=True, blank=True
    )
    assigned_to = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="assigned_tasks"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_tasks"
    )

    # Task details
    task_type = models.CharField(max_length=20, choices=TaskType.choices)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )

    # Status
    is_completed = models.BooleanField(default=False)
    is_overdue = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "referrals_task"
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        indexes = [
            models.Index(fields=["assigned_to", "is_completed"]),
            models.Index(fields=["task_type"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["due_at"]),
        ]

    def __str__(self) -> str:
        return f"Task: {self.title} (assigned to {self.assigned_to.get_full_name()})"

    def mark_completed(self) -> None:
        """Mark task as completed."""
        if not self.is_completed:
            self.is_completed = True
            from django.utils import timezone

            self.completed_at = timezone.now()
            self.save(update_fields=["is_completed", "completed_at"])
