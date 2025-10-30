#!/usr/bin/env python
"""Create simple test accounts with easy-to-remember credentials"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vitanips.settings')
django.setup()

from django.contrib.auth import get_user_model
from doctors.models import Doctor, Specialty
from pharmacy.models import Pharmacy

User = get_user_model()

print('\n🆕 CREATING SIMPLE TEST ACCOUNTS...')
print('=' * 60)

# 1. Simple Doctor Account
print('\n1️⃣  Creating Simple Doctor Account:')
doc_user, created = User.objects.get_or_create(
    email='doctor@test.com',
    defaults={
        'username': 'doctor',
        'first_name': 'John',
        'last_name': 'Smith'
    }
)
doc_user.set_password('testpass123')
doc_user.save()

# Create doctor profile if doesn't exist
if not hasattr(doc_user, 'doctor_profile') or doc_user.doctor_profile is None:
    specialty = Specialty.objects.first()
    doctor_profile = Doctor.objects.create(
        user=doc_user,
        first_name='John',
        last_name='Smith',
        gender='M',
        years_of_experience=10,
        education='MD from Medical University',
        bio='Experienced general practitioner',
        consultation_fee=50.00,
        is_verified=True
    )
    if specialty:
        doctor_profile.specialties.add(specialty)
    print(f'   ✅ Email: doctor@test.com')
    print(f'   ✅ Password: testpass123')
    print(f'   ✅ Status: Created with doctor profile')
else:
    print(f'   ✅ Email: doctor@test.com')
    print(f'   ✅ Password: testpass123')
    print(f'   ✅ Status: Updated (profile already exists)')

# 2. Simple Patient Account
print('\n2️⃣  Creating Simple Patient Account:')
patient, created = User.objects.get_or_create(
    email='patient@test.com',
    defaults={
        'username': 'patient',
        'first_name': 'Jane',
        'last_name': 'Doe',
        'phone_number': '+1234567890'
    }
)
patient.set_password('testpass123')
patient.is_staff = False
patient.is_pharmacy_staff = False
patient.save()
print(f'   ✅ Email: patient@test.com')
print(f'   ✅ Password: testpass123')
print(f'   ✅ Status: {"Created" if created else "Updated"}')

print('\n' + '=' * 60)
print('✅ SIMPLE ACCOUNTS CREATED!')
print('=' * 60)

print('\n📋 ALL AVAILABLE TEST ACCOUNTS:')
print('=' * 60)
print('\n🔑 EASY TO REMEMBER:')
print('   Admin:    admin@test.com / testpass123')
print('   Doctor:   doctor@test.com / testpass123')
print('   Pharmacy: pharmacy@test.com / testpass123')
print('   Patient:  patient@test.com / testpass123')

print('\n🔑 ADDITIONAL ACCOUNTS:')
print('   Doctor:   user0_christianperez@example.com / testpass123')
print('   Patient:  user8_swalker@example.com / testpass123')

print('\n' + '=' * 60)
print()
