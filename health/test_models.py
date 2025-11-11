# health/test_models.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from faker import Faker
from .models import (
    VitalSign, SymptomLog, FoodLog, ExerciseLog,
    SleepLog, HealthGoal, MedicalDocument
)
from doctors.models import Doctor, Appointment, Specialty
import datetime

User = get_user_model()
fake = Faker()

class HealthModelTests(TestCase):

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
        self.doctor = Doctor.objects.create(
            user=doctor_user,
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            gender='M',
            years_of_experience=10,
            education=fake.text(),
            bio=fake.text(),
            languages_spoken='English, French',
        )
        specialty = Specialty.objects.create(name='Cardiology')
        self.doctor.specialties.add(specialty)

        self.appointment = Appointment.objects.create(
            user=self.user,
            doctor=self.doctor,
            date=datetime.date.today(),
            start_time=datetime.time(10, 0),
            end_time=datetime.time(10, 30),
            reason='Checkup'
        )

    def test_create_vital_sign(self):
        vital = VitalSign.objects.create(
            user=self.user,
            date_recorded=datetime.datetime.now(),
            heart_rate=80,
            systolic_pressure=120,
            diastolic_pressure=80
        )
        self.assertEqual(VitalSign.objects.count(), 1)
        self.assertEqual(vital.user, self.user)
        self.assertEqual(vital.heart_rate, 80)

    def test_create_symptom_log(self):
        symptom = SymptomLog.objects.create(
            user=self.user,
            symptom='Headache',
            date_experienced=datetime.datetime.now(),
            severity=2
        )
        self.assertEqual(SymptomLog.objects.count(), 1)
        self.assertEqual(symptom.symptom, 'Headache')

    def test_create_food_log(self):
        food = FoodLog.objects.create(
            user=self.user,
            food_item='Apple',
            meal_type='snack',
            datetime=datetime.datetime.now(),
            calories=95
        )
        self.assertEqual(FoodLog.objects.count(), 1)
        self.assertEqual(food.food_item, 'Apple')

    def test_create_exercise_log(self):
        exercise = ExerciseLog.objects.create(
            user=self.user,
            activity_type='Running',
            datetime=datetime.datetime.now(),
            duration=30
        )
        self.assertEqual(ExerciseLog.objects.count(), 1)
        self.assertEqual(exercise.activity_type, 'Running')

    def test_create_sleep_log(self):
        sleep = SleepLog.objects.create(
            user=self.user,
            sleep_time=datetime.datetime.now() - datetime.timedelta(hours=8),
            wake_time=datetime.datetime.now(),
            quality=3
        )
        self.assertEqual(SleepLog.objects.count(), 1)
        self.assertAlmostEqual(sleep.duration, 8, delta=0.1)

    def test_create_health_goal(self):
        goal = HealthGoal.objects.create(
            user=self.user,
            goal_type='weight',
            target_value=70,
            unit='kg',
            start_date=datetime.date.today(),
            target_date=datetime.date.today() + datetime.timedelta(days=30)
        )
        self.assertEqual(HealthGoal.objects.count(), 1)
        self.assertEqual(goal.goal_type, 'weight')

    def test_create_medical_document(self):
        doc = MedicalDocument.objects.create(
            user=self.user,
            uploaded_by=self.user,
            appointment=self.appointment,
            description='Lab results'
        )
        self.assertEqual(MedicalDocument.objects.count(), 1)
        self.assertEqual(doc.description, 'Lab results')
