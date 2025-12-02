# payments/premium_features.py
"""
Configuration and utilities for premium features pricing
All prices in Nigerian Naira (₦)
"""
from decimal import Decimal
from typing import Dict, Optional

# Premium feature prices (in NGN)
PREMIUM_FEATURE_PRICES = {
    'health_report': Decimal('500.00'),  # ₦500 per comprehensive health report
    'priority_booking': Decimal('300.00'),  # ₦300 per priority appointment slot
    'extended_consultation': Decimal('1000.00'),  # ₦1000 for 60-minute virtual session
    'premium_sos': Decimal('2000.00'),  # ₦2000/month for premium SOS features
}

# Premium feature descriptions
PREMIUM_FEATURE_DESCRIPTIONS = {
    'health_report': {
        'name': 'Health Report Generation',
        'description': 'Generate comprehensive PDF health reports with detailed analytics and trend analysis',
        'price': PREMIUM_FEATURE_PRICES['health_report'],
        'type': 'one_time',  # One-time payment per report
    },
    'priority_booking': {
        'name': 'Priority Appointment Booking',
        'description': 'Skip the queue and get guaranteed same-day appointments',
        'price': PREMIUM_FEATURE_PRICES['priority_booking'],
        'type': 'one_time',  # One-time payment per slot
    },
    'extended_consultation': {
        'name': 'Extended Virtual Consultation',
        'description': 'Extend your virtual consultation to 60 minutes (vs standard 30 minutes)',
        'price': PREMIUM_FEATURE_PRICES['extended_consultation'],
        'type': 'one_time',  # One-time payment per session
    },
    'premium_sos': {
        'name': 'Premium SOS Features',
        'description': 'Advanced emergency features including GPS tracking, family notifications, and emergency contact management',
        'price': PREMIUM_FEATURE_PRICES['premium_sos'],
        'type': 'recurring',  # Monthly subscription
    },
}


def get_premium_feature_price(feature_key: str) -> Decimal:
    """
    Get the price for a premium feature
    
    Args:
        feature_key: One of 'health_report', 'priority_booking', 'extended_consultation', 'premium_sos'
    
    Returns:
        Price in NGN
    """
    return PREMIUM_FEATURE_PRICES.get(feature_key, Decimal('0.00'))


def get_premium_feature_info(feature_key: str) -> Optional[Dict]:
    """
    Get full information about a premium feature
    
    Args:
        feature_key: One of 'health_report', 'priority_booking', 'extended_consultation', 'premium_sos'
    
    Returns:
        Dict with feature information or None if not found
    """
    return PREMIUM_FEATURE_DESCRIPTIONS.get(feature_key)


def list_all_premium_features() -> Dict:
    """
    Get all available premium features with their information
    
    Returns:
        Dict of all premium features
    """
    return PREMIUM_FEATURE_DESCRIPTIONS


def is_premium_feature_free_for_subscription(feature_key: str, subscription_tier: str) -> bool:
    """
    Check if a premium feature is free for a subscription tier
    
    Args:
        feature_key: The premium feature to check
        subscription_tier: 'free', 'premium', or 'family'
    
    Returns:
        True if the feature is free for this subscription tier
    """
    # Premium and Family plan users get some features for free
    if subscription_tier in ['premium', 'family']:
        # Premium users get priority booking for free
        if feature_key == 'priority_booking':
            return True
        # Premium users get extended consultations for free (up to a limit)
        if feature_key == 'extended_consultation':
            return True
    
    return False

