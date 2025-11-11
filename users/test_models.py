# users/test_models.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from faker import Faker
import datetime
from .models import MedicalHistory, Vaccination

User = get_user_model()
fake = Faker()

class UserModelTests(TestCase):

    def test_create_user(self):
        email = fake.email()
        username = fake.user_name()
        password = 'testpassword'
        user = User.objects.create_user(email=email, username=username, password=password)
        self.assertEqual(user.email, email)
        self.assertEqual(user.username, username)
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        email = fake.email()
        username = fake.user_name()
        password = 'testpassword'
        superuser = User.objects.create_superuser(email=email, username=username, password=password)
        self.assertEqual(superuser.email, email)
        self.assertEqual(superuser.username, username)
        self.assertTrue(superuser.check_password(password))
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

class MedicalHistoryModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email=fake.email(),
            username=fake.user_name(),
            password='testpassword'
        )

    def test_create_medical_history(self):
        medical_history = MedicalHistory.objects.create(
            user=self.user,
            condition='Hypertension',
            diagnosis_date=datetime.date.today()
        )
        self.assertEqual(medical_history.user, self.user)
        self.assertEqual(medical_history.condition, 'Hypertension')
        self.assertEqual(MedicalHistory.objects.count(), 1)
        self.assertEqual(str(medical_history), f"{self.user.email} - Hypertension")

class VaccinationModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email=fake.email(),
            username=fake.user_name(),
            password='testpassword'
        )

    def test_create_vaccination(self):
        vaccination = Vaccination.objects.create(
            user=self.user,
            vaccine_name='COVID-19',
            date_administered=datetime.date.today()
        )
        self.assertEqual(vaccination.user, self.user)
        self.assertEqual(vaccination.vaccine_name, 'COVID-19')
        self.assertEqual(Vaccination.objects.count(), 1)
        self.assertEqual(str(vaccination), f"{self.user.email} - COVID-19 (Dose 1)")