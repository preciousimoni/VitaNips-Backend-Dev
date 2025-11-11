# notifications/test_models.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from faker import Faker
from .models import NotificationTemplate, Notification, NotificationDelivery, NotificationPreference, NotificationSchedule
from django.utils import timezone

User = get_user_model()
fake = Faker()

class NotificationModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email=fake.email(),
            username=fake.user_name(),
            password='testpassword'
        )
        self.template = NotificationTemplate.objects.create(
            name='Test Template',
            template_type='appointment_reminder',
            email_subject='Reminder',
            email_body_html='<p>Hello!</p>'
        )

    def test_create_notification_template(self):
        self.assertEqual(NotificationTemplate.objects.count(), 1)
        self.assertEqual(self.template.name, 'Test Template')

    def test_create_notification(self):
        notification = Notification.objects.create(
            recipient=self.user,
            template=self.template,
            title='Test Notification',
            verb='A test notification was created.'
        )
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(notification.recipient, self.user)
        self.assertTrue(notification.unread)

    def test_create_notification_delivery(self):
        notification = Notification.objects.create(
            recipient=self.user,
            title='Test Notification',
            verb='A test notification was created.'
        )
        delivery = NotificationDelivery.objects.create(
            notification=notification,
            channel='email'
        )
        self.assertEqual(NotificationDelivery.objects.count(), 1)
        self.assertEqual(delivery.status, 'pending')

    def test_create_notification_preference(self):
        preference = NotificationPreference.objects.create(user=self.user)
        self.assertEqual(NotificationPreference.objects.count(), 1)
        self.assertTrue(preference.email_enabled)

    def test_create_notification_schedule(self):
        schedule = NotificationSchedule.objects.create(
            user=self.user,
            template=self.template,
            frequency='daily',
            time_of_day='09:00',
            start_date=timezone.now().date()
        )
        self.assertEqual(NotificationSchedule.objects.count(), 1)
        self.assertTrue(schedule.is_active)