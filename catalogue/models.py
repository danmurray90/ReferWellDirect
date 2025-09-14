"""
Catalogue models for ReferWell Direct.
"""
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Psychologist(models.Model):
    """
    Psychologist model representing a mental health professional in the catalogue.
    """
    class ServiceType(models.TextChoices):
        NHS = 'nhs', 'NHS'
        PRIVATE = 'private', 'Private'
        MIXED = 'mixed', 'Mixed'

    class Modality(models.TextChoices):
        IN_PERSON = 'in_person', 'In-Person'
        REMOTE = 'remote', 'Remote'
        MIXED = 'mixed', 'Mixed'

    class AvailabilityStatus(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        BUSY = 'busy', 'Busy'
        UNAVAILABLE = 'unavailable', 'Unavailable'
        ON_LEAVE = 'on_leave', 'On Leave'

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='psychologist_profile')
    
    # Professional information
    title = models.CharField(max_length=50, blank=True, help_text="Professional title (Dr., Prof., etc.)")
    qualifications = models.JSONField(default=list, blank=True, help_text="List of qualifications")
    specialisms = models.JSONField(default=list, blank=True, help_text="List of specialisms")
    languages = models.JSONField(default=list, help_text="Languages spoken")
    
    # Service information
    service_type = models.CharField(max_length=10, choices=ServiceType.choices, default=ServiceType.MIXED)
    modality = models.CharField(max_length=10, choices=Modality.choices, default=Modality.MIXED)
    
    # Location and availability
    location = gis_models.PointField(null=True, blank=True, srid=4326)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    address_line_1 = models.CharField(max_length=100, blank=True)
    address_line_2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50, blank=True)
    postcode = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=50, default='United Kingdom')
    
    # Professional details
    registration_number = models.CharField(max_length=50, blank=True, help_text="Professional registration number")
    registration_body = models.CharField(max_length=100, blank=True, help_text="Registration body (HCPC, BPS, etc.)")
    years_experience = models.PositiveIntegerField(null=True, blank=True)
    
    # Availability
    availability_status = models.CharField(max_length=20, choices=AvailabilityStatus.choices, default=AvailabilityStatus.AVAILABLE)
    max_patients = models.PositiveIntegerField(default=50, help_text="Maximum number of patients")
    current_patients = models.PositiveIntegerField(default=0, help_text="Current number of patients")
    
    # Pricing (for private services)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Hourly rate in GBP")
    session_duration = models.PositiveIntegerField(default=60, help_text="Standard session duration in minutes")
    
    # Matching preferences
    preferred_age_groups = models.JSONField(default=list, blank=True, help_text="Preferred patient age groups")
    preferred_conditions = models.JSONField(default=list, blank=True, help_text="Preferred conditions to treat")
    max_distance_km = models.PositiveIntegerField(default=100, help_text="Maximum distance willing to travel")
    
    # Embedding for similarity matching
    embedding = models.TextField(null=True, blank=True, help_text="Vector embedding for similarity matching")
    
    # Status and verification
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_accepting_referrals = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_updated_embedding = models.DateTimeField(null=True, blank=True)
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_psychologists')

    class Meta:
        db_table = 'catalogue_psychologist'
        verbose_name = 'Psychologist'
        verbose_name_plural = 'Psychologists'
        indexes = [
            models.Index(fields=['service_type']),
            models.Index(fields=['modality']),
            models.Index(fields=['availability_status']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_accepting_referrals']),
            models.Index(fields=['registration_number']),
        ]

    def save(self, *args, **kwargs):
        """Override save to update location from lat/lon."""
        super().save(*args, **kwargs)
        if self.latitude and self.longitude and not self.location:
            self.update_location()

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_service_type_display()}"

    @property
    def capacity_available(self):
        """Check if psychologist has capacity for new patients."""
        return self.current_patients < self.max_patients and self.is_accepting_referrals

    @property
    def is_available(self):
        """Check if psychologist is available for new referrals."""
        return (
            self.availability_status == self.AvailabilityStatus.AVAILABLE and
            self.is_active and
            self.is_accepting_referrals and
            self.capacity_available
        )

    @property
    def appointments_as_psychologist(self):
        """Get appointments where this psychologist is the provider."""
        from referrals.models import Appointment
        return Appointment.objects.filter(psychologist=self.user)

    def update_embedding(self, embedding_vector):
        """Update the embedding vector for similarity matching."""
        import json
        self.embedding = json.dumps(embedding_vector.tolist())
        from django.utils import timezone
        self.last_updated_embedding = timezone.now()
        self.save(update_fields=['embedding', 'last_updated_embedding'])

    def get_embedding(self):
        """Get the embedding vector as a numpy array."""
        if not self.embedding:
            return None
        import json
        import numpy as np
        return np.array(json.loads(self.embedding))

    def update_location(self):
        """Update the PostGIS location field from latitude and longitude."""
        if self.latitude and self.longitude:
            self.location = Point(self.longitude, self.latitude, srid=4326)
            self.save(update_fields=['location'])

    def get_distance_to(self, lat, lon):
        """Calculate distance to another point in meters."""
        if not self.location:
            return None
        from django.contrib.gis.geos import Point
        point = Point(lon, lat, srid=4326)
        return self.location.distance(point) * 111000  # Convert to meters (approximate)


