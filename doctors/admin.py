from django.contrib import admin
from .models import Specialty, Doctor, DoctorReview, DoctorAvailability, Appointment, Prescription, PrescriptionItem, VirtualSession

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'gender', 'years_of_experience', 'consultation_fee', 'is_verified', 'application_status', 'is_available_for_virtual', 'created_at')
    search_fields = ('first_name', 'last_name', 'bio', 'license_number', 'hospital_name', 'user__email')
    list_filter = ('is_verified', 'is_available_for_virtual', 'application_status', 'gender', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'submitted_at', 'reviewed_at')
    filter_horizontal = ('specialties',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'first_name', 'last_name', 'gender', 'profile_picture', 'specialties')
        }),
        ('Professional Details', {
            'fields': ('years_of_experience', 'education', 'bio', 'languages_spoken', 'consultation_fee', 'is_available_for_virtual')
        }),
        ('Verification Status', {
            'fields': ('is_verified', 'application_status')
        }),
        ('License Information', {
            'fields': ('license_number', 'license_issuing_authority', 'license_expiry_date'),
            'classes': ('collapse',)
        }),
        ('Hospital/Clinic Information', {
            'fields': ('hospital_name', 'hospital_address', 'hospital_phone', 'hospital_email', 'hospital_contact_person'),
            'classes': ('collapse',)
        }),
        ('Application Review', {
            'fields': ('submitted_at', 'reviewed_at', 'reviewed_by', 'review_notes', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(DoctorReview)
class DoctorReviewAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'user', 'rating', 'created_at', 'updated_at')
    search_fields = ('doctor__first_name', 'doctor__last_name', 'user__email', 'comment')
    list_filter = ('rating', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Review Details', {
            'fields': ('doctor', 'user', 'rating', 'comment')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'day_of_week', 'start_time', 'end_time', 'is_available')
    list_filter = ('day_of_week', 'is_available')
    search_fields = ('doctor__first_name', 'doctor__last_name')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'doctor', 'date', 'start_time', 'end_time', 'status', 'appointment_type', 'payment_status', 'created_at')
    search_fields = ('user__email', 'doctor__first_name', 'doctor__last_name', 'reason', 'payment_reference')
    list_filter = ('status', 'appointment_type', 'payment_status', 'followup_required', 'insurance_claim_generated', 'date', 'created_at')
    ordering = ('-date', '-start_time')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Appointment Details', {
            'fields': ('user', 'doctor', 'date', 'start_time', 'end_time', 'appointment_type', 'status', 'reason', 'notes', 'followup_required')
        }),
        ('Insurance Information', {
            'fields': ('user_insurance', 'consultation_fee', 'insurance_covered_amount', 'patient_copay', 'insurance_claim_generated'),
            'classes': ('collapse',)
        }),
        ('Payment Information', {
            'fields': ('payment_reference', 'payment_status'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'doctor', 'appointment', 'date_prescribed', 'diagnosis', 'created_at')
    search_fields = ('user__email', 'doctor__first_name', 'doctor__last_name', 'diagnosis', 'notes')
    list_filter = ('date_prescribed', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Prescription Details', {
            'fields': ('appointment', 'user', 'doctor', 'date_prescribed', 'diagnosis', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(admin.ModelAdmin):
    list_display = ('prescription', 'medication', 'medication_name', 'dosage', 'frequency', 'duration')
    search_fields = ('medication_name', 'medication__name', 'dosage', 'frequency')
    list_filter = ('prescription__date_prescribed',)
    fieldsets = (
        ('Item Details', {
            'fields': ('prescription', 'medication', 'medication_name', 'dosage', 'frequency', 'duration', 'instructions')
        }),
    )

@admin.register(VirtualSession)
class VirtualSessionAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'room_name', 'status', 'started_at', 'ended_at', 'duration_minutes', 'created_at')
    search_fields = ('room_name', 'room_sid', 'appointment__user__email', 'appointment__doctor__first_name')
    list_filter = ('status', 'started_at', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'room_name')
    fieldsets = (
        ('Session Details', {
            'fields': ('appointment', 'room_name', 'room_sid', 'status')
        }),
        ('Timing', {
            'fields': ('started_at', 'ended_at', 'duration_minutes')
        }),
        ('Recording', {
            'fields': ('recording_url', 'notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )