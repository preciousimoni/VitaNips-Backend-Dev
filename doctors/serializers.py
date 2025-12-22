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

class DoctorApplicationSerializer(serializers.ModelSerializer):
    """Serializer for doctors to submit their application"""
    specialty_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Specialty.objects.all(),
        source='specialties',
        write_only=True,
        required=True,
        help_text="List of specialty IDs"
    )
    specialties = SpecialtySerializer(many=True, read_only=True)

    class Meta:
        model = Doctor
        fields = [
            'id', 'first_name', 'last_name', 'specialty_ids', 'specialties',
            'profile_picture', 'gender', 'years_of_experience', 'education',
            'bio', 'languages_spoken', 'consultation_fee', 'is_available_for_virtual',
            'license_number', 'license_issuing_authority', 'license_expiry_date',
            'hospital_name', 'hospital_address', 'hospital_phone', 'hospital_email',
            'hospital_contact_person', 'application_status', 'submitted_at',
        ]
        read_only_fields = ['id', 'application_status', 'submitted_at', 'specialties']

    def validate_license_number(self, value):
        if not value:
            raise serializers.ValidationError("License number is required for application.")
        return value

    def validate_hospital_name(self, value):
        if not value:
            raise serializers.ValidationError("Hospital name is required for application.")
        return value

    def validate_hospital_phone(self, value):
        if not value:
            raise serializers.ValidationError("Hospital contact phone is required for application.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("User must be authenticated to submit application.")
        
        specialties = validated_data.pop('specialties', [])
        doctor = Doctor.objects.create(
            user=request.user,
            application_status='submitted',
            **validated_data
        )
        doctor.specialties.set(specialties)
        
        # Set submitted_at timestamp
        from django.utils import timezone
        doctor.submitted_at = timezone.now()
        doctor.save()
        
        return doctor

    def update(self, instance, validated_data):
        specialties = validated_data.pop('specialties', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if specialties is not None:
            instance.specialties.set(specialties)
        
        instance.save()
        return instance


class DoctorSerializer(serializers.ModelSerializer):
    specialties = SpecialtySerializer(many=True, read_only=True)
    average_rating = serializers.ReadOnlyField()
    user = DoctorUserSerializer(read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = [
            'id', 'user', 'first_name', 'last_name', 'full_name', 'specialties',
            'profile_picture', 'gender', 'years_of_experience', 'education',
            'bio', 'languages_spoken', 'consultation_fee', 'is_available_for_virtual',
            'is_verified', 'average_rating', 'application_status', 'license_number',
            'license_issuing_authority', 'license_expiry_date', 'hospital_name',
            'hospital_address', 'hospital_phone', 'hospital_email', 'hospital_contact_person',
            'submitted_at', 'reviewed_at', 'reviewed_by', 'reviewed_by_name', 'review_notes', 'rejection_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'full_name', 'average_rating',
            'reviewed_at', 'reviewed_by', 'is_verified', 'reviewed_by_name'
        ]

    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return f"{obj.reviewed_by.first_name} {obj.reviewed_by.last_name}".strip() or obj.reviewed_by.username
        return None

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Fallback to user profile picture if doctor profile picture is missing
        if not ret.get('profile_picture') and instance.user and instance.user.profile_picture:
            try:
                request = self.context.get('request')
                if request:
                    ret['profile_picture'] = request.build_absolute_uri(instance.user.profile_picture.url)
                else:
                    ret['profile_picture'] = instance.user.profile_picture.url
            except Exception:
                # Fallback if URL construction fails
                pass
        return ret

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
    
    def validate_start_time(self, value):
        """Ensure start_time is in correct format"""
        if isinstance(value, str):
            # Handle "HH:MM" format by converting to "HH:MM:SS"
            if len(value) == 5 and value.count(':') == 1:
                return f"{value}:00"
        return value
    
    def validate_end_time(self, value):
        """Ensure end_time is in correct format"""
        if isinstance(value, str):
            # Handle "HH:MM" format by converting to "HH:MM:SS"
            if len(value) == 5 and value.count(':') == 1:
                return f"{value}:00"
        return value
    
    def validate(self, data):
        """Validate that end_time is after start_time"""
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if start_time and end_time:
            # Convert to time objects for comparison
            from datetime import datetime
            try:
                if isinstance(start_time, str):
                    start = datetime.strptime(start_time, '%H:%M:%S').time()
                else:
                    start = start_time
                
                if isinstance(end_time, str):
                    end = datetime.strptime(end_time, '%H:%M:%S').time()
                else:
                    end = end_time
                
                if start >= end:
                    raise serializers.ValidationError({
                        'end_time': 'End time must be after start time.'
                    })
            except ValueError:
                # If parsing fails, let Django handle the validation
                pass
        
        return data

class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField(read_only=True)
    patient_email = serializers.EmailField(source='user.email', read_only=True)
    doctor_name = serializers.SerializerMethodField(read_only=True)
    user_insurance_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text="ID of the insurance plan to use for this appointment"
    )
    user_insurance = serializers.SerializerMethodField(read_only=True)
    payment_reference = serializers.CharField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text="Payment reference/transaction ID from payment gateway"
    )
    payment_status = serializers.SerializerMethodField(read_only=True)
    original_appointment_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text="ID of the original appointment if this is a follow-up"
    )
    test_request_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text="ID of the test request to link this follow-up appointment to"
    )
    is_followup = serializers.BooleanField(read_only=True)
    original_appointment = serializers.IntegerField(source='original_appointment.id', read_only=True, allow_null=True)
    followup_discount_percentage = serializers.DecimalField(read_only=True, max_digits=5, decimal_places=2)
    linked_test_request = serializers.SerializerMethodField(read_only=True, required=False)
    test_results = serializers.SerializerMethodField(read_only=True, required=False)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'user', 'doctor', 'date', 'start_time', 'end_time',
            'appointment_type', 'status', 'reason', 'notes', 'followup_required',
            'patient_name', 'patient_email', 'doctor_name',
            'user_insurance', 'user_insurance_id', 'consultation_fee',
            'insurance_covered_amount', 'patient_copay', 'insurance_claim_generated',
            'payment_reference', 'payment_status',
            'is_followup', 'original_appointment_id', 'original_appointment',
            'test_request_id', 'followup_discount_percentage',
            'linked_test_request', 'test_results',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user', 'patient_name', 'patient_email', 'doctor_name',
            'user_insurance', 'consultation_fee', 'insurance_covered_amount',
            'patient_copay', 'insurance_claim_generated',
            'is_followup', 'original_appointment', 'followup_discount_percentage',
            'created_at', 'updated_at'
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

    def get_payment_status(self, obj):
        """Safely get payment_status, handling cases where the field doesn't exist in DB yet"""
        try:
            # Check if the field exists on the model instance
            if hasattr(obj, 'payment_status'):
                return obj.payment_status
            return 'pending'  # Default value if field doesn't exist
        except (AttributeError, KeyError):
            return 'pending'

    def get_patient_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return None
    
    def get_doctor_name(self, obj):
        try:
            if obj.doctor:
                if obj.doctor.last_name:
                    return f"Dr. {obj.doctor.last_name}"
                elif obj.doctor.first_name:
                    return f"Dr. {obj.doctor.first_name}"
                else:
                    return "Dr. Unknown"
            return None
        except (AttributeError, TypeError):
            return None

    def get_linked_test_request(self, obj):
        """Get test request linked to this follow-up appointment"""
        # Early return if not a follow-up - check multiple ways to be safe
        try:
            # Check is_followup field
            is_followup = False
            if hasattr(obj, 'is_followup'):
                is_followup = bool(obj.is_followup)
            # Also check original_appointment as fallback
            if not is_followup and hasattr(obj, 'original_appointment'):
                try:
                    is_followup = obj.original_appointment is not None
                except Exception:
                    pass
            
            if not is_followup:
                return None
        except Exception:
            return None
            
        try:
            from .models import TestRequest
            from health.models import MedicalDocument
            
            # Use get() with a try-except to avoid errors if no test request exists
            try:
                test_request = TestRequest.objects.filter(followup_appointment=obj).select_related('doctor', 'patient', 'appointment').first()
                if not test_request:
                    return None
            except Exception:
                return None
                
            # Count test results directly to avoid related manager issues
            try:
                results_count = MedicalDocument.objects.filter(test_request=test_request).count()
            except Exception:
                results_count = 0
            
            # Return minimal data to avoid circular serialization issues
            return {
                'id': test_request.id,
                'test_name': getattr(test_request, 'test_name', ''),
                'test_description': getattr(test_request, 'test_description', None),
                'instructions': getattr(test_request, 'instructions', None),
                'status': getattr(test_request, 'status', 'pending'),
                'has_test_results': results_count > 0,
                'test_results_count': results_count,
            }
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error getting linked test request for appointment {getattr(obj, 'id', 'unknown')}: {e}", exc_info=True)
        return None

    def get_test_results(self, obj):
        """Get test results (documents) for this follow-up appointment's test request"""
        # Return empty list immediately if any error occurs - be very defensive
        try:
            # Check if this is a follow-up appointment - multiple checks
            is_followup = False
            try:
                if hasattr(obj, 'is_followup'):
                    is_followup = bool(obj.is_followup)
            except (AttributeError, TypeError):
                pass
            
            # Fallback check
            if not is_followup:
                try:
                    if hasattr(obj, 'original_appointment_id') and obj.original_appointment_id:
                        is_followup = True
                    elif hasattr(obj, 'original_appointment') and obj.original_appointment:
                        is_followup = True
                except (AttributeError, TypeError):
                    pass
            
            if not is_followup:
                return []
            
            # Only proceed if it's a follow-up
            from .models import TestRequest
            from health.models import MedicalDocument
            
            # Get test request - use try-except for safety
            test_request = None
            try:
                test_request = TestRequest.objects.filter(followup_appointment_id=obj.id).first()
            except Exception:
                try:
                    test_request = TestRequest.objects.filter(followup_appointment=obj).first()
                except Exception:
                    return []
            
            if not test_request:
                return []
            
            # Get documents
            documents = []
            try:
                documents = list(MedicalDocument.objects.filter(test_request_id=test_request.id).order_by('-uploaded_at')[:10])  # Limit to 10
            except Exception:
                return []
                
            # Return minimal data
            results = []
            request = self.context.get('request') if self.context else None
            
            for doc in documents:
                try:
                    file_url = None
                    if hasattr(doc, 'file') and doc.file:
                        try:
                            if request:
                                file_url = request.build_absolute_uri(doc.file.url)
                            else:
                                file_url = doc.file.url
                        except Exception:
                            pass
                    
                    filename = None
                    if hasattr(doc, 'file') and doc.file:
                        try:
                            filename = doc.file.name.split('/')[-1]
                        except Exception:
                            try:
                                filename = str(doc.file)
                            except Exception:
                                filename = None
                    
                    uploaded_at = None
                    if hasattr(doc, 'uploaded_at') and doc.uploaded_at:
                        try:
                            uploaded_at = doc.uploaded_at.isoformat()
                        except Exception:
                            pass
                    
                    results.append({
                        'id': getattr(doc, 'id', None),
                        'file_url': file_url,
                        'filename': filename,
                        'description': getattr(doc, 'description', None),
                        'document_type': getattr(doc, 'document_type', None),
                        'uploaded_at': uploaded_at,
                    })
                except Exception:
                    # Skip this document if there's an error
                    continue
                    
            return results
        except Exception as e:
            # Log but don't fail - return empty list to allow serialization to continue
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error in get_test_results for appointment {getattr(obj, 'id', 'unknown')}: {e}", exc_info=True)
            return []

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
    instructions = serializers.CharField(required=False, allow_blank=True, default='')
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
    patient_vitals_summary = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'date', 'start_time', 'end_time', 'reason', 'status',
            'user', 'patient_email', 'patient_name',
            'has_existing_prescription', 'patient_vitals_summary'
        ]

    def get_patient_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
        return "N/A"

    def get_has_existing_prescription(self, obj):
        return Prescription.objects.filter(appointment=obj).exists()
    
    def get_patient_vitals_summary(self, obj):
        """Get summary of patient's recent vitals (last 7 days)"""
        from health.vitals_utils import get_vitals_summary
        return get_vitals_summary(obj.user.id, days=7)

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


