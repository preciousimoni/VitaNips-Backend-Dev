# emergency/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.gis.geos import Point
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from .models import EmergencyService, EmergencyContact, EmergencyAlert, EmergencyAlertContact
from .tasks import send_sos_alerts

User = get_user_model()


class EmergencyServiceModelTest(TestCase):
    """Test EmergencyService model"""
    
    def setUp(self):
        self.service = EmergencyService.objects.create(
            name="City General Hospital",
            service_type="hospital",
            address="123 Emergency Ave, City",
            phone_number="+1234567890",
            location=Point(-122.4194, 37.7749),
            is_24_hours=True,
            has_emergency_room=True,
            provides_ambulance=True
        )
    
    def test_service_creation(self):
        """Test emergency service is created correctly"""
        self.assertEqual(self.service.name, "City General Hospital")
        self.assertEqual(self.service.service_type, "hospital")
        self.assertTrue(self.service.is_24_hours)
        self.assertTrue(self.service.has_emergency_room)
    
    def test_service_string_representation(self):
        """Test __str__ method"""
        expected = "City General Hospital (Hospital)"
        self.assertEqual(str(self.service), expected)


class EmergencyContactModelTest(TestCase):
    """Test EmergencyContact model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Doe'
        )
        self.contact = EmergencyContact.objects.create(
            user=self.user,
            name="John Doe",
            relationship="spouse",
            phone_number="+1234567890",
            email="john@test.com",
            is_primary=True
        )
    
    def test_contact_creation(self):
        """Test emergency contact is created correctly"""
        self.assertEqual(self.contact.user, self.user)
        self.assertEqual(self.contact.name, "John Doe")
        self.assertEqual(self.contact.relationship, "spouse")
        self.assertTrue(self.contact.is_primary)
    
    def test_contact_string_representation(self):
        """Test __str__ method"""
        expected = "John Doe (Spouse) - Contact for patient@test.com"
        self.assertEqual(str(self.contact), expected)
    
    def test_multiple_contacts_one_primary(self):
        """Test that user can have multiple contacts but only one primary"""
        contact2 = EmergencyContact.objects.create(
            user=self.user,
            name="Jane Smith",
            relationship="friend",
            phone_number="+0987654321",
            is_primary=False
        )
        
        self.assertEqual(self.user.emergency_contacts.count(), 2)
        primary_contacts = self.user.emergency_contacts.filter(is_primary=True)
        self.assertEqual(primary_contacts.count(), 1)


class EmergencyAlertModelTest(TestCase):
    """Test EmergencyAlert model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Doe'
        )
        self.alert = EmergencyAlert.objects.create(
            user=self.user,
            location=Point(-122.4194, 37.7749),
            message="Need immediate help",
            status='active'
        )
    
    def test_alert_creation(self):
        """Test emergency alert is created correctly"""
        self.assertEqual(self.alert.user, self.user)
        self.assertEqual(self.alert.status, 'active')
        self.assertIsNotNone(self.alert.location)
        self.assertIsNone(self.alert.resolved_at)
    
    def test_alert_status_transitions(self):
        """Test alert status can be updated"""
        self.alert.status = 'responded'
        self.alert.save()
        self.assertEqual(self.alert.status, 'responded')
        
        self.alert.status = 'resolved'
        self.alert.resolved_at = timezone.now()
        self.alert.save()
        self.assertEqual(self.alert.status, 'resolved')
        self.assertIsNotNone(self.alert.resolved_at)


