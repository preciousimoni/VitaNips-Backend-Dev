
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import Specialty, Doctor, DoctorReview, DoctorAvailability, Appointment, Prescription, PrescriptionItem, VirtualSession
from pharmacy.models import Medication

User = get_user_model()

class DoctorModelsTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='password')
        self.doctor_user = User.objects.create_user(username='testdoctor', email='testdoctor@example.com', password='password')
        self.specialty = Specialty.objects.create(name='Cardiology', description='Heart related issues')
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            first_name='John',
            last_name='Doe',
            gender='M',
            years_of_experience=10,
            education='MD from Test University',
            bio='A test doctor.',
            languages_spoken='English',
            consultation_fee=Decimal('100.00')
        )
        self.doctor.specialties.add(self.specialty)

    def test_specialty_creation(self):
        self.assertEqual(str(self.specialty), 'Cardiology')
        self.assertEqual(self.specialty.description, 'Heart related issues')

    def test_doctor_creation(self):
        self.assertEqual(str(self.doctor), 'Dr. John Doe')
        self.assertEqual(self.doctor.full_name, 'Dr. John Doe')
        self.assertEqual(self.doctor.user.email, 'testdoctor@example.com')
        self.assertIn(self.specialty, self.doctor.specialties.all())

    def test_doctor_average_rating(self):
        self.assertEqual(self.doctor.average_rating, 0)
        DoctorReview.objects.create(doctor=self.doctor, user=self.user, rating=5)
        self.assertEqual(self.doctor.average_rating, 5)
        another_user = User.objects.create_user(username='anotheruser', email='another@example.com', password='password')
        DoctorReview.objects.create(doctor=self.doctor, user=another_user, rating=3)
        self.assertEqual(self.doctor.average_rating, 4)

    def test_doctor_review_creation(self):
        review = DoctorReview.objects.create(doctor=self.doctor, user=self.user, rating=4, comment='Good doctor.')
        self.assertEqual(str(review), f"{self.user.email} - {self.doctor.full_name} - 4")
        self.assertEqual(review.comment, 'Good doctor.')

    def test_doctor_review_unique_constraint(self):
        DoctorReview.objects.create(doctor=self.doctor, user=self.user, rating=4)
        with self.assertRaises(Exception): # IntegrityError
            DoctorReview.objects.create(doctor=self.doctor, user=self.user, rating=5)

    def test_doctor_availability_creation(self):
        availability = DoctorAvailability.objects.create(
            doctor=self.doctor,
            day_of_week=0, # Monday
            start_time='09:00:00',
            end_time='17:00:00'
        )
        self.assertEqual(str(availability), f"{self.doctor.full_name} - Monday (09:00:00 - 17:00:00)")

    def test_appointment_creation(self):
        appointment = Appointment.objects.create(
            user=self.user,
            doctor=self.doctor,
            date='2025-12-25',
            start_time='10:00:00',
            end_time='10:30:00',
            reason='Checkup'
        )
        self.assertEqual(str(appointment), f"{self.user.email} - {self.doctor.full_name} - 2025-12-25 10:00:00")
        self.assertEqual(appointment.status, 'scheduled')

    def test_prescription_creation(self):
        appointment = Appointment.objects.create(
            user=self.user,
            doctor=self.doctor,
            date='2025-12-25',
            start_time='10:00:00',
            end_time='10:30:00',
            reason='Checkup'
        )
        prescription = Prescription.objects.create(
            appointment=appointment,
            user=self.user,
            doctor=self.doctor,
            diagnosis='Common Cold'
        )
        self.assertEqual(str(prescription), f"Prescription for {self.user.email} by {self.doctor.full_name}")

    def test_prescription_item_creation(self):
        appointment = Appointment.objects.create(
            user=self.user,
            doctor=self.doctor,
            date='2025-12-25',
            start_time='10:00:00',
            end_time='10:30:00',
            reason='Checkup'
        )
        prescription = Prescription.objects.create(
            appointment=appointment,
            user=self.user,
            doctor=self.doctor,
            diagnosis='Common Cold'
        )
        medication = Medication.objects.create(name='TestMed', description='A test med', dosage_form='Tablet', strength='100mg')
        item = PrescriptionItem.objects.create(
            prescription=prescription,
            medication=medication,
            medication_name='TestMed',
            dosage='1 tablet',
            frequency='daily',
            duration='7 days',
            instructions='Take with water'
        )
        self.assertIn('TestMed', str(item))

    def test_virtual_session_creation(self):
        appointment = Appointment.objects.create(
            user=self.user,
            doctor=self.doctor,
            date='2025-12-25',
            start_time='10:00:00',
            end_time='10:30:00',
            appointment_type='virtual',
            reason='Virtual Checkup'
        )
        session = VirtualSession.objects.create(appointment=appointment)
        self.assertTrue(session.room_name.startswith(f"vitanips-{appointment.id}-"))
        self.assertEqual(session.status, 'scheduled')
        self.assertEqual(str(session), f"Virtual Session for Appointment #{appointment.id} - scheduled")
