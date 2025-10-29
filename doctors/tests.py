# doctors/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta, time
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from .models import Doctor, Specialty, DoctorAvailability, Appointment, DoctorReview
from .tasks import send_appointment_reminders_task

User = get_user_model()


class DoctorModelTest(TestCase):
    """Test Doctor model functionality"""
    
    def setUp(self):
        self.specialty = Specialty.objects.create(
            name="Cardiology",
            description="Heart specialist"
        )
        self.doctor = Doctor.objects.create(
            first_name="John",
            last_name="Smith",
            gender="M",
            years_of_experience=10,
            education="MD from Harvard Medical School",
            bio="Experienced cardiologist",
            languages_spoken="English, Spanish",
            consultation_fee=150.00,
            is_available_for_virtual=True,
            is_verified=True
        )
        self.doctor.specialties.add(self.specialty)
    
    def test_doctor_creation(self):
        """Test doctor is created correctly"""
        self.assertEqual(self.doctor.first_name, "John")
        self.assertEqual(self.doctor.last_name, "Smith")
        self.assertEqual(self.doctor.gender, "M")
        self.assertTrue(self.doctor.is_verified)
    
    def test_doctor_full_name_property(self):
        """Test full_name property"""
        self.assertEqual(self.doctor.full_name, "Dr. John Smith")
    
    def test_doctor_string_representation(self):
        """Test __str__ method"""
        self.assertEqual(str(self.doctor), "Dr. John Smith")
    
    def test_doctor_average_rating_no_reviews(self):
        """Test average_rating property with no reviews"""
        self.assertEqual(self.doctor.average_rating, 0)
    
    def test_doctor_average_rating_with_reviews(self):
        """Test average_rating property with reviews"""
        user1 = User.objects.create_user(
            username='patient1',
            email='patient1@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Doe'
        )
        user2 = User.objects.create_user(
            username='patient2',
            email='patient2@test.com',
            password='testpass123',
            first_name='Bob',
            last_name='Wilson'
        )
        
        DoctorReview.objects.create(doctor=self.doctor, user=user1, rating=5, comment="Excellent!")
        DoctorReview.objects.create(doctor=self.doctor, user=user2, rating=4, comment="Very good")
        
        self.assertEqual(self.doctor.average_rating, 4.5)


class AppointmentModelTest(TestCase):
    """Test Appointment model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Doe'
        )
        self.doctor = Doctor.objects.create(
            first_name="Sarah",
            last_name="Johnson",
            gender="F",
            years_of_experience=8,
            education="MD",
            bio="General practitioner",
            languages_spoken="English"
        )
        self.tomorrow = timezone.now() + timedelta(days=1)
        self.appointment = Appointment.objects.create(
            user=self.user,
            doctor=self.doctor,
            date=self.tomorrow.date(),
            start_time=time(10, 0),
            end_time=time(11, 0),
            appointment_type=Appointment.TypeChoices.IN_PERSON,
            status=Appointment.StatusChoices.SCHEDULED,
            reason="Annual checkup"
        )
    
    def test_appointment_creation(self):
        """Test appointment is created correctly"""
        self.assertEqual(self.appointment.user, self.user)
        self.assertEqual(self.appointment.doctor, self.doctor)
        self.assertEqual(self.appointment.status, Appointment.StatusChoices.SCHEDULED)
        self.assertEqual(self.appointment.appointment_type, Appointment.TypeChoices.IN_PERSON)
    
    def test_appointment_string_representation(self):
        """Test __str__ method"""
        expected = f"{self.user.email} with {self.doctor.full_name} on {self.appointment.date}"
        self.assertEqual(str(self.appointment), expected)
    
    def test_appointment_status_choices(self):
        """Test all status choices are valid"""
        for status_choice in Appointment.StatusChoices:
            self.appointment.status = status_choice
            self.appointment.save()
            self.assertEqual(self.appointment.status, status_choice)


class AppointmentAPITest(APITestCase):
    """Test Appointment API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Doe'
        )
        self.doctor = Doctor.objects.create(
            first_name="Sarah",
            last_name="Johnson",
            gender="F",
            years_of_experience=8,
            education="MD",
            bio="General practitioner",
            languages_spoken="English"
        )
        # Create availability for tomorrow
        tomorrow_weekday = (timezone.now() + timedelta(days=1)).weekday()
        DoctorAvailability.objects.create(
            doctor=self.doctor,
            day_of_week=tomorrow_weekday,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_available=True
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_appointment(self):
        """Test creating a new appointment"""
        tomorrow = timezone.now() + timedelta(days=1)
        url = '/api/appointments/'
        data = {
            'doctor': self.doctor.id,
            'date': tomorrow.date().isoformat(),
            'start_time': '10:00',
            'end_time': '11:00',
            'appointment_type': 'in_person',
            'reason': 'Regular checkup'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Appointment.objects.count(), 1)
        appointment = Appointment.objects.first()
        self.assertEqual(appointment.user, self.user)
        self.assertEqual(appointment.doctor, self.doctor)
        self.assertEqual(appointment.reason, 'Regular checkup')
    
    def test_list_user_appointments(self):
        """Test listing user's appointments"""
        tomorrow = timezone.now() + timedelta(days=1)
        Appointment.objects.create(
            user=self.user,
            doctor=self.doctor,
            date=tomorrow.date(),
            start_time=time(10, 0),
            end_time=time(11, 0),
            appointment_type=Appointment.TypeChoices.IN_PERSON,
            status=Appointment.StatusChoices.SCHEDULED,
            reason="Test appointment"
        )
        
        url = '/api/appointments/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_cancel_appointment(self):
        """Test cancelling an appointment"""
        tomorrow = timezone.now() + timedelta(days=1)
        appointment = Appointment.objects.create(
            user=self.user,
            doctor=self.doctor,
            date=tomorrow.date(),
            start_time=time(10, 0),
            end_time=time(11, 0),
            appointment_type=Appointment.TypeChoices.IN_PERSON,
            status=Appointment.StatusChoices.SCHEDULED,
            reason="Test appointment"
        )
        
        url = f'/api/appointments/{appointment.id}/cancel/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.StatusChoices.CANCELLED)
    
    def test_cannot_create_past_appointment(self):
        """Test that appointments cannot be created in the past"""
        yesterday = timezone.now() - timedelta(days=1)
        url = '/api/appointments/'
        data = {
            'doctor': self.doctor.id,
            'date': yesterday.date().isoformat(),
            'start_time': '10:00',
            'end_time': '11:00',
            'appointment_type': 'in_person',
            'reason': 'Test'
        }
        response = self.client.post(url, data, format='json')
        
        # Should fail validation
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_201_CREATED])


