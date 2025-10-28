# Email & SMS Notifications Setup Guide

This guide explains how to configure email and SMS notifications for appointment and medication reminders in VitaNips.

## ✅ What's Already Complete

### Backend Infrastructure
- ✅ Celery task queue configured with Redis
- ✅ `django-celery-beat` installed for scheduled tasks
- ✅ Appointment reminder task (`doctors/tasks.py`)
- ✅ Medication reminder task (`pharmacy/tasks.py`)
- ✅ Email templates created with professional styling
- ✅ User notification preferences in User model
- ✅ Twilio SMS integration ready
- ✅ Push notifications configured

### Email Templates Created
- ✅ `templates/emails/base.html` - Base template with responsive design
- ✅ `templates/emails/appointment_reminder.html` - Appointment reminders
- ✅ `templates/emails/medication_reminder.html` - Medication reminders

### Current Configuration
Your `.env` file is now configured with:
- Gmail SMTP for email delivery
- Twilio credentials for SMS
- Firebase credentials for push notifications

---

## 🚀 Testing the Notification System

### 1. Start Required Services

#### Start Redis (required for Celery):
```bash
# On macOS with Homebrew:
brew services start redis

# Or run manually:
redis-server
```

#### Start Celery Worker:
```bash
cd VitaNips-Backend-Dev
celery -A vitanips worker -l info
```

#### Start Celery Beat (scheduler):
```bash
# In a new terminal:
cd VitaNips-Backend-Dev
celery -A vitanips beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### 2. Test Email Sending

You can test email delivery with the Django shell:

```python
python manage.py shell

# In the Python shell:
from vitanips.core.utils import send_app_email
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()  # Get a test user

# Test appointment reminder email
context = {
    'user': user,
    'appointment': {
        'date': '2025-10-29',
        'start_time': '10:00 AM',
        'appointment_type': 'in_person',
        'reason': 'Regular checkup'
    },
    'doctor_name': 'Dr. Smith',
    'subject': 'Appointment Reminder'
}

send_app_email(
    to_email='your-email@example.com',
    subject='Test Appointment Reminder',
    template_name='emails/appointment_reminder.html',
    context=context
)
```

### 3. Test SMS Sending

```python
python manage.py shell

# In the Python shell:
from twilio.rest import Client
from django.conf import settings

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

message = client.messages.create(
    body="Test SMS from VitaNips!",
    from_=settings.TWILIO_PHONE_NUMBER,
    to='+1234567890'  # Your phone number in E.164 format
)

print(f"Message SID: {message.sid}")
```

### 4. Create Test Appointment for Reminders

```python
python manage.py shell

from django.utils import timezone
from datetime import timedelta
from doctors.models import Appointment, Doctor
from django.contrib.auth import get_user_model

User = get_user_model()

# Get or create a test user and doctor
user = User.objects.first()
doctor = Doctor.objects.first()

# Create appointment 1 hour from now (will trigger 1-hour reminder)
appointment_time = timezone.now() + timedelta(hours=1)

appointment = Appointment.objects.create(
    user=user,
    doctor=doctor,
    date=appointment_time.date(),
    start_time=appointment_time.time(),
    end_time=(appointment_time + timedelta(hours=1)).time(),
    appointment_type='in_person',
    status='scheduled',
    reason='Test appointment for notifications'
)

print(f"Created appointment: {appointment.id}")
```

---

## 📧 Email Backend Options

### Option 1: Gmail (Current - Development/Testing)
**Pros:** Free, easy to set up
**Cons:** Limited to 500 emails/day, may be marked as spam

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

**Important:** Use an [App Password](https://myaccount.google.com/apppasswords), not your regular Gmail password.

### Option 2: SendGrid (Recommended for Production)
**Pros:** 100 emails/day free, reliable, good deliverability
**Cons:** Requires API key

```bash
# Install django-anymail
pip install django-anymail[sendgrid]
```

Update `.env`:
```env
EMAIL_BACKEND=anymail.backends.sendgrid.EmailBackend
SENDGRID_API_KEY=SG.your_api_key_here
DEFAULT_FROM_EMAIL=VitaNips <noreply@yourdomain.com>
```

Get your API key at: https://app.sendgrid.com/settings/api_keys

### Option 3: AWS SES (For Production at Scale)
**Pros:** Very cheap, highly scalable, reliable
**Cons:** Requires AWS account, initial verification

```bash
pip install django-anymail[amazon-ses]
```

Update `.env`:
```env
EMAIL_BACKEND=anymail.backends.amazon_ses.EmailBackend
AWS_SES_REGION_NAME=us-east-1
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
DEFAULT_FROM_EMAIL=VitaNips <noreply@yourdomain.com>
```

---

## 📱 SMS Configuration (Twilio)

### Current Status: ✅ Configured

Your Twilio credentials are already set up in `.env`. 

### Testing Your Phone Number

Twilio requires phone numbers to be in **E.164 format**:
- ✅ Correct: `+2348149960190` (Nigeria)
- ✅ Correct: `+14155552671` (USA)
- ❌ Wrong: `08149960190`
- ❌ Wrong: `(415) 555-2671`

### Verify Phone Number (Development)

If using a Twilio trial account, verify recipient phone numbers at:
https://console.twilio.com/us1/develop/phone-numbers/manage/verified

### SMS Costs (Production)

Typical costs per SMS:
- USA: $0.0079 per message
- Nigeria: $0.0455 per message
- Canada: $0.0079 per message

Monitor usage: https://console.twilio.com/us1/billing/usage

---

## 🔔 Push Notifications Configuration

### Current Status: ⚠️ Partially Configured

Firebase credentials are set, but you need the **FCM Server Key**.

### Get FCM Server Key

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: `vitanips-800cd`
3. Go to **Project Settings** > **Cloud Messaging** tab
4. Copy the **Server Key** (not the Sender ID)
5. Update `.env`:
   ```env
   FCM_SERVER_KEY=AAAAxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

