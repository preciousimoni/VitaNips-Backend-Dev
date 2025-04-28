# notifications/serializers.py
from rest_framework import serializers
from .models import Notification
# Optional: Import a minimal user serializer if needed for 'actor'
# from users.serializers import UserMinimalSerializer

class NotificationSerializer(serializers.ModelSerializer):
    # Example: Use a simple string representation for the actor
    actor_username = serializers.CharField(source='actor.username', read_only=True, default=None)
    # Or use a nested serializer:
    # actor = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'actor_username', # Or 'actor' if using nested serializer
            'verb',
            'level',
            'unread',
            'timestamp',
            'target_url',
        ]
        read_only_fields = fields # Notifications generally read-only via API