# doctors/serializers.py
from rest_framework import serializers
from .models import Specialty, Doctor, DoctorReview, DoctorAvailability, Appointment, Prescription, PrescriptionItem

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

class PrescriptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        fields = ['id', 'prescription', 'medication_name', 'dosage', 'frequency', 'duration', 'instructions']

class PrescriptionSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True, read_only=True)

    class Meta:
        model = Prescription
        fields = ['id', 'appointment', 'user', 'doctor', 'date_prescribed', 'diagnosis', 'notes', 'items', 'created_at', 'updated_at']
        read_only_fields = ['user', 'doctor', 'date_prescribed', 'created_at', 'updated_at']