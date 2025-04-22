from django.contrib import admin
from .models import VitalSign, SymptomLog, FoodLog, ExerciseLog, SleepLog, HealthGoal

@admin.register(VitalSign)
class VitalSignAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_recorded', 'heart_rate', 'blood_glucose', 'weight')
    search_fields = ('user__email',)
    list_filter = ('date_recorded',)
    ordering = ('-date_recorded',)

@admin.register(SymptomLog)
class SymptomLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'symptom', 'date_experienced', 'severity')
    search_fields = ('user__email', 'symptom')
    list_filter = ('severity', 'date_experienced')
    ordering = ('-date_experienced',)

@admin.register(FoodLog)
class FoodLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'food_item', 'meal_type', 'datetime', 'calories')
    search_fields = ('user__email', 'food_item')
    list_filter = ('meal_type', 'datetime')
    ordering = ('-datetime',)

@admin.register(ExerciseLog)
class ExerciseLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'datetime', 'duration', 'calories_burned')
    search_fields = ('user__email', 'activity_type')
    list_filter = ('datetime',)
    ordering = ('-datetime',)

@admin.register(SleepLog)
class SleepLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'sleep_time', 'wake_time', 'quality', 'duration')
    search_fields = ('user__email',)
    list_filter = ('quality', 'sleep_time')
    ordering = ('-sleep_time',)

@admin.register(HealthGoal)
class HealthGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'goal_type', 'target_value', 'unit', 'status')
    search_fields = ('user__email',)
    list_filter = ('goal_type', 'status')
    ordering = ('-start_date',)