class Availability(models.Model):
    """
    Availability model for psychologist scheduling.
    """
    class DayOfWeek(models.TextChoices):
        MONDAY = 'monday', 'Monday'
        TUESDAY = 'tuesday', 'Tuesday'
        WEDNESDAY = 'wednesday', 'Wednesday'
        THURSDAY = 'thursday', 'Thursday'
        FRIDAY = 'friday', 'Friday'
        SATURDAY = 'saturday', 'Saturday'
        SUNDAY = 'sunday', 'Sunday'

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    psychologist = models.ForeignKey(Psychologist, on_delete=models.CASCADE, related_name='availabilities')
    
    # Schedule details
    day_of_week = models.CharField(max_length=10, choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Modality for this time slot
    modality = models.CharField(max_length=10, choices=Psychologist.Modality.choices, default=Psychologist.Modality.IN_PERSON)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'catalogue_availability'
        verbose_name = 'Availability'
        verbose_name_plural = 'Availabilities'
        unique_together = ['psychologist', 'day_of_week', 'start_time', 'end_time']
        indexes = [
            models.Index(fields=['psychologist', 'day_of_week']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.psychologist.user.get_full_name()} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class Specialism(models.Model):
    """
    Specialism model for categorizing psychologist expertise.
    """
    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, blank=True, help_text="Category grouping (e.g., 'Anxiety', 'Trauma')")
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'catalogue_specialism'
        verbose_name = 'Specialism'
        verbose_name_plural = 'Specialisms'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


class Qualification(models.Model):
    """
    Qualification model for psychologist credentials.
    """
    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    abbreviation = models.CharField(max_length=20, blank=True, help_text="Common abbreviation (e.g., 'DClinPsy')")
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'catalogue_qualification'
        verbose_name = 'Qualification'
        verbose_name_plural = 'Qualifications'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['abbreviation']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


class Review(models.Model):
    """
    Review model for psychologist feedback and ratings.
    """
    class Rating(models.IntegerChoices):
        ONE = 1, '1 Star'
        TWO = 2, '2 Stars'
        THREE = 3, '3 Stars'
        FOUR = 4, '4 Stars'
        FIVE = 5, '5 Stars'

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    psychologist = models.ForeignKey(Psychologist, on_delete=models.CASCADE, related_name='reviews')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    
    # Review content
    rating = models.IntegerField(choices=Rating.choices)
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # Status
    is_verified = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'catalogue_review'
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        unique_together = ['psychologist', 'patient']
        indexes = [
            models.Index(fields=['psychologist', 'rating']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['is_public']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Review of {self.psychologist.user.get_full_name()} by {self.patient.get_full_name()}"
