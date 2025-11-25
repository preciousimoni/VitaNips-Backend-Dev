# pharmacy/serializers.py
from rest_framework import serializers
from .models import (
    Pharmacy, Medication, PharmacyInventory,
    MedicationOrder, MedicationOrderItem, MedicationReminder,
    MedicationLog
)
from users.serializers import UserSerializer
from django.contrib.gis.geos import Point

class PharmacySerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)

    class Meta:
        model = Pharmacy
        fields = [
            'id', 'name', 'address', 'phone_number', 'email',
            'latitude', 'longitude', 'operating_hours', 'is_24_hours',
            'offers_delivery', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.location:
            rep['latitude'] = instance.location.y
            rep['longitude'] = instance.location.x
        else:
            rep['latitude'] = None
            rep['longitude'] = None
        return rep

    def validate(self, data):
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        if (latitude is not None) ^ (longitude is not None):
            raise serializers.ValidationError("Both latitude and longitude must be provided together.")
        return data

    def create(self, validated_data):
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        if latitude is not None and longitude is not None:
            validated_data['location'] = Point(longitude, latitude, srid=4326)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        if latitude is not None and longitude is not None:
            validated_data['location'] = Point(longitude, latitude, srid=4326)
        return super().update(instance, validated_data)


class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = [
            'id', 'name', 'generic_name', 'description', 'dosage_form',
            'strength', 'manufacturer', 'requires_prescription',
            'side_effects', 'contraindications', 'storage_instructions',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PharmacyInventorySerializer(serializers.ModelSerializer):
    medication = MedicationSerializer(read_only=True)
    medication_id = serializers.PrimaryKeyRelatedField(
        queryset=Medication.objects.all(),
        source='medication',
        write_only=True,
        required=False
    )

    class Meta:
        model = PharmacyInventory
        fields = ['id', 'pharmacy', 'medication', 'medication_id', 'in_stock', 'quantity', 'price', 'last_updated']
        read_only_fields = ['last_updated', 'pharmacy']


class PharmacyOrderItemViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationOrderItem
        fields = ['id', 'medication_name_text', 'dosage_text', 'quantity', 'price_per_unit', 'total_price']
        read_only_fields = fields

class MedicationOrderItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = MedicationOrderItem
        fields = ['id', 'prescription_item', 'quantity', 'price_per_unit', 'total_price']
        read_only_fields = ['id', 'price_per_unit', 'total_price']
        extra_kwargs = {
            'prescription_item': {'required': True}
        }


class PharmacyOrderListSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = MedicationOrder
        fields = ['id', 'patient_name', 'status', 'order_date', 'is_delivery', 'pickup_or_delivery_date', 'prescription']

    def get_patient_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
        return "N/A"

class PharmacyOrderDetailSerializer(serializers.ModelSerializer):
    items = PharmacyOrderItemViewSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    user_insurance = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MedicationOrder
        fields = [
            'id', 'user', 'pharmacy', 'prescription', 'status', 'is_delivery',
            'delivery_address', 'total_amount', 'order_date',
            'pickup_or_delivery_date', 'notes', 'items',
            'user_insurance', 'insurance_covered_amount', 'patient_copay',
            'insurance_claim_generated'
        ]
        read_only_fields = [
            'id', 'user', 'pharmacy', 'prescription', 'order_date',
            'items', 'is_delivery', 'delivery_address', 'total_amount',
            'user_insurance', 'insurance_covered_amount', 'patient_copay',
            'insurance_claim_generated'
        ]
    
    def get_user_insurance(self, obj):
        if obj.user_insurance:
            from insurance.serializers import UserInsuranceSerializer
            return UserInsuranceSerializer(obj.user_insurance).data
        return None

class MedicationOrderSerializer(serializers.ModelSerializer):
    items = MedicationOrderItemSerializer(many=True)
    pharmacy_details = PharmacySerializer(source='pharmacy', read_only=True)
    pharmacy = serializers.PrimaryKeyRelatedField(
        queryset=Pharmacy.objects.all(), write_only=True
    )
    user = UserSerializer(read_only=True)
    user_insurance_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text="ID of the insurance plan to use for this order"
    )
    user_insurance = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MedicationOrder
        fields = [
            'id', 'user', 'pharmacy', 'pharmacy_details', 'prescription', 'status', 'is_delivery',
            'delivery_address', 'total_amount', 'order_date',
            'pickup_or_delivery_date', 'notes', 'items',
            'user_insurance', 'user_insurance_id', 'insurance_covered_amount',
            'patient_copay', 'insurance_claim_generated'
        ]
        read_only_fields = [
            'user', 'order_date', 'status', 'total_amount',
            'user_insurance', 'insurance_covered_amount', 'patient_copay',
            'insurance_claim_generated'
        ]
    
    def validate_user_insurance_id(self, value):
        """Validate that the insurance belongs to the requesting user."""
        if value is None:
            return value
        
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            from insurance.models import UserInsurance
            try:
                insurance = UserInsurance.objects.get(id=value, user=request.user)
                return value
            except UserInsurance.DoesNotExist:
                raise serializers.ValidationError("Insurance plan not found or does not belong to you.")
        return value
    
    def get_user_insurance(self, obj):
        if obj.user_insurance:
            from insurance.serializers import UserInsuranceSerializer
            return UserInsuranceSerializer(obj.user_insurance).data
        return None

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = MedicationOrder.objects.create(**validated_data)
        for item_data in items_data:
            MedicationOrderItem.objects.create(order=order, **item_data)
        return order


class PharmacyOrderUpdateSerializer(serializers.ModelSerializer):
    user_insurance = serializers.SerializerMethodField(read_only=True)
    ALLOWED_STATUS_TRANSITIONS = {
        'pending': ['processing', 'cancelled'],
        'processing': ['ready', 'cancelled'],
        'ready': ['delivering', 'completed', 'cancelled'],
        'delivering': ['completed', 'cancelled'],
    }

    class Meta:
        model = MedicationOrder
        fields = [
            'status', 'notes', 'pickup_or_delivery_date', 'total_amount',
            'user_insurance', 'insurance_covered_amount', 'patient_copay',
            'insurance_claim_generated'
        ]
        read_only_fields = [
            'user_insurance', 'insurance_covered_amount', 'patient_copay',
            'insurance_claim_generated'
        ]
    
    def get_user_insurance(self, obj):
        if obj.user_insurance:
            from insurance.serializers import UserInsuranceSerializer
            return UserInsuranceSerializer(obj.user_insurance).data
        return None

    def validate_status(self, value):
        if self.instance:
            current_status = self.instance.status
            allowed_next = self.ALLOWED_STATUS_TRANSITIONS.get(current_status, [])
            if value not in allowed_next:
                raise serializers.ValidationError(
                    f"Cannot transition from status '{current_status}' to '{value}'. "
                    f"Allowed transitions: {', '.join(allowed_next) or 'None'}."
                )
        return value


class MedicationReminderSerializer(serializers.ModelSerializer):
    medication_display = MedicationSerializer(source='medication', read_only=True)
    medication_id = serializers.PrimaryKeyRelatedField(
        queryset=Medication.objects.all(),
        source='medication',
        write_only=True,
        required=False
    )
    medication_name_input = serializers.CharField(
        write_only=True,
        required=True,
        help_text="Name of the medication for the reminder."
    )

    class Meta:
        model = MedicationReminder
        fields = [
            'id', 'user', 'medication_display', 'medication_id', 'medication_name_input',
            'prescription_item', 'start_date', 'end_date', 'time_of_day', 'frequency',
            'custom_frequency', 'dosage', 'notes', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
        extra_kwargs = {
            'prescription_item': {'required': False, 'allow_null': True}
        }

    def validate(self, data):
        if not data.get('medication') and not data.get('medication_name_input'):
            raise serializers.ValidationError("Either medication_id or medication_name_input is required.")
        return data

class MedicationLogSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source='reminder.medication.name', read_only=True)
    
    class Meta:
        model = MedicationLog
        fields = [
            'id', 'reminder', 'medication_name', 'scheduled_time', 
            'taken_at', 'status', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']