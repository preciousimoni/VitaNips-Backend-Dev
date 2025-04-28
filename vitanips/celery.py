# vitanips/celery.py
import os
from celery import Celery
from celery.schedules import crontab # For scheduling

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vitanips.settings')

app = Celery('vitanips')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Define schedules (alternative to Django Admin setup)
# app.conf.beat_schedule = {
#     'send-appointment-reminders-every-15-mins': {
#         'task': 'doctors.tasks.send_appointment_reminders_task',
#         'schedule': crontab(minute='*/15'), # Run every 15 minutes
#     },
#     'send-medication-reminders-daily': {
#         'task': 'pharmacy.tasks.send_medication_reminders_task',
#         'schedule': crontab(hour=8, minute=0), # Run daily at 8:00 AM
#     },
# }

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')