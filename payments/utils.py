# payments/utils.py
"""
Utility functions for subscription and premium feature checks
"""
from .models import UserSubscription
from django.utils import timezone


def user_has_premium(user):
    """Check if user has active premium subscription"""
    subscription = UserSubscription.objects.filter(
        user=user,
        status='active'
    ).first()
    return subscription and subscription.is_active


def get_user_subscription_tier(user):
    """Get user's current subscription tier"""
    subscription = UserSubscription.objects.filter(
        user=user,
        status='active'
    ).first()
    
    if subscription and subscription.is_active:
        return subscription.plan.tier
    return 'free'


def user_can_book_appointment(user):
    """Check if user can book appointment based on subscription"""
    subscription = UserSubscription.objects.filter(
        user=user,
        status='active'
    ).first()
    
    if not subscription or not subscription.is_active:
        # Free tier - check monthly limit
        from doctors.models import Appointment
        
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        appointments_this_month = Appointment.objects.filter(
            user=user,
            created_at__gte=month_start
        ).count()
        
        return appointments_this_month < 3  # Free tier limit
    else:
        # Premium - check plan limits
        max_appointments = subscription.plan.max_appointments_per_month
        if max_appointments is None:
            return True  # Unlimited
        
        # Check monthly limit
        from doctors.models import Appointment
        
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        appointments_this_month = Appointment.objects.filter(
            user=user,
            created_at__gte=month_start
        ).count()
        
        return appointments_this_month < max_appointments

