# vitanips/celery.py
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vitanips.settings')

app = Celery('vitanips')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send-appointment-reminders-every-15-mins': {
        'task': 'doctors.tasks.send_appointment_reminders_task',
        'schedule': crontab(minute='*/15'),
    },
    'send-medication-reminders-daily': {
        'task': 'pharmacy.tasks.send_medication_reminders_task',
        'schedule': crontab(hour=8, minute=0),
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')