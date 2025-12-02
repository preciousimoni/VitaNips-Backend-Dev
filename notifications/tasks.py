from celery import shared_task
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from twilio.rest import Client
from push_notifications.models import APNSDevice, GCMDevice
import logging
from datetime import timedelta, datetime
from .models import (
    Notification, NotificationDelivery, NotificationPreference,
    NotificationSchedule, NotificationTemplate
)
from doctors.models import Appointment
from pharmacy.models import MedicationReminder

logger = logging.getLogger(__name__)


# ========== SCHEDULED REMINDER TASKS ==========

@shared_task(bind=True, max_retries=3)
def check_appointment_reminders(self):
    """Check for upcoming appointments and send reminders"""
    now = timezone.now()
    now_date = now.date()
    now_time = now.time()
    
    # 24-hour reminders
    tomorrow = now + timedelta(hours=24)
    tomorrow_date = tomorrow.date()
    
    # Get all confirmed appointments and filter in Python to combine date + start_time
    all_appointments = Appointment.objects.filter(
        status='confirmed',
        date__gte=now_date,
        date__lte=tomorrow_date
    ).select_related('user', 'doctor')
    
    appointments_24h = []
    for appointment in all_appointments:
        # Combine date and start_time into a datetime
        appointment_datetime = timezone.make_aware(
            datetime.combine(appointment.date, appointment.start_time)
        )
        if now <= appointment_datetime <= tomorrow:
            appointments_24h.append(appointment)
    
    for appointment in appointments_24h:
        # Check if reminder already sent
        existing = Notification.objects.filter(
            recipient=appointment.user,
            category='appointment',
            metadata__appointment_id=appointment.id,
            metadata__reminder_type='24h',
            timestamp__gte=now - timedelta(hours=1)
        ).exists()
        
        if not existing:
            send_appointment_reminder.delay(appointment.id, reminder_type='24h')
    
    # 1-hour reminders
    one_hour = now + timedelta(hours=1)
    one_hour_date = one_hour.date()
    
    appointments_1h = []
    for appointment in all_appointments:
        # Combine date and start_time into a datetime
        appointment_datetime = timezone.make_aware(
            datetime.combine(appointment.date, appointment.start_time)
        )
        if now <= appointment_datetime <= one_hour:
            appointments_1h.append(appointment)
    
    for appointment in appointments_1h:
        existing = Notification.objects.filter(
            recipient=appointment.user,
            category='appointment',
            metadata__appointment_id=appointment.id,
            metadata__reminder_type='1h',
            timestamp__gte=now - timedelta(minutes=30)
        ).exists()
        
        if not existing:
            send_appointment_reminder.delay(appointment.id, reminder_type='1h')
    
    logger.info(f"Checked appointment reminders: {len(appointments_24h)} 24h, {len(appointments_1h)} 1h")
    return {'24h': len(appointments_24h), '1h': len(appointments_1h)}


@shared_task(bind=True, max_retries=3)
def check_medication_refill_reminders(self):
    """Check for medications needing refill and send reminders"""
    now = timezone.now()
    
    # Find active medication reminders where end_date is approaching
    reminders = MedicationReminder.objects.filter(
        is_active=True,
        end_date__isnull=False,
        end_date__gte=now.date(),
        end_date__lte=(now + timedelta(days=7)).date()
    ).select_related('user', 'medication')
    
    for reminder in reminders:
        days_remaining = (reminder.end_date - now.date()).days
        
        # Send reminder if 7, 3, or 1 days remaining
        if days_remaining in [7, 3, 1]:
            # Check if reminder already sent today
            existing = Notification.objects.filter(
                recipient=reminder.user,
                category='medication',
                metadata__reminder_id=reminder.id,
                metadata__reminder_type='refill',
                timestamp__gte=now.replace(hour=0, minute=0, second=0)
            ).exists()
            
            if not existing:
                send_refill_reminder.delay(reminder.id, days_remaining)
    
    logger.info(f"Checked {reminders.count()} medication refill reminders")
    return reminders.count()


@shared_task(bind=True, max_retries=3)
def process_scheduled_notifications(self):
    """Process scheduled recurring notifications"""
    now = timezone.now()
    
    schedules = NotificationSchedule.objects.filter(
        is_active=True,
        next_send_at__lte=now
    ).select_related('user', 'template')
    
    for schedule in schedules:
        try:
            create_notification_from_schedule.delay(schedule.id)
        except Exception as e:
            logger.error(f"Error scheduling notification {schedule.id}: {e}")
    
    return schedules.count()


# ========== NOTIFICATION CREATION TASKS ==========

@shared_task(bind=True, max_retries=3)
def send_appointment_reminder(self, appointment_id, reminder_type='24h'):
    """Send appointment reminder notification"""
    try:
        appointment = Appointment.objects.select_related(
            'user', 'doctor'
        ).get(id=appointment_id)
        
        # Combine date and start_time into a datetime
        appointment_datetime = timezone.make_aware(
            datetime.combine(appointment.date, appointment.start_time)
        )
        
        # Create notification
        notification = Notification.objects.create(
            recipient=appointment.user,
            title=f"Appointment Reminder - {reminder_type}",
            verb=f"Your appointment with Dr. {appointment.doctor.user.get_full_name()} is in {reminder_type}",
            level='info',
            category='appointment',
            action_url=f"/appointments/{appointment.id}",
            action_text="View Details",
            metadata={
                'appointment_id': appointment.id,
                'reminder_type': reminder_type,
                'doctor_name': appointment.doctor.user.get_full_name(),
                'appointment_time': appointment_datetime.isoformat(),
            }
        )
        
        # Queue delivery across channels
        deliver_notification.delay(notification.id)
        
        return notification.id
        
    except Appointment.DoesNotExist:
        logger.error(f"Appointment {appointment_id} not found")
        return None
    except Exception as e:
        logger.error(f"Error sending appointment reminder: {e}")
        self.retry(countdown=60, exc=e)


@shared_task(bind=True, max_retries=3)
def send_refill_reminder(self, reminder_id, days_remaining):
    """Send medication refill reminder"""
    try:
        reminder = MedicationReminder.objects.select_related('user', 'medication').get(id=reminder_id)
        
        notification = Notification.objects.create(
            recipient=reminder.user,
            title="Medication Refill Reminder",
            verb=f"Your {reminder.medication.name} refill is due in {days_remaining} day{'s' if days_remaining > 1 else ''}",
            level='warning' if days_remaining <= 3 else 'info',
            category='medication',
            action_url=f"/prescriptions?medication={reminder.medication.id}",
            action_text="Order Refill",
            metadata={
                'reminder_id': reminder.id,
                'medication_name': reminder.medication.name,
                'days_remaining': days_remaining,
                'end_date': reminder.end_date.isoformat(),
                'reminder_type': 'refill'
            }
        )
        
        deliver_notification.delay(notification.id)
        return notification.id
        
    except MedicationReminder.DoesNotExist:
        logger.error(f"Medication reminder {reminder_id} not found")
        return None


@shared_task(bind=True)
def create_notification_from_schedule(self, schedule_id):
    """Create notification from scheduled template"""
    try:
        schedule = NotificationSchedule.objects.select_related('user', 'template').get(id=schedule_id)
        template = schedule.template
        
        # Render template content
        context = schedule.context_data
        
        notification = Notification.objects.create(
            recipient=schedule.user,
            template=template,
            title=template.push_title,
            verb=template.in_app_message,
            category='system',
            metadata=context
        )
        
        # Update schedule
        schedule.last_sent_at = timezone.now()
        schedule.total_sent += 1
        # TODO: Calculate next send time based on frequency
        schedule.save()
        
        deliver_notification.delay(notification.id)
        return notification.id
        
    except NotificationSchedule.DoesNotExist:
        logger.error(f"Notification schedule {schedule_id} not found")


# ========== MULTI-CHANNEL DELIVERY TASKS ==========

@shared_task(bind=True, max_retries=3)
def deliver_notification(self, notification_id):
    """Orchestrate multi-channel notification delivery"""
    try:
        notification = Notification.objects.select_related('recipient').get(id=notification_id)
        user = notification.recipient
        
        # Get or create user preferences
        prefs, _ = NotificationPreference.objects.get_or_create(user=user)
        
        # Check quiet hours
        if not prefs.should_send_now():
            # Reschedule for after quiet hours
            logger.info(f"Notification {notification_id} delayed due to quiet hours")
            return 'delayed_quiet_hours'
        
        # Determine which channels to use based on preferences and category
        channels = []
        category = notification.category
        
        if prefs.email_enabled and prefs.get_channel_preference(category, 'email'):
            channels.append('email')
        
        if prefs.sms_enabled and prefs.get_channel_preference(category, 'sms') and user.phone_number:
            channels.append('sms')
        
        if prefs.push_enabled and prefs.get_channel_preference(category, 'push'):
            channels.append('push')
        
        # Always create in-app notification
        channels.append('in_app')
        
        # Deliver on each channel
        results = {}
        for channel in channels:
            delivery = NotificationDelivery.objects.create(
                notification=notification,
                channel=channel,
                status='queued'
            )
            
            if channel == 'email':
                send_email_notification.delay(delivery.id)
            elif channel == 'sms':
                send_sms_notification.delay(delivery.id)
            elif channel == 'push':
                send_push_notification.delay(delivery.id)
            elif channel == 'in_app':
                delivery.status = 'delivered'
                delivery.delivered_at = timezone.now()
                delivery.save()
            
            results[channel] = 'queued'
        
        notification.sent_at = timezone.now()
        notification.save()
        
        return results
        
    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
        return None


@shared_task(bind=True, max_retries=3)
def send_email_notification(self, delivery_id):
    """Send email notification via configured backend"""
    try:
        delivery = NotificationDelivery.objects.select_related(
            'notification__recipient', 'notification__template'
        ).get(id=delivery_id)
        
        notification = delivery.notification
        user = notification.recipient
        
        # Use template if available
        if notification.template:
            context = notification.metadata
            context.update({
                'user': user,
                'notification': notification,
                'action_url': notification.action_url,
            })
            rendered = notification.template.render(context, channel='email')
            subject = rendered['subject']
            html_content = rendered['body']
        else:
            subject = notification.title
            html_content = f"<p>{notification.verb}</p>"
        
        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=notification.verb,  # Plain text fallback
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        
        email.send()
        
        # Update delivery status
        delivery.status = 'sent'
        delivery.sent_at = timezone.now()
        delivery.save()
        
        logger.info(f"Email sent to {user.email} for notification {notification.id}")
        return 'sent'
        
    except NotificationDelivery.DoesNotExist:
        logger.error(f"Delivery {delivery_id} not found")
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        delivery.status = 'failed'
        delivery.error_message = str(e)
        delivery.failed_at = timezone.now()
        delivery.retry_count += 1
        delivery.save()
        
        if delivery.retry_count < 3:
            self.retry(countdown=60 * delivery.retry_count, exc=e)


