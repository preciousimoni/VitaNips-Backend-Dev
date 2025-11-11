# pharmacy/test_views.py
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from decimal import Decimal
from pharmacy.models import Pharmacy, Medication, MedicationOrder, MedicationOrderItem
from doctors.models import Doctor, Specialty, Appointment, Prescription, PrescriptionItem

User = get_user_model()

class PharmacyAPITests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='password123')
        self.doctor_user = User.objects.create_user(username='testdoctor', email='testdoctor@example.com', password='password123')
        
        self.specialty = Specialty.objects.create(name='Testing')
        self.doctor = Doctor.objects.create(user=self.doctor_user, first_name='Doc', last_name='Test', consultation_fee=150.00)
        self.doctor.specialties.add(self.specialty)

        self.appointment = Appointment.objects.create(
            user=self.user,
            doctor=self.doctor,
            date='2025-11-20',
            start_time='10:00:00',
            end_time='10:30:00',
            reason='Consultation for API testing'
        )

        self.prescription = Prescription.objects.create(
            appointment=self.appointment,
            user=self.user,
            doctor=self.doctor,
            diagnosis='API-induced headache'
        )

        self.pharmacy = Pharmacy.objects.create(
            name='API Test Pharmacy',
            address='123 API Lane',
            phone_number='9876543210',
            location=Point(-74.0060, 40.7128, srid=4326), # NYC
            operating_hours='24/7',
            is_24_hours=True
        )
        self.medication = Medication.objects.create(
            name='Testocillin',
            description='Cures API headaches',
            dosage_form='Capsule',
            strength='500mg'
        )
        self.prescription_item = PrescriptionItem.objects.create(
            prescription=self.prescription,
            medication_name='Testocillin',
            dosage='500mg',
            frequency='As needed',
            duration='1 week',
            instructions='Take one when tests fail'
        )

    def test_list_pharmacies(self):
        url = reverse('pharmacy-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'API Test Pharmacy')

    def test_retrieve_pharmacy(self):
        url = reverse('pharmacy-detail', kwargs={'pk': self.pharmacy.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.pharmacy.name)

    def test_list_medications(self):
        url = reverse('medication-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Testocillin')

    def test_create_medication_order(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('medication-order-list')
        data = {
            'pharmacy': self.pharmacy.pk,
            'prescription': self.prescription.pk,
            'is_delivery': False,
            'items': [
                {
                    'prescription_item': self.prescription_item.pk,
                    'quantity': 1
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MedicationOrder.objects.count(), 1)
        order = MedicationOrder.objects.first()
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().prescription_item, self.prescription_item)

    def test_unauthenticated_user_cannot_order(self):
        url = reverse('medication-order-list')
        data = {'pharmacy': self.pharmacy.pk, 'prescription': self.prescription.pk}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
