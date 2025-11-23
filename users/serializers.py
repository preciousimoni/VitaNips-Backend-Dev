# users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User, MedicalHistory, Vaccination
from insurance.serializers import UserInsuranceSerializer
from emergency.serializers import EmergencyContactSerializer
# from doctors.serializers import DoctorProfileSummarySerializer

User = get_user_model()


class VaccinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vaccination
        fields = ['id', 'vaccine_name', 'date_administered', 'dose_number', 'next_dose_date', 
                 'administered_at', 'batch_number', 'user', 'notes']
        read_only_fields = ['id', 'user']


class UserSerializer(serializers.ModelSerializer):
    insurance_details = UserInsuranceSerializer(
        many=True, read_only=True, source='userinsurance_set')
    emergency_contacts = EmergencyContactSerializer(
        many=True, read_only=True, source='emergencycontact_set')
    vaccinations = VaccinationSerializer(
        many=True, read_only=True, source='vaccination_set')

    is_doctor = serializers.SerializerMethodField()
    doctor_id = serializers.SerializerMethodField()
    # doctor_profile_summary = DoctorProfileSummarySerializer(source='doctor_profile', read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'address', 'date_of_birth', 'profile_picture',
            'medical_history_summary',
            'blood_group', 'genotype', 'allergies',
            'chronic_conditions', 'weight', 'height',
            'notify_appointment_confirmation_email', 'notify_appointment_cancellation_email',
            'notify_appointment_reminder_email', 'notify_prescription_update_email',
            'notify_order_update_email', 'notify_general_updates_email',
            'notify_refill_reminder_email', 'notify_appointment_reminder_sms',
            'notify_appointment_reminder_push', 'is_pharmacy_staff', 'works_at_pharmacy',
            'insurance_details', 'emergency_contacts', 'vaccinations',
            'is_doctor', 'doctor_id', 'is_staff', 'is_superuser', 'is_active', 'created_at', 'updated_at',
            # 'doctor_profile_summary',
        ]
        read_only_fields = ['id', 'username', 'email',
                            'insurance_details', 'emergency_contacts', 'vaccinations',
                            'is_doctor', 'doctor_id', 'created_at',
                            'updated_at', 'is_pharmacy_staff', 'works_at_pharmacy',]

    def get_is_doctor(self, obj):
        # Check if the related 'doctor_profile' exists for the user object 'obj'
        try:
            return obj.doctor_profile is not None
        except AttributeError:  # More specific: User.doctor_profile.RelatedObjectDoesNotExist
            return False

    def get_doctor_id(self, obj):
        try:
            if obj.doctor_profile:
                return obj.doctor_profile.id
            return None
        except AttributeError:
            return None


class UserRegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(
        style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password2', 'first_name', 'last_name',
                  'phone_number', 'date_of_birth', 'blood_group', 'genotype', 'allergies']
        extra_kwargs = {
            'password': {'write_only': True},
            'phone_number': {'required': False},
            'date_of_birth': {'required': False},
            'blood_group': {'required': False},
            'genotype': {'required': False},
            'allergies': {'required': False},
        }

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError(
                {"password": "Passwords must match."})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number', 'address', 'date_of_birth',
            'profile_picture', 'medical_history_summary',
            'blood_group', 'genotype', 'allergies',
            'chronic_conditions',
            'notify_appointment_confirmation_email', 'notify_appointment_cancellation_email',
            'notify_appointment_reminder_email', 'notify_prescription_update_email',
            'notify_order_update_email', 'notify_general_updates_email',
            'notify_refill_reminder_email', 'notify_appointment_reminder_sms',
            'notify_appointment_reminder_push',
            'weight', 'height',
        ]

        extra_kwargs = {
            'profile_picture': {'required': False, 'allow_null': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'phone_number': {'required': False, 'allow_null': True},
            'allergies': {'required': False},
            'chronic_conditions': {'required': False}
        }


class MedicalHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalHistory
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']
