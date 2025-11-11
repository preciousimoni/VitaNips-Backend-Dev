# vitanips/core/tests.py
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from faker import Faker

User = get_user_model()

class AdminViewsTestCase(APITestCase):
    def setUp(self):
        self.fake = Faker()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        self.normal_user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )

    def test_admin_stats_view_as_admin(self):
        """
        Ensure admin users can access the admin stats view.
        """
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('users', response.data)
        self.assertIn('doctors', response.data)
        self.assertIn('pharmacies', response.data)

    def test_admin_stats_view_as_normal_user(self):
        """
        Ensure non-admin users are forbidden from accessing the admin stats view.
        """
        self.client.force_authenticate(user=self.normal_user)
        url = reverse('admin-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_stats_view_unauthenticated(self):
        """
        Ensure unauthenticated users are unauthorized to access the admin stats view.
        """
        url = reverse('admin-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
