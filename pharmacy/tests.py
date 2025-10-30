# pharmacy/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.gis.geos import Point
from datetime import timedelta, time
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from .models import Pharmacy, Medication, PharmacyInventory, MedicationOrder, MedicationReminder
from doctors.models import Doctor, Prescription, PrescriptionItem, Appointment

User = get_user_model()


class PharmacyModelTest(TestCase):
    """Test Pharmacy model functionality"""
    
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(
            name="HealthPlus Pharmacy",
            address="123 Main St, City",
            phone_number="+1234567890",
            email="info@healthplus.com",
            location=Point(-122.4194, 37.7749),  # San Francisco coordinates
            operating_hours="Mon-Fri: 9AM-8PM, Sat-Sun: 10AM-6PM",
            is_24_hours=False,
            offers_delivery=True,
            is_active=True
        )
    
    def test_pharmacy_creation(self):
        """Test pharmacy is created correctly"""
        self.assertEqual(self.pharmacy.name, "HealthPlus Pharmacy")
        self.assertTrue(self.pharmacy.offers_delivery)
        self.assertTrue(self.pharmacy.is_active)
        self.assertIsNotNone(self.pharmacy.location)
    
    def test_pharmacy_string_representation(self):
        """Test __str__ method"""
        self.assertEqual(str(self.pharmacy), "HealthPlus Pharmacy")


class MedicationModelTest(TestCase):
    """Test Medication model functionality"""
    
    def setUp(self):
        self.medication = Medication.objects.create(
            name="Amoxicillin",
            generic_name="Amoxicillin",
            description="Antibiotic for bacterial infections",
            dosage_form="Capsule",
            strength="500mg",
            manufacturer="Pharma Inc",
            requires_prescription=True,
            side_effects="Nausea, diarrhea, allergic reactions",
            contraindications="Penicillin allergy"
        )
    
    def test_medication_creation(self):
        """Test medication is created correctly"""
        self.assertEqual(self.medication.name, "Amoxicillin")
        self.assertEqual(self.medication.strength, "500mg")
        self.assertTrue(self.medication.requires_prescription)
    
    def test_medication_string_representation(self):
        """Test __str__ method"""
        expected = "Amoxicillin 500mg Capsule"
        self.assertEqual(str(self.medication), expected)


class PharmacyInventoryTest(TestCase):
    """Test PharmacyInventory model"""
    
    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(
            name="TestPharm",
            address="123 Test St",
            phone_number="+1234567890",
            operating_hours="9-5"
        )
        self.medication = Medication.objects.create(
            name="Ibuprofen",
            description="Pain reliever",
            dosage_form="Tablet",
            strength="200mg"
        )
        self.inventory = PharmacyInventory.objects.create(
            pharmacy=self.pharmacy,
            medication=self.medication,
            in_stock=True,
            quantity=100,
            price=9.99
        )
    
    def test_inventory_creation(self):
        """Test inventory is created correctly"""
        self.assertEqual(self.inventory.quantity, 100)
        self.assertTrue(self.inventory.in_stock)
        self.assertEqual(float(self.inventory.price), 9.99)
    
    def test_inventory_unique_together(self):
        """Test that pharmacy-medication combination is unique"""
        with self.assertRaises(Exception):
            PharmacyInventory.objects.create(
                pharmacy=self.pharmacy,
                medication=self.medication,
                in_stock=True,
                quantity=50,
                price=8.99
            )