### Testing Push Notifications

Frontend must register device tokens. Check `src/utils/pushNotifications.ts` is initialized in your app.

---

## 🔄 Scheduled Tasks Configuration

### Current Schedule (in `vitanips/celery.py`)

```python
'send-appointment-reminders-every-15-mins': {
    'task': 'doctors.tasks.send_appointment_reminders_task',
    'schedule': crontab(minute='*/15'),  # Every 15 minutes
},
'send-medication-reminders-daily': {
    'task': 'pharmacy.tasks.send_medication_reminders_task',
    'schedule': crontab(hour=8, minute=0),  # Daily at 8 AM
},
```

### Customize Schedule

Edit `vitanips/celery.py` to change timing:

```python
# Every hour instead of every 15 minutes:
'schedule': crontab(minute=0)

# Multiple times per day:
'schedule': crontab(hour='8,12,18', minute=0)  # 8 AM, 12 PM, 6 PM

# Every 30 minutes:
'schedule': crontab(minute='*/30')
```

---

## 🧪 Manual Testing Checklist

### Email Delivery Test
- [ ] Start Django dev server
- [ ] Check terminal for email output (console backend)
- [ ] Or check Gmail sent items (SMTP backend)
- [ ] Verify email formatting looks correct
- [ ] Test on mobile device

### SMS Delivery Test
- [ ] Run test script in Django shell
- [ ] Check phone for SMS receipt
- [ ] Verify message content is clear
- [ ] Check Twilio console logs

### Push Notification Test
- [ ] Open app in browser
- [ ] Grant notification permissions
- [ ] Check browser dev tools console for token
- [ ] Trigger test notification
- [ ] Verify notification appears

### Automated Task Test
- [ ] Start Celery worker
- [ ] Start Celery beat
- [ ] Create test appointment (1 hour from now)
- [ ] Wait for scheduled task to run
- [ ] Verify notification received
- [ ] Check Celery logs for errors

---

## 🐛 Troubleshooting

### Emails Not Sending

**Check 1:** Verify email backend is configured
```python
python manage.py shell
from django.conf import settings
print(settings.EMAIL_BACKEND)
print(settings.EMAIL_HOST_USER)
```

**Check 2:** Test SMTP connection
```bash
telnet smtp.gmail.com 587
```

**Check 3:** Check Gmail App Password
- Must be 16 characters
- No spaces or dashes
- Generate at: https://myaccount.google.com/apppasswords

### SMS Not Sending

**Check 1:** Verify Twilio credentials
```python
python manage.py shell
from django.conf import settings
print(settings.TWILIO_ACCOUNT_SID)
print(settings.TWILIO_AUTH_TOKEN)
print(settings.TWILIO_PHONE_NUMBER)
```

**Check 2:** Check phone number format (E.164)

**Check 3:** Review Twilio logs
https://console.twilio.com/us1/monitor/logs/sms

### Celery Tasks Not Running

**Check 1:** Is Redis running?
```bash
redis-cli ping
# Should return: PONG
```

**Check 2:** Is Celery worker running?
Look for: `celery@hostname ready`

**Check 3:** Is Celery beat running?
Look for: `Scheduler: Sending due task`

**Check 4:** Check scheduled tasks
```python
python manage.py shell
from django_celery_beat.models import PeriodicTask
print(PeriodicTask.objects.all())
```

---

## 📊 Monitoring in Production

### Celery Flower (Task Monitor)
```bash
pip install flower
celery -A vitanips flower
# Access at: http://localhost:5555
```

### Log Files
Check `logs/app.log` for task execution logs.

### Database Check
```sql
-- Check pending notifications
SELECT COUNT(*) FROM notifications_notification WHERE unread = true;

-- Check recent appointments
SELECT * FROM doctors_appointment 
WHERE date >= CURRENT_DATE 
ORDER BY date, start_time;
```

---

## 🎯 Next Steps

1. ✅ **Test Email Delivery** - Send a test email
2. ✅ **Test SMS Delivery** - Send a test SMS
3. ⚠️ **Get FCM Server Key** - Complete push notification setup
4. ✅ **Create Test Appointment** - Verify automated reminders work
5. 📈 **Monitor for 24 hours** - Check logs for any errors
6. 🚀 **Switch to Production Email** - Set up SendGrid or AWS SES

---

## 📞 Support Resources

- **Twilio Documentation:** https://www.twilio.com/docs
- **SendGrid Documentation:** https://docs.sendgrid.com/
- **Firebase FCM Documentation:** https://firebase.google.com/docs/cloud-messaging
- **Celery Documentation:** https://docs.celeryq.dev/
- **Django Email Documentation:** https://docs.djangoproject.com/en/4.2/topics/email/

---

**Need Help?** Check the logs in `logs/app.log` for detailed error messages.
