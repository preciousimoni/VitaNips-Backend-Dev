# health/test_views.py
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from faker import Faker
import datetime
from django.utils import timezone
from .models import VitalSign, SymptomLog, FoodLog, ExerciseLog, SleepLog, HealthGoal, MedicalDocument
from django.core.files.uploadedfile import SimpleUploadedFile
from doctors.models import Doctor, Appointment, Specialty

User = get_user_model()
fake = Faker()

class HealthAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email=fake.email(),
            username=fake.email(),
            password='testpassword'
        )
        doctor_user = User.objects.create_user(
            email=fake.email(),
            username=fake.email(),
            password='testpassword'
        )
        specialty = Specialty.objects.create(name='Cardiology')
        self.doctor = Doctor.objects.create(
            user=doctor_user,
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            gender='M',
            years_of_experience=10,
            education=fake.text(),
            bio=fake.text(),
            languages_spoken='English'
        )
        self.doctor.specialties.add(specialty)
        self.appointment = Appointment.objects.create(
            user=self.user,
            doctor=self.doctor,
            date=datetime.date.today(),
            start_time=datetime.time(10, 0),
            end_time=datetime.time(10, 30),
            reason='Checkup'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_vital_sign(self):
        url = reverse('vital-sign-list')
        data = {
            'date_recorded': timezone.now(),
            'heart_rate': 75,
            'systolic_pressure': 120,
            'diastolic_pressure': 80
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VitalSign.objects.count(), 1)

    def test_create_symptom_log(self):
        url = reverse('symptom-log-list')
        data = {
            'symptom': 'Coughing',
            'date_experienced': timezone.now(),
            'severity': 2
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SymptomLog.objects.count(), 1)

    def test_create_food_log(self):
        url = reverse('food-log-list')
        data = {
            'food_item': 'Salad',
            'meal_type': 'lunch',
            'datetime': timezone.now(),
            'calories': 300
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FoodLog.objects.count(), 1)

    def test_create_exercise_log(self):
        url = reverse('exercise-log-list')
        data = {
            'activity_type': 'Yoga',
            'datetime': timezone.now(),
            'duration': 60
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExerciseLog.objects.count(), 1)

    def test_create_sleep_log(self):
        url = reverse('sleep-log-list')
        data = {
            'sleep_time': timezone.now() - datetime.timedelta(hours=9),
            'wake_time': timezone.now(),
            'quality': 3
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SleepLog.objects.count(), 1)

    def test_create_health_goal(self):
        url = reverse('health-goal-list')
        data = {
            'goal_type': 'steps',
            'target_value': 10000,
            'unit': 'steps',
            'start_date': datetime.date.today(),
            'target_date': datetime.date.today() + datetime.timedelta(days=30)
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(HealthGoal.objects.count(), 1)

    def test_create_medical_document(self):
        url = reverse('medical-document-list')
        # This is a simplified test. File upload would require more setup.
        test_file = SimpleUploadedFile("test_file.txt", b"file_content", content_type="text/plain")
        data = {
            'description': 'Test document',
            'document_type': 'report',
            'appointment': self.appointment.pk,
            'file': test_file
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MedicalDocument.objects.count(), 1)
