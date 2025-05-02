# doctors/tasks.py
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model

# Import models and utils
from .models import Appointment
from notifications.utils import create_notification
from vitanips.core.utils import send_app_email

# Import for Push Notifications
from push_notifications.models import GCMDevice as FCMDevice, APNSDevice

# Import for SMS
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)
User = get_user_model()

# --- Initialize Twilio Client (Check if credentials exist) ---
twilio_client = None
TWILIO_ACCOUNT_SID = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
TWILIO_AUTH_TOKEN = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
TWILIO_PHONE_NUMBER = getattr(settings, 'TWILIO_PHONE_NUMBER', None)

if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
    try:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        logger.info("Twilio client initialized successfully for appointment reminders.")
    except Exception as e:
        logger.error(f"Failed to initialize Twilio client: {e}")
else:
    logger.warning("Twilio credentials not fully configured in settings. SMS reminders will be disabled.")
# --- End Twilio Client Init ---


@shared_task(name="doctors.tasks.send_appointment_reminders_task")
def send_appointment_reminders_task():
    now = timezone.now()
    # Define time windows (e.g., 24 hours and 1 hour before)
    reminder_threshold_24h_start = now + timedelta(hours=23, minutes=55) # ~24h
    reminder_threshold_24h_end = now + timedelta(hours=24, minutes=5)   # ~24h
    reminder_threshold_1h_start = now + timedelta(minutes=55) # ~1h
    reminder_threshold_1h_end = now + timedelta(hours=1, minutes=5)  # ~1h

    # Find appointments within the reminder windows
    # Using Q objects might be slightly clearer, but the original logic is okay
    upcoming_appointments = Appointment.objects.filter(
        status__in=[Appointment.StatusChoices.SCHEDULED, Appointment.StatusChoices.CONFIRMED],
        date__gte=now.date() # Only future dates
    ).filter(
        # Appointments around 24 hours from now
        Q(date=reminder_threshold_24h_start.date(), start_time__gte=reminder_threshold_24h_start.time(), start_time__lt=reminder_threshold_24h_end.time()) |
        # Appointments around 1 hour from now
        Q(date=reminder_threshold_1h_start.date(), start_time__gte=reminder_threshold_1h_start.time(), start_time__lt=reminder_threshold_1h_end.time())
    ).select_related('user', 'doctor').distinct() # Ensure user and doctor are fetched efficiently


    appointment_count = upcoming_appointments.count()
    if appointment_count > 0:
        logger.info(f"Found {appointment_count} appointments for reminder checks.")
    else:
        # logger.debug("No appointments found in reminder window.") # Use debug level if too verbose
        return "No appointments found in reminder windows."

    sent_count = {'email': 0, 'sms': 0, 'push': 0, 'in_app': 0}
    error_count = {'email': 0, 'sms': 0, 'push': 0}

    for appt in upcoming_appointments:
        user = appt.user
        if not user:
            logger.warning(f"Appointment {appt.id} has no associated user. Skipping.")
            continue

        # Common message elements
        doctor_name = f"Dr. {appt.doctor.last_name}" if appt.doctor else "your doctor"
        appointment_time_str = appt.start_time.strftime('%I:%M %p') # e.g., 02:30 PM
        appointment_date_str = appt.date.strftime('%b %d, %Y') # e.g., May 01, 2025
        base_verb_text = f"Reminder: Appointment with {doctor_name} on {appointment_date_str} at {appointment_time_str}."
        target_url = f"/appointments/{appt.id}"

        # 1. In-App Notification (Using existing notification app)
        try:
            # Consider adding a check to prevent sending duplicate in-app reminders
            # (e.g., check if a reminder for this appt was sent recently)
            create_notification(
                recipient=user,
                verb=base_verb_text,
                level='appointment', # Use specific level
                target_url=target_url
            )
            sent_count['in_app'] += 1
        except Exception as e:
            logger.error(f"Failed to create in-app notification for appointment {appt.id}, user {user.id}: {e}")


        # 2. Email Reminder
        if user.email and user.notify_appointment_reminder_email:
            logger.debug(f"Attempting email reminder for appt {appt.id} to {user.email}")
            context = {
                'user': user,
                'appointment': appt,
                'doctor_name': doctor_name, # Pass pre-formatted name
                'subject': f"Appointment Reminder: {appointment_date_str} at {appointment_time_str}"
            }
            email_sent = send_app_email(
                to_email=user.email,
                subject=context['subject'],
                # Ensure this template exists and uses the context variables
                template_name='emails/appointment_reminder.html',
                context=context
            )
            if email_sent:
                sent_count['email'] += 1
            else:
                error_count['email'] += 1
                logger.error(f"send_app_email failed for appt {appt.id}, user {user.id}")

        # 3. SMS Reminder
        if twilio_client and user.notify_appointment_reminder_sms and user.phone_number:
            logger.debug(f"Attempting SMS reminder for appt {appt.id} to {user.phone_number}")
            sms_message_body = f"VitaNips Reminder: Appt with {doctor_name} on {appointment_date_str} at {appointment_time_str}."
            try:
                message = twilio_client.messages.create(
                    to=str(user.phone_number), # Ensure it's a string
                    from_=TWILIO_PHONE_NUMBER,
                    body=sms_message_body
                )
                logger.info(f"SMS sent for appt {appt.id} to {user.phone_number}. SID: {message.sid}, Status: {message.status}")
                sent_count['sms'] += 1
            except TwilioRestException as e:
                logger.error(f"Twilio error sending SMS for appt {appt.id} to {user.phone_number}: {e}")
                error_count['sms'] += 1
            except Exception as e:
                 logger.error(f"Unexpected error sending SMS for appt {appt.id} to {user.phone_number}: {e}")
                 error_count['sms'] += 1

        # 4. Push Notification Reminder
        # Check if PUSH_NOTIFICATIONS_SETTINGS are likely configured (at least FCM key)
        push_enabled = bool(getattr(settings, 'PUSH_NOTIFICATIONS_SETTINGS', {}).get('FCM_API_KEY')) or \
                       bool(getattr(settings, 'PUSH_NOTIFICATIONS_SETTINGS', {}).get('APNS_CERTIFICATE'))
        if push_enabled and user.notify_appointment_reminder_push:
            logger.debug(f"Attempting push reminder for appt {appt.id} to user {user.id}")
            push_title = "Appointment Reminder"
            push_body = base_verb_text
            push_extra = {"type": "appointment_reminder", "appointment_id": appt.id, "url": target_url}

            # Query active devices for the user
            fcm_devices = FCMDevice.objects.filter(user=user, active=True)
            apns_devices = APNSDevice.objects.filter(user=user, active=True)

            push_sent_flag = False
            if fcm_devices.exists():
                try:
                    # Send to all FCM devices for the user
                    fcm_devices.send_message(title=push_title, body=push_body, data=push_extra)
                    logger.info(f"Push sent via FCM for appt {appt.id} to user {user.id} ({fcm_devices.count()} devices)")
                    push_sent_flag = True
                except Exception as e:
                    logger.error(f"Error sending FCM push for appt {appt.id}, user {user.id}: {e}")
                    error_count['push'] += 1 # Count once per user even if multiple devices fail

            if apns_devices.exists():
                try:
                     # Send to all APNS devices for the user
                    apns_devices.send_message(message={"title": push_title, "body": push_body}, extra=push_extra)
                    logger.info(f"Push sent via APNS for appt {appt.id} to user {user.id} ({apns_devices.count()} devices)")
                    push_sent_flag = True
                except Exception as e:
                     logger.error(f"Error sending APNS push for appt {appt.id}, user {user.id}: {e}")
                     # Avoid double counting error if FCM also failed
                     if not fcm_devices.exists() or error_count['push'] == 0:
                          error_count['push'] += 1

            if push_sent_flag:
                sent_count['push'] += 1
        elif not push_enabled and user.notify_appointment_reminder_push:
             logger.warning(f"Push notifications enabled for user {user.id} but PUSH_NOTIFICATIONS_SETTINGS seem incomplete.")


    summary = (f"Sent reminders for {appointment_count} appointments. "
               f"In-App: {sent_count['in_app']}. "
               f"Email: {sent_count['email']} (Errors: {error_count['email']}). "
               f"SMS: {sent_count['sms']} (Errors: {error_count['sms']}). "
               f"Push: {sent_count['push']} (Errors: {error_count['push']}).")
    logger.info(summary)
    return summary