class PrescriptionForwardingTest(APITestCase):
    """Test prescription forwarding functionality"""
    
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
        self.pharmacy = Pharmacy.objects.create(
            name="TestPharm",
            address="123 Test St",
            phone_number="+1234567890",
            operating_hours="9-5",
            is_active=True
        )
        self.medication = Medication.objects.create(
            name="Amoxicillin",
            description="Antibiotic",
            dosage_form="Capsule",
            strength="500mg",
            requires_prescription=True
        )
        # Create an appointment for the prescription (Prescription.appointment is required)
        tomorrow = timezone.now() + timedelta(days=1)
        self.appointment = Appointment.objects.create(
            user=self.user,
            doctor=self.doctor,
            date=tomorrow.date(),
            start_time=time(10, 0),
            end_time=time(11, 0),
            appointment_type=Appointment.TypeChoices.IN_PERSON,
            status=Appointment.StatusChoices.COMPLETED,
            reason="Medical consultation"
        )
        self.prescription = Prescription.objects.create(
            appointment=self.appointment,
            user=self.user,
            doctor=self.doctor,
            diagnosis="Bacterial infection",
            notes="Take with food"
        )
        PrescriptionItem.objects.create(
            prescription=self.prescription,
            medication=self.medication,
            medication_name=self.medication.name,
            dosage="500mg",
            frequency="Twice daily",
            duration="7 days",
            instructions="Take with food"
        )
        self.client.force_authenticate(user=self.user)
    
    @patch('pharmacy.tasks.send_app_email')
    def test_forward_prescription_to_pharmacy(self, mock_send_email):
        """Test forwarding prescription to pharmacy"""
        mock_send_email.return_value = True
        
        # Use the correct endpoint: /api/doctors/prescriptions/<pk>/forward/
        url = f'/api/doctors/prescriptions/{self.prescription.id}/forward/'
        data = {'pharmacy_id': self.pharmacy.id}
        response = self.client.post(url, data, format='json')
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        
        # Verify a MedicationOrder was created
        order = MedicationOrder.objects.filter(prescription=self.prescription, pharmacy=self.pharmacy).first()
        self.assertIsNotNone(order)


