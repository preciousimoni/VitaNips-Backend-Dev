# notifications/test_views.py
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from faker import Faker
from .models import Notification, NotificationPreference
from push_notifications.models import GCMDevice

User = get_user_model()
fake = Faker()

class NotificationAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email=fake.email(),
            username=fake.email(),
            password='testpassword'
        )
        self.client.force_authenticate(user=self.user)
        self.notification = Notification.objects.create(
            recipient=self.user,
            title='Test Notification',
            verb='A test notification was created.'
        )

    def test_list_notifications(self):
        url = reverse('notifications:notification-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_mark_as_read(self):
        url = reverse('notifications:notification-mark-as-read', kwargs={'pk': self.notification.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertFalse(self.notification.unread)

    def test_mark_all_as_read(self):
        url = reverse('notifications:notification-mark-all-as-read')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertFalse(self.notification.unread)

    def test_unread_count(self):
        url = reverse('notifications:notification-unread-count')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 1)

    def test_dismiss_notification(self):
        url = reverse('notifications:notification-dismiss', kwargs={'pk': self.notification.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.dismissed)

class NotificationPreferenceAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email=fake.email(),
            username=fake.email(),
            password='testpassword'
        )
        self.client.force_authenticate(user=self.user)
        # Create preferences for the user
        self.preference = NotificationPreference.objects.create(user=self.user)

    def test_get_preferences(self):
        # The view is designed to be a singleton, accessed without a PK.
        url = reverse('notifications:notification-preferences')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['email_enabled'])

    def test_update_preferences(self):
        # The view's get_object retrieves the object based on the user, so no PK is needed.
        url = reverse('notifications:notification-preferences')
        data = {'email_enabled': False}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.preference.refresh_from_db()
        self.assertFalse(self.preference.email_enabled)

class DeviceRegistrationAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email=fake.email(),
            username=fake.email(),
            password='testpassword'
        )
        self.client.force_authenticate(user=self.user)

    def test_register_device(self):
        url = reverse('notifications:device-register')
        data = {
            'registration_id': fake.uuid4(),
            'type': 'web'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GCMDevice.objects.count(), 1)