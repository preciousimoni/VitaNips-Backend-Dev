# notifications/tests.py
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Notification


User = get_user_model()


class NotificationAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            username="testuser",
            password="password123"
        )
        self.client: APIClient = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create sample notifications
        self.n1 = Notification.objects.create(
            recipient=self.user,
            verb="Test notification 1",
            level="info",
            unread=True,
        )
        self.n2 = Notification.objects.create(
            recipient=self.user,
            verb="Test notification 2",
            level="warning",
            unread=True,
        )

    def test_list_notifications_includes_verb(self):
        url = reverse('notifications:list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.data)
        self.assertTrue(any('verb' in item for item in resp.data['results']))

    def test_unread_count(self):
        url = reverse('notifications:unread-count')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data.get('unread_count'), 2)

    def test_mark_one_as_read_and_count_decrements(self):
        mark_url = reverse('notifications:mark-read', kwargs={'pk': self.n1.id})
        resp = self.client.post(mark_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data.get('unread'))

        count_url = reverse('notifications:unread-count')
        resp2 = self.client.get(count_url)
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertEqual(resp2.data.get('unread_count'), 1)

    def test_mark_all_as_read(self):
        url = reverse('notifications:mark-all-read')
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('status', resp.data)

        count_url = reverse('notifications:unread-count')
        resp2 = self.client.get(count_url)
        self.assertEqual(resp2.data.get('unread_count'), 0)

    def test_device_registration_web(self):
        url = reverse('notifications:device-register')
        payload = {"registration_id": "test-token-123", "type": "web"}
        resp = self.client.post(url, data=payload, format='json')
        self.assertIn(resp.status_code, (status.HTTP_200_OK, status.HTTP_201_CREATED))
        self.assertIn('detail', resp.data)
from django.test import TestCase

# Create your tests here.
