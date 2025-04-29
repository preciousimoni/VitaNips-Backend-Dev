# emergency/serializers.py
from rest_framework import serializers
from .models import EmergencyService, EmergencyContact, EmergencyAlert, EmergencyAlertContact
from django.contrib.gis.geos import Point

class EmergencyServiceSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)

    class Meta:
        model = EmergencyService
        fields = [
            'id', 'name', 'service_type', 'address', 'phone_number', 'alternative_phone',
            'email', 'website', 'latitude', 'longitude', 'is_24_hours', 'operating_hours',
            'has_emergency_room', 'provides_ambulance', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.location:
            representation['latitude'] = instance.location.y
            representation['longitude'] = instance.location.x
        else:
            representation['latitude'] = None
            representation['longitude'] = None
        return representation

    def validate(self, data):
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        if (latitude is not None and longitude is None) or (longitude is not None and latitude is None):
            raise serializers.ValidationError(
                "Both latitude and longitude must be provided together."
            )
        return data

    def create(self, validated_data):
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        if latitude is not None and longitude is not None:
            validated_data['location'] = Point(longitude, latitude, srid=4326)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        if latitude is not None and longitude is not None:
            validated_data['location'] = Point(longitude, latitude, srid=4326)
        elif latitude is None and longitude is None:
            validated_data['location'] = instance.location
        return super().update(instance, validated_data)

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
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)

    class Meta:
        model = EmergencyAlert
        fields = [
            'id', 'user', 'initiated_at', 'latitude', 'longitude', 'message',
            'status', 'resolved_at', 'resolution_notes', 'contacted_persons'
        ]
        read_only_fields = ['user', 'initiated_at', 'contacted_persons']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.location:
            representation['latitude'] = instance.location.y
            representation['longitude'] = instance.location.x
        else:
            representation['latitude'] = None
            representation['longitude'] = None
        return representation

    def validate(self, data):
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        if (latitude is not None and longitude is None) or (longitude is not None and latitude is None):
            raise serializers.ValidationError(
                "Both latitude and longitude must be provided together."
            )
        return data

    def create(self, validated_data):
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        if latitude is not None and longitude is not None:
            validated_data['location'] = Point(longitude, latitude, srid=4326)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        if latitude is not None and longitude is not None:
            validated_data['location'] = Point(longitude, latitude, srid=4326)
        elif latitude is None and longitude is None:
            validated_data['location'] = instance.location
        return super().update(instance, validated_data)