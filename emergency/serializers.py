# emergency/serializers.py
from rest_framework import serializers
from .models import EmergencyService, EmergencyContact, EmergencyAlert, EmergencyAlertContact

class EmergencyServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyService
        fields = [
            'id', 'name', 'service_type', 'address', 'phone_number', 'alternative_phone',
            'email', 'website', 'latitude', 'longitude', 'is_24_hours', 'operating_hours',
            'has_emergency_room', 'provides_ambulance', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = [
            'id', 'user', 'name', 'relationship', 'phone_number', 'alternative_phone',
            'email', 'address', 'is_primary', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

class EmergencyAlertContactSerializer(serializers.ModelSerializer):
    contact = EmergencyContactSerializer(read_only=True)

    class Meta:
        model = EmergencyAlertContact
        fields = [
            'id', 'alert', 'contact', 'sent_at', 'delivery_status',
            'response_received', 'response_time', 'response_message'
        ]
        read_only_fields = ['sent_at']

class EmergencyAlertSerializer(serializers.ModelSerializer):
    contacted_persons = EmergencyAlertContactSerializer(many=True, read_only=True)

    class Meta:
        model = EmergencyAlert
        fields = [
            'id', 'user', 'initiated_at', 'latitude', 'longitude', 'message',
            'status', 'resolved_at', 'resolution_notes', 'contacted_persons'
        ]
        read_only_fields = ['user', 'initiated_at']