# emergency/tasks.py
import os
from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from .models import EmergencyContact, EmergencyAlert, EmergencyAlertContact
from django.contrib.gis.geos import Point
from typing import Optional

User = get_user_model()

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
else:
    print("WARNING: Twilio credentials not found in environment variables. SOS SMS sending will be disabled.")

@shared_task(name="send_sos_alerts_task")
def send_sos_alerts_task(user_id: int, latitude: float, longitude: float, message: Optional[str] = None):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        print(f"Error in send_sos_alerts_task: User with ID {user_id} not found.")
        return f"User {user_id} not found."

    contacts = EmergencyContact.objects.filter(user=user)
    if not contacts.exists():
        print(f"User {user_id} ({user.username}) triggered SOS but has no emergency contacts.")
        EmergencyAlert.objects.create(
            user=user,
            location=Point(longitude, latitude, srid=4326),
            message=message or "SOS Triggered",
            status='resolved',
            resolution_notes="No emergency contacts configured."
        )
        return f"User {user_id} has no contacts."

    alert_instance = EmergencyAlert.objects.create(
        user=user,
        location=Point(longitude, latitude, srid=4326),
        message=message or "SOS Triggered",
        status='active'
    )

    success_count = 0
    failure_count = 0

    user_name = f"{user.first_name} {user.last_name}".strip() or user.username
    location_url = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
    base_sms_body = f"SOS Alert from {user_name}. Location: {location_url}"
    if message:
        base_sms_body += f". Message: {message}"

    if not twilio_client or not TWILIO_PHONE_NUMBER:
        print(f"SOS Triggered for user {user_id} but Twilio is not configured. Logging only.")
        alert_instance.status = 'resolved'
        alert_instance.resolution_notes = "SMS not sent: Twilio service not configured."
        alert_instance.save()
        for contact in contacts:
            EmergencyAlertContact.objects.create(
                alert=alert_instance,
                contact=contact,
                delivery_status='failed_config'
            )
        return f"SOS for user {user_id} logged, but Twilio not configured."

    for contact in contacts:
        contact_phone = getattr(contact, 'phone_number', None)
        if not contact_phone:
            print(f"Skipping contact {contact.name} for user {user_id} - no phone number.")
            failure_count += 1
            EmergencyAlertContact.objects.create(
                alert=alert_instance,
                contact=contact,
                delivery_status='failed_no_phone'
            )
            continue

        formatted_phone = contact_phone
        if not formatted_phone.startswith('+'):
            print(f"WARNING: Phone number for contact {contact.name} ({formatted_phone}) may not be in E.164 format. Attempting anyway.")

        alert_contact_log = EmergencyAlertContact.objects.create(
            alert=alert_instance,
            contact=contact,
            delivery_status='pending'
        )

        try:
            message_instance = twilio_client.messages.create(
                body=base_sms_body,
                from_=TWILIO_PHONE_NUMBER,
                to=formatted_phone
            )
            print(f"SMS sent to {contact.name} ({formatted_phone}), SID: {message_instance.sid}, Status: {message_instance.status}")
            alert_contact_log.delivery_status = message_instance.status
            alert_contact_log.save()
            success_count += 1
        except TwilioRestException as e:
            print(f"Error sending SMS to {contact.name} ({formatted_phone}): {e}")
            failure_count += 1
            alert_contact_log.delivery_status = 'failed_send_error'
            alert_contact_log.response_message = str(e)
            alert_contact_log.save()
        except Exception as e:
            print(f"Unexpected error sending SMS to {contact.name} ({formatted_phone}): {e}")
            failure_count += 1
            alert_contact_log.delivery_status = 'failed_unexpected'
            alert_contact_log.response_message = str(e)
            alert_contact_log.save()

    if failure_count == 0 and success_count > 0:
        alert_instance.status = 'responded'
        alert_instance.resolution_notes = f"Alerts sent successfully to {success_count} contacts."
    elif success_count > 0:
        alert_instance.status = 'responded'
        alert_instance.resolution_notes = f"Alerts sent to {success_count} contacts, failed for {failure_count}."
    else:
        alert_instance.status = 'resolved'
        alert_instance.resolution_notes = f"Failed to send alerts to any of the {contacts.count()} contacts."

    alert_instance.save()

    return f"SOS for user {user_id} processed. Sent: {success_count}, Failed: {failure_count}."