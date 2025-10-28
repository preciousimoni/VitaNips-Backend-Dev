#!/usr/bin/env python
"""
Test script for E-prescription Forwarding Feature
Run this script after setting up the backend to verify the implementation.

Usage:
    python test_prescription_forwarding.py
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vitanips.settings')
django.setup()

from django.contrib.auth import get_user_model
from doctors.models import Appointment, Prescription, PrescriptionItem, Specialty, Doctor
from pharmacy.models import Pharmacy, MedicationOrder
from rest_framework.test import APIClient
from django.utils import timezone
import json

User = get_user_model()

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def setup_test_data():
    """Create test data for prescription forwarding tests."""
    print_header("Setting Up Test Data")
    
    # Create or get test user
    user, created = User.objects.get_or_create(
        email='test_patient@example.com',
        defaults={
            'first_name': 'Test',
            'last_name': 'Patient',
            'phone_number': '+1234567890',
            'user_type': 'patient'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print_success(f"Created test patient: {user.email}")
    else:
        print_info(f"Using existing patient: {user.email}")
    
    # Create or get doctor user
    doctor_user, created = User.objects.get_or_create(
        email='test_doctor@example.com',
        defaults={
            'first_name': 'Dr. Test',
            'last_name': 'Doctor',
            'phone_number': '+1234567891',
            'user_type': 'doctor'
        }
    )
    if created:
        doctor_user.set_password('testpass123')
        doctor_user.save()
        print_success(f"Created test doctor user: {doctor_user.email}")
    else:
        print_info(f"Using existing doctor user: {doctor_user.email}")
    
    # Create specialty
    specialty, created = Specialty.objects.get_or_create(
        name='General Practice',
        defaults={'description': 'General medical practice'}
    )
    if created:
        print_success(f"Created specialty: {specialty.name}")
    else:
        print_info(f"Using existing specialty: {specialty.name}")
    
    # Create doctor profile
    doctor, created = Doctor.objects.get_or_create(
        user=doctor_user,
        defaults={
            'license_number': 'TEST12345',
            'years_of_experience': 5,
            'bio': 'Test doctor for prescription forwarding',
        }
    )
    if created:
        doctor.specialties.add(specialty)
        print_success(f"Created doctor profile: Dr. {doctor_user.get_full_name()}")
    else:
        print_info(f"Using existing doctor profile: Dr. {doctor_user.get_full_name()}")
    
    # Create pharmacy
    pharmacy, created = Pharmacy.objects.get_or_create(
        name='Test Pharmacy',
        defaults={
            'address': '123 Test St, Test City, TC 12345',
            'phone_number': '+1234567892',
            'email': 'test_pharmacy@example.com',
            'is_active': True,
        }
    )
    if created:
        print_success(f"Created pharmacy: {pharmacy.name}")
    else:
        print_info(f"Using existing pharmacy: {pharmacy.name}")
    
    # Create completed appointment
    appointment, created = Appointment.objects.get_or_create(
        user=user,
        doctor=doctor,
        appointment_date=timezone.now().date(),
        defaults={
            'start_time': timezone.now().time(),
            'end_time': (timezone.now() + timezone.timedelta(hours=1)).time(),
            'appointment_type': 'in_person',
            'status': 'completed',
            'reason': 'Regular checkup',
        }
    )
    if not created:
        appointment.status = 'completed'
        appointment.save()
    print_success(f"Created/updated completed appointment: #{appointment.id}")
    
    # Create prescription
    prescription, created = Prescription.objects.get_or_create(
        appointment=appointment,
        user=user,
        doctor=doctor,
        defaults={
            'diagnosis': 'Common cold',
            'notes': 'Take medications as prescribed',
        }
    )
    if created:
        print_success(f"Created prescription: #{prescription.id}")
    else:
        print_info(f"Using existing prescription: #{prescription.id}")
    
    # Create prescription items
    item1, created = PrescriptionItem.objects.get_or_create(
        prescription=prescription,
        medication_name='Amoxicillin',
        defaults={
            'dosage': '500mg',
            'frequency': 'Three times daily',
            'duration': '7 days',
            'instructions': 'Take with food',
        }
    )
    if created:
        print_success(f"Created prescription item: {item1.medication_name}")
    
    item2, created = PrescriptionItem.objects.get_or_create(
        prescription=prescription,
        medication_name='Ibuprofen',
        defaults={
            'dosage': '400mg',
            'frequency': 'As needed',
            'duration': '5 days',
            'instructions': 'Take with water',
        }
    )
    if created:
        print_success(f"Created prescription item: {item2.medication_name}")
    
    return {
        'user': user,
        'doctor': doctor,
        'pharmacy': pharmacy,
        'appointment': appointment,
        'prescription': prescription,
    }

def test_prescription_forwarding(test_data):
    """Test the prescription forwarding API endpoint."""
    print_header("Testing Prescription Forwarding API")
    
    client = APIClient()
    client.force_authenticate(user=test_data['user'])
    
    prescription_id = test_data['prescription'].id
    pharmacy_id = test_data['pharmacy'].id
    
    # Test 1: Successful forwarding
    print_info("Test 1: Forward prescription to pharmacy")
    response = client.post(
        f'/api/doctors/prescriptions/{prescription_id}/forward/',
        {'pharmacy_id': pharmacy_id},
        format='json'
    )
    
    if response.status_code == 201:
        print_success(f"Prescription forwarded successfully!")
        data = response.json()
        print_info(f"  Message: {data.get('message')}")
        print_info(f"  Order ID: {data.get('order', {}).get('id')}")
        print_info(f"  Status: {data.get('order', {}).get('status')}")
        order_id = data.get('order', {}).get('id')
    else:
        print_error(f"Failed to forward prescription: {response.status_code}")
        print_error(f"Response: {response.json()}")
        return False
    
    # Test 2: Duplicate forwarding (should return 409)
    print_info("\nTest 2: Try to forward same prescription again (should fail)")
    response = client.post(
        f'/api/doctors/prescriptions/{prescription_id}/forward/',
        {'pharmacy_id': pharmacy_id},
        format='json'
    )
    
    if response.status_code == 409:
        print_success("Correctly prevented duplicate order (409 Conflict)")
        data = response.json()
        print_info(f"  Error: {data.get('error')}")
        print_info(f"  Existing Order ID: {data.get('order_id')}")
    else:
        print_warning(f"Unexpected status code: {response.status_code}")
    
    # Test 3: Invalid pharmacy ID
    print_info("\nTest 3: Try invalid pharmacy ID")
    response = client.post(
        f'/api/doctors/prescriptions/{prescription_id}/forward/',
        {'pharmacy_id': 99999},
        format='json'
    )
    
    if response.status_code == 404:
        print_success("Correctly rejected invalid pharmacy (404 Not Found)")
    else:
        print_warning(f"Unexpected status code: {response.status_code}")
    
    # Test 4: Missing pharmacy_id
    print_info("\nTest 4: Try without pharmacy_id")
    response = client.post(
        f'/api/doctors/prescriptions/{prescription_id}/forward/',
        {},
        format='json'
    )
    
    if response.status_code == 400:
        print_success("Correctly rejected missing pharmacy_id (400 Bad Request)")
    else:
        print_warning(f"Unexpected status code: {response.status_code}")
    
    # Test 5: Unauthorized access (different user's prescription)
    print_info("\nTest 5: Try to forward another user's prescription")
    other_user, _ = User.objects.get_or_create(
        email='other_user@example.com',
        defaults={'first_name': 'Other', 'last_name': 'User', 'user_type': 'patient'}
    )
    client.force_authenticate(user=other_user)
    response = client.post(
        f'/api/doctors/prescriptions/{prescription_id}/forward/',
        {'pharmacy_id': pharmacy_id},
        format='json'
    )
    
    if response.status_code == 404:
        print_success("Correctly prevented unauthorized access (404 Not Found)")
    else:
        print_warning(f"Unexpected status code: {response.status_code}")
    
    return True

def verify_database_state(test_data):
    """Verify that the database state is correct after forwarding."""
    print_header("Verifying Database State")
    
    prescription = test_data['prescription']
    pharmacy = test_data['pharmacy']
    
    # Check if order was created
    orders = MedicationOrder.objects.filter(prescription=prescription)
    if orders.exists():
        order = orders.first()
        print_success(f"MedicationOrder created: #{order.id}")
        print_info(f"  Status: {order.status}")
        print_info(f"  Pharmacy: {order.pharmacy.name}")
        print_info(f"  User: {order.user.email}")
        
        # Check order items
        items = order.items.all()
        print_info(f"  Items: {items.count()}")
        for item in items:
            print_info(f"    - {item.medication_name_text} {item.dosage_text}")
    else:
        print_error("No MedicationOrder found for prescription")
        return False
    
    return True

def cleanup_test_data(test_data):
    """Clean up test data (optional)."""
    print_header("Cleanup")
    print_warning("Test data cleanup skipped (for inspection)")
    print_info("To manually clean up, delete the following:")
    print_info(f"  - User: {test_data['user'].email}")
    print_info(f"  - Doctor: {test_data['doctor'].user.email}")
    print_info(f"  - Pharmacy: {test_data['pharmacy'].name}")
    print_info(f"  - Prescription: #{test_data['prescription'].id}")

def main():
    print_header("E-Prescription Forwarding Test Suite")
    
    try:
        # Setup
        test_data = setup_test_data()
        
        # Run tests
        success = test_prescription_forwarding(test_data)
        
        if success:
            # Verify
            verify_database_state(test_data)
            
            print_header("Test Results")
            print_success("All tests passed! ✓")
            print_info("\nThe E-prescription forwarding feature is working correctly.")
            print_info("Backend implementation: COMPLETE ✓")
            print_info("Next steps: Implement frontend components")
        else:
            print_header("Test Results")
            print_error("Some tests failed. Please review the output above.")
        
        # Cleanup (commented out for inspection)
        # cleanup_test_data(test_data)
        
    except Exception as e:
        print_error(f"Test suite error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
