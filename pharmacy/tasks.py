# pharmacy/tasks.py
from celery import shared_task
from django.utils import timezone
from .models import MedicationReminder
from vitanips.core.utils import send_app_email

@shared_task(name="send_medication_reminders_task")
def send_medication_reminders_task():
    now = timezone.now()
    reminders_due = MedicationReminder.objects.filter(
        is_active=True,
        start_date__lte=now.date(),
        time_of_day__hour=now.hour, # Check hour
        time_of_day__minute=now.minute
        # Add frequency logic (daily, weekly, etc.) - Complex!
    ).select_related('user', 'medication')

    print(f"Found {reminders_due.count()} medication reminders due.")

    for reminder in reminders_due:
         user = reminder.user
         if user and user.email and user.notify_refill_reminder_email:
             print(f"Attempting to send reminder for medication {reminder.medication.name} to {user.email}")
             context = {
                 'user': user,
                 'reminder': reminder,
                 'medication': reminder.medication,
                 'subject': f"Medication Reminder: Take {reminder.medication.name}"
             }
             send_app_email(
                 to_email=user.email,
                 subject=context['subject'],
                 template_name='emails/medication_reminder.html',
                 context=context
             )
         # --- TODO: Add logic for SMS/Push notifications here ---

    return f"Checked {reminders_due.count()} medication reminders."