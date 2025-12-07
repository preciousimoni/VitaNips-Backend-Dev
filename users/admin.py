from django.contrib import admin
from .models import User, MedicalHistory, Vaccination

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'phone_number', 'date_of_birth', 'blood_group', 'is_staff', 'is_active', 'created_at')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone_number')
    list_filter = ('is_staff', 'is_active', 'is_pharmacy_staff', 'registered_as_doctor', 'blood_group', 'created_at', 'date_of_birth')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'date_joined', 'last_login')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('username', 'email', 'first_name', 'last_name', 'phone_number', 'date_of_birth', 'address', 'profile_picture')
        }),
        ('Medical Information', {
            'fields': ('blood_group', 'genotype', 'allergies', 'chronic_conditions', 'weight', 'height', 'medical_history_summary')
        }),
        ('Permissions & Status', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'is_pharmacy_staff', 'works_at_pharmacy', 'registered_as_doctor')
        }),
        ('Email Notifications', {
            'fields': (
                'notify_appointment_confirmation_email',
                'notify_appointment_cancellation_email',
                'notify_appointment_reminder_email',
                'notify_prescription_update_email',
                'notify_order_update_email',
                'notify_general_updates_email',
                'notify_refill_reminder_email',
            ),
            'classes': ('collapse',)
        }),
        ('SMS & Push Notifications', {
            'fields': (
                'notify_appointment_reminder_sms',
                'notify_appointment_reminder_push',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
    )

@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'condition', 'diagnosis_date', 'is_active', 'treatment', 'created_at', 'updated_at')
    search_fields = ('user__email', 'condition', 'treatment', 'notes')
    list_filter = ('is_active', 'diagnosis_date', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'condition', 'diagnosis_date', 'is_active')
        }),
        ('Details', {
            'fields': ('treatment', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):
    list_display = ('user', 'vaccine_name', 'date_administered', 'dose_number', 'next_dose_date', 'administered_at', 'created_at')
    search_fields = ('user__email', 'vaccine_name', 'batch_number', 'administered_at')
    list_filter = ('date_administered', 'dose_number', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'vaccine_name', 'date_administered', 'dose_number', 'next_dose_date')
        }),
        ('Administration Details', {
            'fields': ('administered_at', 'batch_number')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )