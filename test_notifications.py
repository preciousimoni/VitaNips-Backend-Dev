#!/usr/bin/env python
"""
Test script for VitaNips Notification System
Run with: python test_notifications.py
"""

import os
import django
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vitanips.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from doctors.models import Doctor, Appointment
from pharmacy.models import Medication, MedicationReminder
from vitanips.core.utils import send_app_email
from django.conf import settings

User = get_user_model()


def test_email_configuration():
    """Test email backend configuration"""
    print("\n" + "="*60)
    print("1. TESTING EMAIL CONFIGURATION")
    print("="*60)
    
    print(f"✓ Email Backend: {settings.EMAIL_BACKEND}")
    
    if 'smtp' in settings.EMAIL_BACKEND:
        print(f"✓ SMTP Host: {settings.EMAIL_HOST}")
        print(f"✓ SMTP Port: {settings.EMAIL_PORT}")
        print(f"✓ SMTP User: {settings.EMAIL_HOST_USER}")
        print(f"✓ Use TLS: {settings.EMAIL_USE_TLS}")
    
    print(f"✓ Default From Email: {settings.DEFAULT_FROM_EMAIL}")


def test_twilio_configuration():
    """Test Twilio configuration"""
    print("\n" + "="*60)
    print("2. TESTING TWILIO CONFIGURATION")
    print("="*60)
    
    print(f"✓ Twilio Account SID: {settings.TWILIO_ACCOUNT_SID[:10]}...")
    print(f"✓ Twilio Auth Token: {'*' * 10} (configured)")
    print(f"✓ Twilio Phone Number: {settings.TWILIO_PHONE_NUMBER}")
    print(f"✓ Twilio API Key SID: {settings.TWILIO_API_KEY_SID[:10]}...")
    
    # Test Twilio connection
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        # This will make a simple API call to verify credentials
        account = client.api.accounts(settings.TWILIO_ACCOUNT_SID).fetch()
        print(f"✓ Twilio Connection: SUCCESS (Status: {account.status})")
    except Exception as e:
        print(f"✗ Twilio Connection: FAILED - {str(e)}")


def test_celery_configuration():
    """Test Celery configuration"""
    print("\n" + "="*60)
    print("3. TESTING CELERY CONFIGURATION")
    print("="*60)
    
    print(f"✓ Broker URL: {settings.CELERY_BROKER_URL}")
    print(f"✓ Result Backend: {settings.CELERY_RESULT_BACKEND}")
    
    # Test Redis connection
    try:
        import redis
        r = redis.from_url(settings.CELERY_BROKER_URL)
        r.ping()
        print("✓ Redis Connection: SUCCESS")
    except Exception as e:
        print(f"✗ Redis Connection: FAILED - {str(e)}")
        print("  Make sure Redis is running: brew services start redis")


def test_send_sample_email():
    """Send a test email"""
    print("\n" + "="*60)
    print("4. SENDING TEST EMAIL")
    print("="*60)
    
    test_email = input("Enter your email address for testing (or press Enter to skip): ").strip()
    
    if not test_email:
        print("⊘ Email test skipped")
        return
    
    user = User.objects.first()
    if not user:
        print("✗ No users found in database. Create a user first.")
        return
    
    # Create mock appointment data
    context = {
        'user': user,
        'appointment': type('obj', (object,), {
            'date': (timezone.now() + timedelta(days=1)).date(),
            'start_time': (timezone.now() + timedelta(days=1)).time(),
            'appointment_type': 'in_person',
            'get_appointment_type_display': lambda: 'In-Person',
            'reason': 'Annual checkup',
            'id': 1
        })(),
        'doctor_name': 'Dr. Test Smith',
        'subject': 'Test Appointment Reminder from VitaNips'
    }
    
    try:
        result = send_app_email(
            to_email=test_email,
            subject='Test Appointment Reminder from VitaNips',
            template_name='emails/appointment_reminder.html',
            context=context
        )
        
        if result:
            print(f"✓ Test email sent successfully to {test_email}")
            print("  Check your inbox (and spam folder)")
        else:
            print(f"✗ Failed to send test email")
            
    except Exception as e:
        print(f"✗ Error sending email: {str(e)}")


