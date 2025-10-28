# VitaNips Notifications - Quick Reference

## 🚀 Start Services

```bash
# Terminal 1 - Redis
brew services start redis
# or: redis-server

# Terminal 2 - Celery Worker
cd VitaNips-Backend-Dev
source env/bin/activate  # or: . env/bin/activate
celery -A vitanips worker -l info

# Terminal 3 - Celery Beat (Scheduler)
cd VitaNips-Backend-Dev
source env/bin/activate
celery -A vitanips beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Terminal 4 - Django Server
cd VitaNips-Backend-Dev
source env/bin/activate
python manage.py runserver
```

## 🧪 Quick Tests

```bash
# Test notification system
python test_notifications.py

# Check Redis is running
redis-cli ping
# Should return: PONG

# View Celery logs
tail -f logs/app.log
```

## 📧 Email Templates

- **Base Template:** `templates/emails/base.html`
- **Appointment Reminder:** `templates/emails/appointment_reminder.html`
- **Medication Reminder:** `templates/emails/medication_reminder.html`

## 🔔 Notification Channels

| Channel | Status | User Preference Field |
|---------|--------|----------------------|
| Email | ✅ Ready | `notify_appointment_reminder_email` |
| SMS | ✅ Ready | `notify_appointment_reminder_sms` |
| Push | ⚠️ Needs FCM Key | `notify_appointment_reminder_push` |
| In-App | ✅ Ready | Always on |

## ⏰ Reminder Schedule

| Task | Frequency | Time |
|------|-----------|------|
| Appointment Reminders | Every 15 mins | 24h & 1h before |
| Medication Reminders | Daily | 8:00 AM |

## 📝 User Preference Fields

```python
# Appointment notifications
notify_appointment_confirmation_email = BooleanField(default=True)
notify_appointment_cancellation_email = BooleanField(default=True)
notify_appointment_reminder_email = BooleanField(default=True)
notify_appointment_reminder_sms = BooleanField(default=False)
notify_appointment_reminder_push = BooleanField(default=True)

# Prescription/Medication notifications
notify_prescription_update_email = BooleanField(default=True)
notify_refill_reminder_email = BooleanField(default=True)

# Order notifications
notify_order_update_email = BooleanField(default=True)

# General
notify_general_updates_email = BooleanField(default=True)
```

## 🐛 Common Issues

### Emails not sending
```bash
# Check email backend
python manage.py shell
>>> from django.conf import settings
>>> print(settings.EMAIL_BACKEND)
>>> print(settings.EMAIL_HOST_USER)
```

### SMS not sending
- Verify phone number is in E.164 format: `+1234567890`
- Check Twilio logs: https://console.twilio.com/us1/monitor/logs/sms
- Verify number in Twilio console (trial accounts)

### Tasks not running
- Check if Redis is running: `redis-cli ping`
- Check if Celery worker is running
- Check if Celery beat is running
- View logs: `tail -f logs/app.log`

## 📊 Monitoring Commands

```bash
# View scheduled tasks
python manage.py shell
>>> from django_celery_beat.models import PeriodicTask
>>> for task in PeriodicTask.objects.all():
...     print(f"{task.name}: {task.enabled}")

# View recent tasks in Celery
# Install flower: pip install flower
celery -A vitanips flower
# Access at: http://localhost:5555

# Check notification count
python manage.py shell
>>> from notifications.models import Notification
>>> Notification.objects.filter(unread=True).count()
```

## 🔑 Environment Variables

```env
# Email (Gmail)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=VitaNips <your-email@gmail.com>

# SMS (Twilio)
TWILIO_ACCOUNT_SID=ACxxxxx...
TWILIO_AUTH_TOKEN=xxxxx...
TWILIO_PHONE_NUMBER=+1234567890

# Push (Firebase)
FCM_SERVER_KEY=AAAAxxxxx...

# Celery (Redis)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=django-db
```

## 📚 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/notifications/` | GET | List notifications |
| `/api/notifications/unread_count/` | GET | Get unread count |
| `/api/notifications/<id>/read/` | POST | Mark as read |
| `/api/notifications/read_all/` | POST | Mark all as read |

## 🎯 Production Checklist

- [ ] Switch from Gmail to SendGrid/AWS SES
- [ ] Set up proper domain authentication (SPF, DKIM)
- [ ] Configure FCM Server Key for push notifications
- [ ] Set up monitoring (Sentry, Datadog, etc.)
- [ ] Configure proper logging
- [ ] Set up Celery beat database backup
- [ ] Test email deliverability
- [ ] Monitor Twilio SMS costs
- [ ] Set up rate limiting
- [ ] Configure retry policies

## 📞 Support

- **Twilio Console:** https://console.twilio.com/
- **Firebase Console:** https://console.firebase.google.com/
- **SendGrid Dashboard:** https://app.sendgrid.com/
- **Celery Docs:** https://docs.celeryq.dev/
