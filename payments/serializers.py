# payments/serializers.py
from rest_framework import serializers
from .models import (
    SubscriptionPlan,
    UserSubscription,
    DoctorSubscription,
    DoctorSubscriptionRecord,
    PharmacySubscription,
    PharmacySubscriptionRecord,
    Transaction
)


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'tier', 'description',
            'monthly_price', 'annual_price',
            'features', 'max_appointments_per_month',
            'max_family_members', 'is_active'
        ]


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    is_active = serializers.ReadOnlyField()
    price = serializers.ReadOnlyField()
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'plan', 'status', 'billing_cycle',
            'started_at', 'current_period_start',
            'current_period_end', 'cancelled_at',
            'auto_renew', 'is_active', 'price'
        ]


class DoctorSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorSubscription
        fields = '__all__'


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'transaction_id', 'transaction_type',
            'gross_amount', 'platform_commission',
            'net_amount', 'status', 'payment_method',
            'currency', 'created_at', 'completed_at'
        ]
        read_only_fields = ['transaction_id', 'created_at', 'completed_at']


class PharmacySubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PharmacySubscription
        fields = '__all__'


class PharmacySubscriptionRecordSerializer(serializers.ModelSerializer):
    plan = PharmacySubscriptionSerializer(read_only=True)
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = PharmacySubscriptionRecord
        fields = [
            'id', 'plan', 'status',
            'current_period_start', 'current_period_end',
            'auto_renew', 'is_active'
        ]