class AppointmentReminderTaskTest(TestCase):
    """Test appointment reminder Celery task"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Doe',
            phone_number='+1234567890',
            notify_appointment_reminder_email=True,
            notify_appointment_reminder_sms=True
        )
        self.doctor = Doctor.objects.create(
            first_name="Sarah",
            last_name="Johnson",
            gender="F",
            years_of_experience=8,
            education="MD",
            bio="General practitioner",
            languages_spoken="English"
        )
    
    @patch('doctors.tasks.send_app_email')
    @patch('doctors.tasks.send_sms')
    def test_send_reminders_for_upcoming_appointments(self, mock_send_sms, mock_send_app_email):
        """Test that reminders are sent for appointments in the next 24 hours"""
        # Create appointment 12 hours from now
        future_time = timezone.now() + timedelta(hours=12)
        appointment = Appointment.objects.create(
            user=self.user,
            doctor=self.doctor,
            date=future_time.date(),
            start_time=future_time.time(),
            end_time=(future_time + timedelta(hours=1)).time(),
            appointment_type=Appointment.TypeChoices.IN_PERSON,
            status=Appointment.StatusChoices.SCHEDULED,
            reason="Test appointment"
        )
        
        # Mock successful sends
        mock_send_app_email.return_value = True
        mock_send_sms.return_value = True
        
        # Run the task
        send_appointment_reminders_task()
        
        # Verify email and SMS were called
        self.assertTrue(mock_send_app_email.called)
        self.assertTrue(mock_send_sms.called)
        
        # Refresh appointment
        appointment.refresh_from_db()
        self.assertTrue(appointment.reminder_sent)
    
    @patch('doctors.tasks.send_app_email')
    def test_no_reminders_for_distant_appointments(self, mock_send_email):
        """Test that reminders are not sent for appointments more than 24 hours away"""
        # Create appointment 3 days from now
        future_time = timezone.now() + timedelta(days=3)
        Appointment.objects.create(
            user=self.user,
            doctor=self.doctor,
            date=future_time.date(),
            start_time=future_time.time(),
            end_time=(future_time + timedelta(hours=1)).time(),
            appointment_type=Appointment.TypeChoices.IN_PERSON,
            status=Appointment.StatusChoices.SCHEDULED,
            reason="Test appointment"
        )
        
        # Run the task
        send_appointment_reminders_task()
        
        # Email should not be sent
        self.assertFalse(mock_send_email.called)


class DoctorAvailabilityTest(TestCase):
    """Test DoctorAvailability model"""
    
    def setUp(self):
        self.doctor = Doctor.objects.create(
            first_name="Sarah",
            last_name="Johnson",
            gender="F",
            years_of_experience=8,
            education="MD",
            bio="General practitioner",
            languages_spoken="English"
        )
    
    def test_create_availability(self):
        """Test creating doctor availability"""
        availability = DoctorAvailability.objects.create(
            doctor=self.doctor,
            day_of_week=0,  # Monday
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_available=True
        )
        
        self.assertEqual(availability.doctor, self.doctor)
        self.assertEqual(availability.day_of_week, 0)
        self.assertTrue(availability.is_available)
    
    def test_availability_string_representation(self):
        """Test __str__ method"""
        availability = DoctorAvailability.objects.create(
            doctor=self.doctor,
            day_of_week=0,
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        expected = f"{self.doctor.full_name} - Monday (09:00:00 - 17:00:00)"
        self.assertEqual(str(availability), expected)