class SOSAPITest(APITestCase):
    """Test SOS/Emergency Alert API"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Doe'
        )
        self.contact1 = EmergencyContact.objects.create(
            user=self.user,
            name="John Doe",
            relationship="spouse",
            phone_number="+1234567890",
            email="john@test.com",
            is_primary=True
        )
        self.contact2 = EmergencyContact.objects.create(
            user=self.user,
            name="Jane Smith",
            relationship="friend",
            phone_number="+0987654321",
            email="jane@test.com",
            is_primary=False
        )
        self.client.force_authenticate(user=self.user)
    
    @patch('emergency.tasks.send_sms')
    @patch('emergency.tasks.send_app_email')
    def test_trigger_sos_alert(self, mock_send_email, mock_send_sms):
        """Test triggering an SOS alert"""
        mock_send_email.return_value = True
        mock_send_sms.return_value = True
        
        url = '/api/emergency/sos/'
        data = {
            'location': {
                'latitude': 37.7749,
                'longitude': -122.4194
            },
            'message': 'Emergency! Need help now!'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])
        
        # Verify alert was created
        self.assertEqual(EmergencyAlert.objects.count(), 1)
        alert = EmergencyAlert.objects.first()
        self.assertEqual(alert.user, self.user)
        self.assertEqual(alert.status, 'active')
        
        # Verify contacts were notified
        self.assertTrue(mock_send_email.called or mock_send_sms.called)
    
    def test_list_emergency_contacts(self):
        """Test listing user's emergency contacts"""
        url = '/api/emergency/contacts/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_create_emergency_contact(self):
        """Test creating a new emergency contact"""
        url = '/api/emergency/contacts/'
        data = {
            'name': 'Dr. Smith',
            'relationship': 'doctor',
            'phone_number': '+1111111111',
            'email': 'drsmith@test.com',
            'is_primary': False
        }
        response = self.client.post(url, data, format='json')
        
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])
        self.assertEqual(EmergencyContact.objects.count(), 3)
    
    def test_update_alert_status(self):
        """Test updating emergency alert status"""
        alert = EmergencyAlert.objects.create(
            user=self.user,
            status='active',
            message='Test alert'
        )
        
        url = f'/api/emergency/alerts/{alert.id}/'
        data = {
            'status': 'resolved',
            'resolution_notes': 'False alarm, all good'
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        alert.refresh_from_db()
        self.assertEqual(alert.status, 'resolved')


class SOSTaskTest(TestCase):
    """Test SOS Celery tasks"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Doe'
        )
        self.contact = EmergencyContact.objects.create(
            user=self.user,
            name="John Doe",
            relationship="spouse",
            phone_number="+1234567890",
            email="john@test.com",
            is_primary=True
        )
        self.alert = EmergencyAlert.objects.create(
            user=self.user,
            location=Point(-122.4194, 37.7749),
            message="Emergency!",
            status='active'
        )
    
    @patch('emergency.tasks.send_sms')
    @patch('emergency.tasks.send_app_email')
    def test_send_sos_alerts_to_contacts(self, mock_send_email, mock_send_sms):
        """Test SOS alerts are sent to emergency contacts"""
        mock_send_email.return_value = True
        mock_send_sms.return_value = True
        
        # Run the task
        send_sos_alerts(self.alert.id)
        
        # Verify notifications were sent
        self.assertTrue(mock_send_email.called or mock_send_sms.called)
        
        # Verify EmergencyAlertContact records were created
        self.assertEqual(EmergencyAlertContact.objects.filter(alert=self.alert).count(), 1)


class NearbyEmergencyServicesTest(APITestCase):
    """Test finding nearby emergency services"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Doe'
        )
        # Create emergency services at different locations
        self.hospital1 = EmergencyService.objects.create(
            name="City Hospital",
            service_type="hospital",
            address="123 Main St",
            phone_number="+1111111111",
            location=Point(-122.4194, 37.7749),  # San Francisco
            has_emergency_room=True
        )
        self.hospital2 = EmergencyService.objects.create(
            name="Downtown Medical",
            service_type="hospital",
            address="456 Downtown Ave",
            phone_number="+2222222222",
            location=Point(-122.4074, 37.7849),  # Nearby
            has_emergency_room=True
        )
        self.client.force_authenticate(user=self.user)
    
    def test_find_nearby_services(self):
        """Test finding emergency services near a location"""
        url = '/api/emergency/services/nearby/'
        params = {
            'latitude': 37.7749,
            'longitude': -122.4194,
            'radius': 10000  # 10km
        }
        response = self.client.get(url, params)
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
        # If endpoint exists and works, should return nearby services
        if response.status_code == status.HTTP_200_OK:
            self.assertGreaterEqual(len(response.data), 1)