def test_send_sample_sms():
    """Send a test SMS"""
    print("\n" + "="*60)
    print("5. SENDING TEST SMS")
    print("="*60)
    
    test_phone = input("Enter phone number for testing (E.164 format, e.g., +1234567890) or press Enter to skip: ").strip()
    
    if not test_phone:
        print("⊘ SMS test skipped")
        return
    
    if not test_phone.startswith('+'):
        print("✗ Phone number must be in E.164 format (starting with +)")
        return
    
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body="🏥 Test SMS from VitaNips notification system. If you received this, SMS is working!",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=test_phone
        )
        
        print(f"✓ Test SMS sent successfully")
        print(f"  Message SID: {message.sid}")
        print(f"  Status: {message.status}")
        print(f"  Check your phone!")
        
    except Exception as e:
        print(f"✗ Error sending SMS: {str(e)}")


def show_upcoming_appointments():
    """Show appointments that will trigger reminders"""
    print("\n" + "="*60)
    print("6. UPCOMING APPOINTMENTS (Next 48 hours)")
    print("="*60)
    
    now = timezone.now()
    upcoming = Appointment.objects.filter(
        date__gte=now.date(),
        date__lte=(now + timedelta(days=2)).date(),
        status__in=['scheduled', 'confirmed']
    ).select_related('user', 'doctor')
    
    if not upcoming.exists():
        print("⊘ No upcoming appointments in the next 48 hours")
        print("\n  To create a test appointment, run:")
        print("  python manage.py shell")
        print("  >>> from test_notifications import create_test_appointment")
        print("  >>> create_test_appointment()")
    else:
        print(f"Found {upcoming.count()} upcoming appointment(s):\n")
        for appt in upcoming:
            print(f"  • {appt.user.email}")
            print(f"    Doctor: Dr. {appt.doctor.last_name}")
            print(f"    Date: {appt.date} at {appt.start_time}")
            print(f"    Type: {appt.get_appointment_type_display()}")
            print()


def create_test_appointment():
    """Helper function to create a test appointment"""
    user = User.objects.first()
    doctor = Doctor.objects.first()
    
    if not user or not doctor:
        print("✗ Need at least one user and one doctor in the database")
        return None
    
    # Create appointment 1 hour from now
    appointment_time = timezone.now() + timedelta(hours=1)
    
    appointment = Appointment.objects.create(
        user=user,
        doctor=doctor,
        date=appointment_time.date(),
        start_time=appointment_time.time(),
        end_time=(appointment_time + timedelta(hours=1)).time(),
        appointment_type='in_person',
        status='scheduled',
        reason='Test appointment for notification testing'
    )
    
    print(f"✓ Created test appointment (ID: {appointment.id})")
    print(f"  User: {user.email}")
    print(f"  Doctor: {doctor.full_name}")
    print(f"  Time: {appointment.date} at {appointment.start_time}")
    print(f"\n  This appointment will trigger a reminder in ~1 hour")
    print(f"  Make sure Celery beat is running!")
    
    return appointment


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  VITANIPS NOTIFICATION SYSTEM TEST")
    print("="*60)
    
    try:
        test_email_configuration()
        test_twilio_configuration()
        test_celery_configuration()
        test_send_sample_email()
        test_send_sample_sms()
        show_upcoming_appointments()
        
        print("\n" + "="*60)
        print("  TEST COMPLETE")
        print("="*60)
        print("\nNext Steps:")
        print("1. Start Celery worker: celery -A vitanips worker -l info")
        print("2. Start Celery beat: celery -A vitanips beat -l info")
        print("3. Create test appointments for reminder testing")
        print("4. Monitor logs/app.log for task execution")
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
