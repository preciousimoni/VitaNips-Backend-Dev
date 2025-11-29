from rest_framework import serializers
from .models import VitalSign, FoodLog, ExerciseLog, SleepLog, HealthGoal, MedicalDocument, WaterIntakeLog, HealthInsight
from users.serializers import UserSerializer

class VitalSignSerializer(serializers.ModelSerializer):
    class Meta:
        model = VitalSign
        fields = [
            'id', 'user', 'date_recorded', 'heart_rate', 'systolic_pressure',
            'diastolic_pressure', 'respiratory_rate', 'temperature', 'oxygen_saturation',
            'blood_glucose', 'weight', 'notes', 'source', 'created_at'
        ]
        read_only_fields = ['user', 'created_at']

class FoodLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodLog
        fields = [
            'id', 'user', 'food_item', 'meal_type', 'datetime', 'calories',
            'carbohydrates', 'proteins', 'fats', 'notes', 'created_at'
        ]
        read_only_fields = ['user', 'created_at']

class ExerciseLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseLog
        fields = [
            'id', 'user', 'activity_type', 'datetime', 'duration',
            'calories_burned', 'distance', 'intensity', 'heart_rate_avg', 'notes', 'created_at'
        ]
        read_only_fields = ['user', 'created_at']

class SleepLogSerializer(serializers.ModelSerializer):
    duration = serializers.ReadOnlyField()

    class Meta:
        model = SleepLog
        fields = [
            'id', 'user', 'sleep_time', 'wake_time', 'quality',
            'interruptions', 'notes', 'source', 'duration', 'created_at'
        ]
        read_only_fields = ['user', 'created_at', 'duration']

class WaterIntakeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterIntakeLog
        fields = [
            'id', 'user', 'date', 'amount_ml', 'logged_at', 'daily_goal_ml'
        ]
        read_only_fields = ['user', 'logged_at']

class HealthGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthGoal
        fields = [
            'id', 'user', 'goal_type', 'custom_type', 'target_value', 'current_value', 'unit',
            'start_date', 'target_date', 'status', 'frequency', 'reminders_enabled', 'progress', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

class HealthInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthInsight
        fields = [
            'id', 'user', 'insight_type', 'title', 'description', 
            'related_metric', 'is_read', 'priority', 'generated_at', 'expires_at'
        ]
        read_only_fields = ['user', 'generated_at']

class MedicalDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    filename = serializers.SerializerMethodField()

    class Meta:
        model = MedicalDocument
        fields = [
            'id', 'user', 'uploaded_by', 'appointment', 'file', 'file_url',
            'filename', 'description', 'document_type', 'uploaded_at',
        ]
        read_only_fields = [
            'user',
            'uploaded_by',
            'uploaded_at',
            'file_url',
            'filename',
        ]

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        elif obj.file:
             try:
                 return obj.file.url
             except Exception:
                 return None
        return None

    def get_filename(self, obj):
        """Return the base filename."""
        if obj.file:
            try:
                return obj.file.name.split('/')[-1]
            except Exception:
                return str(obj.file)
        return None