class TestRequestSerializer(serializers.ModelSerializer):
    """Serializer for TestRequest model"""
    patient_name = serializers.SerializerMethodField(read_only=True)
    patient_email = serializers.EmailField(source='patient.email', read_only=True)
    doctor_name = serializers.SerializerMethodField(read_only=True)
    appointment_date = serializers.DateField(source='appointment.date', read_only=True)
    has_test_results = serializers.SerializerMethodField(read_only=True)
    test_results_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        from .models import TestRequest
        model = TestRequest
        fields = [
            'id', 'appointment', 'appointment_date', 'doctor', 'doctor_name',
            'patient', 'patient_name', 'patient_email', 'test_name',
            'test_description', 'instructions', 'status', 'requested_at',
            'completed_at', 'notes', 'followup_appointment',
            'has_test_results', 'test_results_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'doctor', 'patient', 'requested_at', 'completed_at',
            'patient_name', 'patient_email', 'doctor_name', 'appointment_date',
            'has_test_results', 'test_results_count',
            'created_at', 'updated_at'
        ]
    
    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}".strip() or obj.patient.username
        return "N/A"
    
    def get_doctor_name(self, obj):
        if obj.doctor:
            return obj.doctor.full_name
        return "N/A"
    
    def get_has_test_results(self, obj):
        """Check if test results have been uploaded"""
        return obj.test_results.exists() if hasattr(obj, 'test_results') else False
    
    def get_test_results_count(self, obj):
        """Get count of uploaded test results"""
        return obj.test_results.count() if hasattr(obj, 'test_results') else 0


class TestRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating test requests (doctor only)"""
    appointment_id = serializers.IntegerField(
        write_only=True,
        help_text="ID of the appointment this test request is for"
    )
    
    class Meta:
        from .models import TestRequest
        model = TestRequest
        fields = [
            'appointment_id', 'test_name', 'test_description',
            'instructions', 'notes'
        ]
    
    def validate_appointment_id(self, value):
        """Validate that the appointment belongs to the doctor"""
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'doctor_profile'):
            raise serializers.ValidationError("Only doctors can create test requests.")
        
        from .models import Appointment
        try:
            appointment = Appointment.objects.get(id=value, doctor=request.user.doctor_profile)
        except Appointment.DoesNotExist:
            raise serializers.ValidationError("Appointment not found or not assigned to you.")
        
        return value
    
    def create(self, validated_data):
        appointment_id = validated_data.pop('appointment_id')
        from .models import Appointment, TestRequest
        appointment = Appointment.objects.get(id=appointment_id)
        request = self.context.get('request')
        
        test_request = TestRequest.objects.create(
            appointment=appointment,
            doctor=request.user.doctor_profile,
            patient=appointment.user,
            **validated_data
        )
        
        return test_request