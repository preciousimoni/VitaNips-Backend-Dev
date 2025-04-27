from rest_framework import serializers
from .models import Pharmacy, Medication, PharmacyInventory, MedicationOrder, MedicationOrderItem, MedicationReminder
from users.serializers import UserSerializer
from doctors.serializers import PrescriptionItemSerializer

class PharmacySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pharmacy
        fields = [
            'id', 'name', 'address', 'phone_number', 'email', 'latitude',
            'longitude', 'operating_hours', 'is_24_hours', 'offers_delivery',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        
class PharmacyOrderItemViewSerializer(serializers.ModelSerializer):
    # prescription_item = PrescriptionItemSerializer(read_only=True) # Optionally show original details
    class Meta:
        model = MedicationOrderItem
        fields = [
            'id', 'medication_name_text', 'dosage_text', 'quantity',
            'price_per_unit', 'total_price'
            # Add frequency, duration, instructions if needed
        ]
        read_only_fields = fields # Read-only view for pharmacy initially

# Serializer for listing orders for the pharmacy dashboard
class PharmacyOrderListSerializer(serializers.ModelSerializer):
    # Show minimal patient info (consider privacy)
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = MedicationOrder
        fields = [
            'id', 'patient_name', 'status', 'order_date', 'is_delivery',
            'pickup_or_delivery_date', 'prescription' # Prescription ID for reference
        ]

    def get_patient_name(self, obj):
        # Example: Concatenate first/last name. Check if user object exists.
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
        return "N/A"

# Serializer for viewing/updating a specific order by pharmacy
class PharmacyOrderDetailSerializer(serializers.ModelSerializer):
    items = PharmacyOrderItemViewSerializer(many=True, read_only=True) # Use the read-only item view
    user = UserSerializer(read_only=True) # Show patient details (adjust fields in UserSerializer if needed)
    # Optionally add more details about the prescription or doctor

    class Meta:
        model = MedicationOrder
        fields = [
            'id', 'user', 'pharmacy', 'prescription', 'status', 'is_delivery',
            'delivery_address', 'total_amount', 'order_date', 'pickup_or_delivery_date',
            'notes', 'items'
        ]
        # Fields pharmacy can potentially UPDATE: status, notes, pickup_or_delivery_date
        # Price/Total Amount update might need a separate mechanism or serializer
        read_only_fields = [
            'id', 'user', 'pharmacy', 'prescription', 'order_date', 'items',
            'is_delivery', 'delivery_address', 'total_amount' # Initially read-only
            ]

# Serializer specifically for pharmacy updating an order (e.g., status, notes)
class PharmacyOrderUpdateSerializer(serializers.ModelSerializer):
     # Example: Define allowed status transitions
     ALLOWED_STATUS_TRANSITIONS = {
         'pending': ['processing', 'cancelled'],
         'processing': ['ready', 'cancelled'],
         'ready': ['delivering', 'completed', 'cancelled'], # If delivery offered
         'delivering': ['completed', 'cancelled'],
         # Cannot transition from completed or cancelled easily
     }

     class Meta:
        model = MedicationOrder
        fields = [
            'status', 'notes', 'pickup_or_delivery_date',
            # Possibly add total_amount here if pharmacy sets it directly
            # 'total_amount'
        ]
        # Price per item might need separate handling via item endpoint or nested writable serializer

     def validate_status(self, value):
        """Check for valid status transitions."""
        if self.instance: # Check only during updates
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