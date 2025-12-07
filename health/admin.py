from django.contrib import admin
from .models import VitalSign, FoodLog, ExerciseLog, SleepLog, HealthGoal, WaterIntakeLog, HealthInsight, MedicalDocument

@admin.register(VitalSign)
class VitalSignAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_recorded', 'heart_rate', 'systolic_pressure', 'diastolic_pressure', 'temperature', 'blood_glucose', 'weight', 'source', 'created_at')
    search_fields = ('user__email', 'notes')
    list_filter = ('source', 'date_recorded', 'created_at')
    ordering = ('-date_recorded',)
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'date_recorded', 'source', 'notes')
        }),
        ('Vital Signs', {
            'fields': (
                ('heart_rate', 'respiratory_rate'),
                ('systolic_pressure', 'diastolic_pressure'),
                ('temperature', 'oxygen_saturation'),
                ('blood_glucose', 'weight'),
            )
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(FoodLog)
class FoodLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'food_item', 'meal_type', 'datetime', 'calories', 'carbohydrates', 'proteins', 'fats', 'created_at')
    search_fields = ('user__email', 'food_item', 'notes')
    list_filter = ('meal_type', 'datetime', 'created_at')
    ordering = ('-datetime',)
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Food Information', {
            'fields': ('user', 'food_item', 'meal_type', 'datetime', 'notes')
        }),
        ('Nutritional Information', {
            'fields': ('calories', 'carbohydrates', 'proteins', 'fats')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(ExerciseLog)
class ExerciseLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'datetime', 'duration', 'intensity', 'calories_burned', 'distance', 'heart_rate_avg', 'created_at')
    search_fields = ('user__email', 'activity_type', 'notes')
    list_filter = ('intensity', 'datetime', 'created_at')
    ordering = ('-datetime',)
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Exercise Information', {
            'fields': ('user', 'activity_type', 'datetime', 'duration', 'intensity', 'notes')
        }),
        ('Metrics', {
            'fields': ('calories_burned', 'distance', 'heart_rate_avg')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(SleepLog)
class SleepLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'sleep_time', 'wake_time', 'duration', 'quality', 'interruptions', 'source', 'created_at')
    search_fields = ('user__email', 'notes')
    list_filter = ('quality', 'source', 'sleep_time', 'created_at')
    ordering = ('-sleep_time',)
    readonly_fields = ('created_at', 'duration')
    fieldsets = (
        ('Sleep Information', {
            'fields': ('user', 'sleep_time', 'wake_time', 'quality', 'interruptions', 'source', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(WaterIntakeLog)
class WaterIntakeLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'amount_ml', 'daily_goal_ml', 'logged_at')
    search_fields = ('user__email',)
    list_filter = ('date', 'logged_at')
    ordering = ('-date', '-logged_at')
    readonly_fields = ('logged_at',)

@admin.register(HealthGoal)
class HealthGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'goal_type', 'custom_type', 'target_value', 'current_value', 'unit', 'status', 'progress', 'start_date', 'target_date')
    search_fields = ('user__email', 'custom_type', 'notes')
    list_filter = ('goal_type', 'status', 'frequency', 'reminders_enabled', 'start_date', 'target_date')
    ordering = ('-start_date',)
    readonly_fields = ('created_at', 'updated_at', 'progress')
    fieldsets = (
        ('Goal Information', {
            'fields': ('user', 'goal_type', 'custom_type', 'status', 'frequency', 'reminders_enabled')
        }),
        ('Targets', {
            'fields': ('target_value', 'current_value', 'unit', 'start_date', 'target_date', 'progress')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(HealthInsight)
class HealthInsightAdmin(admin.ModelAdmin):
    list_display = ('user', 'insight_type', 'title', 'priority', 'is_read', 'generated_at', 'expires_at')
    search_fields = ('user__email', 'title', 'description', 'related_metric')
    list_filter = ('insight_type', 'priority', 'is_read', 'generated_at')
    ordering = ('-generated_at',)
    readonly_fields = ('generated_at',)
    fieldsets = (
        ('Insight Information', {
            'fields': ('user', 'insight_type', 'title', 'description', 'related_metric', 'priority', 'is_read')
        }),
        ('Timing', {
            'fields': ('generated_at', 'expires_at')
        }),
    )

@admin.register(MedicalDocument)
class MedicalDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'uploaded_by', 'description', 'document_type', 'file_size', 'is_shared', 'uploaded_at')
    search_fields = ('user__email', 'uploaded_by__email', 'description', 'document_type')
    list_filter = ('document_type', 'is_shared', 'uploaded_at')
    ordering = ('-uploaded_at',)
    readonly_fields = ('uploaded_at', 'file_size', 'mime_type')
    fieldsets = (
        ('Document Information', {
            'fields': ('user', 'uploaded_by', 'appointment', 'description', 'document_type', 'is_shared')
        }),
        ('File Details', {
            'fields': ('file', 'file_size', 'mime_type', 'thumbnail')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )