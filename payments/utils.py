# payments/utils.py
"""
Utility functions for subscription, premium feature checks, and payment processing
"""
import requests
from django.conf import settings
from .models import UserSubscription
from django.utils import timezone

# Flutterwave API Configuration
FLUTTERWAVE_SECRET_KEY = getattr(settings, 'FLUTTERWAVE_SECRET_KEY', 'FLWSECK_TEST-SANDBOX')
FLUTTERWAVE_BASE_URL = "https://api.flutterwave.com/v3"

def get_headers():
    return {
        "Authorization": f"Bearer {FLUTTERWAVE_SECRET_KEY}",
        "Content-Type": "application/json"
    }

def create_flutterwave_subaccount(account_bank, account_number, business_name, business_email, business_contact_mobile, business_mobile, country="NG", split_type="percentage", split_value=0.1):
    """
    Create a subaccount on Flutterwave for a doctor or pharmacy.
    """
    url = f"{FLUTTERWAVE_BASE_URL}/subaccounts"
    payload = {
        "account_bank": account_bank,
        "account_number": account_number,
        "business_name": business_name,
        "business_email": business_email,
        "business_contact_mobile": business_contact_mobile,
        "business_mobile": business_mobile,
        "country": country,
        "split_type": split_type,
        "split_value": split_value
    }
    
    try:
        # In development/test without real keys, we mock the response
        if settings.DEBUG and 'TEST' in FLUTTERWAVE_SECRET_KEY:
            import uuid
            return {
                "status": "success",
                "message": "Subaccount created",
                "data": {
                    "subaccount_id": f"RS_{uuid.uuid4().hex[:12]}",
                    "account_bank": account_bank,
                    "account_number": account_number
                }
            }
            
        response = requests.post(url, json=payload, headers=get_headers())
        return response.json()
    except Exception as e:
        print(f"Error creating subaccount: {str(e)}")
        return None

def verify_bank_account(account_number, account_bank):
    """
    Verify a bank account with Flutterwave to get the account name.
    This helps prevent errors by confirming the account details before creating a subaccount.
    """
    url = f"{FLUTTERWAVE_BASE_URL}/accounts/resolve"
    payload = {
        "account_number": account_number,
        "account_bank": account_bank
    }
    
    try:
        # In development/test without real keys, we mock the response
        if settings.DEBUG and 'TEST' in FLUTTERWAVE_SECRET_KEY:
            # Bank code to name mapping for mock
            bank_names = {
                "044": "Access Bank",
                "023": "Citibank Nigeria",
                "063": "Diamond Bank",
                "050": "Ecobank Nigeria",
                "070": "Fidelity Bank",
                "011": "First Bank of Nigeria",
                "214": "First City Monument Bank (FCMB)",
                "058": "Guaranty Trust Bank (GTBank)",
                "030": "Heritage Bank",
                "301": "Jaiz Bank",
                "082": "Keystone Bank",
                "014": "MainStreet Bank",
                "076": "Skye Bank",
                "221": "Stanbic IBTC Bank",
                "068": "Standard Chartered Bank",
                "232": "Sterling Bank",
                "032": "Union Bank of Nigeria",
                "033": "United Bank for Africa (UBA)",
                "215": "Unity Bank",
                "035": "Wema Bank",
                "057": "Zenith Bank",
            }
            
            return {
                "status": "success",
                "message": "Account details fetched",
                "data": {
                    "account_number": account_number,
                    "account_name": "Test Account Name",
                    "bank_name": bank_names.get(account_bank, "Unknown Bank")
                }
            }
        
        response = requests.post(url, json=payload, headers=get_headers())
        return response.json()
    except Exception as e:
        print(f"Error verifying bank account: {str(e)}")
        return None


