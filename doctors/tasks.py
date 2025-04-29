# doctors/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Appointment
from notifications.utils import create_notification
from vitanips.core.utils import send_app_email

@shared_task(name="send_appointment_reminders_task")
def send_appointment_reminders_task():
    now = timezone.now()
    reminder_threshold_24h_start = now + timedelta(hours=24)
    reminder_threshold_24h_end = now + timedelta(hours=25)
    reminder_threshold_1h_start = now + timedelta(hours=1)
    reminder_threshold_1h_end = now + timedelta(hours=2)

    upcoming_appointments = Appointment.objects.filter(
        status__in=['scheduled', 'confirmed'],
        date=reminder_threshold_24h_start.date(),
        start_time__gte=reminder_threshold_24h_start.time(),
        start_time__lt=reminder_threshold_24h_end.time()
    ) | Appointment.objects.filter(
        status__in=['scheduled', 'confirmed'],
        date=reminder_threshold_1h_start.date(),
        start_time__gte=reminder_threshold_1h_start.time(),
        start_time__lt=reminder_threshold_1h_end.time()
    )

    upcoming_appointments = upcoming_appointments.distinct().select_related('user', 'doctor')

    print(f"Found {upcoming_appointments.count()} appointments for reminder checks.")

    for appt in upcoming_appointments:
        user = appt.user
        if not user: continue
        
        verb_text = f"Reminder: Your appointment with Dr. {appt.doctor.last_name} is on {appt.date.strftime('%b %d')} at {appt.start_time.strftime('%I:%M %p')}."
        target_url = f"/appointments/{appt.id}"

        create_notification(
            recipient=user,
            verb=verb_text,
            level='appointment',
            target_url=target_url
        )
        
        if user and user.email and user.notify_appointment_reminder_email:
            print(f"Attempting to send reminder for appointment {appt.id} to {user.email}")
            context = {
                'user': user,
                'appointment': appt,
                'subject': f"Appointment Reminder: {appt.date} at {appt.start_time.strftime('%I:%M %p')}"
            }
            send_app_email(
                to_email=user.email,
                subject=context['subject'],
                template_name='emails/appointment_reminder.html',
                context=context
            )
        # --- TODO: Add logic for SMS/Push notifications here ---
        # if user.phone_number and user.notify_appointment_reminder_sms:
        #    send_sms(user.phone_number, message)
        # if user_has_push_device and user.notify_appointment_reminder_push:
        #    send_push_notification(user_device, message)

    return f"Checked {upcoming_appointments.count()} appointments."