from django.contrib import admin
from .models import User, MedicalHistory, Vaccination

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'date_of_birth', 'created_at')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('created_at', 'blood_group')
    ordering = ('-created_at',)

@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'condition', 'diagnosis_date', 'is_active', 'created_at')
    search_fields = ('user__email', 'condition')
    list_filter = ('is_active', 'diagnosis_date')
    ordering = ('-created_at',)

@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):
    list_display = ('user', 'vaccine_name', 'date_administered', 'dose_number', 'created_at')
    search_fields = ('user__email', 'vaccine_name')
    list_filter = ('date_administered',)
    ordering = ('-created_at',)