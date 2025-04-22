from django.contrib import admin
from .models import Specialty, Doctor, DoctorReview, DoctorAvailability, Appointment, Prescription, PrescriptionItem

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'gender', 'years_of_experience', 'is_verified', 'created_at')
    search_fields = ('first_name', 'last_name', 'bio')
    list_filter = ('is_verified', 'is_available_for_virtual')
    ordering = ('-created_at',)

@admin.register(DoctorReview)
class DoctorReviewAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'user', 'rating', 'created_at')
    search_fields = ('doctor__first_name', 'doctor__last_name', 'user__email')
    list_filter = ('rating', 'created_at')
    ordering = ('-created_at',)

@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'day_of_week', 'start_time', 'end_time', 'is_available')
    list_filter = ('day_of_week', 'is_available')
    search_fields = ('doctor__first_name', 'doctor__last_name')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'doctor', 'date', 'start_time', 'status', 'appointment_type')
    search_fields = ('user__email', 'doctor__first_name', 'doctor__last_name')
    list_filter = ('status', 'appointment_type', 'date')
    ordering = ('-date',)

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'doctor', 'date_prescribed', 'created_at')
    search_fields = ('user__email', 'doctor__first_name', 'doctor__last_name')
    list_filter = ('date_prescribed',)
    ordering = ('-created_at',)

@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(admin.ModelAdmin):
    list_display = ('prescription', 'medication_name', 'dosage', 'frequency')
    search_fields = ('medication_name',)