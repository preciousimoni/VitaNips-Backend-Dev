# emergency/test_models.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from faker import Faker
from .models import EmergencyService, EmergencyContact, EmergencyAlert, EmergencyAlertContact

User = get_user_model()
fake = Faker()

class EmergencyModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email=fake.email(),
            username=fake.email(),
            password='testpassword',
            first_name=fake.first_name(),
            last_name=fake.last_name()
        )
        self.location = Point(float(fake.longitude()), float(fake.latitude()), srid=4326)

    def test_create_emergency_service(self):
        service = EmergencyService.objects.create(
            name=fake.company(),
            service_type='hospital',
            address=fake.address(),
            phone_number=fake.phone_number(),
            location=self.location,
            is_24_hours=True
        )
        self.assertEqual(EmergencyService.objects.count(), 1)
        self.assertEqual(service.name, service.__str__().split(' (')[0])
        self.assertEqual(str(service), f"{service.name} (Hospital)")

    def test_create_emergency_contact(self):
        contact = EmergencyContact.objects.create(
            user=self.user,
            name=fake.name(),
            relationship='spouse',
            phone_number=fake.phone_number(),
            is_primary=True
        )
        self.assertEqual(EmergencyContact.objects.count(), 1)
        self.assertEqual(contact.user, self.user)
        self.assertTrue(contact.is_primary)
        self.assertEqual(str(contact), f"{contact.name} (Spouse) - Contact for {self.user.email}")

    def test_create_emergency_alert(self):
        alert = EmergencyAlert.objects.create(
            user=self.user,
            location=self.location,
            message="Medical emergency, requires immediate attention."
        )
        self.assertEqual(EmergencyAlert.objects.count(), 1)
        self.assertEqual(alert.user, self.user)
        self.assertEqual(alert.status, 'active')
        self.assertIn(self.user.email, str(alert))

    def test_create_emergency_alert_contact(self):
        contact = EmergencyContact.objects.create(
            user=self.user,
            name=fake.name(),
            relationship='friend',
            phone_number=fake.phone_number()
        )
        alert = EmergencyAlert.objects.create(
            user=self.user,
            location=self.location
        )
        alert_contact = EmergencyAlertContact.objects.create(
            alert=alert,
            contact=contact
        )
        self.assertEqual(EmergencyAlertContact.objects.count(), 1)
        self.assertEqual(alert_contact.alert, alert)
        self.assertEqual(alert_contact.contact, contact)
        self.assertEqual(alert_contact.delivery_status, 'pending')
        self.assertIn(contact.name, str(alert_contact))
        self.assertIn(self.user.email, str(alert_contact))
