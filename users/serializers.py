# users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User, MedicalHistory, Vaccination
from insurance.serializers import UserInsuranceSerializer
from emergency.serializers import EmergencyContactSerializer

User = get_user_model()

class VaccinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vaccination
        fields = ['id', 'vaccine_name', 'date_administered', 'user', 'notes']
        read_only_fields = ['id', 'user']
class UserSerializer(serializers.ModelSerializer):
    insurance_details = UserInsuranceSerializer(many=True, read_only=True, source='userinsurance_set')
    emergency_contacts = EmergencyContactSerializer(many=True, read_only=True, source='emergencycontact_set')
    vaccinations = VaccinationSerializer(many=True, read_only=True, source='vaccination_set')
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'address', 'date_of_birth', 'profile_picture',
            'medical_history_summary', 'emergency_contact_name', 'emergency_contact_relationship',
            'emergency_contact_phone', 'blood_group', 'genotype', 'allergies',
            'chronic_conditions', 'is_hmo_member', 'hmo_provider', 'hmo_policy_number',
            'notify_appointment_confirmation_email', 'notify_appointment_cancellation_email',
            'notify_appointment_reminder_email', 'notify_prescription_update_email',
            'notify_order_update_email', 'notify_general_updates_email',
            'notify_refill_reminder_email', 'notify_appointment_reminder_sms',
            'notify_appointment_reminder_push',
            'insurance_details', 'emergency_contacts', 'vaccinations',
        ]
        read_only_fields = ['id', 'username', 'email', 'insurance_details', 'emergency_contacts', 'vaccinations', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }

class UserRegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password2', 'first_name', 'last_name']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords must match."})
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
             'profile_picture', 'medical_history_summary', 'emergency_contact_name',
             'emergency_contact_relationship', 'emergency_contact_phone', 'blood_group', 'genotype', 'allergies',
             'chronic_conditions', 'is_hmo_member', 'hmo_provider', 'hmo_policy_number',
            'notify_appointment_confirmation_email', 'notify_appointment_cancellation_email',
            'notify_appointment_reminder_email', 'notify_prescription_update_email',
            'notify_order_update_email', 'notify_general_updates_email',
            'notify_refill_reminder_email', 'notify_appointment_reminder_sms',
            'notify_appointment_reminder_push',
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