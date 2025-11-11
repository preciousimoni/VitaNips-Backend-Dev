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
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=InsurancePlan.objects.all(), source='plan', write_only=True
    )

    class Meta:
        model = UserInsurance
        fields = [
            'id', 'user', 'plan', 'plan_id', 'policy_number', 'group_number', 'member_id',
            'start_date', 'end_date', 'is_primary', 'insurance_card_front',
            'insurance_card_back', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

class InsuranceClaimSerializer(serializers.ModelSerializer):
    user_insurance = UserInsuranceSerializer(read_only=True)
    user_insurance_id = serializers.PrimaryKeyRelatedField(
        queryset=UserInsurance.objects.all(), source='user_insurance', write_only=True
    )

    class Meta:
        model = InsuranceClaim
        fields = [
            'id', 'user', 'user_insurance', 'user_insurance_id', 'claim_number', 'service_date',
            'provider_name', 'service_description', 'claimed_amount', 'approved_amount',
            'patient_responsibility', 'status', 'date_submitted', 'date_processed',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

class InsuranceDocumentSerializer(serializers.ModelSerializer):
    user_insurance_id = serializers.PrimaryKeyRelatedField(
        queryset=UserInsurance.objects.all(), source='user_insurance', write_only=True, required=False
    )
    claim_id = serializers.PrimaryKeyRelatedField(
        queryset=InsuranceClaim.objects.all(), source='claim', write_only=True, required=False
    )

    class Meta:
        model = InsuranceDocument
        fields = [
            'id', 'user', 'user_insurance', 'user_insurance_id', 'claim', 'claim_id', 'title', 'document',
            'document_type', 'date_uploaded', 'notes', 'created_at'
        ]
        read_only_fields = ['user', 'date_uploaded', 'created_at']