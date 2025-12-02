# payments/commission_service.py
"""
Service for calculating platform commissions and fees
"""
from decimal import Decimal
from django.conf import settings
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

# Commission rates (can be moved to settings or database)
COMMISSION_RATES = {
    'appointment': Decimal('0.12'),  # 12% commission on appointments
    'medication_order': Decimal('0.08'),  # 8% commission on medication orders
    'virtual_session': Decimal('0.10'),  # 10% commission on virtual sessions
    'virtual_session_fee': Decimal('3.00'),  # Flat $3 fee per virtual session
}

# Minimum commission amounts
MIN_COMMISSIONS = {
    'appointment': Decimal('2.00'),
    'medication_order': Decimal('1.00'),
    'virtual_session': Decimal('2.00'),
}

# Maximum commission amounts (optional, to protect providers)
MAX_COMMISSIONS = {
    'appointment': Decimal('50.00'),
    'medication_order': Decimal('20.00'),
    'virtual_session': Decimal('15.00'),
}


def calculate_commission(
    transaction_type: str,
    gross_amount: Decimal,
    use_flat_fee: bool = False
) -> Tuple[Decimal, Decimal]:
    """
    Calculate platform commission and net amount for a transaction
    
    Args:
        transaction_type: Type of transaction ('appointment', 'medication_order', 'virtual_session')
        gross_amount: Total amount paid by user
        use_flat_fee: For virtual sessions, use flat fee instead of percentage
    
    Returns:
        Tuple of (platform_commission, net_amount)
    """
    if transaction_type not in COMMISSION_RATES:
        logger.warning(f"Unknown transaction type: {transaction_type}, using 0% commission")
        return Decimal('0.00'), gross_amount
    
    # For virtual sessions, can use flat fee
    if transaction_type == 'virtual_session' and use_flat_fee:
        commission = COMMISSION_RATES.get('virtual_session_fee', Decimal('3.00'))
    else:
        # Calculate percentage-based commission
        rate = COMMISSION_RATES[transaction_type]
        commission = gross_amount * rate
    
    # Apply minimum commission
    min_commission = MIN_COMMISSIONS.get(transaction_type, Decimal('0.00'))
    if commission < min_commission:
        commission = min_commission
    
    # Apply maximum commission (if set)
    max_commission = MAX_COMMISSIONS.get(transaction_type)
    if max_commission and commission > max_commission:
        commission = max_commission
    
    # Calculate net amount (what provider receives)
    net_amount = gross_amount - commission
    
    # Ensure net amount is not negative
    if net_amount < 0:
        net_amount = Decimal('0.00')
        commission = gross_amount
    
    return commission, net_amount


def calculate_appointment_commission(consultation_fee: Decimal) -> Tuple[Decimal, Decimal]:
    """Calculate commission for appointment booking"""
    return calculate_commission('appointment', consultation_fee)


def calculate_medication_order_commission(order_total: Decimal) -> Tuple[Decimal, Decimal]:
    """Calculate commission for medication order"""
    return calculate_commission('medication_order', order_total)


def calculate_virtual_session_commission(
    consultation_fee: Decimal,
    use_flat_fee: bool = True
) -> Tuple[Decimal, Decimal]:
    """
    Calculate commission for virtual consultation
    
    Args:
        consultation_fee: Doctor's consultation fee
        use_flat_fee: If True, use flat $3 fee; if False, use percentage
    """
    return calculate_commission('virtual_session', consultation_fee, use_flat_fee=use_flat_fee)


def get_commission_breakdown(transaction_type: str, gross_amount: Decimal) -> Dict:
    """
    Get detailed commission breakdown for display/analytics
    
    Returns:
        Dict with commission details
    """
    commission, net_amount = calculate_commission(transaction_type, gross_amount)
    rate = COMMISSION_RATES.get(transaction_type, Decimal('0.00'))
    
    return {
        'gross_amount': str(gross_amount),
        'commission_rate': f"{rate * 100}%",
        'platform_commission': str(commission),
        'provider_net_amount': str(net_amount),
        'commission_percentage': float(rate * 100),
    }

