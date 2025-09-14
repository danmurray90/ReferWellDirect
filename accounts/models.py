"""
User account models for ReferWell Direct.
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.core.validators import RegexValidator
import uuid


class UserManager(BaseUserManager):
    """
    Custom user manager for email-based authentication.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        # Remove username from extra_fields if present to avoid conflict
        extra_fields.pop('username', None)
        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
            
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model with role-based access control.
    """
    class UserType(models.TextChoices):
        GP = 'gp', 'GP'
        PATIENT = 'patient', 'Patient'
        PSYCHOLOGIST = 'psychologist', 'Psychologist'
        ADMIN = 'admin', 'Admin'
        HIGH_TOUCH_REFERRER = 'high_touch_referrer', 'High-Touch Referrer'

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_type = models.CharField(max_length=20, choices=UserType.choices)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )],
        blank=True
    )
    
    # Profile fields
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # Preferences
    preferred_language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='Europe/London')
    
    # Audit fields
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users')
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'user_type']
    
    objects = UserManager()

    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    @property
    def is_gp(self):
        return self.user_type == self.UserType.GP

    @property
    def is_patient(self):
        return self.user_type == self.UserType.PATIENT

    @property
    def is_psychologist(self):
        return self.user_type == self.UserType.PSYCHOLOGIST

    @property
    def is_admin(self):
        return self.user_type == self.UserType.ADMIN

    @property
    def is_high_touch_referrer(self):
        return self.user_type == self.UserType.HIGH_TOUCH_REFERRER


class Organisation(models.Model):
    """
    Organisation model for GPs, clinics, and other healthcare providers.
    """
    class OrganisationType(models.TextChoices):
        GP_PRACTICE = 'gp_practice', 'GP Practice'
        CLINIC = 'clinic', 'Clinic'
        HOSPITAL = 'hospital', 'Hospital'
        MENTAL_HEALTH_SERVICE = 'mental_health_service', 'Mental Health Service'
        PRIVATE_PRACTICE = 'private_practice', 'Private Practice'
        OTHER = 'other', 'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    organisation_type = models.CharField(max_length=30, choices=OrganisationType.choices)
    
    # Contact information
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    
    # Address
    address_line_1 = models.CharField(max_length=100)
    address_line_2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50)
    postcode = models.CharField(max_length=10)
    country = models.CharField(max_length=50, default='United Kingdom')
    
    # Geographic location (temporarily disabled - requires PostGIS/GDAL)
    location = gis_models.PointField(null=True, blank=True, srid=4326)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # NHS specific fields
    ods_code = models.CharField(max_length=10, blank=True, help_text="NHS Organisation Data Service code")
    ccg_code = models.CharField(max_length=10, blank=True, help_text="Clinical Commissioning Group code")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'accounts_organisation'
        verbose_name = 'Organisation'
        verbose_name_plural = 'Organisations'
        indexes = [
            models.Index(fields=['ods_code']),
            models.Index(fields=['ccg_code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Auto-populate location from address if not set
        if not self.location and self.postcode:
            # This would typically use a geocoding service
            # For now, we'll leave it as None
            pass
        super().save(*args, **kwargs)


class UserOrganisation(models.Model):
    """
    Many-to-many relationship between users and organisations.
    """
    class Role(models.TextChoices):
        OWNER = 'owner', 'Owner'
        ADMIN = 'admin', 'Administrator'
        MEMBER = 'member', 'Member'
        VIEWER = 'viewer', 'Viewer'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_organisations')
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='user_organisations')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_user_organisations')

    class Meta:
        db_table = 'accounts_user_organisation'
        verbose_name = 'User Organisation'
        verbose_name_plural = 'User Organisations'
        unique_together = ['user', 'organisation']
        indexes = [
            models.Index(fields=['user', 'organisation']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.organisation.name} ({self.get_role_display()})"


class OnboardingStep(models.Model):
    """
    Model to define onboarding steps for different user types.
    """
    class StepType(models.TextChoices):
        PROFILE_SETUP = 'profile_setup', 'Profile Setup'
        ORGANISATION_SETUP = 'organisation_setup', 'Organisation Setup'
        PREFERENCES = 'preferences', 'Preferences'
        VERIFICATION = 'verification', 'Verification'
        COMPLETION = 'completion', 'Completion'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    step_type = models.CharField(max_length=30, choices=StepType.choices)
    user_type = models.CharField(max_length=20, choices=User.UserType.choices)
    order = models.PositiveIntegerField()
    is_required = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    help_text = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_onboarding_step'
        verbose_name = 'Onboarding Step'
        verbose_name_plural = 'Onboarding Steps'
        unique_together = ['user_type', 'order']
        ordering = ['user_type', 'order']

    def __str__(self):
        return f"{self.get_user_type_display()} - {self.name}"


class UserOnboardingProgress(models.Model):
    """
    Model to track user progress through onboarding steps.
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        SKIPPED = 'skipped', 'Skipped'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='onboarding_progress')
    step = models.ForeignKey(OnboardingStep, on_delete=models.CASCADE, related_name='user_progress')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Progress tracking
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    data = models.JSONField(default=dict, blank=True, help_text="Step-specific data")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_user_onboarding_progress'
        verbose_name = 'User Onboarding Progress'
        verbose_name_plural = 'User Onboarding Progress'
        unique_together = ['user', 'step']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['step', 'status']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.step.name} ({self.get_status_display()})"

    @property
    def is_completed(self):
        return self.status == self.Status.COMPLETED

    @property
    def is_skipped(self):
        return self.status == self.Status.SKIPPED

    def mark_started(self):
        """Mark step as started."""
        if self.status == self.Status.PENDING:
            self.status = self.Status.IN_PROGRESS
            from django.utils import timezone
            self.started_at = timezone.now()
            self.save(update_fields=['status', 'started_at'])

    def mark_completed(self, data=None):
        """Mark step as completed with optional data."""
        self.status = self.Status.COMPLETED
        from django.utils import timezone
        self.completed_at = timezone.now()
        if data:
            self.data = data
        self.save(update_fields=['status', 'completed_at', 'data'])

    def mark_skipped(self):
        """Mark step as skipped."""
        self.status = self.Status.SKIPPED
        from django.utils import timezone
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])


