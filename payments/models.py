# payments/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid


def generate_transaction_id():
    """Generate a unique transaction ID"""
    return f"TXN-{uuid.uuid4().hex[:12].upper()}"

class SubscriptionPlan(models.Model):
    """Subscription plans for patients"""
    PLAN_TIERS = (
        ('free', 'Free'),
        ('premium', 'Premium'),
        ('family', 'Family Plan'),
    )
    
    name = models.CharField(max_length=100)
    tier = models.CharField(max_length=20, choices=PLAN_TIERS, unique=True)
    description = models.TextField()
    
    # Pricing
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    annual_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Features (stored as JSON for flexibility)
    features = models.JSONField(default=dict, help_text="Dictionary of features and their values")
    
    # Limits
    max_appointments_per_month = models.IntegerField(null=True, blank=True, help_text="Null = unlimited")
    max_family_members = models.IntegerField(default=1)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.tier})"
    
    class Meta:
        ordering = ['monthly_price']


class UserSubscription(models.Model):
    """User subscription to a plan"""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('past_due', 'Past Due'),
    )
    
    BILLING_CYCLE_CHOICES = (
        ('monthly', 'Monthly'),
        ('annual', 'Annual'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='user_subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    billing_cycle = models.CharField(max_length=10, choices=BILLING_CYCLE_CHOICES, default='monthly')
    
    # Dates
    started_at = models.DateTimeField(auto_now_add=True)
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Payment
    payment_reference = models.CharField(max_length=255, null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status})"
    
    @property
    def is_active(self):
        return self.status == 'active' and self.current_period_end > timezone.now()
    
    @property
    def price(self):
        if self.billing_cycle == 'annual' and self.plan.annual_price:
            return self.plan.annual_price
        return self.plan.monthly_price
    
    class Meta:
        ordering = ['-created_at']


class DoctorSubscription(models.Model):
    """Subscription plans for doctors/providers"""
    PLAN_TIERS = (
        ('basic', 'Basic'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
    )
    
    name = models.CharField(max_length=100)
    tier = models.CharField(max_length=20, choices=PLAN_TIERS, unique=True)
    description = models.TextField()
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=dict)
    max_appointments_per_month = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.tier})"


class DoctorSubscriptionRecord(models.Model):
    """Doctor's subscription to a plan"""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('past_due', 'Past Due'),
    )
    
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(DoctorSubscription, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    payment_reference = models.CharField(max_length=255, null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.doctor.full_name} - {self.plan.name} ({self.status})"
    
    @property
    def is_active(self):
        return self.status == 'active' and self.current_period_end > timezone.now()


class Transaction(models.Model):
    """Track all financial transactions"""
    TRANSACTION_TYPES = (
        ('appointment', 'Appointment Payment'),
        ('medication_order', 'Medication Order'),
        ('virtual_session', 'Virtual Consultation'),
        ('subscription', 'Subscription Payment'),
        ('premium_feature', 'Premium Feature'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    # Transaction details
    transaction_id = models.CharField(max_length=255, unique=True, default=generate_transaction_id)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    reference = models.CharField(max_length=255, null=True, blank=True)  # Payment gateway reference
    
    # User and related object
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='transactions')
    related_object_id = models.PositiveIntegerField(null=True, blank=True)  # Appointment ID, Order ID, etc.
    related_object_type = models.CharField(max_length=50, null=True, blank=True)  # 'appointment', 'order', etc.
    
    # Amounts
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total amount paid by user")
    platform_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Our commission")
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount to provider (gross - commission)")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Metadata
    payment_gateway = models.CharField(max_length=50, default='flutterwave')
    payment_method = models.CharField(max_length=50, null=True, blank=True)  # card, bank_transfer, etc.
    currency = models.CharField(max_length=3, default='NGN')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.transaction_id} - {self.transaction_type} - {self.gross_amount}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['transaction_type', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]


class RevenueReport(models.Model):
    """Aggregated revenue reports for analytics"""
    REPORT_PERIODS = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    )
    
    period_type = models.CharField(max_length=10, choices=REPORT_PERIODS)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Revenue breakdown
    total_gross_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_platform_commission = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_subscription_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_premium_feature_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Transaction counts
    total_transactions = models.IntegerField(default=0)
    successful_transactions = models.IntegerField(default=0)
    failed_transactions = models.IntegerField(default=0)
    
    # Breakdown by type
    appointment_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    medication_order_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    virtual_session_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('period_type', 'period_start', 'period_end')
        ordering = ['-period_start']

