# insurance/serializers.py
from rest_framework import serializers
from .models import InsuranceProvider, InsurancePlan, UserInsurance, InsuranceClaim, InsuranceDocument

class InsuranceProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceProvider
        fields = [
            'id', 'name', 'description', 'logo', 'contact_phone',
            'contact_email', 'website', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class InsurancePlanSerializer(serializers.ModelSerializer):
    provider = InsuranceProviderSerializer(read_only=True)

    class Meta:
        model = InsurancePlan
        fields = [
            'id', 'provider', 'name', 'plan_type', 'description', 'monthly_premium',
            'annual_deductible', 'out_of_pocket_max', 'coverage_details', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class UserInsuranceSerializer(serializers.ModelSerializer):
    plan = InsurancePlanSerializer(read_only=True)

    class Meta:
        model = UserInsurance
        fields = [
            'id', 'user', 'plan', 'policy_number', 'group_number', 'member_id',
            'start_date', 'end_date', 'is_primary', 'insurance_card_front',
            'insurance_card_back', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

class InsuranceClaimSerializer(serializers.ModelSerializer):
    user_insurance = UserInsuranceSerializer(read_only=True)

    class Meta:
        model = InsuranceClaim
        fields = [
            'id', 'user', 'user_insurance', 'claim_number', 'service_date',
            'provider_name', 'service_description', 'claimed_amount', 'approved_amount',
            'patient_responsibility', 'status', 'date_submitted', 'date_processed',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

class InsuranceDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceDocument
        fields = [
            'id', 'user', 'user_insurance', 'claim', 'title', 'document',
            'document_type', 'date_uploaded', 'notes', 'created_at'
        ]
        read_only_fields = ['user', 'date_uploaded', 'created_at']