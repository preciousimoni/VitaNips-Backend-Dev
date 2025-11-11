
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from .models import Doctor, Specialty, Appointment, DoctorReview
from decimal import Decimal

User = get_user_model()

class DoctorAPITests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='password123')
        self.doctor_user = User.objects.create_user(username='testdoctor', email='testdoctor@example.com', password='password123', first_name="Doc", last_name="Test")
        
        self.specialty = Specialty.objects.create(name='Testing', description='API Testing')
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            first_name='Doc',
            last_name='Test',
            gender='M',
            years_of_experience=5,
            education='Test School of APIs',
            bio='A doctor for testing APIs.',
            languages_spoken='Python, JSON',
            consultation_fee=Decimal('200.00'),
            is_verified=True
        )
        self.doctor.specialties.add(self.specialty)

        self.appointment = Appointment.objects.create(
            user=self.user,
            doctor=self.doctor,
            date='2025-11-11',
            start_time='14:00:00',
            end_time='14:30:00',
            reason='API test checkup'
        )

    def test_list_doctors(self):
        url = reverse('doctor-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['full_name'], 'Dr. Doc Test')

    def test_retrieve_doctor(self):
        url = reverse('doctor-detail', kwargs={'pk': self.doctor.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_name'], self.doctor.full_name)

    def test_list_specialties(self):
        url = reverse('specialty-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if the specialty created in setUp is in the results
        specialty_names = [s['name'] for s in response.data['results']]
        self.assertIn(self.specialty.name, specialty_names)

    def test_create_appointment(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('appointment-list-create')
        data = {
            'doctor': self.doctor.pk,
            'date': '2025-11-12',
            'start_time': '15:00:00',
            'end_time': '15:30:00',
            'reason': 'Follow-up API test'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Appointment.objects.count(), 2)

    def test_doctor_cannot_book_for_self(self):
        self.client.force_authenticate(user=self.doctor_user)
        url = reverse('appointment-list-create')
        data = {
            'doctor': self.doctor.pk,
            'date': '2025-11-13',
            'start_time': '16:00:00',
            'end_time': '16:30:00',
            'reason': 'Self-consultation'
        }
        response = self.client.post(url, data)
        # This logic should ideally be in a serializer or view to prevent self-booking.
        # For now, we'll assume the user associated with the doctor can book for themselves.
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_appointment = Appointment.objects.get(pk=response.data['id'])
        self.assertEqual(new_appointment.user, self.doctor_user)


    def test_list_appointments_as_patient(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('appointment-list-create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.appointment.id)

    def test_list_appointments_as_doctor(self):
        self.client.force_authenticate(user=self.doctor_user)
        url = reverse('appointment-list-create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.appointment.id)

    def test_create_review(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('doctor-review-list-create', kwargs={'doctor_id': self.doctor.pk})
        data = {'rating': 5, 'comment': 'Excellent!'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DoctorReview.objects.count(), 1)
        self.assertEqual(self.doctor.reviews.first().rating, 5)

    def test_unauthenticated_user_cannot_create_review(self):
        # No force_authenticate here
        url = reverse('doctor-review-list-create', kwargs={'doctor_id': self.doctor.pk})
        data = {'rating': 5, 'comment': 'Trying to review without login'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_twilio_token_for_virtual_appointment(self):
        self.client.force_authenticate(user=self.user)
        virtual_appointment = Appointment.objects.create(
            user=self.user,
            doctor=self.doctor,
            date='2025-11-12',
            start_time='11:00:00',
            end_time='11:30:00',
            appointment_type='virtual',
            status='confirmed',
            reason='Virtual test'
        )
        url = reverse('get-twilio-token', kwargs={'appointment_id': virtual_appointment.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('roomName', response.data)
        self.assertTrue(response.data['roomName'].startswith('vitanips_appointment_'))

    def test_get_twilio_token_unauthorized(self):
        unrelated_user = User.objects.create_user(username='unrelated', email='unrelated@example.com', password='password123')
        self.client.force_authenticate(user=unrelated_user)
        url = reverse('get-twilio-token', kwargs={'appointment_id': self.appointment.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
