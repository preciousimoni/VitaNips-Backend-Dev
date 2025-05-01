from django.contrib import admin
from .models import EmergencyService, EmergencyContact, EmergencyAlert, EmergencyAlertContact

@admin.register(EmergencyService)
class EmergencyServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_type', 'phone_number', 'is_24_hours', 'created_at')
    search_fields = ('name', 'address')
    list_filter = ('service_type', 'is_24_hours')
    ordering = ('-created_at',)

@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'relationship', 'phone_number', 'is_primary')
    search_fields = ('user__email', 'name')
    list_filter = ('relationship', 'is_primary')
    ordering = ('-created_at',)

@admin.register(EmergencyAlert)
class EmergencyAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'initiated_at', 'status')
    search_fields = ('user__email',)
    list_filter = ('status', 'initiated_at')
    ordering = ('-initiated_at',)

@admin.register(EmergencyAlertContact)
class EmergencyAlertContactAdmin(admin.ModelAdmin):
    list_display = ('alert', 'contact', 'sent_at', 'delivery_status')
    search_fields = ('contact__name',)
    list_filter = ('delivery_status', 'sent_at')
    ordering = ('-sent_at',)