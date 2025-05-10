# pharmacy/serializers.py
from rest_framework import serializers
from .models import Pharmacy, Medication, PharmacyInventory, MedicationOrder, MedicationOrderItem, MedicationReminder
from users.serializers import UserSerializer
from doctors.serializers import PrescriptionItemSerializer
from django.contrib.gis.geos import Point

class PharmacySerializer(serializers.ModelSerializer):
    # Define latitude and longitude as serializer fields (not model fields)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)

    class Meta:
        model = Pharmacy
        fields = [
            'id', 'name', 'address', 'phone_number', 'email', 'latitude',
            'longitude', 'operating_hours', 'is_24_hours', 'offers_delivery',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_representation(self, instance):
        """
        Convert the PointField (location) to separate latitude and longitude fields in the response.
        """
        representation = super().to_representation(instance)
        if instance.location:
            # Extract latitude (y) and longitude (x) from Point
            representation['latitude'] = instance.location.y
            representation['longitude'] = instance.location.x
        else:
            representation['latitude'] = None
            representation['longitude'] = None
        return representation

    def validate(self, data):
        """
        Ensure that both latitude and longitude are provided together if one is present.
        """
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        if (latitude is not None and longitude is None) or (longitude is not None and latitude is None):
            raise serializers.ValidationError(
                "Both latitude and longitude must be provided together."
            )
        return data

    def create(self, validated_data):
        """
        Convert latitude and longitude to a PointField for the location.
        """
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        if latitude is not None and longitude is not None:
            validated_data['location'] = Point(longitude, latitude, srid=4326)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update the location PointField if latitude and longitude are provided.
        """
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        if latitude is not None and longitude is not None:
            validated_data['location'] = Point(longitude, latitude, srid=4326)
        elif latitude is None and longitude is None:
            # Preserve existing location if neither is provided
            validated_data['location'] = instance.location
        return super().update(instance, validated_data)

class PharmacyOrderItemViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationOrderItem
        fields = [
            'id', 'medication_name_text', 'dosage_text', 'quantity',
            'price_per_unit', 'total_price'
        ]
        read_only_fields = fields

class PharmacyOrderListSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = MedicationOrder
        fields = [
            'id', 'patient_name', 'status', 'order_date', 'is_delivery',
            'pickup_or_delivery_date', 'prescription'
        ]

    def get_patient_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
        return "N/A"

class PharmacyOrderDetailSerializer(serializers.ModelSerializer):
    items = PharmacyOrderItemViewSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = MedicationOrder
        fields = [
            'id', 'user', 'pharmacy', 'prescription', 'status', 'is_delivery',
            'delivery_address', 'total_amount', 'order_date', 'pickup_or_delivery_date',
            'notes', 'items'
        ]
        
        read_only_fields = [
            'id', 'user', 'pharmacy', 'prescription', 'order_date', 'items',
            'is_delivery', 'delivery_address', 'total_amount'
        ]

class PharmacyOrderUpdateSerializer(serializers.ModelSerializer):
    ALLOWED_STATUS_TRANSITIONS = {
        'pending': ['processing', 'cancelled'],
        'processing': ['ready', 'cancelled'],
        'ready': ['delivering', 'completed', 'cancelled'],
        'delivering': ['completed', 'cancelled'],
    }

    class Meta:
        model = MedicationOrder
        fields = [
            'status', 'notes', 'pickup_or_delivery_date', 'total_amount'
        ]

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

class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = [
            'id', 'name', 'generic_name', 'description', 'dosage_form', 'strength',
            'manufacturer', 'requires_prescription', 'side_effects', 'contraindications',
            'storage_instructions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class PharmacyInventorySerializer(serializers.ModelSerializer):
    medication = MedicationSerializer(read_only=True)

    class Meta:
        model = PharmacyInventory
        fields = ['id', 'pharmacy', 'medication', 'in_stock', 'quantity', 'price', 'last_updated']
        read_only_fields = ['last_updated']

class MedicationOrderItemSerializer(serializers.ModelSerializer):
    medication_name = serializers.ReadOnlyField(source='medication_name_text')
    dosage = serializers.ReadOnlyField(source='dosage_text')

    class Meta:
        model = MedicationOrderItem
        fields = ['id', 'order', 'prescription_item', 'medication_name', 'dosage', 'quantity', 'price_per_unit', 'total_price']
        read_only_fields = ['total_price', 'order', 'medication_name', 'dosage']

class MedicationOrderSerializer(serializers.ModelSerializer):
    items = MedicationOrderItemSerializer(many=True, read_only=True)
    pharmacy = PharmacySerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = MedicationOrder
        fields = [
            'id', 'user', 'pharmacy', 'prescription', 'status', 'is_delivery',
            'delivery_address', 'total_amount', 'order_date', 'pickup_or_delivery_date',
            'notes', 'items'
        ]
        read_only_fields = ['user', 'order_date', 'items', 'status', 'total_amount']

class MedicationReminderSerializer(serializers.ModelSerializer):
    medication = MedicationSerializer(read_only=True)

    class Meta:
        model = MedicationReminder
        fields = [
            'id', 'user', 'medication', 'prescription_item', 'start_date', 'end_date',
            'time_of_day', 'frequency', 'custom_frequency', 'dosage', 'notes',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']