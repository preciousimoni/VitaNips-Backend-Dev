from django.contrib import admin
from .models import EmergencyService, EmergencyContact, EmergencyAlert, EmergencyAlertContact

@admin.register(EmergencyService)
class EmergencyServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_type', 'phone_number', 'alternative_phone', 'is_24_hours', 'has_emergency_room', 'provides_ambulance', 'created_at')
    search_fields = ('name', 'address', 'phone_number', 'email', 'website', 'notes')
    list_filter = ('service_type', 'is_24_hours', 'has_emergency_room', 'provides_ambulance', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'service_type', 'address')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'alternative_phone', 'email', 'website')
        }),
        ('Services & Hours', {
            'fields': ('is_24_hours', 'operating_hours', 'has_emergency_room', 'provides_ambulance')
        }),
        ('Location', {
            'fields': ('location',),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'relationship', 'phone_number', 'alternative_phone', 'email', 'is_primary', 'created_at')
    search_fields = ('user__email', 'name', 'phone_number', 'email', 'address', 'notes')
    list_filter = ('relationship', 'is_primary', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Contact Information', {
            'fields': ('user', 'name', 'relationship', 'is_primary')
        }),
        ('Contact Details', {
            'fields': ('phone_number', 'alternative_phone', 'email', 'address')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(EmergencyAlert)
class EmergencyAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'initiated_at', 'status', 'resolved_at')
    search_fields = ('user__email', 'message', 'resolution_notes')
    list_filter = ('status', 'initiated_at', 'resolved_at')
    ordering = ('-initiated_at',)
    readonly_fields = ('initiated_at',)
    fieldsets = (
        ('Alert Information', {
            'fields': ('user', 'status', 'initiated_at', 'resolved_at')
        }),
        ('Location & Message', {
            'fields': ('location', 'message')
        }),
        ('Resolution', {
            'fields': ('resolution_notes',)
        }),
    )

@admin.register(EmergencyAlertContact)
class EmergencyAlertContactAdmin(admin.ModelAdmin):
    list_display = ('alert', 'contact', 'sent_at', 'delivery_status', 'response_received', 'response_time')
    search_fields = ('contact__name', 'alert__user__email', 'response_message')
    list_filter = ('delivery_status', 'response_received', 'sent_at', 'response_time')
    ordering = ('-sent_at',)
    readonly_fields = ('sent_at',)
    fieldsets = (
        ('Alert & Contact', {
            'fields': ('alert', 'contact')
        }),
        ('Delivery Status', {
            'fields': ('sent_at', 'delivery_status')
        }),
        ('Response', {
            'fields': ('response_received', 'response_time', 'response_message')
        }),
    )