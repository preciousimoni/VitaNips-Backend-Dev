# pharmacy/test_models.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from decimal import Decimal
from pharmacy.models import Pharmacy, Medication, PharmacyInventory, MedicationOrder, MedicationOrderItem, MedicationReminder
from doctors.models import Doctor, Prescription, PrescriptionItem, Specialty, Appointment

User = get_user_model()

class PharmacyModelsTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='password123')
        self.doctor_user = User.objects.create_user(username='testdoctor', email='testdoctor@example.com', password='password123')
        self.specialty = Specialty.objects.create(name='Cardiology', description='Heart related issues')
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            first_name='John',
            last_name='Doe',
            consultation_fee=100.00
        )
        self.doctor.specialties.add(self.specialty)

        self.appointment = Appointment.objects.create(
            user=self.user,
            doctor=self.doctor,
            date='2025-01-01',
            start_time='10:00:00',
            end_time='10:30:00',
            reason='Test appointment'
        )

        self.pharmacy = Pharmacy.objects.create(
            name='Test Pharmacy',
            address='123 Test St',
            phone_number='1234567890',
            location=Point(-73.9857, 40.7484, srid=4326), # New York City
            operating_hours='9am-5pm',
            is_24_hours=False,
            offers_delivery=True
        )
        self.medication = Medication.objects.create(
            name='TestMed',
            description='A medication for testing',
            dosage_form='Tablet',
            strength='500mg',
            requires_prescription=True
        )
        self.inventory_item = PharmacyInventory.objects.create(
            pharmacy=self.pharmacy,
            medication=self.medication,
            quantity=100,
            price=Decimal('19.99')
        )
        self.prescription = Prescription.objects.create(
            appointment=self.appointment,
            user=self.user,
            doctor=self.doctor,
            diagnosis='Hypertension'
        )
        self.prescription_item = PrescriptionItem.objects.create(
            prescription=self.prescription,
            medication_name='TestMed',
            dosage='500mg',
            frequency='Once a day',
            duration='30 days',
            instructions='Take one tablet daily.'
        )
        self.order = MedicationOrder.objects.create(
            user=self.user,
            pharmacy=self.pharmacy,
            prescription=self.prescription,
            status='pending',
            is_delivery=True,
            delivery_address='456 Test Ave'
        )
        self.order_item = MedicationOrderItem.objects.create(
            order=self.order,
            prescription_item=self.prescription_item,
            medication_name_text='TestMed 500mg',
            quantity=1,
            price_per_unit=Decimal('19.99')
        )

    def test_pharmacy_creation(self):
        self.assertEqual(self.pharmacy.name, 'Test Pharmacy')
        self.assertEqual(str(self.pharmacy), 'Test Pharmacy')
        self.assertEqual(self.pharmacy.location.srid, 4326)

    def test_medication_creation(self):
        self.assertEqual(self.medication.name, 'TestMed')
        self.assertEqual(str(self.medication), 'TestMed 500mg Tablet')

    def test_pharmacy_inventory_creation(self):
        self.assertEqual(self.inventory_item.pharmacy, self.pharmacy)
        self.assertEqual(self.inventory_item.medication, self.medication)
        self.assertEqual(self.inventory_item.quantity, 100)
        self.assertTrue(self.inventory_item.in_stock)
        self.assertEqual(str(self.inventory_item), "Test Pharmacy - TestMed - In Stock")

    def test_medication_order_creation(self):
        self.assertEqual(self.order.user, self.user)
        self.assertEqual(self.order.pharmacy, self.pharmacy)
        self.assertEqual(self.order.status, 'pending')
        self.assertTrue(self.order.is_delivery)
        self.assertEqual(str(self.order), f"Order {self.order.id} - {self.user.email} - pending")

    def test_medication_order_item_creation(self):
        self.assertEqual(self.order_item.order, self.order)
        self.assertEqual(self.order_item.quantity, 1)
        self.assertEqual(self.order_item.total_price, Decimal('19.99'))
        self.assertEqual(str(self.order_item), f"Order {self.order.id} - TestMed 500mg")

    def test_medication_reminder_creation(self):
        reminder = MedicationReminder.objects.create(
            user=self.user,
            medication=self.medication,
            prescription_item=self.prescription_item,
            start_date='2025-01-01',
            time_of_day='09:00:00',
            frequency='daily',
            dosage='1 tablet'
        )
        self.assertEqual(reminder.user, self.user)
        self.assertEqual(reminder.medication, self.medication)
        self.assertEqual(reminder.frequency, 'daily')
        self.assertEqual(str(reminder), f"{self.user.email} - {self.medication.name} - 09:00:00")
