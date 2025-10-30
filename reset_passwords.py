#!/usr/bin/env python
"""Reset test account passwords"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vitanips.settings')
django.setup()

from django.contrib.auth import get_user_model
from doctors.models import Doctor
from pharmacy.models import Pharmacy

User = get_user_model()

print('\n🔧 RESETTING TEST ACCOUNT PASSWORDS...')
print('=' * 60)

# 1. Reset/Create Admin
print('\n1️⃣  ADMIN ACCOUNT:')
admin, created = User.objects.get_or_create(
    email='admin@test.com',
    defaults={
        'username': 'admin',
        'first_name': 'Admin',
        'last_name': 'User',
        'is_staff': True,
        'is_superuser': True
    }
)
admin.set_password('testpass123')
admin.is_staff = True
admin.is_superuser = True
admin.save()
print(f'   ✅ Email: admin@test.com')
print(f'   ✅ Password: testpass123')
print(f'   ✅ Status: {"Created" if created else "Updated"}')

# 2. Reset Doctor Password
print('\n2️⃣  DOCTOR ACCOUNT:')
doctor = Doctor.objects.select_related('user').first()
if doctor and doctor.user:
    doctor.user.set_password('testpass123')
    doctor.user.save()
    print(f'   ✅ Email: {doctor.user.email}')
    print(f'   ✅ Username: {doctor.user.username}')
    print(f'   ✅ Password: testpass123')
    print(f'   ✅ Doctor: Dr. {doctor.first_name} {doctor.last_name}')
else:
    print('   ❌ No doctor found')

# 3. Reset Pharmacy Staff
print('\n3️⃣  PHARMACY ACCOUNT:')
pharmacy_staff = User.objects.filter(email='pharmacy@test.com').first()
if pharmacy_staff:
    pharmacy_staff.set_password('testpass123')
    pharmacy_staff.save()
    print(f'   ✅ Email: pharmacy@test.com')
    print(f'   ✅ Password: testpass123')
else:
    # Create if doesn't exist
    pharmacy = Pharmacy.objects.first()
    if pharmacy:
        pharmacy_staff = User.objects.create_user(
            email='pharmacy@test.com',
            username='pharmacystaff',
            password='testpass123',
            first_name='John',
            last_name='Pharmacist',
            is_pharmacy_staff=True,
            works_at_pharmacy=pharmacy
        )
        print(f'   ✅ Email: pharmacy@test.com')
        print(f'   ✅ Password: testpass123')
        print(f'   ✅ Status: Created')
    else:
        print('   ❌ No pharmacy found to assign staff')

# 4. Reset Patient Password
print('\n4️⃣  PATIENT ACCOUNT:')
patient = User.objects.filter(
    is_staff=False,
    is_pharmacy_staff=False,
    doctor_profile__isnull=True
).first()
if patient:
    patient.set_password('testpass123')
    patient.save()
    print(f'   ✅ Email: {patient.email}')
    print(f'   ✅ Username: {patient.username}')
    print(f'   ✅ Password: testpass123')
    print(f'   ✅ Name: {patient.first_name} {patient.last_name}')
else:
    print('   ❌ No patient found')

print('\n' + '=' * 60)
print('✅ PASSWORD RESET COMPLETE!')
print('=' * 60)

# Print summary
print('\n📋 UPDATED CREDENTIALS:')
print('-' * 60)
print('Admin:    admin@test.com / testpass123')
if doctor and doctor.user:
    print(f'Doctor:   {doctor.user.email} / testpass123')
if pharmacy_staff:
    print('Pharmacy: pharmacy@test.com / testpass123')
if patient:
    print(f'Patient:  {patient.email} / testpass123')
print('-' * 60)
print()
