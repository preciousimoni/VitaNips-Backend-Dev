from rest_framework import serializers
from .models import Pharmacy, Medication, PharmacyInventory, MedicationOrder, MedicationOrderItem, MedicationReminder

class PharmacySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pharmacy
        fields = [
            'id', 'name', 'address', 'phone_number', 'email', 'latitude',
            'longitude', 'operating_hours', 'is_24_hours', 'offers_delivery',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

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
    # Optionally add nested Pharmacy/User details if needed for display
    # pharmacy = PharmacySerializer(read_only=True)
    # user = UserSerializer(read_only=True) # Assuming UserSerializer is available

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