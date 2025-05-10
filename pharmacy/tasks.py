# pharmacy/tasks.py
import logging
from datetime import date
from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from .models import MedicationReminder
from vitanips.core.utils import send_app_email
from notifications.utils import create_notification

logger = logging.getLogger(__name__)

def is_reminder_due(reminder: MedicationReminder, today: date) -> bool:
    start_date = reminder.start_date
    if reminder.frequency == MedicationReminder.FrequencyChoices.DAILY:
        return True
    elif reminder.frequency == MedicationReminder.FrequencyChoices.WEEKLY:
        return start_date.weekday() == today.weekday()
    elif reminder.frequency == MedicationReminder.FrequencyChoices.MONTHLY:
        try:
            return start_date.day == today.day
        except ValueError:
            return False
    elif reminder.frequency == MedicationReminder.FrequencyChoices.CUSTOM:
        try:
            days_interval = int(reminder.custom_frequency)
            if days_interval > 0:
                delta_days = (today - start_date).days
                return delta_days >= 0 and delta_days % days_interval == 0
        except (ValueError, TypeError):
            logger.warning(f"Invalid custom_frequency for reminder {reminder.id}")
    return False

@shared_task(name="pharmacy.tasks.send_medication_reminders_task", bind=True)
def send_medication_reminders_task(self):
    """Send medication reminders for due schedules."""
    try:
        now = timezone.now()
        today = now.date()
        current_time = now.time()

        potential_reminders = MedicationReminder.objects.filter(
            is_active=True,
            start_date__lte=today,
            time_of_day__hour=current_time.hour,
            time_of_day__minute=current_time.minute,
        ).filter(
            Q(end_date__gte=today) | Q(end_date__isnull=True)
        ).select_related('user', 'medication').prefetch_related('user__profile')

        if not potential_reminders.exists():
            logger.info("No medication reminders for current time slot")
            return "No reminders to process"

        reminders_due_count = 0
        for reminder in potential_reminders:
            if not is_reminder_due(reminder, today):
                continue

            user = reminder.user
            if not (user and user.email and user.notify_refill_reminder_email):
                logger.debug(f"Skipping reminder {reminder.id}: Invalid user or notification settings")
                continue

            reminders_due_count += 1
            try:
                context = {
                    'user': user,
                    'reminder': reminder,
                    'medication': reminder.medication,
                    'subject': f"Medication Reminder: {reminder.medication.name}"
                }
                send_app_email(
                    to_email=user.email,
                    subject=context['subject'],
                    template_name='emails/medication_reminder.html',
                    context=context
                )
                create_notification(
                    user=user,
                    notification_type='MEDICATION_REMINDER',
                    message=f"Time to take {reminder.medication.name}",
                    related_object=reminder
                )
                logger.info(f"Sent reminder for '{reminder.medication.name}' to {user.email}")
            except Exception as e:
                logger.error(f"Failed to send reminder {reminder.id} to {user.email}: {str(e)}")

        result = f"Processed {potential_reminders.count()} reminders, sent {reminders_due_count}"
        logger.info(result)
        return result

    except Exception as e:
        logger.error(f"Medication reminder task failed: {str(e)}", exc_info=True)
        raise self.retry(countdown=300)