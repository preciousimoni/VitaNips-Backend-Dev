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
    category: str = 'system',
    title: Optional[str] = None,
    target_url: Optional[str] = None,
    action_url: Optional[str] = None,
    action_text: Optional[str] = None,
) -> Optional[Notification]:
    """
    Helper function to create an in-app notification.
    
    Args:
        recipient: User who will receive the notification
        verb: The action/description of the notification (e.g., "Your order is ready")
        actor: Optional user who triggered the notification
        level: Notification level - 'info', 'success', 'warning', 'error', 'urgent'
        category: Notification category - 'appointment', 'prescription', 'medication', 'order', 'health', 'emergency', 'system'
        title: Optional title for the notification (defaults to verb if not provided)
        target_url: Deprecated - use action_url instead
        action_url: URL to navigate to when notification is clicked
        action_text: Text for the action button (optional)
    """
    try:
        # Validate level
        valid_levels = ['info', 'success', 'warning', 'error', 'urgent']
        if level not in valid_levels:
            level = 'info'
        
        # Validate category
        valid_categories = ['appointment', 'prescription', 'medication', 'order', 'health', 'emergency', 'system']
        if category not in valid_categories:
            category = 'system'
        
        # Use target_url if action_url not provided (backward compatibility)
        if not action_url and target_url:
            action_url = target_url
        
        # Generate title from verb if not provided
        if not title:
            title = verb[:200]  # Truncate to max length
        
        notif = Notification.objects.create(
            recipient=recipient,
            title=title,
            verb=verb,
            actor=actor,
            level=level,
            category=category,
            action_url=action_url,
            action_text=action_text,
            unread=True
        )
        print(f"Notification {notif.id} created for {recipient.username}: {title}")
        return notif
    except Exception as e:
        print(f"ERROR creating notification for {recipient.username}: {e}")
        import traceback
        traceback.print_exc()
        return None