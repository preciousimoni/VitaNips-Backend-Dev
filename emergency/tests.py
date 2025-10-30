# emergency/tests.py
from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import EmergencyContact, EmergencyAlert, EmergencyAlertContact
from .tasks import send_sos_alerts_task

User = get_user_model()


class TriggerSOSTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="sosuser@example.com",
            username="sosuser",
            password="password123"
        )
        self.client: APIClient = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('emergency.views.send_sos_alerts_task')
    def test_trigger_sos_accepted_when_task_enqueued(self, mock_task):
        # Simulate successful queuing
        mock_task.delay.return_value = None

        url = reverse('emergency-trigger-sos')
        payload = {"latitude": 6.5244, "longitude": 3.3792}
        resp = self.client.post(url, data=payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('status', resp.data)
        mock_task.delay.assert_called_once()

    def test_trigger_sos_missing_coords(self):
        url = reverse('emergency-trigger-sos')
        resp = self.client.post(url, data={}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', resp.data)


class EmergencyContactModelTest(TestCase):
    """Test EmergencyContact model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_emergency_contact(self):
        """Test creating an emergency contact"""
        contact = EmergencyContact.objects.create(
            user=self.user,
            name='John Doe',
            relationship='Brother',
            phone_number='+1234567890',
            email='john@example.com',
            is_primary=True
        )
        
        self.assertEqual(contact.user, self.user)
        self.assertEqual(contact.name, 'John Doe')
        self.assertEqual(contact.relationship, 'Brother')
        self.assertTrue(contact.is_primary)
    
    def test_emergency_contact_string_representation(self):
        """Test __str__ method"""
        contact = EmergencyContact.objects.create(
            user=self.user,
            name='Jane Smith',
            relationship='Mother',
            phone_number='+1234567890'
        )
        expected = f"{contact.name} ({contact.relationship}) - {self.user.username}"
        self.assertEqual(str(contact), expected)


class SOSAlertsTaskTest(TestCase):
    """Test send_sos_alerts_task Celery task"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.contact1 = EmergencyContact.objects.create(
            user=self.user,
            name='Contact One',
            relationship='Friend',
            phone_number='+1234567890',
            is_primary=True
        )
        self.contact2 = EmergencyContact.objects.create(
            user=self.user,
            name='Contact Two',
            relationship='Family',
            phone_number='+0987654321',
            is_primary=False
        )
        self.latitude = 6.5244
        self.longitude = 3.3792
    
    @patch('emergency.tasks.twilio_client')
    def test_sos_task_sends_to_all_contacts(self, mock_twilio):
        """Test that SOS task sends SMS to all emergency contacts"""
        # Mock Twilio message creation
        mock_message = MagicMock()
        mock_message.sid = 'SM123456789'
        mock_message.status = 'queued'
        mock_twilio.messages.create.return_value = mock_message
        
        # Run the task
        result = send_sos_alerts_task(
            user_id=self.user.id,
            latitude=self.latitude,
            longitude=self.longitude,
            message="Help! Emergency!"
        )
        
        # Verify Twilio was called twice (once per contact)
        self.assertEqual(mock_twilio.messages.create.call_count, 2)
        
        # Verify alert was created
        alert = EmergencyAlert.objects.get(user=self.user)
        self.assertEqual(alert.status, 'responded')
        self.assertIn(str(self.longitude), str(alert.location.coords))
        self.assertIn(str(self.latitude), str(alert.location.coords))
        
        # Verify alert contacts were logged
        alert_contacts = EmergencyAlertContact.objects.filter(alert=alert)
        self.assertEqual(alert_contacts.count(), 2)
        
        # Verify result message
        self.assertIn('Sent: 2', result)
        self.assertIn('Failed: 0', result)
    
    def test_sos_task_no_contacts(self):
        """Test SOS task when user has no emergency contacts"""
        # Create user without contacts
        user_no_contacts = User.objects.create_user(
            username='nocontacts',
            email='nocontacts@example.com',
            password='testpass123'
        )
        
        result = send_sos_alerts_task(
            user_id=user_no_contacts.id,
            latitude=self.latitude,
            longitude=self.longitude
        )
        
        # Verify alert was created but marked as resolved
        alert = EmergencyAlert.objects.get(user=user_no_contacts)
        self.assertEqual(alert.status, 'resolved')
        self.assertIn('No emergency contacts', alert.resolution_notes)
        
        # Verify result message
        self.assertIn('has no contacts', result)
    
    @patch('emergency.tasks.twilio_client')
    def test_sos_task_partial_failure(self, mock_twilio):
        """Test SOS task when some messages fail to send"""
        # Mock Twilio to succeed for first, fail for second
        def side_effect(*args, **kwargs):
            if kwargs['to'] == self.contact1.phone_number:
                mock_msg = MagicMock()
                mock_msg.sid = 'SM123'
                mock_msg.status = 'sent'
                return mock_msg
            else:
                from twilio.base.exceptions import TwilioRestException
                raise TwilioRestException(
                    status=400,
                    uri='/Messages',
                    msg='Invalid phone number'
                )
        
        mock_twilio.messages.create.side_effect = side_effect
        
        result = send_sos_alerts_task(
            user_id=self.user.id,
            latitude=self.latitude,
            longitude=self.longitude
        )
        
        # Verify result shows partial success
        self.assertIn('Sent: 1', result)
        self.assertIn('Failed: 1', result)
        
        # Verify alert status
        alert = EmergencyAlert.objects.get(user=self.user)
        self.assertEqual(alert.status, 'responded')
        self.assertIn('failed for 1', alert.resolution_notes)
    
    def test_sos_task_user_not_found(self):
        """Test SOS task with non-existent user"""
        result = send_sos_alerts_task(
            user_id=99999,  # Non-existent user ID
            latitude=self.latitude,
            longitude=self.longitude
        )
        
        self.assertIn('not found', result)
    
    @patch('emergency.tasks.twilio_client', None)
    def test_sos_task_twilio_not_configured(self):
        """Test SOS task when Twilio is not configured"""
        result = send_sos_alerts_task(
            user_id=self.user.id,
            latitude=self.latitude,
            longitude=self.longitude
        )
        
        # Verify alert was created but marked as resolved
        alert = EmergencyAlert.objects.get(user=self.user)
        self.assertEqual(alert.status, 'resolved')
        self.assertIn('Twilio service not configured', alert.resolution_notes)
        
        # Verify contacts were logged with failed status
        alert_contacts = EmergencyAlertContact.objects.filter(alert=alert)
        for ac in alert_contacts:
            self.assertEqual(ac.delivery_status, 'failed_config')
    
    @patch('emergency.tasks.twilio_client')
    def test_sos_task_with_custom_message(self, mock_twilio):
        """Test SOS task includes custom message in SMS"""
        mock_message = MagicMock()
        mock_message.sid = 'SM123'
        mock_message.status = 'queued'
        mock_twilio.messages.create.return_value = mock_message
        
        custom_msg = "Car accident at Main St"
        send_sos_alerts_task(
            user_id=self.user.id,
            latitude=self.latitude,
            longitude=self.longitude,
            message=custom_msg
        )
        
        # Verify custom message was included in SMS body
        call_args = mock_twilio.messages.create.call_args_list[0]
        sms_body = call_args[1]['body']
        self.assertIn(custom_msg, sms_body)
        self.assertIn('SOS Alert', sms_body)
        self.assertIn('Test User', sms_body)


class EmergencyAlertModelTest(TestCase):
    """Test EmergencyAlert model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_emergency_alert(self):
        """Test creating an emergency alert"""
        location = Point(3.3792, 6.5244, srid=4326)
        alert = EmergencyAlert.objects.create(
            user=self.user,
            location=location,
            message='Help needed',
            status='active'
        )
        
        self.assertEqual(alert.user, self.user)
        self.assertEqual(alert.status, 'active')
        self.assertEqual(alert.message, 'Help needed')
        self.assertIsNotNone(alert.triggered_at)
    
    def test_emergency_alert_status_choices(self):
        """Test all valid status choices"""
        location = Point(3.3792, 6.5244, srid=4326)
        alert = EmergencyAlert.objects.create(
            user=self.user,
            location=location,
            status='active'
        )
        
        for status_choice in ['active', 'responded', 'resolved']:
            alert.status = status_choice
            alert.save()
            alert.refresh_from_db()
            self.assertEqual(alert.status, status_choice)