@shared_task(bind=True, max_retries=3)
def send_sms_notification(self, delivery_id):
    """Send SMS notification via Twilio"""
    try:
        delivery = NotificationDelivery.objects.select_related(
            'notification__recipient', 'notification__template'
        ).get(id=delivery_id)
        
        notification = delivery.notification
        user = notification.recipient
        
        if not user.phone_number:
            delivery.status = 'failed'
            delivery.error_message = "User has no phone number"
            delivery.save()
            return 'no_phone'
        
        # Use template if available
        if notification.template:
            context = notification.metadata
            context['user'] = user
            message = notification.template.render(context, channel='sms')
        else:
            message = f"{notification.title}: {notification.verb}"[:160]
        
        # Send via Twilio
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        sms = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=user.phone_number
        )
        
        delivery.status = 'sent'
        delivery.sent_at = timezone.now()
        delivery.external_id = sms.sid
        delivery.provider_response = {
            'status': sms.status,
            'error_code': sms.error_code,
            'error_message': sms.error_message,
        }
        delivery.save()
        
        logger.info(f"SMS sent to {user.phone_number} for notification {notification.id}")
        return 'sent'
        
    except NotificationDelivery.DoesNotExist:
        logger.error(f"Delivery {delivery_id} not found")
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        delivery.status = 'failed'
        delivery.error_message = str(e)
        delivery.failed_at = timezone.now()
        delivery.retry_count += 1
        delivery.save()
        
        if delivery.retry_count < 3:
            self.retry(countdown=60 * delivery.retry_count, exc=e)


@shared_task(bind=True, max_retries=3)
def send_push_notification(self, delivery_id):
    """Send push notification via FCM/APNS"""
    try:
        delivery = NotificationDelivery.objects.select_related(
            'notification__recipient', 'notification__template'
        ).get(id=delivery_id)
        
        notification = delivery.notification
        user = notification.recipient
        
        # Use template if available
        if notification.template:
            context = notification.metadata
            context['user'] = user
            rendered = notification.template.render(context, channel='push')
            title = rendered['title']
            body = rendered['body']
        else:
            title = notification.title
            body = notification.verb
        
        # Get user's devices
        apns_devices = APNSDevice.objects.filter(user=user, active=True)
        gcm_devices = GCMDevice.objects.filter(user=user, active=True)
        
        # Prepare extra data
        extra_data = {
            'notification_id': notification.id,
            'category': notification.category,
            'action_url': notification.action_url or '',
        }
        
        # Send to iOS devices
        if apns_devices.exists():
            apns_devices.send_message(
                message={"title": title, "body": body},
                extra=extra_data
            )
        
        # Send to Android devices
        if gcm_devices.exists():
            gcm_devices.send_message(
                message={"title": title, "body": body},
                extra=extra_data
            )
        
        delivery.status = 'sent'
        delivery.sent_at = timezone.now()
        delivery.save()
        
        logger.info(f"Push notification sent to {user.email}")
        return 'sent'
        
    except NotificationDelivery.DoesNotExist:
        logger.error(f"Delivery {delivery_id} not found")
    except Exception as e:
        logger.error(f"Error sending push notification: {e}")
        delivery.status = 'failed'
        delivery.error_message = str(e)
        delivery.failed_at = timezone.now()
        delivery.retry_count += 1
        delivery.save()
        
        if delivery.retry_count < 3:
            self.retry(countdown=60 * delivery.retry_count, exc=e)


# ========== UTILITY TASKS ==========

@shared_task
def cleanup_old_notifications():
    """Delete old read notifications (older than 90 days)"""
    threshold = timezone.now() - timedelta(days=90)
    deleted = Notification.objects.filter(
        unread=False,
        timestamp__lt=threshold
    ).delete()
    logger.info(f"Cleaned up {deleted[0]} old notifications")
    return deleted[0]


@shared_task
def retry_failed_deliveries():
    """Retry failed notification deliveries"""
    now = timezone.now()
    failed_deliveries = NotificationDelivery.objects.filter(
        status='failed',
        retry_count__lt=3,
        next_retry_at__lte=now
    )
    
    for delivery in failed_deliveries:
        if delivery.channel == 'email':
            send_email_notification.delay(delivery.id)
        elif delivery.channel == 'sms':
            send_sms_notification.delay(delivery.id)
        elif delivery.channel == 'push':
            send_push_notification.delay(delivery.id)
    
    return failed_deliveries.count()
