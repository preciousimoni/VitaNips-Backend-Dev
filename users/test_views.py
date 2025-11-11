# users/test_views.py
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from faker import Faker
import datetime
from .models import MedicalHistory, Vaccination

User = get_user_model()
fake = Faker()

class UserAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email=fake.email(),
            username=fake.email(),
            password='testpassword'
        )
        self.client.force_authenticate(user=self.user)

    def test_user_registration(self):
        url = reverse('user-register')
        data = {
            'email': fake.email(),
            'username': fake.user_name(),
            'password': 'newpassword',
            'password2': 'newpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)

    def test_get_user_profile(self):
        url = reverse('user-profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_update_user_profile(self):
        url = reverse('user-profile')
        data = {'first_name': 'John', 'last_name': 'Doe'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'John')

    def test_create_medical_history(self):
        url = reverse('medical-history-list')
        data = {
            'condition': 'Asthma',
            'diagnosis_date': datetime.date.today()
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MedicalHistory.objects.count(), 1)

    def test_create_vaccination(self):
        url = reverse('vaccination-list')
        data = {
            'vaccine_name': 'Flu Shot',
            'date_administered': datetime.date.today()
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Vaccination.objects.count(), 1)