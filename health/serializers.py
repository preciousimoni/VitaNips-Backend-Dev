from rest_framework import serializers
from .models import VitalSign, SymptomLog, FoodLog, ExerciseLog, SleepLog, HealthGoal

class VitalSignSerializer(serializers.ModelSerializer):
    class Meta:
        model = VitalSign
        fields = [
            'id', 'user', 'date_recorded', 'heart_rate', 'systolic_pressure',
            'diastolic_pressure', 'respiratory_rate', 'temperature', 'oxygen_saturation',
            'blood_glucose', 'weight', 'notes', 'created_at'
        ]
        read_only_fields = ['user', 'created_at']

class SymptomLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SymptomLog
        fields = [
            'id', 'user', 'symptom', 'date_experienced', 'severity',
            'duration', 'notes', 'created_at'
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
            'calories_burned', 'distance', 'notes', 'created_at'
        ]
        read_only_fields = ['user', 'created_at']

class SleepLogSerializer(serializers.ModelSerializer):
    duration = serializers.ReadOnlyField()

    class Meta:
        model = SleepLog
        fields = [
            'id', 'user', 'sleep_time', 'wake_time', 'quality',
            'interruptions', 'notes', 'duration', 'created_at'
        ]
        read_only_fields = ['user', 'created_at', 'duration']

class HealthGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthGoal
        fields = [
            'id', 'user', 'goal_type', 'custom_type', 'target_value', 'unit',
            'start_date', 'target_date', 'status', 'progress', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']