"""
Payments models for ReferWell Direct (stubbed).
"""
from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Payment(models.Model):
    """
    Payment model (stubbed for MVP).
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        CANCELLED = 'cancelled', 'Cancelled'
        REFUNDED = 'refunded', 'Refunded'

    class PaymentType(models.TextChoices):
        SESSION_FEE = 'session_fee', 'Session Fee'
        PLATFORM_FEE = 'platform_fee', 'Platform Fee'
        REFERRAL_FEE = 'referral_fee', 'Referral Fee'
        OTHER = 'other', 'Other'

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_id = models.CharField(max_length=100, unique=True, help_text="External payment ID")
    
    # Relationships
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    referral = models.ForeignKey('referrals.Referral', on_delete=models.CASCADE, null=True, blank=True, related_name='payments')
    
    # Payment details
    payment_type = models.CharField(max_length=20, choices=PaymentType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount in GBP")
    currency = models.CharField(max_length=3, default='GBP')
    
    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # External service details (stubbed)
    external_payment_id = models.CharField(max_length=100, blank=True, help_text="Stripe payment ID")
    external_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="External service fee")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payments_payment'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['payment_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Payment {self.payment_id} - {self.amount} {self.currency}"


class PaymentMethod(models.Model):
    """
    Payment method model (stubbed for MVP).
    """
    class MethodType(models.TextChoices):
        CARD = 'card', 'Card'
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
        PAYPAL = 'paypal', 'PayPal'
        OTHER = 'other', 'Other'

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    
    # Method details
    method_type = models.CharField(max_length=20, choices=MethodType.choices)
    name = models.CharField(max_length=100, help_text="Display name for the method")
    
    # External service details (stubbed)
    external_method_id = models.CharField(max_length=100, blank=True, help_text="External method ID")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments_payment_method'
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['method_type']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.name}"