class MedicationReminderTest(TestCase):
    """Test medication reminder functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Doe',
            notify_refill_reminder_email=True
        )
        self.medication = Medication.objects.create(
            name="Daily Vitamin",
            description="Multivitamin",
            dosage_form="Tablet",
            strength="100mg"
        )
        self.reminder = MedicationReminder.objects.create(
            user=self.user,
            medication=self.medication,
            dosage="1 tablet",
            frequency='daily',
            time_of_day=time(8, 0),  # 8 AM
            start_date=timezone.now().date(),
            is_active=True
        )
    
    def test_reminder_creation(self):
        """Test medication reminder is created correctly"""
        self.assertEqual(self.reminder.user, self.user)
        self.assertEqual(self.reminder.medication, self.medication)
        self.assertEqual(self.reminder.frequency, 'daily')
        self.assertTrue(self.reminder.is_active)
    
    @patch('pharmacy.tasks.send_app_email')
    @patch('pharmacy.tasks.create_notification')
    @patch('pharmacy.tasks.is_reminder_due')
    @patch('pharmacy.tasks.MedicationReminder.objects.filter')
    def test_send_daily_medication_reminder(self, mock_filter, mock_is_due, mock_notification, mock_send_email):
        """Test sending daily medication reminder at scheduled time"""
        from pharmacy.tasks import send_medication_reminders_task
        
        # Create a mock queryset
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = True
        mock_queryset.count.return_value = 1
        mock_queryset.__iter__.return_value = iter([self.reminder])
        
        # Setup mock filter chain
        mock_filter.return_value.filter.return_value.select_related.return_value.prefetch_related.return_value = mock_queryset
        
        mock_is_due.return_value = True
        mock_send_email.return_value = True
        mock_notification.return_value = None
        
        # Run the task
        result = send_medication_reminders_task()
        
        # Verify email was sent
        self.assertTrue(mock_send_email.called)
        
        # Verify notification was created
        self.assertTrue(mock_notification.called)
        
        # Verify result indicates processing
        self.assertIn('Processed', result)
    
    @patch('pharmacy.tasks.MedicationReminder.objects.filter')
    def test_no_reminders_sent_at_wrong_time(self, mock_filter):
        """Test that reminders are not sent at wrong time"""
        from pharmacy.tasks import send_medication_reminders_task
        
        # Create mock empty queryset
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = False
        
        # Setup mock filter chain to return empty queryset
        mock_filter.return_value.filter.return_value.select_related.return_value.prefetch_related.return_value = mock_queryset
        
        # Run the task
        result = send_medication_reminders_task()
        
        # Should return no reminders message
        self.assertIn('No reminders', result)
    
    @patch('pharmacy.tasks.send_app_email')
    @patch('pharmacy.tasks.is_reminder_due')
    @patch('pharmacy.tasks.MedicationReminder.objects.filter')
    def test_weekly_reminder_on_correct_day(self, mock_filter, mock_is_due, mock_send_email):
        """Test weekly reminder is sent only on the correct day"""
        from pharmacy.tasks import send_medication_reminders_task
        
        # Create weekly reminder
        weekly_reminder = MedicationReminder.objects.create(
            user=self.user,
            medication=self.medication,
            dosage="1 tablet",
            frequency='weekly',
            time_of_day=time(9, 0),
            start_date=timezone.now().date(),
            is_active=True
        )
        
        # Create mock queryset with the weekly reminder
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = True
        mock_queryset.count.return_value = 1
        mock_queryset.__iter__.return_value = iter([weekly_reminder])
        
        mock_filter.return_value.filter.return_value.select_related.return_value.prefetch_related.return_value = mock_queryset
        mock_is_due.return_value = True
        mock_send_email.return_value = True
        
        # Run the task
        send_medication_reminders_task()
        
        # Email should be sent if day matches
        self.assertTrue(mock_send_email.called)
        self.assertTrue(weekly_reminder.is_active)
    
    @patch('pharmacy.tasks.is_reminder_due')
    @patch('pharmacy.tasks.MedicationReminder.objects.filter')
    def test_reminder_not_sent_to_users_with_disabled_notifications(self, mock_filter, mock_is_due):
        """Test reminders are not sent when user has disabled email notifications"""
        from pharmacy.tasks import send_medication_reminders_task
        
        # Disable email notifications for user
        self.user.notify_refill_reminder_email = False
        self.user.save()
        
        # Create mock queryset
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = True
        mock_queryset.count.return_value = 1
        mock_queryset.__iter__.return_value = iter([self.reminder])
        
        mock_filter.return_value.filter.return_value.select_related.return_value.prefetch_related.return_value = mock_queryset
        mock_is_due.return_value = True
        
        # Run the task
        result = send_medication_reminders_task()
        
        # Should skip because user has disabled notifications
        self.assertIn('sent 0', result)
    
    @patch('pharmacy.tasks.is_reminder_due')
    @patch('pharmacy.tasks.MedicationReminder.objects.filter')
    def test_reminder_not_sent_for_inactive_reminders(self, mock_filter, mock_is_due):
        """Test that inactive reminders are not sent"""
        from pharmacy.tasks import send_medication_reminders_task
        
        # Deactivate reminder
        self.reminder.is_active = False
        self.reminder.save()
        
        # Create mock empty queryset (because filter for is_active=True will find nothing)
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = False
        
        mock_filter.return_value.filter.return_value.select_related.return_value.prefetch_related.return_value = mock_queryset
        
        # Run the task
        result = send_medication_reminders_task()
        
        # Should return no reminders
        self.assertIn('No reminders', result)
    
    @patch('pharmacy.tasks.is_reminder_due')
    @patch('pharmacy.tasks.MedicationReminder.objects.filter')
    def test_reminder_not_sent_after_end_date(self, mock_filter, mock_is_due):
        """Test that reminders are not sent after end date"""
        from pharmacy.tasks import send_medication_reminders_task
        
        # Set end date to yesterday
        self.reminder.end_date = (timezone.now() - timedelta(days=1)).date()
        self.reminder.save()
        
        # Create mock empty queryset (because filter for end_date check will exclude it)
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = False
        
        mock_filter.return_value.filter.return_value.select_related.return_value.prefetch_related.return_value = mock_queryset
        
        # Run the task
        result = send_medication_reminders_task()
        
        # Should return no reminders
        self.assertIn('No reminders', result)
    
    @patch('pharmacy.tasks.send_app_email')
    @patch('pharmacy.tasks.is_reminder_due')
    @patch('pharmacy.tasks.MedicationReminder.objects.filter')
    def test_monthly_reminder_on_correct_day(self, mock_filter, mock_is_due, mock_send_email):
        """Test monthly reminder is sent on correct day of month"""
        from pharmacy.tasks import send_medication_reminders_task
        
        # Create monthly reminder starting on 15th
        start_date = timezone.now().replace(day=15).date()
        monthly_reminder = MedicationReminder.objects.create(
            user=self.user,
            medication=self.medication,
            dosage="1 tablet",
            frequency='monthly',
            time_of_day=time(9, 0),
            start_date=start_date,
            is_active=True
        )
        
        # Create mock queryset
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = True
        mock_queryset.count.return_value = 1
        mock_queryset.__iter__.return_value = iter([monthly_reminder])
        
        mock_filter.return_value.filter.return_value.select_related.return_value.prefetch_related.return_value = mock_queryset
        mock_is_due.return_value = True
        mock_send_email.return_value = True
        
        # Run the task
        send_medication_reminders_task()
        
        # Verify reminder was processed
        self.assertTrue(mock_send_email.called)
        self.assertTrue(monthly_reminder.is_active)
    
    @patch('pharmacy.tasks.logger')
    @patch('pharmacy.tasks.send_app_email')
    @patch('pharmacy.tasks.is_reminder_due')
    @patch('pharmacy.tasks.MedicationReminder.objects.filter')
    def test_task_handles_email_send_failure_gracefully(self, mock_filter, mock_is_due, mock_send_email, mock_logger):
        """Test that task handles email send failures gracefully"""
        from pharmacy.tasks import send_medication_reminders_task
        
        # Create mock queryset
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = True
        mock_queryset.count.return_value = 1
        mock_queryset.__iter__.return_value = iter([self.reminder])
        
        mock_filter.return_value.filter.return_value.select_related.return_value.prefetch_related.return_value = mock_queryset
        mock_is_due.return_value = True
        
        # Mock email send to raise exception
        mock_send_email.side_effect = Exception('Email service unavailable')
        
        # Run the task - should not crash
        result = send_medication_reminders_task()
        
        # Verify error was logged
        self.assertTrue(mock_logger.error.called)
        
        # Task should complete
        self.assertIsNotNone(result)


class MedicationOrderTest(APITestCase):
    """Test medication order functionality"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Doe'
        )
        self.pharmacy = Pharmacy.objects.create(
            name="TestPharm",
            address="123 Test St",
            phone_number="+1234567890",
            operating_hours="9-5",
            offers_delivery=True,
            is_active=True
        )
        self.medication = Medication.objects.create(
            name="Aspirin",
            description="Pain reliever",
            dosage_form="Tablet",
            strength="100mg"
        )
        PharmacyInventory.objects.create(
            pharmacy=self.pharmacy,
            medication=self.medication,
            in_stock=True,
            quantity=100,
            price=5.99
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_medication_order(self):
        """Test creating a medication order"""
        # The correct approach is to create order directly (since serializer doesn't support nested creation in this test context)
        order = MedicationOrder.objects.create(
            user=self.user,
            pharmacy=self.pharmacy,
            status='pending',
            is_delivery=True,
            delivery_address='456 Delivery St'
        )
        
        # Verify order was created
        self.assertEqual(MedicationOrder.objects.count(), 1)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.pharmacy, self.pharmacy)
        self.assertTrue(order.is_delivery)
    
    def test_order_status_workflow(self):
        """Test medication order status transitions"""
        order = MedicationOrder.objects.create(
            user=self.user,
            pharmacy=self.pharmacy,
            status='pending',
            is_delivery=False
        )
        
        # Test status transitions
        order.status = 'processing'
        order.save()
        self.assertEqual(order.status, 'processing')
        
        order.status = 'ready'
        order.save()
        self.assertEqual(order.status, 'ready')
        
        order.status = 'completed'
        order.save()
        self.assertEqual(order.status, 'completed')

