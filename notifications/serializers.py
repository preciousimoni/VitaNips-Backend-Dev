# notifications/serializers.py
from rest_framework import serializers
from .models import Notification, NotificationPreference, NotificationDelivery


class NotificationDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationDelivery
        fields = ['id', 'channel', 'status', 'sent_at', 'delivered_at', 'error_message']


class NotificationSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    deliveries = NotificationDeliverySerializer(many=True, read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'verb', 'level', 'category',
            'action_url', 'action_text',
            'actor_name', 'unread', 'read_at',
            'timestamp', 'time_ago', 'deliveries', 'metadata'
        ]
        read_only_fields = fields
    
    def get_actor_name(self, obj):
        if obj.actor:
            return obj.actor.get_full_name() or obj.actor.email
        return None
    
    def get_time_ago(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.timestamp)


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            'email_enabled', 'sms_enabled', 'push_enabled',
            'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end',
            'category_preferences',
            'max_daily_emails', 'max_daily_sms',
            'digest_enabled', 'digest_frequency', 'digest_time',
            'updated_at'
        ]