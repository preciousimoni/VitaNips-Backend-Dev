# doctors/serializers.py
from rest_framework import serializers
from .models import Specialty, Doctor, DoctorReview, DoctorAvailability, Appointment, Prescription, PrescriptionItem
from pharmacy.models import Medication
# from pharmacy.serializers import MedicationSerializer

class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ['id', 'name', 'description']

class DoctorUserSerializer(serializers.Serializer):
    """Nested serializer for user data in DoctorSerializer"""
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    username = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

class DoctorSerializer(serializers.ModelSerializer):
    specialties = SpecialtySerializer(many=True, read_only=True)
    average_rating = serializers.ReadOnlyField()
    user = DoctorUserSerializer(read_only=True)

    class Meta:
        model = Doctor
        fields = [
            'id', 'user', 'first_name', 'last_name', 'full_name', 'specialties',
            'profile_picture', 'gender', 'years_of_experience', 'education',
            'bio', 'languages_spoken', 'consultation_fee', 'is_available_for_virtual',
            'is_verified', 'average_rating', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'full_name', 'average_rating']

class DoctorReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorReview
        fields = ['id', 'doctor', 'user', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['doctor', 'user', 'created_at', 'updated_at']

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    
    def validate(self, data):
        # Check if user has already reviewed this doctor
        request = self.context.get('request')
        doctor_id = self.context.get('view').kwargs.get('doctor_id')
        
        if request and doctor_id:
            user = request.user
            if DoctorReview.objects.filter(doctor_id=doctor_id, user=user).exists():
                raise serializers.ValidationError(
                    "You have already submitted a review for this doctor. Each user can only review a doctor once."
                )
        
        return data

class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorAvailability
        fields = ['id', 'doctor', 'day_of_week', 'start_time', 'end_time', 'is_available']
        read_only_fields = ['doctor']

class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField(read_only=True)
    patient_email = serializers.EmailField(source='user.email', read_only=True)
    doctor_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'user', 'doctor', 'date', 'start_time', 'end_time',
            'appointment_type', 'status', 'reason', 'notes', 'followup_required',
            'patient_name', 'patient_email', 'doctor_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'patient_name', 'patient_email', 'doctor_name', 'created_at', 'updated_at']

    def get_patient_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return None
    
    def get_doctor_name(self, obj):
        if obj.doctor:
            return f"Dr. {obj.doctor.last_name}" if obj.doctor.last_name else f"Dr. {obj.doctor.first_name}"
        return None

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
    from pharmacy.serializers import MedicationSerializer
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
        # Fixed: Use the correct status choice
        if appointment.status != Appointment.StatusChoices.COMPLETED:
            raise serializers.ValidationError(f"Prescriptions can only be written for 'Completed' appointments. This one is '{appointment.get_status_display()}'.")
        if Prescription.objects.filter(appointment=appointment).exists():
            raise serializers.ValidationError("A prescription already exists for this appointment.")
        return appointment

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        appointment = validated_data.pop('appointment')  # Remove from validated_data to avoid passing it twice

        # Get doctor and user from extra kwargs passed by perform_create, or fallback to context
        doctor = validated_data.pop('doctor', None) or self.context['request'].user.doctor_profile
        user = validated_data.pop('user', None) or appointment.user

        try:
            prescription = Prescription.objects.create(
                doctor=doctor,
                user=user,
                appointment=appointment,
                **validated_data  # Now only contains diagnosis and notes
            )

            for item_data in items_data:
                medication_name = item_data.pop('medication_name_input')
                # Try to find existing medication with case-insensitive match
                medication_obj = Medication.objects.filter(name__iexact=medication_name).first()
                if not medication_obj:
                    # Create new medication if not found
                    medication_obj = Medication.objects.create(
                        name=medication_name,
                        description=f'Medication: {medication_name}',
                        dosage_form='To be specified',
                        strength=item_data.get('dosage', 'To be specified'),
                        requires_prescription=True,
                    )
                PrescriptionItem.objects.create(
                    prescription=prescription, 
                    medication=medication_obj, 
                    medication_name=medication_name, 
                    **item_data
                )
            return prescription
        except Exception as e:
            import traceback
            print(f"Error creating prescription: {str(e)}")
            print(traceback.format_exc())
            raise serializers.ValidationError(f"Failed to create prescription: {str(e)}")

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


class VirtualSessionSerializer(serializers.ModelSerializer):
    """Serializer for VirtualSession model"""
    appointment_id = serializers.IntegerField(source='appointment.id', read_only=True)
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    appointment_date = serializers.SerializerMethodField()
    
    class Meta:
        from .models import VirtualSession
        model = VirtualSession
        fields = [
            'id', 'appointment_id', 'room_name', 'room_sid',
            'status', 'started_at', 'ended_at', 'duration_minutes',
            'recording_url', 'notes', 'patient_name', 'doctor_name',
            'appointment_date', 'created_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_patient_name(self, obj):
        if obj.appointment and obj.appointment.patient:
            return obj.appointment.patient.get_full_name()
        return "Unknown"
    
    def get_doctor_name(self, obj):
        if obj.appointment and obj.appointment.doctor:
            return obj.appointment.doctor.user.get_full_name()
        return "Unknown"
    
    def get_appointment_date(self, obj):
        if obj.appointment:
            return obj.appointment.date_time.isoformat() if hasattr(obj.appointment, 'date_time') else str(obj.appointment.date)
        return None