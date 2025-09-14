"""
User account models for ReferWell Direct.
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
# from django.contrib.gis.db import models as gis_models
# from django.contrib.gis.geos import Point
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
    
    # Geographic location (temporarily disabled - requires PostGIS)
    # location = gis_models.PointField(null=True, blank=True, srid=4326)
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
