# notifications/utils.py (create this file)
from typing import Optional
from django.contrib.auth import get_user_model
from .models import Notification

User = get_user_model()

def create_notification(
    recipient: User,
    verb: str,
    *, # Force subsequent arguments to be keyword-only
    actor: Optional[User] = None,
    level: str = 'info',
    target_url: Optional[str] = None,
    # Optional: Pass target object if using GenericForeignKey
    # target: Optional[models.Model] = None,
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
            # target=target, # If using GenericForeignKey
            unread=True
        )
        print(f"Notification {notif.id} created for {recipient.username}: {verb}")
        return notif
    except Exception as e:
        # Log this error properly in a real application
        print(f"ERROR creating notification for {recipient.username}: {e}")
        return None

# Example Usage (Call this from your views, signals, or Celery tasks):
# from notifications.utils import create_notification
# from django.contrib.auth.models import User # Or your custom User model
#
# patient = User.objects.get(pk=1)
# doctor_user = User.objects.get(pk=5) # Example doctor user
# appointment_instance = Appointment.objects.get(pk=10) # Example target
#
# create_notification(
#     recipient=patient,
#     verb=f"Your appointment with Dr. {appointment_instance.doctor.last_name} was confirmed.",
#     actor=doctor_user, # Optional: who confirmed it?
#     level='appointment',
#     target_url=f'/appointments/{appointment_instance.id}/' # Example URL
#     # target=appointment_instance # If using GenericForeignKey
# )