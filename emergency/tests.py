# emergency/tests.py
from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

User = get_user_model()


class TriggerSOSTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="sosuser@example.com",
            username="sosuser",
            password="password123"
        )
        self.client: APIClient = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('emergency.views.send_sos_alerts_task')
    def test_trigger_sos_accepted_when_task_enqueued(self, mock_task):
        # Simulate successful queuing
        mock_task.delay.return_value = None

        url = reverse('emergency-trigger-sos')
        payload = {"latitude": 6.5244, "longitude": 3.3792}
        resp = self.client.post(url, data=payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('status', resp.data)
        mock_task.delay.assert_called_once()

    def test_trigger_sos_missing_coords(self):
        url = reverse('emergency-trigger-sos')
        resp = self.client.post(url, data={}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', resp.data)
 

