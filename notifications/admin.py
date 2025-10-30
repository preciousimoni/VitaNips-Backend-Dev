from django.contrib import admin
from .models import (
    NotificationTemplate, Notification, NotificationDelivery,
    NotificationPreference, NotificationSchedule
)


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_active', 'created_at']
    list_filter = ['template_type', 'is_active']
    search_fields = ['name', 'template_type']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'title', 'category', 'level', 'unread', 'timestamp']
    list_filter = ['category', 'level', 'unread', 'timestamp']
    search_fields = ['recipient__email', 'title', 'verb']
    readonly_fields = ['timestamp', 'sent_at', 'read_at', 'dismissed_at']
    date_hierarchy = 'timestamp'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipient', 'actor', 'template')


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = ['notification', 'channel', 'status', 'sent_at', 'delivered_at']
    list_filter = ['channel', 'status', 'created_at']
    search_fields = ['notification__title', 'external_id']
    readonly_fields = ['created_at', 'updated_at', 'sent_at', 'delivered_at', 'failed_at']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('notification', 'notification__recipient')


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_enabled', 'sms_enabled', 'push_enabled', 'updated_at']
    list_filter = ['email_enabled', 'sms_enabled', 'push_enabled', 'quiet_hours_enabled']
    search_fields = ['user__email']
    readonly_fields = ['updated_at']


@admin.register(NotificationSchedule)
class NotificationScheduleAdmin(admin.ModelAdmin):
    list_display = ['user', 'template', 'frequency', 'is_active', 'last_sent_at', 'total_sent']
    list_filter = ['frequency', 'is_active', 'created_at']
    search_fields = ['user__email', 'template__name']
    readonly_fields = ['created_at', 'updated_at', 'last_sent_at', 'total_sent']
    date_hierarchy = 'created_at'