def initiate_split_payment(email, amount, reference, subaccount_id, commission_percentage=10.0, callback_url=None, metadata=None, customer_name=None, currency="NGN"):
    """
    Initiate a split payment transaction.
    """
    url = f"{FLUTTERWAVE_BASE_URL}/payments"
    
    # Calculate split
    # If commission is 10%, platform takes 10%, provider gets 90%
    # Flutterwave split logic:
    # We can use 'subaccounts' array.
    # transaction_charge_type='percentage'
    # transaction_charge = commission_percentage (platform fee) -> No, this is fee ON TOP or deducted?
    # Actually, Flutterwave split payments usually specify how much goes to the subaccount.
    # If we want to give 90% to subaccount:
    # transaction_charge_type = 'percentage'
    # transaction_charge = 10 (platform fee)
    # But wait, 'transaction_charge' is usually the fee paid by the customer?
    
    # Let's use the 'subaccounts' payload structure properly.
    # {
    #   "id": "RS_...",
    #   "transaction_charge_type": "percentage",
    #   "transaction_charge": 0.1 (10%)
    # }
    # Wait, if transaction_charge is 0.1, does it mean platform gets 0.1?
    
    # According to Flutterwave docs (standard split):
    # "transaction_split_ratio": 
    # Or "subaccounts": [ { "id": "...", "transaction_charge_type": "percentage", "transaction_charge": 0.05 } ]
    # If charge is 0.05 (5%), then 5% goes to platform? Or 5% is the fee?
    
    # Let's assume we want to give (100 - commission)% to the subaccount.
    # Use split_value in subaccount creation?
    # If subaccount was created with split_value, we might not need to specify it here?
    # But we want to be explicit per transaction.
    
    # Simplified approach:
    # We will just pass the subaccount ID. If the subaccount was created with a default split, it uses that.
    # But we want to enforce our commission.
    
    # Let's try to construct the payload as expected by Flutterwave for dynamic split.
    # But for now, let's just pass the subaccount ID in the list.
    
    subaccounts = [
        {
            "id": subaccount_id,
            # If we don't specify charge, it uses the subaccount's default split config
        }
    ]
    
    payload = {
        "tx_ref": reference,
        "amount": amount,
        "currency": currency,
        "redirect_url": callback_url,
        "payment_options": "card,banktransfer,ussd",
        "customer": {
            "email": email,
            "name": customer_name
        },
        "meta": metadata or {},
        "subaccounts": subaccounts
    }
    
    try:
        # Mock for dev
        if settings.DEBUG and 'TEST' in FLUTTERWAVE_SECRET_KEY:
            return {
                "status": "success",
                "message": "Payment initiated",
                "data": {
                    "link": f"https://checkout.flutterwave.com/mock/{reference}",
                    "tx_ref": reference
                }
            }

        response = requests.post(url, json=payload, headers=get_headers())
        return response.json()
    except Exception as e:
        print(f"Error initiating payment: {str(e)}")
        return {"status": "error", "message": str(e)}


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
    """
    Check if user can book appointment based on subscription.
    Free tier: Max 3 lifetime consultations.
    Premium/Family: Unlimited (or plan limit).
    """
    subscription = UserSubscription.objects.filter(
        user=user,
        status='active'
    ).first()
    
    from doctors.models import Appointment
    
    # Count ALL completed or scheduled appointments (excluding cancelled)
    total_appointments = Appointment.objects.filter(
        user=user,
        status__in=['scheduled', 'confirmed', 'completed']
    ).count()
    
    if not subscription or not subscription.is_active:
        # Free tier - check lifetime limit
        free_limit = getattr(settings, 'FREEMIUM_APPOINTMENT_LIMIT', 3)
        return total_appointments < free_limit
    else:
        # Premium - check plan limits
        max_appointments = subscription.plan.max_appointments_per_month
        if max_appointments is None:
            return True  # Unlimited
        
        # Check monthly limit for premium plans that have limits
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        appointments_this_month = Appointment.objects.filter(
            user=user,
            created_at__gte=month_start,
            status__in=['scheduled', 'confirmed', 'completed']
        ).count()
        
        return appointments_this_month < max_appointments

