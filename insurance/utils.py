# insurance/utils.py
from decimal import Decimal
from .models import UserInsurance, InsurancePlan


def calculate_insurance_coverage(
    user_insurance: UserInsurance,
    total_amount: Decimal,
    service_type: str = 'consultation'  # 'consultation' or 'medication'
) -> dict:
    """
    Calculate insurance coverage for a service.
    
    Returns:
        dict with keys:
        - covered_amount: Amount covered by insurance
        - patient_copay: Patient's out-of-pocket amount
        - coverage_percentage: Percentage of coverage
        - deductible_applied: Whether deductible was applied
    """
    if not user_insurance:
        return {
            'covered_amount': Decimal('0.00'),
            'patient_copay': total_amount,
            'coverage_percentage': Decimal('0.00'),
            'deductible_applied': False,
        }
    
    plan = user_insurance.plan
    
    # Default coverage percentages (can be customized per plan)
    # HMO typically covers 80-100%, PPO 70-90%, etc.
    coverage_percentages = {
        'HMO': Decimal('0.90'),  # 90% coverage
        'PPO': Decimal('0.80'),  # 80% coverage
        'EPO': Decimal('0.85'),  # 85% coverage
        'POS': Decimal('0.75'),  # 75% coverage
        'HDHP': Decimal('0.60'),  # 60% coverage (after deductible)
        'other': Decimal('0.70'),  # 70% coverage
    }
    
    coverage_percentage = coverage_percentages.get(plan.plan_type, Decimal('0.70'))
    
    # For medications, some plans have different coverage
    if service_type == 'medication':
        # Medications might have slightly different coverage
        if plan.plan_type == 'HMO':
            coverage_percentage = Decimal('0.85')  # 85% for medications
        elif plan.plan_type == 'PPO':
            coverage_percentage = Decimal('0.75')  # 75% for medications
    
    # Calculate covered amount
    covered_amount = total_amount * coverage_percentage
    
    # Apply deductible if applicable (simplified - in real system, track cumulative deductible)
    # For HDHP, deductible must be met first
    if plan.plan_type == 'HDHP' and plan.annual_deductible > 0:
        # Simplified: assume deductible is already met or apply it
        # In production, you'd track cumulative deductible usage
        deductible_remaining = max(Decimal('0'), plan.annual_deductible)
        if deductible_remaining > 0:
            # Patient pays deductible first
            if total_amount <= deductible_remaining:
                return {
                    'covered_amount': Decimal('0.00'),
                    'patient_copay': total_amount,
                    'coverage_percentage': Decimal('0.00'),
                    'deductible_applied': True,
                }
            else:
                # Deductible met, apply coverage to remaining
                remaining_after_deductible = total_amount - deductible_remaining
                covered_amount = remaining_after_deductible * coverage_percentage
                patient_copay = deductible_remaining + (remaining_after_deductible - covered_amount)
                return {
                    'covered_amount': covered_amount,
                    'patient_copay': patient_copay,
                    'coverage_percentage': coverage_percentage,
                    'deductible_applied': True,
                }
    
    # Standard calculation
    patient_copay = total_amount - covered_amount
    
    # Ensure covered amount doesn't exceed total
    if covered_amount > total_amount:
        covered_amount = total_amount
        patient_copay = Decimal('0.00')
    
    return {
        'covered_amount': covered_amount.quantize(Decimal('0.01')),
        'patient_copay': patient_copay.quantize(Decimal('0.01')),
        'coverage_percentage': coverage_percentage,
        'deductible_applied': False,
    }


def generate_insurance_claim(
    user_insurance: UserInsurance,
    service_type: str,
    service_date,
    provider_name: str,
    service_description: str,
    claimed_amount: Decimal,
    approved_amount: Decimal = None,
    patient_responsibility: Decimal = None,
) -> 'InsuranceClaim':
    """
    Generate an insurance claim automatically.
    """
    from .models import InsuranceClaim
    from django.utils import timezone
    import random
    import string
    
    # Generate claim number
    claim_number = f"CLM-{timezone.now().strftime('%Y%m%d')}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
    
    claim = InsuranceClaim.objects.create(
        user=user_insurance.user,
        user_insurance=user_insurance,
        claim_number=claim_number,
        service_date=service_date,
        provider_name=provider_name,
        service_description=service_description,
        claimed_amount=claimed_amount,
        approved_amount=approved_amount or claimed_amount,
        patient_responsibility=patient_responsibility or Decimal('0.00'),
        status='submitted',
        date_submitted=timezone.now().date(),
    )
    
    return claim

