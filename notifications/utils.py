# notifications/utils.py
from typing import Optional
from django.contrib.auth import get_user_model
from .models import Notification

User = get_user_model()

def create_notification(
    recipient: User,
    verb: str,
    *,
    actor: Optional[User] = None,
    level: str = 'info',
    target_url: Optional[str] = None,
) -> Notification:
    """
    Helper function to create an in-app notification.
    """
    try:
        notif = Notification.objects.create(
            recipient=recipient,
            verb=verb,
            actor=actor,
            level=level,
            target_url=target_url,
            unread=True
        )
        print(f"Notification {notif.id} created for {recipient.username}: {verb}")
        return notif
    except Exception as e:
        print(f"ERROR creating notification for {recipient.username}: {e}")
        return None