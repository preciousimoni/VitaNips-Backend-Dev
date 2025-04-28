# pharmacy/tasks.py
from celery import shared_task
from django.utils import timezone
from .models import MedicationReminder # Assuming this model exists
from vitanips.core.utils import send_app_email # Adjust import path

@shared_task(name="send_medication_reminders_task")
def send_medication_reminders_task():
    """Sends reminders for medication doses due."""
    now = timezone.now()
    # Query MedicationReminder model based on time_of_day, frequency, start/end dates
    # This logic depends HEAVILY on how MedicationReminder is designed.
    # Example (very basic - needs refinement):
    reminders_due = MedicationReminder.objects.filter(
        is_active=True,
        start_date__lte=now.date(),
        # Add end_date check: Q(end_date__isnull=True) | Q(end_date__gte=now.date())
        time_of_day__hour=now.hour, # Check hour
        time_of_day__minute=now.minute # Check minute (run task frequently)
        # Add frequency logic (daily, weekly, etc.) - Complex!
    ).select_related('user', 'medication')

    print(f"Found {reminders_due.count()} medication reminders due.")

    for reminder in reminders_due:
         user = reminder.user
         # Check user preferences
         if user and user.email and user.notify_refill_reminder_email: # Use correct pref field
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
                 template_name='emails/medication_reminder.html', # Create this template
                 context=context
             )
         # --- TODO: Add logic for SMS/Push notifications here ---

    return f"Checked {reminders_due.count()} medication reminders."