# pharmacy/tasks.py
import logging
from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from datetime import date, timedelta
from .models import MedicationReminder, Medication
from vitanips.core.utils import send_app_email
from notifications.utils import create_notification

logger = logging.getLogger(__name__)

@shared_task(name="pharmacy.tasks.send_medication_reminders_task")
def send_medication_reminders_task():
    now = timezone.now()
    today = now.date()
    current_time = now.time()

    potential_reminders = MedicationReminder.objects.filter(
        is_active=True,
        start_date__lte=today,
        time_of_day__hour=current_time.hour,
        time_of_day__minute=current_time.minute
    ).filter(
        Q(end_date__gte=today) | Q(end_date__isnull=True)
    ).select_related('user', 'medication')

    if not potential_reminders.exists():
        logger.info("No potential medication reminders matching current time.")
        return "No potential medication reminders matching current time."

    reminders_due_count = 0
    for reminder in potential_reminders:
        is_due_today = False
        if reminder.frequency == MedicationReminder.FrequencyChoices.DAILY:
            is_due_today = True
        elif reminder.frequency == MedicationReminder.FrequencyChoices.WEEKLY:
            if reminder.start_date.weekday() == today.weekday():
                is_due_today = True
        elif reminder.frequency == MedicationReminder.FrequencyChoices.MONTHLY:
            # This is a bit tricky if start_date.day > days_in_current_month
            # A safer approach for monthly might be "every Nth day of the month"
            # or "same day of month as start_date, if valid for current month"
            if reminder.start_date.day == today.day:
                is_due_today = True
            # Add more robust monthly logic if needed, e.g., handle last day of month
        elif reminder.frequency == MedicationReminder.FrequencyChoices.CUSTOM:
            # Example for "every X days" if custom_frequency stores an integer X
            if reminder.custom_frequency and reminder.custom_frequency.isdigit():
                days_interval = int(reminder.custom_frequency)
                if days_interval > 0:
                    delta_days = (today - reminder.start_date).days
                    if delta_days >= 0 and delta_days % days_interval == 0:
                        is_due_today = True
            # else: Implement other custom logic based on custom_frequency format

        if is_due_today:
            reminders_due_count += 1
            user = reminder.user
            if user and user.email and user.notify_refill_reminder_email:
                logger.info(f"Sending medication reminder for '{reminder.medication.name}' to {user.email}")
                context = {
                    'user': user,
                    'reminder': reminder,
                    'medication': reminder.medication,
                    'subject': f"Medication Reminder: Time for your {reminder.medication.name}"
                }
                send_app_email(
                    to_email=user.email,
                    subject=context['subject'],
                    template_name='emails/medication_reminder.html',
                    context=context
                )
    logger.info(f"Processed medication reminders. {reminders_due_count} were due and processed.")
    return f"Checked {potential_reminders.count()} potential medication reminders. Sent for {reminders_due_count}."