"""
Matching models for ReferWell Direct.
"""
from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class MatchingRun(models.Model):
    """
    Model to track matching runs for referrals.
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    referral = models.ForeignKey('referrals.Referral', on_delete=models.CASCADE, related_name='matching_runs')
    
    # Status and timing
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    candidates_found = models.PositiveIntegerField(default=0)
    candidates_shortlisted = models.PositiveIntegerField(default=0)
    candidates_invited = models.PositiveIntegerField(default=0)
    
    # Configuration
    config = models.JSONField(default=dict, help_text="Matching configuration used")
    
    # Error handling
    error_message = models.TextField(blank=True, help_text="Error message if failed")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'matching_matching_run'
        verbose_name = 'Matching Run'
        verbose_name_plural = 'Matching Runs'
        indexes = [
            models.Index(fields=['referral', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Matching run for {self.referral.referral_id} - {self.get_status_display()}"


class MatchingAlgorithm(models.Model):
    """
    Model to track different matching algorithms and their performance.
    """
    class AlgorithmType(models.TextChoices):
        VECTOR_SIMILARITY = 'vector_similarity', 'Vector Similarity'
        BM25 = 'bm25', 'BM25'
        HYBRID = 'hybrid', 'Hybrid'
        STRUCTURED_ONLY = 'structured_only', 'Structured Only'

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    algorithm_type = models.CharField(max_length=20, choices=AlgorithmType.choices)
    version = models.CharField(max_length=20, default='1.0')
    
    # Configuration
    config = models.JSONField(default=dict, help_text="Algorithm configuration")
    
    # Performance metrics
    accuracy = models.FloatField(null=True, blank=True, help_text="Overall accuracy score")
    precision = models.FloatField(null=True, blank=True, help_text="Precision score")
    recall = models.FloatField(null=True, blank=True, help_text="Recall score")
    f1_score = models.FloatField(null=True, blank=True, help_text="F1 score")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'matching_matching_algorithm'
        verbose_name = 'Matching Algorithm'
        verbose_name_plural = 'Matching Algorithms'
        unique_together = ['name', 'version']
        indexes = [
            models.Index(fields=['algorithm_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_default']),
        ]

    def __str__(self):
        return f"{self.name} v{self.version}"


class CalibrationModel(models.Model):
    """
    Model to track calibration models for confidence scoring.
    """
    class CalibrationType(models.TextChoices):
        ISOTONIC = 'isotonic', 'Isotonic Regression'
        PLATT = 'platt', 'Platt Scaling'
        TEMPERATURE = 'temperature', 'Temperature Scaling'

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    calibration_type = models.CharField(max_length=20, choices=CalibrationType.choices)
    version = models.CharField(max_length=20, default='1.0')
    
    # Model data
    model_data = models.TextField(help_text="Serialized model data")
    
    # Performance metrics
    brier_score = models.FloatField(null=True, blank=True, help_text="Brier score for calibration")
    reliability_score = models.FloatField(null=True, blank=True, help_text="Reliability score")
    
    # Training data
    training_samples = models.PositiveIntegerField(default=0)
    training_date = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'matching_calibration_model'
        verbose_name = 'Calibration Model'
        verbose_name_plural = 'Calibration Models'
        unique_together = ['name', 'version']
        indexes = [
            models.Index(fields=['calibration_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_default']),
        ]

    def __str__(self):
        return f"{self.name} v{self.version} ({self.get_calibration_type_display()})"


class MatchingThreshold(models.Model):
    """
    Model to track matching thresholds for different user types.
    """
    class UserType(models.TextChoices):
        GP = 'gp', 'GP'
        PATIENT = 'patient', 'Patient'
        PSYCHOLOGIST = 'psychologist', 'Psychologist'
        ADMIN = 'admin', 'Admin'

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_type = models.CharField(max_length=20, choices=UserType.choices)
    
    # Thresholds
    auto_threshold = models.FloatField(help_text="Threshold for automatic matching")
    high_touch_threshold = models.FloatField(help_text="Threshold for high-touch matching")
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'matching_matching_threshold'
        verbose_name = 'Matching Threshold'
        verbose_name_plural = 'Matching Thresholds'
        unique_together = ['user_type']
        indexes = [
            models.Index(fields=['user_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"Thresholds for {self.get_user_type_display()}"
