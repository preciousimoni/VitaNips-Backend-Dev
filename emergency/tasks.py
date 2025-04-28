# emergency/tasks.py
import os
from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from twilio.rest import Client # Import Twilio client
from twilio.base.exceptions import TwilioRestException # Import Twilio exceptions
from .models import EmergencyContact, EmergencyAlert, EmergencyAlertContact
from typing import Optional

User = get_user_model()

# --- Get Twilio Credentials (Use environment variables!) ---
# It's best practice to load these via settings using decouple/config
# Example direct environment variable access (ensure these are set where celery runs):
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER') # Your Twilio phone number

# Initialize Twilio client (only if credentials are provided)
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
else:
    print("WARNING: Twilio credentials not found in environment variables. SOS SMS sending will be disabled.")
# --- End Twilio Setup ---


@shared_task(name="send_sos_alerts_task")
def send_sos_alerts_task(user_id: int, latitude: float, longitude: float, message: Optional[str] = None):
    """
    Fetches emergency contacts for a user and sends them an SMS alert via Twilio.
    Logs the alert event in the database.
    """
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        print(f"Error in send_sos_alerts_task: User with ID {user_id} not found.")
        return f"User {user_id} not found."

    contacts = EmergencyContact.objects.filter(user=user)
    if not contacts.exists():
        print(f"User {user_id} ({user.username}) triggered SOS but has no emergency contacts.")
        # Log the attempt even if no contacts? Optional.
        EmergencyAlert.objects.create(
             user=user, latitude=latitude, longitude=longitude, message=message or "SOS Triggered",
             status='resolved', resolution_notes="No emergency contacts configured."
         )
        return f"User {user_id} has no contacts."

    # Create the main Alert record
    alert_instance = EmergencyAlert.objects.create(
        user=user,
        latitude=latitude,
        longitude=longitude,
        message=message or "SOS Triggered", # Use provided message or default
        status='active' # Initial status
    )

    success_count = 0
    failure_count = 0

    # Format the core message
    user_name = f"{user.first_name} {user.last_name}".strip() or user.username
    location_url = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
    base_sms_body = f"SOS Alert from {user_name}. Location: {location_url}"
    if message:
        base_sms_body += f". Message: {message}"

    if not twilio_client or not TWILIO_PHONE_NUMBER:
         print(f"SOS Triggered for user {user_id} but Twilio is not configured. Logging only.")
         alert_instance.status = 'resolved' # Or a new status like 'failed_config'
         alert_instance.resolution_notes = "SMS not sent: Twilio service not configured."
         alert_instance.save()
         # Log contacts that *would* have been notified
         for contact in contacts:
            EmergencyAlertContact.objects.create(
                alert=alert_instance,
                contact=contact,
                delivery_status='failed_config'
            )
         return f"SOS for user {user_id} logged, but Twilio not configured."


    # Send SMS to each contact
    for contact in contacts:
        contact_phone = getattr(contact, 'phone_number', None) # Ensure field exists
        if not contact_phone:
            print(f"Skipping contact {contact.name} for user {user_id} - no phone number.")
            failure_count += 1
            EmergencyAlertContact.objects.create(
                alert=alert_instance,
                contact=contact,
                delivery_status='failed_no_phone'
            )
            continue

        # Ensure phone number is in E.164 format for Twilio (e.g., +14155552671)
        # Add basic formatting/validation if your stored numbers aren't E.164
        formatted_phone = contact_phone # Replace with actual formatting if needed
        if not formatted_phone.startswith('+'):
             print(f"WARNING: Phone number for contact {contact.name} ({formatted_phone}) may not be in E.164 format. Attempting anyway.")
             # formatted_phone = f"+{formatted_phone}" # Example naive addition - use a library for real validation/formatting

        alert_contact_log = EmergencyAlertContact.objects.create(
            alert=alert_instance,
            contact=contact,
            delivery_status='pending' # Initial status before sending
        )

        try:
            message_instance = twilio_client.messages.create(
                body=base_sms_body,
                from_=TWILIO_PHONE_NUMBER,
                to=formatted_phone
            )
            print(f"SMS sent to {contact.name} ({formatted_phone}), SID: {message_instance.sid}, Status: {message_instance.status}")
            # Update log status based on Twilio's initial response
            alert_contact_log.delivery_status = message_instance.status # e.g., 'queued', 'sending'
            alert_contact_log.save()
            success_count += 1
        except TwilioRestException as e:
            print(f"Error sending SMS to {contact.name} ({formatted_phone}): {e}")
            failure_count += 1
            alert_contact_log.delivery_status = 'failed_send_error'
            alert_contact_log.response_message = str(e) # Store error message
            alert_contact_log.save()
        except Exception as e: # Catch other potential errors
             print(f"Unexpected error sending SMS to {contact.name} ({formatted_phone}): {e}")
             failure_count += 1
             alert_contact_log.delivery_status = 'failed_unexpected'
             alert_contact_log.response_message = str(e)
             alert_contact_log.save()


    # Update overall alert status based on sending attempts
    if failure_count == 0 and success_count > 0:
        alert_instance.status = 'responded' # Assuming 'responded' means 'sent to contacts'
        alert_instance.resolution_notes = f"Alerts sent successfully to {success_count} contacts."
    elif success_count > 0:
         alert_instance.status = 'responded' # Partially successful
         alert_instance.resolution_notes = f"Alerts sent to {success_count} contacts, failed for {failure_count}."
    else:
        alert_instance.status = 'resolved' # Failed to send to any
        alert_instance.resolution_notes = f"Failed to send alerts to any of the {contacts.count()} contacts."

    alert_instance.save()

    return f"SOS for user {user_id} processed. Sent: {success_count}, Failed: {failure_count}."