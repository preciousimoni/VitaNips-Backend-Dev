# notifications/serializers.py
from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source='actor.username', read_only=True, default=None)

    class Meta:
        model = Notification
        fields = [
            'id',
            'actor_username',
            'level',
            'unread',
            'timestamp',
            'target_url',
        ]
        read_only_fields = fields