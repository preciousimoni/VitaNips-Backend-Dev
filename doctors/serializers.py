# doctors/serializers.py
from rest_framework import serializers
from .models import Specialty, Doctor, DoctorReview, DoctorAvailability, Appointment, Prescription, PrescriptionItem
from pharmacy.models import Medication
from pharmacy.serializers import MedicationSerializer

class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ['id', 'name', 'description']

class DoctorSerializer(serializers.ModelSerializer):
    specialties = SpecialtySerializer(many=True, read_only=True)
    average_rating = serializers.ReadOnlyField()

    class Meta:
        model = Doctor
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'specialties',
            'profile_picture', 'gender', 'years_of_experience', 'education',
            'bio', 'languages_spoken', 'consultation_fee', 'is_available_for_virtual',
            'is_verified', 'average_rating', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'full_name', 'average_rating']

class DoctorReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorReview
        fields = ['id', 'doctor', 'user', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorAvailability
        fields = ['id', 'doctor', 'day_of_week', 'start_time', 'end_time', 'is_available']
        read_only_fields = ['doctor']

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            'id', 'user', 'doctor', 'date', 'start_time', 'end_time',
            'appointment_type', 'status', 'reason', 'notes', 'followup_required',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def validate(self, data):
        instance = getattr(self, 'instance', None)

        start_time = data.get('start_time', instance.start_time if instance else None)
        end_time = data.get('end_time', instance.end_time if instance else None)

        if start_time is not None and end_time is not None:
            if start_time >= end_time:
                raise serializers.ValidationError({
                    "detail": "End time must be after start time.",
                    "start_time": f"Start time ({start_time}) cannot be after or equal to end time ({end_time}).",
                    "end_time": f"End time ({end_time}) must be after start time ({start_time}).",
                })
        return data
    
class DoctorPrescriptionItemCreateSerializer(serializers.ModelSerializer):
    medication_name_input = serializers.CharField(
        write_only=True, required=True,
        help_text="Name of the medication. A Medication object will be looked up or created."
    )
    # medication_id = serializers.PrimaryKeyRelatedField(queryset=Medication.objects.all(), source='medication', required=False, allow_null=True)

    class Meta:
        model = PrescriptionItem
        fields = [
            'medication_name_input', # Doctor types this
            # 'medication_id', # Alternative input
            'dosage',
            'frequency',
            'duration',
            'instructions',
        ]

class DoctorPrescriptionItemDisplaySerializer(serializers.ModelSerializer):
    medication_display = MedicationSerializer(source='medication', read_only=True)

    class Meta:
        model = PrescriptionItem
        fields = [
            'id',
            'medication_display',
            'medication_name',
            'dosage',
            'frequency',
            'duration',
            'instructions',
        ]

class DoctorPrescriptionCreateSerializer(serializers.ModelSerializer):
    items = DoctorPrescriptionItemCreateSerializer(many=True)
    appointment_id = serializers.PrimaryKeyRelatedField(
        queryset=Appointment.objects.all(),
        source='appointment',
        write_only=True,
        help_text="ID of the completed appointment this prescription is for."
    )

    class Meta:
        model = Prescription
        fields = [
            'appointment_id',
            'diagnosis',
            'notes',
            'items',
        ]

    def validate_appointment_id(self, appointment):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not hasattr(request.user, 'doctor_profile'):
            raise serializers.ValidationError("User or doctor profile not found in request context.")

        doctor_profile = request.user.doctor_profile

        if appointment.doctor != doctor_profile:
            raise serializers.ValidationError("This appointment is not assigned to you.")
        if appointment.status != Appointment.StatusChoices.COMPLETED:
            raise serializers.ValidationError(f"Prescriptions can only be written for 'Completed' appointments. This one is '{appointment.get_status_display()}'.")
        if Prescription.objects.filter(appointment=appointment).exists():
            raise serializers.ValidationError("A prescription already exists for this appointment.")
        return appointment

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        appointment = validated_data.get('appointment')

        doctor = self.context['request'].user.doctor_profile
        patient = appointment.user

        prescription = Prescription.objects.create(
            doctor=doctor,
            user=patient,
            **validated_data
        )

        for item_data in items_data:
            medication_name = item_data.pop('medication_name_input')
            medication_obj, _ = Medication.objects.get_or_create(
                name__iexact=medication_name,
                defaults={
                    'description': f'Medication: {medication_name}',
                    'dosage_form': 'To be specified',
                    'strength': item_data.get('dosage', 'To be specified'),
                    'requires_prescription': True,
                }
            )
            PrescriptionItem.objects.create(prescription=prescription, medication=medication_obj, medication_name=medication_name, **item_data)
        return prescription

class DoctorPrescriptionListDetailSerializer(serializers.ModelSerializer):
    items = DoctorPrescriptionItemDisplaySerializer(many=True, read_only=True)
    patient_email = serializers.EmailField(source='user.email', read_only=True)
    patient_name = serializers.SerializerMethodField(read_only=True)
    appointment_date = serializers.DateField(source='appointment.date', read_only=True)


    class Meta:
        model = Prescription
        fields = [
            'id', 'appointment', 'appointment_date', 'user', 'patient_email', 'patient_name',
            'doctor', 'date_prescribed', 'diagnosis', 'notes', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'doctor', 'date_prescribed', 'created_at', 'updated_at', 'items', 'patient_email', 'patient_name', 'appointment_date']

    def get_patient_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
        return "N/A"

class DoctorEligibleAppointmentSerializer(serializers.ModelSerializer):
    patient_email = serializers.EmailField(source='user.email', read_only=True)
    patient_name = serializers.SerializerMethodField(read_only=True)
    has_existing_prescription = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'date', 'start_time', 'end_time', 'reason', 'status',
            'user', 'patient_email', 'patient_name',
            'has_existing_prescription'
        ]

    def get_patient_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
        return "N/A"

    def get_has_existing_prescription(self, obj):
        return Prescription.objects.filter(appointment=obj).exists()

class PrescriptionItemSerializer(serializers.ModelSerializer):
    # Move the medication serializer import inside the to_representation method
    # to break the circular import
    medication_details = serializers.SerializerMethodField()
    
    # Use deferred import and queryset assignment for medication_id
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from pharmacy.models import Medication
        self.fields['medication_id'] = serializers.PrimaryKeyRelatedField(
            queryset=Medication.objects.all(),
            source='medication',
            write_only=True,
            allow_null=True,
            required=False
        )

    class Meta:
        model = PrescriptionItem
        fields = ['id', 'prescription', 'medication_id', 'medication_details', 'medication_name', 'dosage', 'frequency', 'duration', 'instructions']

    def get_medication_details(self, obj):
        if obj.medication:
            # Import here to avoid circular import
            from pharmacy.serializers import MedicationSerializer
            return MedicationSerializer(obj.medication).data
        return None

class PrescriptionSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True, read_only=True)

    class Meta:
        model = Prescription
        fields = ['id', 'appointment', 'user', 'doctor', 'date_prescribed', 'diagnosis', 'notes', 'items', 'created_at', 'updated_at']
        read_only_fields = ['user', 'doctor', 'date_prescribed', 'created_at', 'updated_at']