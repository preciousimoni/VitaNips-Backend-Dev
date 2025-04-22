from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import MedicalHistory, Vaccination

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'phone_number',
            'date_of_birth', 'profile_picture', 'blood_group', 'allergies',
            'chronic_conditions', 'weight', 'height', 'emergency_contact_name',
            'emergency_contact_relationship', 'emergency_contact_phone',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
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
            'first_name', 'last_name', 'phone_number', 'date_of_birth',
            'profile_picture', 'blood_group', 'allergies', 'chronic_conditions',
            'weight', 'height', 'emergency_contact_name',
            'emergency_contact_relationship', 'emergency_contact_phone'
        ]
        extra_kwargs = {
            'profile_picture': {'required': False},
            'allergies': {'required': False},
            'chronic_conditions': {'required': False}
        }

class MedicalHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalHistory
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

class VaccinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vaccination
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']