class OnboardingSession(models.Model):
    """
    Model to track overall onboarding session for a user.
    """
    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', 'Not Started'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        ABANDONED = 'abandoned', 'Abandoned'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='onboarding_session')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED)
    current_step = models.ForeignKey(OnboardingStep, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Progress tracking
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    # Session data
    session_data = models.JSONField(default=dict, blank=True, help_text="Session-wide data")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_onboarding_session'
        verbose_name = 'Onboarding Session'
        verbose_name_plural = 'Onboarding Sessions'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_status_display()}"

    @property
    def is_completed(self):
        return self.status == self.Status.COMPLETED

    @property
    def progress_percentage(self):
        """Calculate completion percentage."""
        total_steps = OnboardingStep.objects.filter(
            user_type=self.user.user_type,
            is_active=True
        ).count()
        
        if total_steps == 0:
            return 100
        
        completed_steps = self.user.onboarding_progress.filter(
            status=UserOnboardingProgress.Status.COMPLETED
        ).count()
        
        return int((completed_steps / total_steps) * 100)

    def get_next_step(self):
        """Get the next incomplete step."""
        completed_step_ids = self.user.onboarding_progress.filter(
            status__in=[
                UserOnboardingProgress.Status.COMPLETED,
                UserOnboardingProgress.Status.SKIPPED
            ]
        ).values_list('step_id', flat=True)
        
        next_step = OnboardingStep.objects.filter(
            user_type=self.user.user_type,
            is_active=True
        ).exclude(
            id__in=completed_step_ids
        ).order_by('order').first()
        
        return next_step

    def start(self):
        """Start the onboarding session."""
        self.status = self.Status.IN_PROGRESS
        from django.utils import timezone
        self.started_at = timezone.now()
        self.current_step = self.get_next_step()
        self.save(update_fields=['status', 'started_at', 'current_step'])

    def complete(self):
        """Complete the onboarding session."""
        self.status = self.Status.COMPLETED
        from django.utils import timezone
        self.completed_at = timezone.now()
        self.current_step = None
        self.save(update_fields=['status', 'completed_at', 'current_step'])

    def abandon(self):
        """Abandon the onboarding session."""
        self.status = self.Status.ABANDONED
        from django.utils import timezone
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
